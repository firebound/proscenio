@tool
extends RefCounted

# Builds slot anchor Node2D parents under the skeleton (SPEC 004 Wave 4.2).
#
# A slot in the .proscenio document is a `{name, bone, default,
# attachments[]}` record. Each slot becomes a `Node2D` child of the
# matching `Bone2D` (or of the `Skeleton2D` root when `bone` is empty).
# The sprite builders -- polygon_builder.gd / sprite_frame_builder.gd
# -- consult the slot map this module returns and route any sprite
# whose name appears in some `attachments[]` under the slot Node2D
# instead of the bone-or-skeleton fallback.
#
# Per-attachment visibility is set during sprite construction:
# `sprite.visible = (sprite.name == slot.default)`. Animation track
# flips at runtime live in `animation_builder.gd`'s `slot_attachment`
# handler.


class SlotInfo:
	extends RefCounted
	var node: Node2D
	var default: String  # already sanitized (Godot-name shape)


const NodeNameUtil := preload("res://addons/proscenio/builders/node_name_util.gd")


# Re-export of the shared sanitiser so existing callers
# (``SlotBuilder.sanitize(...)``) keep compiling. See
# ``node_name_util.gd`` for the dot/slash/colon/at replacement rules.
static func sanitize(name: String) -> String:
	return NodeNameUtil.sanitize(name)


static func build(skeleton: Skeleton2D, slots_data: Array) -> Dictionary:
	# Returns `{sanitized_attachment_name: SlotInfo}`. Sprite builders look up
	# by their sprite's sanitized name (matching what Godot stored in
	# ``Node.name``); absence means the sprite is not in any slot and falls
	# back to bone-routing.
	var slot_map: Dictionary = {}
	for slot_data in slots_data:
		var info := _build_one_slot(skeleton, slot_data)
		if info == null:
			continue
		var attachments: Array = slot_data.get("attachments", [])
		for attachment_name in attachments:
			slot_map[sanitize(String(attachment_name))] = info
	return slot_map


static func _build_one_slot(skeleton: Skeleton2D, slot_data: Dictionary) -> SlotInfo:
	var raw_slot_name: String = slot_data.get("name", "")
	if raw_slot_name == "":
		push_warning("Proscenio: slot entry missing name -- skipping")
		return null

	var node := Node2D.new()
	node.name = sanitize(raw_slot_name)

	var bone_name: String = sanitize(String(slot_data.get("bone", "")))
	var parent: Node = skeleton
	if bone_name != "":
		var bone := skeleton.find_child(bone_name, true, false)
		if bone != null:
			parent = bone
		else:
			push_warning(
				(
					(
						"Proscenio: slot '%s' references missing bone '%s' -- "
						+ "anchoring at skeleton root."
					)
					% [raw_slot_name, bone_name]
				)
			)
	parent.add_child(node)

	var info := SlotInfo.new()
	info.node = node
	info.default = sanitize(String(slot_data.get("default", "")))
	return info
