@tool
extends SceneTree

# Headless smoke test for the Proscenio builders.
#
# Bypasses EditorImportPlugin._import (which requires an editor session) and
# exercises the SkeletonBuilder / PolygonBuilder / SpriteFrameBuilder /
# AnimationBuilder pipeline directly against parsed .proscenio documents.
# Validates the no-GDExtension rule by importing under a fixture-only project
# that has the addon disabled.
#
# Run from the repository root:
#
#     godot --headless --script godot-plugin/tests/test_importer.gd

const SkeletonBuilder := preload("res://addons/proscenio/builders/skeleton_builder.gd")
const PolygonBuilder := preload("res://addons/proscenio/builders/polygon_builder.gd")
const SpriteFrameBuilder := preload("res://addons/proscenio/builders/sprite_frame_builder.gd")
const AnimationBuilder := preload("res://addons/proscenio/builders/animation_builder.gd")

const FIXTURE := "res://tests/fixtures/dummy.proscenio"
const EFFECT_FIXTURE := "res://tests/fixtures/effect.proscenio"
const SKINNED_FIXTURE := "res://tests/fixtures/skinned_dummy.proscenio"

var _failures: Array[String] = []
var _passes: int = 0  # gdlint: ignore=unused-private-class-variable


func _initialize() -> void:
	_run_dummy_checks()
	_run_effect_checks()
	_run_skinned_checks()
	_finish()


func _run_dummy_checks() -> void:
	var data := _load_fixture(FIXTURE)
	if data.is_empty():
		_fail("could not load %s" % FIXTURE)
		return

	var character := _build_character(data)

	_assert_eq(character.name, "dummy", "dummy: root name")
	var skeleton: Skeleton2D = character.get_node("Skeleton2D")
	_assert_eq(skeleton.name, "Skeleton2D", "dummy: skeleton name")

	var bones := _collect_descendants_of_type(skeleton, "Bone2D")
	_assert_eq(bones.size(), 3, "dummy: bone count")
	var bone_names := PackedStringArray()
	for bone: Node in bones:
		bone_names.append(String(bone.name))
	bone_names.sort()
	_assert_eq(", ".join(bone_names), "head, root, torso", "dummy: bone names")

	var sprites := _collect_descendants_of_type(skeleton, "Polygon2D")
	_assert_eq(sprites.size(), 3, "dummy: sprite count")

	var player: AnimationPlayer = character.get_node("AnimationPlayer")
	_assert_true(player.has_animation_library(""), "dummy: default library present")
	if player.has_animation_library(""):
		var lib := player.get_animation_library("")
		var anim_names := lib.get_animation_list()
		_assert_eq(anim_names.size(), 1, "dummy: animation count")
		_assert_eq(anim_names[0], "idle", "dummy: animation name")
		var anim := lib.get_animation("idle")
		_assert_true(anim.length > 0.0, "dummy: animation length > 0")

	_run_idempotency_check(data, character)

	character.free()


func _run_effect_checks() -> void:
	var data := _load_fixture(EFFECT_FIXTURE)
	if data.is_empty():
		_fail("could not load %s" % EFFECT_FIXTURE)
		return

	var character := _build_character(data)

	_assert_eq(character.name, "effect", "effect: root name")
	var skeleton: Skeleton2D = character.get_node("Skeleton2D")

	var sprites := _collect_descendants_of_type(skeleton, "Sprite2D")
	_assert_eq(sprites.size(), 1, "effect: Sprite2D count")
	if sprites.size() == 1:
		var glint: Sprite2D = sprites[0]
		_assert_eq(glint.name, "glint", "effect: sprite name")
		_assert_eq(glint.hframes, 4, "effect: hframes")
		_assert_eq(glint.vframes, 1, "effect: vframes")
		_assert_eq(glint.frame, 0, "effect: initial frame")
		_assert_true(glint.centered, "effect: centered default")

	var leaked_polygons := _collect_descendants_of_type(skeleton, "Polygon2D")
	_assert_eq(leaked_polygons.size(), 0, "effect: dispatcher kept Polygon2D path off")

	var player: AnimationPlayer = character.get_node("AnimationPlayer")
	_assert_true(player.has_animation("play"), "effect: play animation present")
	if player.has_animation("play"):
		var anim := player.get_animation("play")
		_assert_eq(anim.get_track_count(), 1, "effect: track count")
		if anim.get_track_count() == 1:
			_assert_eq(
				anim.track_get_interpolation_type(0),
				Animation.INTERPOLATION_NEAREST,
				"effect: frame track uses NEAREST"
			)
			_assert_eq(anim.track_get_key_count(0), 4, "effect: frame key count")

	character.free()


