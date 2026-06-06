@tool
extends RefCounted

const NodeNameUtil := preload("res://addons/proscenio/builders/node_name_util.gd")
const SpriteAttachUtil := preload("res://addons/proscenio/builders/sprite_attach_util.gd")


static func _apply_skinning(
	poly: Polygon2D,
	skeleton: Skeleton2D,
	weights: Array[ProscenioWeight],
) -> void:
	# Wire Polygon2D.skeleton + per-bone weight arrays. Each Weight entry
	# from the .proscenio document carries `{bone, values[]}`. Bones whose
	# name does not resolve under the skeleton are reported and skipped;
	# the rest of the rig still imports.
	poly.skeleton = poly.get_path_to(skeleton)
	poly.clear_bones()
	for weight in weights:
		var bone_name := NodeNameUtil.sanitize(weight.bone)
		var bone_node := skeleton.find_child(bone_name, true, false)
		if bone_node == null:
			push_error(
				(
					"Proscenio: sprite '%s' weight entry references missing bone '%s' - skipping."
					% [poly.name, bone_name]
				)
			)
			continue
		var packed := PackedFloat32Array(weight.values)
		poly.add_bone(poly.get_path_to(bone_node), packed)


static func attach_sprites(
	skeleton: Skeleton2D,
	sprites: Array[ProscenioSprite],
	atlas: Texture2D,
	slot_map: Dictionary = {},
	source_dir: String = "",
) -> void:
	if sprites == null:
		return
	for sprite_res: ProscenioSprite in sprites:
		# Discriminator dispatch: this builder only handles polygon sprites.
		# Default to ProscenioPolygonSprite when `type` is absent (v1 backwards-compat).
		if not (sprite_res is ProscenioPolygonSprite):
			continue
		_build_polygon(sprite_res as ProscenioPolygonSprite, skeleton, atlas, slot_map, source_dir)


static func _build_polygon(
	sprite: ProscenioPolygonSprite,
	skeleton: Skeleton2D,
	atlas: Texture2D,
	slot_map: Dictionary,
	source_dir: String,
) -> void:
	var poly := Polygon2D.new()
	poly.name = sprite.name

	var pts := PackedVector2Array()
	for p: PackedFloat32Array in sprite.polygon:
		pts.append(Vector2(p[0], p[1]))
	poly.polygon = pts

	var sprite_tex := SpriteAttachUtil.resolve_sprite_texture(
		sprite.texture, sprite.name, atlas, source_dir
	)

	var uvs := PackedVector2Array()
	# .proscenio stores UVs normalized [0, 1] - engine-agnostic. Godot's
	# Polygon2D expects UVs in texture pixel space, so multiply by the
	# resolved texture's size at import time. Sprites without a texture
	# keep raw UVs.
	var uv_scale := Vector2.ONE
	if sprite_tex != null:
		uv_scale = sprite_tex.get_size()
	for u: PackedFloat32Array in sprite.uv:
		uvs.append(Vector2(u[0] * uv_scale.x, u[1] * uv_scale.y))
	poly.uv = uvs

	if sprite_tex != null:
		poly.texture = sprite_tex

	var weights: Array[ProscenioWeight] = sprite.weights
	var is_skinned: bool = weights != null and not weights.is_empty()

	var bone_name := NodeNameUtil.sanitize(sprite.bone)
	# Slot routing (shared with sprite_frame_builder via sprite_attach_util):
	# slot attachment wins; otherwise rigid polygons parent to their Bone2D,
	# while skinned polygons stay under the skeleton (weights drive deform).
	# Lookup uses ``poly.name`` (already Godot-sanitized via Node.name set).
	var sanitized_name := String(poly.name)
	var routing := SpriteAttachUtil.resolve_sprite_parent(
		skeleton, sanitized_name, bone_name, slot_map, not is_skinned
	)
	poly.visible = routing.visible
	routing.node.add_child(poly)

	if is_skinned:
		_apply_skinning(poly, skeleton, weights)
