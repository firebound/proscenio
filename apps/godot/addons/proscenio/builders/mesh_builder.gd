@tool
extends RefCounted

const NodeNameUtil := preload("res://addons/proscenio/builders/node_name_util.gd")
const PackedVecUtil := preload("res://addons/proscenio/builders/packed_vec_util.gd")
const SpriteAttachUtil := preload("res://addons/proscenio/builders/sprite_attach_util.gd")


static func _apply_skinning(
	poly: Polygon2D,
	skeleton: Skeleton2D,
	weights: Array[ProscenioWeight],
) -> void:
	# Resolve weights BEFORE binding. Binding a Polygon2D to a skeleton with zero
	# resolved bones leaves it skeleton-deformed by nothing and collapses it to a
	# point, so an all-missing-bone mesh stays unbound (a plain rig-root mesh)
	# instead. Bones that do not resolve are skipped, not fatal.
	var bone_paths: Array[NodePath] = []
	var bone_values: Array[PackedFloat32Array] = []
	for weight in weights:
		var bone_name := NodeNameUtil.sanitize(weight.bone)
		var bone_node := skeleton.find_child(bone_name, true, false)
		# find_child matches by name across node types, so a slot Node2D anchor
		# sharing a bone name would resolve here; require a Bone2D so a non-bone
		# match is skipped, not skinned to.
		if not (bone_node is Bone2D):
			push_error(
				(
					"Proscenio: sprite '%s' weight entry references missing bone '%s' - skipping."
					% [poly.name, bone_name]
				)
			)
			continue
		bone_paths.append(poly.get_path_to(bone_node))
		bone_values.append(PackedFloat32Array(weight.values))

	if bone_paths.is_empty():
		push_error(
			(
				"Proscenio: sprite '%s' has no resolvable skin weights - leaving it unbound."
				% poly.name
			)
		)
		return

	poly.skeleton = poly.get_path_to(skeleton)
	poly.clear_bones()
	for i in bone_paths.size():
		poly.add_bone(bone_paths[i], bone_values[i])


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
		pts.append(PackedVecUtil.to_vec2(p))
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
		uvs.append(PackedVecUtil.to_vec2(u) * uv_scale)
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
	if is_skinned:
		# A skinned Polygon2D must be a SIBLING of the Skeleton2D, never its
		# child: when it is a child, Godot's skinning double-applies the skeleton
		# transform and collapses every vertex to a point (the mesh vanishes).
		# Parent it under the skeleton's parent (the rig root) and point its
		# `skeleton` NodePath back at the Skeleton2D. If the Skeleton2D has no
		# parent there is no sibling slot to use; falling back to the skeleton
		# itself would recreate the collapse, so fail clearly instead.
		var host: Node = skeleton.get_parent()
		if host == null:
			push_error(
				(
					(
						"Proscenio: skinned mesh '%s' needs the Skeleton2D to have a parent "
						+ "(the rig root) to attach as a sibling; skipping to avoid a "
						+ "collapsed mesh."
					)
					% poly.name
				)
			)
			poly.queue_free()
			return
		host.add_child(poly)
		_apply_skinning(poly, skeleton, weights)
		return

	# Slot attachment wins; otherwise rigid meshes parent to their Bone2D.
	# Lookup uses ``poly.name``, already Godot-sanitized by the Node.name setter.
	var sanitized_name := String(poly.name)
	var routing := SpriteAttachUtil.resolve_sprite_parent(
		skeleton, sanitized_name, bone_name, slot_map, not is_skinned
	)
	poly.visible = routing.visible
	routing.node.add_child(poly)
