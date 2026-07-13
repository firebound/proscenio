@tool
extends RefCounted

# Shared sprite-attachment helpers for mesh_builder.gd and
# sprite_builder.gd: per-element texture resolution and slot / bone parent
# routing.

const SlotBuilder := preload("res://addons/proscenio/builders/slot_builder.gd")


class SpriteParent:
	extends RefCounted
	var node: Node
	var visible: bool = true


static func resolve_sprite_texture(
	per_sprite_path: String,
	sprite_name: String,
	fallback_atlas: Texture2D,
	source_dir: String,
) -> Texture2D:
	# Resolution order:
	# 1. sprite.texture field - load <source_dir>/<filename>.
	# 2. <sprite.name>.png next to the .proscenio (filename-by-convention).
	# 3. fallback_atlas - the scene-wide single-image case.
	if per_sprite_path != "" and source_dir != "":
		var path := source_dir.path_join(per_sprite_path)
		if ResourceLoader.exists(path):
			return ResourceLoader.load(path, "Texture2D") as Texture2D
	if source_dir != "":
		var by_name := source_dir.path_join("%s.png" % sprite_name)
		if ResourceLoader.exists(by_name):
			return ResourceLoader.load(by_name, "Texture2D") as Texture2D
	return fallback_atlas


static func element_local_transform(
	skeleton: Skeleton2D,
	parent: Node,
	rest: Transform2D,
) -> Transform2D:
	# Convert an element's absolute (skeleton-space) rest transform into the
	# local transform under `parent`, cancelling the parent's own skeleton-space
	# rest: local = parent_in_skeleton^-1 * rest. The bones carry no pose at
	# build time, so global_transform IS the rest chain - the same
	# live-rest-globals technique slot_builder.gd uses for the anchor cancel.
	# Under the skeleton root or a slot anchor (whose transform already cancels
	# its bone) the parent term is identity and `rest` passes through; under a
	# Bone2D it cancels the bone's cumulative rest so the element renders where
	# it was authored and only the pose delta moves it. A non-Node2D parent
	# (defensive) contributes identity.
	var parent_2d := parent as Node2D
	if parent_2d == null:
		return rest
	var parent_in_skeleton := (
		skeleton.global_transform.affine_inverse() * parent_2d.global_transform
	)
	return parent_in_skeleton.affine_inverse() * rest


static func resolve_sprite_parent(
	skeleton: Skeleton2D,
	sanitized_name: String,
	bone_name: String,
	slot_map: Dictionary,
	allow_bone_parent: bool,
) -> SpriteParent:
	# Slot routing wins: a sprite whose sanitized name is in slot_map re-parents
	# under the slot Node2D and takes the slot's default visibility. Otherwise,
	# when bone-parenting is allowed and a bone matches, parent to that Bone2D;
	# else the skeleton root. `visible` stays true outside the slot case.
	var result := SpriteParent.new()
	var slot_info: SlotBuilder.SlotInfo = slot_map.get(sanitized_name, null)
	if slot_info != null:
		result.node = slot_info.node
		result.visible = sanitized_name == slot_info.default
		return result
	if allow_bone_parent and bone_name != "":
		var found := skeleton.find_child(bone_name, true, false)
		result.node = found if found != null else skeleton
		return result
	result.node = skeleton
	return result
