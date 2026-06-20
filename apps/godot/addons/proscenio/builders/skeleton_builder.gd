@tool
extends RefCounted

const PackedVecUtil := preload("res://addons/proscenio/builders/packed_vec_util.gd")


static func build(skeleton_resource: ProscenioSkeleton) -> Skeleton2D:
	var skeleton := Skeleton2D.new()
	skeleton.name = "Skeleton2D"

	if skeleton_resource == null:
		return skeleton

	# `nodes` aligns by index with `skeleton_resource.bones` so every created
	# Bone2D is parented even when names collide. `by_name` is the parent-lookup
	# dict, keyed by the original JSON name and kept first-wins on a clash.
	var nodes: Array[Bone2D] = []
	var by_name: Dictionary = {}
	for bone_res: ProscenioBone in skeleton_resource.bones:
		var bone := _make_bone(bone_res)
		nodes.append(bone)
		if by_name.has(bone_res.name):
			push_warning(
				(
					(
						"Proscenio: duplicate bone name '%s' - parent lookups resolve to "
						+ "the first; both bone nodes are still built."
					)
					% bone_res.name
				)
			)
		else:
			by_name[bone_res.name] = bone

	for i in skeleton_resource.bones.size():
		var bone_res := skeleton_resource.bones[i]
		var bone := nodes[i]
		var parent: Bone2D = null
		if bone_res.parent != "":
			parent = by_name.get(bone_res.parent)
		if parent == null:
			skeleton.add_child(bone)
		else:
			parent.add_child(bone)

	return skeleton


static func _make_bone(bone_res: ProscenioBone) -> Bone2D:
	var bone := Bone2D.new()
	# Node.name normalizes dots to underscores; the lookup dict keys off the
	# original JSON name so parent resolution uses the unmodified string.
	bone.name = bone_res.name
	bone.position = PackedVecUtil.to_vec2(bone_res.position)
	bone.rotation = bone_res.rotation
	bone.scale = PackedVecUtil.to_vec2_or(bone_res.scale, Vector2.ONE)
	if bone_res.length > 0.0:
		bone.set_length(bone_res.length)
		# Authoritative length supplied - stop Skeleton2D inferring it from
		# (missing) child Bone2D nodes.
		bone.set_autocalculate_length_and_angle(false)
	# Capture authored pose as the rest pose so animations replace it cleanly.
	bone.set_rest(bone.transform)
	return bone
