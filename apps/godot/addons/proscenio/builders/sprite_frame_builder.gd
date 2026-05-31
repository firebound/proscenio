@tool
extends RefCounted

# Attaches Sprite2D-backed sprites declared as `type: "sprite_frame"` in the
# .proscenio document. Companion of polygon_builder.gd - each builder
# discriminator-filters its own kind so importer.gd can call both blindly.

const NodeNameUtil := preload("res://addons/proscenio/builders/node_name_util.gd")
const SlotBuilder := preload("res://addons/proscenio/builders/slot_builder.gd")


static func _resolve_sprite_texture(
	per_sprite_path: String,
	sprite_name: String,
	fallback_atlas: Texture2D,
	source_dir: String,
) -> Texture2D:
	# Mirror of polygon_builder._resolve_sprite_texture - see that file for
	# the resolution order rationale (per-sprite `texture` field ->
	# `<sprite.name>.png` next to source -> fallback atlas).
	if per_sprite_path != "" and source_dir != "":
		var path := source_dir.path_join(per_sprite_path)
		if ResourceLoader.exists(path):
			return ResourceLoader.load(path, "Texture2D") as Texture2D
	if source_dir != "":
		var by_name := source_dir.path_join("%s.png" % sprite_name)
		if ResourceLoader.exists(by_name):
			return ResourceLoader.load(by_name, "Texture2D") as Texture2D
	return fallback_atlas


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
		if not (sprite_res is ProscenioSpriteFrameSprite):
			continue
		_build_sprite_frame(
			sprite_res as ProscenioSpriteFrameSprite, skeleton, atlas, slot_map, source_dir
		)


static func _build_sprite_frame(
	sprite_res: ProscenioSpriteFrameSprite,
	skeleton: Skeleton2D,
	atlas: Texture2D,
	slot_map: Dictionary,
	source_dir: String,
) -> void:
	var sprite := Sprite2D.new()
	sprite.name = sprite_res.name

	var sprite_tex := _resolve_sprite_texture(
		sprite_res.texture, sprite_res.name, atlas, source_dir
	)
	if sprite_tex != null:
		sprite.texture = sprite_tex

	sprite.hframes = sprite_res.hframes
	sprite.vframes = sprite_res.vframes
	sprite.frame = sprite_res.frame
	sprite.centered = sprite_res.centered

	if sprite_res.offset.size() >= 2:
		sprite.offset = Vector2(sprite_res.offset[0], sprite_res.offset[1])

	# Optional sub-rectangle of the atlas. Absent means use the full texture.
	# Godot's Sprite2D divides region_rect into hframes x vframes when
	# region_enabled is true.
	if sprite_res.texture_region.size() >= 4:
		sprite.region_enabled = true
		sprite.region_rect = Rect2(
			sprite_res.texture_region[0],
			sprite_res.texture_region[1],
			sprite_res.texture_region[2],
			sprite_res.texture_region[3],
		)

	var bone_name := NodeNameUtil.sanitize(sprite_res.bone)
	# Slot routing (the slot system D6): sprite_frame attachments compose with
	# polygon attachments under the same slot Node2D. Default-attachment
	# starts visible, others start hidden - the slot_attachment track
	# (animation_builder.gd) flips visibility per key at runtime.
	# ``sprite.name`` is post-sanitize (Godot strips ``.`` etc); slot_map
	# keys are sanitized in slot_builder for consistency.
	var sanitized_name := String(sprite.name)
	var slot_info: SlotBuilder.SlotInfo = slot_map.get(sanitized_name, null)
	var parent: Node
	if slot_info != null:
		parent = slot_info.node
		sprite.visible = sanitized_name == slot_info.default
	elif bone_name != "":
		parent = skeleton
		var found := skeleton.find_child(bone_name, true, false)
		if found != null:
			parent = found
	else:
		parent = skeleton
	parent.add_child(sprite)
