@tool
extends RefCounted


static func populate(player: AnimationPlayer, skeleton: Skeleton2D, animations_data: Array) -> void:
	var library := AnimationLibrary.new()

	for anim_data in animations_data:
		var anim := Animation.new()
		anim.length = float(anim_data.get("length", 1.0))
		anim.loop_mode = (
			Animation.LOOP_LINEAR if bool(anim_data.get("loop", false)) else Animation.LOOP_NONE
		)
		for track_data in anim_data.get("tracks", []):
			_add_track(anim, skeleton, track_data)
		library.add_animation(anim_data.get("name", "anim"), anim)

	player.add_animation_library("", library)


static func _add_track(anim: Animation, skeleton: Skeleton2D, track_data: Dictionary) -> void:
	var track_type: String = track_data.get("type", "")
	var target: String = track_data.get("target", "")
	var keys: Array = track_data.get("keys", [])

	if keys.is_empty():
		return

	var character_root := skeleton.get_parent()
	if character_root == null:
		push_error("Proscenio: skeleton has no parent — animation tracks cannot resolve paths")
		return

	match track_type:
		"bone_transform":
			var bone := skeleton.find_child(target, true, false)
			if bone == null:
				push_error("Proscenio: bone '%s' not found for animation track" % target)
				return
			var base_path := str(character_root.get_path_to(bone))
			_add_value_track_if_present(anim, base_path, "position", keys)
			_add_value_track_if_present(anim, base_path, "rotation", keys)
			_add_value_track_if_present(anim, base_path, "scale", keys)
		"sprite_frame":
			var sprite := character_root.find_child(target, true, false)
			if sprite == null:
				push_error("Proscenio: sprite '%s' not found for sprite_frame track" % target)
				return
			if not (sprite is Sprite2D):
				push_error(
					(
						(
							"Proscenio: sprite '%s' is %s, not Sprite2D — sprite_frame "
							+ "tracks only target sprites of type 'sprite_frame'."
						)
						% [target, sprite.get_class()]
					)
				)
				return
			var base_path := str(character_root.get_path_to(sprite))
			_add_frame_track(anim, base_path, keys)
		"slot_attachment", "visibility":
			push_warning("Proscenio: track type '%s' not implemented yet" % track_type)
		_:
			push_warning("Proscenio: unknown track type '%s'" % track_type)


static func _add_value_track_if_present(
	anim: Animation, base_path: String, property: String, keys: Array
) -> void:
	var has_any := false
	for key in keys:
		if key.has(property):
			has_any = true
			break
	if not has_any:
		return

	var idx := anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(idx, NodePath("%s:%s" % [base_path, property]))
	# Cubic spline interpolation gives smooth motion between keys without
	# needing per-key Bezier handles in the .proscenio format. Rotation uses
	# the *_ANGLE variant so wrap-around at ±π is handled correctly.
	var interp := Animation.INTERPOLATION_LINEAR
	match property:
		"rotation":
			interp = Animation.INTERPOLATION_CUBIC_ANGLE
		"position", "scale":
			interp = Animation.INTERPOLATION_CUBIC
	anim.track_set_interpolation_type(idx, interp)

	for key in keys:
		if not key.has(property):
			continue
		var t := float(key.get("time", 0.0))
		anim.track_insert_key(idx, t, _key_value_for(property, key[property]))


static func _add_frame_track(anim: Animation, base_path: String, keys: Array) -> void:
	# Frame indexes are discrete integers; smooth blending between them has no
	# semantic meaning, so the track uses NEAREST interpolation.
	var idx := anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(idx, NodePath("%s:frame" % base_path))
	anim.track_set_interpolation_type(idx, Animation.INTERPOLATION_NEAREST)
	for key in keys:
		if not key.has("frame"):
			continue
		var t := float(key.get("time", 0.0))
		anim.track_insert_key(idx, t, int(key["frame"]))


static func _key_value_for(property: String, raw: Variant) -> Variant:
	match property:
		"position", "scale":
			var arr: Array = raw
			return Vector2(arr[0], arr[1])
		"rotation":
			return float(raw)
		_:
			return raw
