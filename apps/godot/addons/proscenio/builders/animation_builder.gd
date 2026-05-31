@tool
extends RefCounted

const SlotBuilder := preload("res://addons/proscenio/builders/slot_builder.gd")


static func populate(
	player: AnimationPlayer,
	skeleton: Skeleton2D,
	animations: Array[ProscenioAnimation],
) -> void:
	var library := AnimationLibrary.new()

	if animations == null:
		player.add_animation_library("", library)
		return

	for anim_res: ProscenioAnimation in animations:
		var anim := _populate_godot_animation(anim_res, skeleton)
		library.add_animation(anim_res.name, anim)

	player.add_animation_library("", library)


static func _populate_godot_animation(
	anim_res: ProscenioAnimation, skeleton: Skeleton2D
) -> Animation:
	# Local alias for Godot's Animation class (the function arg) to avoid
	# shadowing the type name from the model.
	var anim := Animation.new()
	anim.length = anim_res.length
	anim.loop_mode = (Animation.LOOP_LINEAR if anim_res.loop else Animation.LOOP_NONE)
	for track_res: ProscenioTrack in anim_res.tracks:
		_add_track(anim, skeleton, track_res)
	return anim


static func _add_track(anim: Animation, skeleton: Skeleton2D, track_res: ProscenioTrack) -> void:
	var track_type := track_res.type
	# Sanitize so ``find_child`` matches the Godot-shaped node name (Node.name
	# replaces ``.`` etc with ``_`` on assignment); the .proscenio document
	# carries Blender-shaped names with dots intact.
	var target := SlotBuilder.sanitize(track_res.target)
	var keys: Array[ProscenioKey] = track_res.keys

	if keys.is_empty():
		return

	var character_root := skeleton.get_parent()
	if character_root == null:
		push_error("Proscenio: skeleton has no parent - animation tracks cannot resolve paths")
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
							"Proscenio: sprite '%s' is %s, not Sprite2D - sprite_frame "
							+ "tracks only target sprites of type 'sprite_frame'."
						)
						% [target, sprite.get_class()]
					)
				)
				return
			var base_path := str(character_root.get_path_to(sprite))
			_add_frame_track(anim, base_path, keys)
		"slot_attachment":
			var slot_node := character_root.find_child(target, true, false)
			if slot_node == null:
				push_error("Proscenio: slot '%s' not found for slot_attachment track" % target)
				return
			_add_slot_attachment_tracks(anim, character_root, slot_node, keys)
		"visibility":
			push_warning("Proscenio: track type '%s' not implemented yet" % track_type)
		_:
			push_warning("Proscenio: unknown track type '%s'" % track_type)


static func _key_has_property(key: ProscenioKey, property: String) -> bool:
	# `_set_fields` records which keys actually appeared in the parsed JSON
	# dictionary; checking it here keeps phantom channels out of the
	# generated animation (a key that lands without `rotation` no longer
	# pulls in a rotation track that resets the authored pose to zero).
	return key._set_fields.has(property)


static func _add_value_track_if_present(
	anim: Animation, base_path: String, property: String, keys: Array[ProscenioKey]
) -> void:
	# bone_transform tracks emit one Godot value track per animated property
	# (position, rotation, scale). The .proscenio writer only places a key in
	# `keys[]` when the matching property has data; the per-property emit
	# below checks each key with `_key_has_property` so a position-only
	# track does not register a phantom rotation channel.
	var has_any := false
	for key in keys:
		if _key_has_property(key, property):
			has_any = true
			break
	if not has_any:
		return

	var idx := anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(idx, NodePath("%s:%s" % [base_path, property]))
	# Cubic spline interpolation gives smooth motion between keys without
	# needing per-key Bezier handles in the .proscenio format. Rotation uses
	# the *_ANGLE variant so wrap-around at +/-pi is handled correctly.
	var interp := Animation.INTERPOLATION_LINEAR
	match property:
		"rotation":
			interp = Animation.INTERPOLATION_CUBIC_ANGLE
		"position", "scale":
			interp = Animation.INTERPOLATION_CUBIC
	anim.track_set_interpolation_type(idx, interp)

	for key in keys:
		if not _key_has_property(key, property):
			continue
		anim.track_insert_key(idx, key.time, _key_value_for(property, key))


static func _add_slot_attachment_tracks(
	anim: Animation, character_root: Node, slot_node: Node, keys: Array[ProscenioKey]
) -> void:
	# Slot attachment animation = N visibility tracks, one per attachment
	# child of the slot Node2D. At each key time, exactly one attachment is
	# visible (the one named in `key.attachment`); the rest go hidden. Uses
	# NEAREST interpolation - attachment swaps are hard cuts, not blends
	# (the slot system D5).
	var slot_path := str(character_root.get_path_to(slot_node))
	for child in slot_node.get_children():
		if not (child is CanvasItem):
			continue
		var idx := anim.add_track(Animation.TYPE_VALUE)
		anim.track_set_path(idx, NodePath("%s/%s:visible" % [slot_path, child.name]))
		anim.track_set_interpolation_type(idx, Animation.INTERPOLATION_NEAREST)
		for key in keys:
			if key.attachment == "":
				continue
			# Normalise the keyed attachment name through the same sanitiser
			# slot_builder uses so dotted Blender names (`face.angry`) match
			# the Godot-shaped child name (`face_angry`).
			var attachment_name := SlotBuilder.sanitize(key.attachment)
			anim.track_insert_key(idx, key.time, child.name == attachment_name)


static func _add_frame_track(anim: Animation, base_path: String, keys: Array[ProscenioKey]) -> void:
	# Frame indexes are discrete integers; smooth blending between them has no
	# semantic meaning, so the track uses NEAREST interpolation.
	var idx := anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(idx, NodePath("%s:frame" % base_path))
	anim.track_set_interpolation_type(idx, Animation.INTERPOLATION_NEAREST)
	for key in keys:
		# `frame` defaults to 0; treat key as a frame key whenever the writer
		# emitted it on a sprite_frame track. The dispatcher above ensures we
		# only land here for sprite_frame target types.
		anim.track_insert_key(idx, key.time, key.frame)


static func _key_value_for(property: String, key: ProscenioKey) -> Variant:
	match property:
		"position":
			return Vector2(key.position[0], key.position[1])
		"scale":
			return Vector2(key.scale[0], key.scale[1])
		"rotation":
			return key.rotation
	return null
