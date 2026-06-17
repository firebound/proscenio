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
	# region_rect into hframes x vframes when region_enabled is true. The
	# .proscenio region is normalized [0, 1] (the same convention as mesh UVs);
	# Sprite2D.region_rect wants texture pixels, so the pixel rect can only be
	# computed once the texture size is known. Without a texture the rect cannot
	# be sized, and an enabled region with a zero-area rect draws NOTHING - worse
	# than a plain sprite. Nothing fills the rect later (importer._import has no
	# second pass), so enable the region only when the texture is present and the
	# rect can be set together; a texture-less sprite ships region-disabled. This
	# matches mesh_builder.gd, which leaves UVs raw when there is no texture.
	if sprite_res.texture_region.size() >= 4 and sprite_tex != null:
		sprite.region_enabled = true
		# Clip the texture filter to the region edge so neighbouring atlas frames
		# do not bleed in at the seam (rides the region path for free).
		sprite.region_filter_clip_enabled = true
		var tex_size := sprite_tex.get_size()
		sprite.region_rect = Rect2(
			sprite_res.texture_region[0] * tex_size.x,
			sprite_res.texture_region[1] * tex_size.y,
			sprite_res.texture_region[2] * tex_size.x,
			sprite_res.texture_region[3] * tex_size.y,
		)

	# CanvasItem appearance plus the Sprite2D-only flips. An absent modulate
	# keeps Godot's default white; z_index / flips default to 0 / false.
	if sprite_res.modulate.size() >= 4:
		sprite.modulate = Color(
			sprite_res.modulate[0],
			sprite_res.modulate[1],
			sprite_res.modulate[2],
			sprite_res.modulate[3],
		)
	sprite.z_index = sprite_res.z_index
	sprite.flip_h = sprite_res.flip_h
	sprite.flip_v = sprite_res.flip_v

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
