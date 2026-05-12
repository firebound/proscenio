@tool
extends RefCounted


static func build(skeleton_data: Dictionary) -> Skeleton2D:
	var skeleton := Skeleton2D.new()
	skeleton.name = "Skeleton2D"

	var bones_data: Array = skeleton_data.get("bones", [])
	var bones: Dictionary = {}

	for bone_data in bones_data:
		var json_name: String = bone_data.get("name", "bone")
		var bone := Bone2D.new()
		# Setting Node.name normalizes special chars (dots become underscores)
		# in Godot 4 - we still key the lookup dict by the original JSON name
		# so the parent-resolution pass below uses the unmodified string.
		bone.name = json_name
		var pos: Array = bone_data.get("position", [0.0, 0.0])
		bone.position = Vector2(pos[0], pos[1])
		bone.rotation = float(bone_data.get("rotation", 0.0))
		var scale_arr: Array = bone_data.get("scale", [1.0, 1.0])
		bone.scale = Vector2(scale_arr[0], scale_arr[1])
		var length: float = float(bone_data.get("length", 0.0))
		if length > 0.0:
			bone.set_length(length)
			# Stop Skeleton2D from inferring length/angle from missing child
			# Bone2D nodes - we already supplied authoritative values.
			bone.set_autocalculate_length_and_angle(false)
		# Capture authored pose as the rest pose so animations replace it cleanly.
		bone.set_rest(bone.transform)
		bones[json_name] = bone

	for bone_data in bones_data:
		var bone_name: String = bone_data.get("name", "")
		var parent_name = bone_data.get("parent", null)
		var bone: Bone2D = bones[bone_name]
		if parent_name == null:
			skeleton.add_child(bone)
		else:
			var parent: Bone2D = bones.get(parent_name)
			if parent == null:
				skeleton.add_child(bone)
			else:
				parent.add_child(bone)

	return skeleton
