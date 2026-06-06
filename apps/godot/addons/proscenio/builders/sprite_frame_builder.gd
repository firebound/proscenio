@tool
extends RefCounted

# Attaches Sprite2D-backed sprites declared as `type: "sprite_frame"` in the
# .proscenio document. Companion of polygon_builder.gd - each builder
# discriminator-filters its own kind so importer.gd can call both blindly.

const NodeNameUtil := preload("res://addons/proscenio/builders/node_name_util.gd")
const SpriteAttachUtil := preload("res://addons/proscenio/builders/sprite_attach_util.gd")


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

	var sprite_tex := SpriteAttachUtil.resolve_sprite_texture(
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
	# Slot routing (shared with polygon_builder via sprite_attach_util):
	# sprite_frame attachments compose with polygon attachments under the same
	# slot Node2D; default-attachment starts visible, others hidden until the
	# slot_attachment track (animation_builder.gd) flips them at runtime.
	var sanitized_name := String(sprite.name)
	var routing := SpriteAttachUtil.resolve_sprite_parent(
		skeleton, sanitized_name, bone_name, slot_map, true
	)
	sprite.visible = routing.visible
	routing.node.add_child(sprite)