func _run_skinned_checks() -> void:
	var data := _load_fixture(SKINNED_FIXTURE)
	if data.is_empty():
		_fail("could not load %s" % SKINNED_FIXTURE)
		return

	var character := _build_character(data)
	var skeleton: Skeleton2D = character.get_node("Skeleton2D")

	var sprites := _collect_descendants_of_type(skeleton, "Polygon2D")
	_assert_eq(sprites.size(), 1, "skinned: Polygon2D count")
	if sprites.size() == 1:
		var torso: Polygon2D = sprites[0]
		_assert_eq(torso.name, "torso", "skinned: sprite name")
		# Skinned polygons live under the skeleton, not the bone — weights
		# move vertices, not the parent transform.
		_assert_true(torso.get_parent() == skeleton, "skinned: parented to skeleton")
		_assert_true(not torso.skeleton.is_empty(), "skinned: skeleton NodePath set")
		_assert_eq(torso.get_bone_count(), 2, "skinned: bone count = 2")
		if torso.get_bone_count() >= 2:
			# add_bone preserves insertion order: upper first, lower second.
			var upper_weights := torso.get_bone_weights(0)
			var lower_weights := torso.get_bone_weights(1)
			_assert_eq(upper_weights.size(), 4, "skinned: upper weights len")
			_assert_eq(lower_weights.size(), 4, "skinned: lower weights len")
			# Vertex 0 is at the top — fully weighted to 'upper'.
			_assert_eq(upper_weights[0], 1.0, "skinned: vertex 0 → upper = 1.0")
			_assert_eq(lower_weights[0], 0.0, "skinned: vertex 0 → lower = 0.0")

	character.free()


func _build_character(data: Dictionary) -> Node2D:
	var character := Node2D.new()
	character.name = data.get("name", "Character")

	var skeleton: Skeleton2D = SkeletonBuilder.build(data.get("skeleton", {}))
	character.add_child(skeleton)
	# Both builders discriminator-filter their own kind — calling both is
	# the same dispatch flow used in importer.gd._import.
	var sprites_data: Array = data.get("sprites", [])
	PolygonBuilder.attach_sprites(skeleton, sprites_data, null)
	SpriteFrameBuilder.attach_sprites(skeleton, sprites_data, null)

	var player := AnimationPlayer.new()
	player.name = "AnimationPlayer"
	character.add_child(player)
	AnimationBuilder.populate(player, skeleton, data.get("animations", []))

	return character


# SPEC 001: re-running the importer on the same `.proscenio` must produce
# a structurally identical scene. We cannot diff packed-scene bytes
# headlessly without an editor session, so the equivalence check compares
# the construction output (node hierarchy + key transforms + animation
# library) of two independent builds.
func _run_idempotency_check(data: Dictionary, original: Node2D) -> void:
	var twin := _build_character(data)
	_assert_eq(
		_describe(twin), _describe(original), "dummy: idempotent rebuild matches first build"
	)
	twin.free()


func _describe(node: Node) -> String:
	var lines: PackedStringArray = []
	_describe_recursive(node, "", lines)
	return "\n".join(lines)


func _describe_recursive(node: Node, prefix: String, out: PackedStringArray) -> void:
	var line := "%s%s:%s" % [prefix, node.name, node.get_class()]
	if node is Node2D:
		var n2d: Node2D = node
		line += (
			" pos=(%.3f,%.3f) rot=%.4f scale=(%.3f,%.3f)"
			% [n2d.position.x, n2d.position.y, n2d.rotation, n2d.scale.x, n2d.scale.y]
		)
	if node is AnimationPlayer:
		var ap: AnimationPlayer = node
		var libs: PackedStringArray = ap.get_animation_library_list()
		libs.sort()
		line += " libs=" + ", ".join(libs)
	out.append(line)
	for child: Node in node.get_children():
		_describe_recursive(child, prefix + "  ", out)


func _load_fixture(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var json := JSON.new()
	if json.parse(file.get_as_text()) != OK:
		return {}
	return json.data as Dictionary


func _collect_descendants_of_type(node: Node, type_name: String) -> Array:
	var out: Array = []
	for child in node.get_children():
		if child.get_class() == type_name or child.is_class(type_name):
			out.append(child)
		out.append_array(_collect_descendants_of_type(child, type_name))
	return out


func _assert_eq(actual: Variant, expected: Variant, label: String) -> void:
	if actual == expected:
		_passes += 1
		print("  ok  %s" % label)
	else:
		_fail("%s — expected %s, got %s" % [label, expected, actual])


func _assert_true(condition: bool, label: String) -> void:
	if condition:
		_passes += 1
		print("  ok  %s" % label)
	else:
		_fail(label)


func _fail(msg: String) -> void:
	_failures.append(msg)
	push_error("FAIL: %s" % msg)


func _finish() -> void:
	if _failures.is_empty():
		print("PASS: %d assertions" % _passes)
		quit(0)
	else:
		printerr("FAIL: %d failure(s) of %d total" % [_failures.size(), _passes + _failures.size()])
		quit(1)
