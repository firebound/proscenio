@tool
extends RefCounted


static func build(skeleton_resource: ProscenioSkeleton) -> Skeleton2D:
	var skeleton := Skeleton2D.new()
	skeleton.name = "Skeleton2D"

	if skeleton_resource == null:
		return skeleton

	var bones: Dictionary = {}

	for bone_res: ProscenioBone in skeleton_resource.bones:
		var json_name := bone_res.name
		var bone := Bone2D.new()
		# Node.name normalizes dots to underscores; key the lookup dict by the
		# original JSON name so parent resolution below uses the unmodified string.
		bone.name = json_name
		bone.position = _vec2_from_packed(bone_res.position)
		bone.rotation = bone_res.rotation
		bone.scale = _vec2_from_packed_or(bone_res.scale, Vector2.ONE)
		if bone_res.length > 0.0:
			bone.set_length(bone_res.length)
			# Authoritative length supplied - stop Skeleton2D inferring it from
			# (missing) child Bone2D nodes.
			bone.set_autocalculate_length_and_angle(false)
		# Capture authored pose as the rest pose so animations replace it cleanly.
		bone.set_rest(bone.transform)
		bones[json_name] = bone

	for bone_res: ProscenioBone in skeleton_resource.bones:
		var bone_name := bone_res.name
		var bone: Bone2D = bones[bone_name]
		if bone_res.parent == "":
			skeleton.add_child(bone)
		else:
			var parent: Bone2D = bones.get(bone_res.parent)
			if parent == null:
				skeleton.add_child(bone)
			else:
				parent.add_child(bone)

	return skeleton


static func _vec2_from_packed(arr: PackedFloat32Array) -> Vector2:
	if arr.size() < 2:
		return Vector2.ZERO
	return Vector2(arr[0], arr[1])


static func _vec2_from_packed_or(arr: PackedFloat32Array, fallback: Vector2) -> Vector2:
	if arr.size() < 2:
		return fallback
	return Vector2(arr[0], arr[1])
