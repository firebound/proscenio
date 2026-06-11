@tool
extends RefCounted

const NodeNameUtil := preload("res://addons/proscenio/builders/node_name_util.gd")
const SpriteAttachUtil := preload("res://addons/proscenio/builders/sprite_attach_util.gd")


static func _apply_skinning(
	poly: Polygon2D,
	skeleton: Skeleton2D,
	weights: Array[ProscenioWeight],
) -> void:
	# Bones whose name does not resolve under the skeleton are skipped, not
	# fatal - the rest of the rig still imports.
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


static func attach_elements(
	skeleton: Skeleton2D,
	elements: Array[ProscenioElement],
	atlas: Texture2D,
	slot_map: Dictionary = {},
	source_dir: String = "",
) -> void:
	if elements == null:
		return
	for element: ProscenioElement in elements:
		# Handles only ProscenioMeshElement. The "type absent -> mesh" default
		# lives in ProscenioElement.from_dict, not in this filter - change it there.
		if not (element is ProscenioMeshElement):
			continue
		_build_mesh(element as ProscenioMeshElement, skeleton, atlas, slot_map, source_dir)


static func _build_mesh(
	sprite: ProscenioMeshElement,
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

	# Multi-face meshes carry per-face vertex-index arrays (automesh
	# triangulation, multi-island cutouts); Polygon2D.polygons renders each
	# face. Absent or empty means the single `polygon` ring is the whole shape.
	if not sprite.polygons.is_empty():
		var faces: Array = []
		for face: PackedInt32Array in sprite.polygons:
			faces.append(face)
		poly.polygons = faces

	var sprite_tex := SpriteAttachUtil.resolve_sprite_texture(
		sprite.texture, sprite.name, atlas, source_dir
	)

	var uvs := PackedVector2Array()
	# .proscenio UVs are normalized [0, 1]; Polygon2D wants texture pixel
	# space, so scale by texture size. Sprites with no texture keep raw UVs.
	var uv_scale := Vector2.ONE
	if sprite_tex != null:
		uv_scale = sprite_tex.get_size()
	for u: PackedFloat32Array in sprite.uv:
		uvs.append(Vector2(u[0] * uv_scale.x, u[1] * uv_scale.y))
	poly.uv = uvs

	if sprite_tex != null:
		poly.texture = sprite_tex

	# CanvasItem appearance: tint and draw order. An absent modulate keeps
	# Godot's default white; z_index defaults to 0 (the front plane).
	if sprite.modulate.size() >= 4:
		poly.modulate = Color(
			sprite.modulate[0], sprite.modulate[1], sprite.modulate[2], sprite.modulate[3]
		)
	poly.z_index = sprite.z_index

	var weights: Array[ProscenioWeight] = sprite.weights
	var is_skinned: bool = weights != null and not weights.is_empty()

	var bone_name := NodeNameUtil.sanitize(sprite.bone)
	# Slot attachment wins; otherwise rigid meshes parent to their Bone2D while
	# skinned meshes stay under the skeleton (weights drive deform). Lookup uses
	# ``poly.name``, already Godot-sanitized by the Node.name setter.
	var sanitized_name := String(poly.name)
	var routing := SpriteAttachUtil.resolve_sprite_parent(
		skeleton, sanitized_name, bone_name, slot_map, not is_skinned
	)
	poly.visible = routing.visible
	routing.node.add_child(poly)

	if is_skinned:
		_apply_skinning(poly, skeleton, weights)
