@tool
extends RefCounted


static func _apply_skinning(
	poly: Polygon2D,
	skeleton: Skeleton2D,
	weights_data: Array,
) -> void:
	# Wire Polygon2D.skeleton + per-bone weight arrays. Each entry in
	# weights_data is `{bone, values[]}` from the .proscenio document.
	# Bones whose name does not resolve under the skeleton are reported
	# and skipped — the rest of the rig still imports.
	poly.skeleton = poly.get_path_to(skeleton)
	poly.clear_bones()
	for weight_entry in weights_data:
		var bone_name: String = weight_entry.get("bone", "")
		var bone_node := skeleton.find_child(bone_name, true, false)
		if bone_node == null:
			push_error(
				(
					"Proscenio: sprite '%s' weight entry references missing bone '%s' — skipping."
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

		var uv_pts: Array = sprite_data.get("uv", [])
		var uvs := PackedVector2Array()
		# .proscenio stores UVs normalized [0, 1] — engine-agnostic. Godot's
		# Polygon2D expects UVs in texture pixel space, so multiply by atlas
		# size at import time. Sprites without an atlas keep raw UVs.
		var uv_scale := Vector2.ONE
		if atlas != null:
			uv_scale = atlas.get_size()
		for u in uv_pts:
			uvs.append(Vector2(u[0] * uv_scale.x, u[1] * uv_scale.y))
		poly.uv = uvs

		if atlas != null:
			poly.texture = atlas

		var weights_data: Array = sprite_data.get("weights", [])
		var is_skinned: bool = not weights_data.is_empty()

		var bone_name: String = sprite_data.get("bone", "")
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
