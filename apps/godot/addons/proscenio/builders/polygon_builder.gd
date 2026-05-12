@tool
extends RefCounted

const NodeNameUtil := preload("res://addons/proscenio/builders/node_name_util.gd")


static func _resolve_sprite_texture(
	sprite_data: Dictionary,
	fallback_atlas: Texture2D,
	source_dir: String,
) -> Texture2D:
	# Per-sprite texture resolution order:
	# 1. sprite.texture field (writer emits it when the mesh has an Image
	#    Texture on its material) - load <source_dir>/<filename>.
	# 2. <sprite.name>.png next to the .proscenio - filename-by-convention
	#    fallback for fixtures (doll) whose materials carry flat colors but
	#    whose body parts ship as separate PNGs alongside the document.
	# 3. fallback_atlas - the scene-wide single-image case.
	var per_sprite: String = sprite_data.get("texture", "")
	if per_sprite != "" and source_dir != "":
		var path := source_dir.path_join(per_sprite)
		if ResourceLoader.exists(path):
			return ResourceLoader.load(path, "Texture2D") as Texture2D
	if source_dir != "":
		var by_name := source_dir.path_join("%s.png" % sprite_data.get("name", ""))
		if ResourceLoader.exists(by_name):
			return ResourceLoader.load(by_name, "Texture2D") as Texture2D
	return fallback_atlas


static func _apply_skinning(
	poly: Polygon2D,
	skeleton: Skeleton2D,
	weights_data: Array,
) -> void:
	# Wire Polygon2D.skeleton + per-bone weight arrays. Each entry in
	# weights_data is `{bone, values[]}` from the .proscenio document.
	# Bones whose name does not resolve under the skeleton are reported
	# and skipped - the rest of the rig still imports.
	poly.skeleton = poly.get_path_to(skeleton)
	poly.clear_bones()
	for weight_entry in weights_data:
		var bone_name: String = NodeNameUtil.sanitize(weight_entry.get("bone", ""))
		var bone_node := skeleton.find_child(bone_name, true, false)
		if bone_node == null:
			push_error(
				(
					"Proscenio: sprite '%s' weight entry references missing bone '%s' - skipping."
					% [poly.name, bone_name]
				)
			)
			continue
		var values: Array = weight_entry.get("values", [])
		var packed := PackedFloat32Array()
		packed.resize(values.size())
		for i in range(values.size()):
			packed[i] = float(values[i])
		poly.add_bone(poly.get_path_to(bone_node), packed)


static func attach_sprites(
	skeleton: Skeleton2D,
	sprites_data: Array,
	atlas: Texture2D,
	slot_map: Dictionary = {},
	source_dir: String = "",
) -> void:
	for sprite_data in sprites_data:
		# Discriminator dispatch: this builder only handles polygon sprites.
		# Default to "polygon" when `type` is absent (v1 backwards-compat).
		var sprite_type: String = sprite_data.get("type", "polygon")
		if sprite_type != "polygon":
			continue

		var poly := Polygon2D.new()
		poly.name = sprite_data.get("name", "sprite")

		var polygon_pts: Array = sprite_data.get("polygon", [])
		var pts := PackedVector2Array()
		for p in polygon_pts:
			pts.append(Vector2(p[0], p[1]))
		poly.polygon = pts

		var sprite_tex := _resolve_sprite_texture(sprite_data, atlas, source_dir)

		var uv_pts: Array = sprite_data.get("uv", [])
		var uvs := PackedVector2Array()
		# .proscenio stores UVs normalized [0, 1] - engine-agnostic. Godot's
		# Polygon2D expects UVs in texture pixel space, so multiply by the
		# resolved texture's size at import time. Sprites without a texture
		# keep raw UVs.
		var uv_scale := Vector2.ONE
		if sprite_tex != null:
			uv_scale = sprite_tex.get_size()
		for u in uv_pts:
			uvs.append(Vector2(u[0] * uv_scale.x, u[1] * uv_scale.y))
		poly.uv = uvs

		if sprite_tex != null:
			poly.texture = sprite_tex

		var weights_data: Array = sprite_data.get("weights", [])
		var is_skinned: bool = not weights_data.is_empty()

		var bone_name: String = NodeNameUtil.sanitize(sprite_data.get("bone", ""))
		# Slot routing (SPEC 004 D6): sprites whose name appears in a slot's
		# attachments[] reparent under the slot Node2D and inherit visibility
		# from the slot's default. Otherwise: skinned polygons live under the
		# skeleton (per-vertex weights drive deformation), rigid polygons stay
		# parented to the matching Bone2D so the bone transform carries them.
		# Lookup uses ``poly.name`` (already Godot-sanitized via Node.name set);
		# slot_map keys are sanitized in slot_builder for consistency.
		var sanitized_name: String = String(poly.name)
		var slot_info = slot_map.get(sanitized_name, null)
		var parent: Node
		if slot_info != null:
			parent = slot_info.node
			poly.visible = sanitized_name == slot_info.default
		elif not is_skinned and bone_name != "":
			parent = skeleton
			var found := skeleton.find_child(bone_name, true, false)
			if found != null:
				parent = found
		else:
			parent = skeleton
		parent.add_child(poly)

		if is_skinned:
			_apply_skinning(poly, skeleton, weights_data)
