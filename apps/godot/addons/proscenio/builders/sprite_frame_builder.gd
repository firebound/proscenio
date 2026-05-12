@tool
extends RefCounted

# Attaches Sprite2D-backed sprites declared as `type: "sprite_frame"` in the
# .proscenio document. Companion of polygon_builder.gd — each builder
# discriminator-filters its own kind so importer.gd can call both blindly.

const NodeNameUtil := preload("res://addons/proscenio/builders/node_name_util.gd")


static func _resolve_sprite_texture(
	sprite_data: Dictionary,
	fallback_atlas: Texture2D,
	source_dir: String,
) -> Texture2D:
	# Mirror of polygon_builder._resolve_sprite_texture -- see that file for
	# the resolution order rationale (per-sprite `texture` field ->
	# `<sprite.name>.png` next to source -> fallback atlas).
	var per_sprite: String = sprite_data.get("texture", "")
	if per_sprite != "" and source_dir != "":
		var path := source_dir.path_join(per_sprite)
		if ResourceLoader.exists(path):
			return ResourceLoader.load(path, "Texture2D") as Texture2D
	if source_dir != "":
		var by_name := source_dir.path_join("%s.png" % sprite_data.get("name", ""))
		if ResourceLoader.exists(by_name):
			return ResourceLoader.load(by_name, "Texture2D") as Texture2D
	return fallback_atlas


static func attach_sprites(
	skeleton: Skeleton2D,
	sprites_data: Array,
	atlas: Texture2D,
	slot_map: Dictionary = {},
	source_dir: String = "",
) -> void:
	for sprite_data in sprites_data:
		var sprite_type: String = sprite_data.get("type", "polygon")
		if sprite_type != "sprite_frame":
			continue

		var sprite := Sprite2D.new()
		sprite.name = sprite_data.get("name", "sprite")

		var sprite_tex := _resolve_sprite_texture(sprite_data, atlas, source_dir)
		if sprite_tex != null:
			sprite.texture = sprite_tex

		sprite.hframes = int(sprite_data.get("hframes", 1))
		sprite.vframes = int(sprite_data.get("vframes", 1))
		sprite.frame = int(sprite_data.get("frame", 0))
		sprite.centered = bool(sprite_data.get("centered", true))

		var offset: Array = sprite_data.get("offset", [0.0, 0.0])
		sprite.offset = Vector2(offset[0], offset[1])

		# Optional sub-rectangle of the atlas. Absent → use the full texture.
		# Godot's Sprite2D divides region_rect into hframes × vframes when
		# region_enabled is true.
		if sprite_data.has("texture_region"):
			var region: Array = sprite_data.get("texture_region")
			sprite.region_enabled = true
			sprite.region_rect = Rect2(region[0], region[1], region[2], region[3])

		var bone_name: String = NodeNameUtil.sanitize(sprite_data.get("bone", ""))
		# Slot routing (SPEC 004 D6): sprite_frame attachments compose with
		# polygon attachments under the same slot Node2D. Default-attachment
		# starts visible, others start hidden -- the slot_attachment track
		# (animation_builder.gd) flips visibility per key at runtime.
		# ``sprite.name`` is post-sanitize (Godot strips ``.`` etc); slot_map
		# keys are sanitized in slot_builder for consistency.
		var sanitized_name: String = String(sprite.name)
		var slot_info = slot_map.get(sanitized_name, null)
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
