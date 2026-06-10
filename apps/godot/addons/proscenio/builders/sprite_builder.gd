@tool
extends RefCounted

# Attaches Sprite2D-backed sprite elements (`type: "sprite"`). Companion of
# mesh_builder.gd - each builder filters its own kind so importer.gd can call
# both blindly.

const NodeNameUtil := preload("res://addons/proscenio/builders/node_name_util.gd")
const SpriteAttachUtil := preload("res://addons/proscenio/builders/sprite_attach_util.gd")


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
		if not (element is ProscenioSpriteElement):
			continue
		_build_sprite(element as ProscenioSpriteElement, skeleton, atlas, slot_map, source_dir)


static func _build_sprite(
	sprite_res: ProscenioSpriteElement,
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

	# Optional atlas sub-rect; absent means the full texture. Sprite2D divides
	# region_rect into hframes x vframes when region_enabled is true.
	if sprite_res.texture_region.size() >= 4:
		sprite.region_enabled = true
		sprite.region_rect = Rect2(
			sprite_res.texture_region[0],
			sprite_res.texture_region[1],
			sprite_res.texture_region[2],
			sprite_res.texture_region[3],
		)

	var bone_name := NodeNameUtil.sanitize(sprite_res.bone)
	# Sprite and mesh attachments compose under the same slot Node2D. The
	# default attachment starts visible, others hidden until the
	# slot_attachment track flips them at runtime.
	var sanitized_name := String(sprite.name)
	var routing := SpriteAttachUtil.resolve_sprite_parent(
		skeleton, sanitized_name, bone_name, slot_map, true
	)
	sprite.visible = routing.visible
	routing.node.add_child(sprite)
