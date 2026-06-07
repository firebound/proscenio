@tool
extends RefCounted

# Builds slot anchor Node2D parents under the skeleton.
#
# A slot in the .proscenio document is a `{name, bone, default,
# attachments[]}` record. Each slot becomes a `Node2D` child of the
# matching `Bone2D` (or of the `Skeleton2D` root when `bone` is empty).
# The element builders - mesh_builder.gd / sprite_builder.gd
# - consult the slot map this module returns and route any element
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


static func build(skeleton: Skeleton2D, slot_resources: Array[ProscenioSlot]) -> Dictionary:
	# Returns `{sanitized_attachment_name: SlotInfo}`. Sprite builders look up
	# by their sprite's sanitized name (matching what Godot stored in
	# ``Node.name``); absence means the sprite is not in any slot and falls
	# back to bone-routing.
	var slot_map: Dictionary = {}
	if slot_resources == null:
		return slot_map
	for slot_res: ProscenioSlot in slot_resources:
		var info := _build_one_slot(skeleton, slot_res)
		if info == null:
			continue
		for attachment_name: String in slot_res.attachments:
			slot_map[NodeNameUtil.sanitize(attachment_name)] = info
	return slot_map


static func _build_one_slot(skeleton: Skeleton2D, slot_res: ProscenioSlot) -> SlotInfo:
	if slot_res.name == "":
		push_warning("Proscenio: slot entry missing name - skipping")
		return null

	var node := Node2D.new()
	node.name = NodeNameUtil.sanitize(slot_res.name)

	var bone_name := NodeNameUtil.sanitize(slot_res.bone)
	var parent: Node = skeleton
	if bone_name != "":
		var bone := skeleton.find_child(bone_name, true, false)
		if bone != null:
			parent = bone
		else:
			push_warning(
				(
					(
						"Proscenio: slot '%s' references missing bone '%s' - "
						+ "anchoring at skeleton root."
					)
					% [slot_res.name, bone_name]
				)
			)
	parent.add_child(node)

	var info := SlotInfo.new()
	info.node = node
	info.default = NodeNameUtil.sanitize(slot_res.default)
	return info
