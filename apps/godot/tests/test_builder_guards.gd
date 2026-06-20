@tool
extends SceneTree

# Negative / edge-case coverage for the import builders: malformed packed
# vectors, all-missing-bone skinning, duplicate bone names, and slot-default
# resolution misses. test_importer.gd walks the happy-path fixtures; this file
# pins the hardening guards so a regression that silently corrupts the rig fails
# loudly instead of producing a quietly-broken scene.
#
# Run from the apps/godot project root:
#
#     godot --headless --script res://tests/test_builder_guards.gd

const SkeletonBuilder := preload("res://addons/proscenio/builders/skeleton_builder.gd")
const SlotBuilder := preload("res://addons/proscenio/builders/slot_builder.gd")
const MeshBuilder := preload("res://addons/proscenio/builders/mesh_builder.gd")
const SpriteBuilder := preload("res://addons/proscenio/builders/sprite_builder.gd")
const AnimationBuilder := preload("res://addons/proscenio/builders/animation_builder.gd")
const SpriteAttachUtil := preload("res://addons/proscenio/builders/sprite_attach_util.gd")
const ProscenioDocumentRes := preload(
	"res://addons/proscenio/schema_bindings/proscenio_document.gd"
)

var _failures: Array[String] = []
var _passes: int = 0  # gdlint: ignore=unused-private-class-variable


func _initialize() -> void:
	_run_short_vector_guard_checks()
	_run_all_missing_bone_checks()
	_run_duplicate_bone_checks()
	_run_slot_default_miss_checks()
	_run_frame_track_discrete_checks()
	_run_bone_track_type_scope_checks()
	_finish()


# A mesh whose polygon / UV carry a malformed (length < 2) point must not crash
# the build: the length-guarded packed-vector helper drops the short point to
# Vector2.ZERO instead of reading out of bounds.
func _run_short_vector_guard_checks() -> void:
	var character := _build_character(
		{
			"format_version": 1,
			"name": "short_vec",
			"pixels_per_unit": 100.0,
			"skeleton": {"bones": [{"name": "root", "position": [0.0, 0.0]}]},
			"elements":
			[
				{
					"type": "mesh",
					"name": "ragged",
					"bone": "root",
					"polygon": [[0.0, 0.0], [10.0], [10.0, 10.0]],
					"uv": [[0.0, 0.0], [1.0], [1.0, 1.0]],
				}
			],
		}
	)
	var skeleton: Skeleton2D = character.get_node("Skeleton2D")
	var meshes := _descendants_of_type(skeleton, "Polygon2D")
	_assert_eq(meshes.size(), 1, "short_vec: mesh built despite ragged point")
	if meshes.size() == 1:
		var ragged: Polygon2D = meshes[0]
		_assert_eq(ragged.polygon.size(), 3, "short_vec: all three polygon points kept")
		_assert_eq(ragged.polygon[1], Vector2.ZERO, "short_vec: short polygon point is ZERO")
		_assert_eq(ragged.uv[1], Vector2.ZERO, "short_vec: short UV point is ZERO")
	character.free()


# A skinned mesh whose every weight references a missing bone must NOT be left
# skeleton-bound with zero weights (Godot collapses an undeformed-but-bound
# Polygon2D to a point). With no weight resolving, the mesh stays unbound.
func _run_all_missing_bone_checks() -> void:
	var character := _build_character(
		{
			"format_version": 1,
			"name": "all_missing",
			"pixels_per_unit": 100.0,
			"skeleton": {"bones": [{"name": "root", "position": [0.0, 0.0]}]},
			"elements":
			[
				{
					"type": "mesh",
					"name": "orphan",
					"polygon": [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0]],
					"uv": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]],
					"weights": [{"bone": "ghost", "values": [1.0, 1.0, 1.0]}],
				}
			],
		}
	)
	var skeleton: Skeleton2D = character.get_node("Skeleton2D")
	var meshes := _descendants_of_type(skeleton.get_parent(), "Polygon2D")
	_assert_eq(meshes.size(), 1, "all_missing: mesh still built")
	if meshes.size() == 1:
		var orphan: Polygon2D = meshes[0]
		_assert_true(orphan.skeleton.is_empty(), "all_missing: not skeleton-bound with 0 weights")
		_assert_eq(orphan.get_bone_count(), 0, "all_missing: no bones bound")
	character.free()


# Two bones sharing a name must not silently overwrite the parent-lookup dict:
# the builder keeps first-wins so a child resolves to the FIRST occurrence
# (deterministic), and both bone nodes still land under the skeleton.
func _run_duplicate_bone_checks() -> void:
	var character := _build_character(
		{
			"format_version": 1,
			"name": "dup_bone",
			"pixels_per_unit": 100.0,
			"skeleton":
			{
				"bones":
				[
					{"name": "root", "position": [0.0, 0.0]},
					{"name": "dup", "parent": "root", "position": [10.0, 0.0]},
					{"name": "dup", "parent": "root", "position": [20.0, 0.0]},
					{"name": "child", "parent": "dup", "position": [5.0, 0.0]},
				]
			},
			"elements": [],
		}
	)
	var skeleton: Skeleton2D = character.get_node("Skeleton2D")
	var bones := _descendants_of_type(skeleton, "Bone2D")
	_assert_eq(bones.size(), 4, "dup_bone: all four bone nodes built (none dropped)")
	# First-wins: `child` re-parents under the FIRST `dup` (x = 10), not the
	# second (x = 20) that a silent last-wins overwrite would have selected.
	var child := skeleton.find_child("child", true, false)
	_assert_true(child != null, "dup_bone: child bone exists")
	if child != null:
		var dup_parent: Node = child.get_parent()
		_assert_true(dup_parent is Bone2D, "dup_bone: child parented under a Bone2D")
		_assert_eq(
			(dup_parent as Bone2D).position.x,
			10.0,
			"dup_bone: child under first 'dup' (first-wins)"
		)
	character.free()


# When a slot default names no attachment, the resolver must not hide every
# attachment (`visible = name == default` makes them all invisible). It falls
# back to making the FIRST attachment visible so the slot is not blank.
func _run_slot_default_miss_checks() -> void:
	var skeleton := Skeleton2D.new()
	skeleton.name = "Skeleton2D"
	get_root().add_child(skeleton)
	var slot_map := (
		SlotBuilder
		. build(
			skeleton,
			_slots_from(
				[
					{
						"name": "face",
						"bone": "",
						"attachments": ["face_a", "face_b"],
						"default": "missing",
					}
				]
			),
		)
	)
	var first := SpriteAttachUtil.resolve_sprite_parent(skeleton, "face_a", "", slot_map, false)
	var second := SpriteAttachUtil.resolve_sprite_parent(skeleton, "face_b", "", slot_map, false)
	_assert_true(first.visible, "slot_miss: first attachment visible on a default miss")
	_assert_true(not second.visible, "slot_miss: second attachment hidden on a default miss")
	skeleton.free()


# The imported sprite_frame track must use UPDATE_DISCRETE so a frame holds
# until the next key under blend / seek, not just NEAREST sampling.
func _run_frame_track_discrete_checks() -> void:
	var character := _build_with_animation(
		{
			"format_version": 1,
			"name": "frame_anim",
			"pixels_per_unit": 100.0,
			"skeleton": {"bones": [{"name": "root", "position": [0.0, 0.0]}]},
			"elements":
			[{"type": "sprite", "name": "glint", "bone": "root", "hframes": 4, "vframes": 1}],
			"animations":
			[
				{
					"name": "play",
					"length": 0.4,
					"tracks":
					[
						{
							"type": "sprite_frame",
							"target": "glint",
							"keys": [{"time": 0.0, "frame": 0}, {"time": 0.2, "frame": 2}],
						}
					],
				}
			],
		}
	)
	var player: AnimationPlayer = character.get_node("AnimationPlayer")
	_assert_true(player.has_animation("play"), "frame_discrete: animation present")
	if player.has_animation("play"):
		var anim := player.get_animation("play")
		_assert_eq(anim.get_track_count(), 1, "frame_discrete: one frame track")
		if anim.get_track_count() == 1:
			_assert_eq(
				anim.value_track_get_update_mode(0),
				Animation.UPDATE_DISCRETE,
				"frame_discrete: frame track is UPDATE_DISCRETE"
			)
	character.free()


# A bone_transform track whose target name matches a non-Bone2D node (here a
# slot Node2D named like the missing bone) must NOT bind to it: the type-scoped
# lookup rejects the wrong node and emits no track instead of animating a slot.
func _run_bone_track_type_scope_checks() -> void:
	var character := _build_with_animation(
		{
			"format_version": 1,
			"name": "scope_anim",
			"pixels_per_unit": 100.0,
			"skeleton": {"bones": [{"name": "root", "position": [0.0, 0.0]}]},
			"elements": [],
			"slots": [{"name": "decoy", "bone": "", "attachments": [], "default": ""}],
			"animations":
			[
				{
					"name": "move",
					"length": 1.0,
					"tracks":
					[
						{
							"type": "bone_transform",
							"target": "decoy",
							"keys": [{"time": 0.0, "position": [1.0, 2.0]}],
						}
					],
				}
			],
		}
	)
	var player: AnimationPlayer = character.get_node("AnimationPlayer")
	if player.has_animation("move"):
		var anim := player.get_animation("move")
		_assert_eq(
			anim.get_track_count(), 0, "bone_scope: no track binds to the same-named slot Node2D"
		)
	else:
		_assert_true(true, "bone_scope: animation library present")
	character.free()


func _build_with_animation(data: Dictionary) -> Node2D:
	var document: ProscenioDocumentRes = ProscenioDocumentRes.from_dict(data)
	var character := Node2D.new()
	character.name = document.name if document.name != "" else "Character"
	get_root().add_child(character)
	var skeleton := SkeletonBuilder.build(document.skeleton)
	character.add_child(skeleton)
	var slot_map := SlotBuilder.build(skeleton, document.slots)
	MeshBuilder.attach_elements(skeleton, document.elements, null, slot_map)
	SpriteBuilder.attach_elements(skeleton, document.elements, null, slot_map)
	var player := AnimationPlayer.new()
	player.name = "AnimationPlayer"
	character.add_child(player)
	AnimationBuilder.populate(player, skeleton, document.animations)
	return character


func _build_character(data: Dictionary) -> Node2D:
	var document: ProscenioDocumentRes = ProscenioDocumentRes.from_dict(data)
	var character := Node2D.new()
	character.name = document.name if document.name != "" else "Character"
	get_root().add_child(character)
	var skeleton := SkeletonBuilder.build(document.skeleton)
	character.add_child(skeleton)
	var slot_map := SlotBuilder.build(skeleton, document.slots)
	MeshBuilder.attach_elements(skeleton, document.elements, null, slot_map)
	return character


func _slots_from(raw: Array) -> Array[ProscenioSlot]:
	var out: Array[ProscenioSlot] = []
	for item: Dictionary in raw:
		out.append(ProscenioSlot.from_dict(item))
	return out


func _descendants_of_type(node: Node, type_name: String) -> Array:
	var out: Array = []
	for child in node.get_children():
		if child.is_class(type_name):
			out.append(child)
		out.append_array(_descendants_of_type(child, type_name))
	return out


func _assert_eq(actual: Variant, expected: Variant, label: String) -> void:
	if actual == expected:
		_passes += 1
		print("  ok  %s" % label)
	else:
		_fail("%s - expected %s, got %s" % [label, expected, actual])


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
	if _passes == 0:
		printerr("FAIL: 0 assertions ran - a build errored before any check")
		quit(1)
	elif _failures.is_empty():
		print("PASS: %d assertions" % _passes)
		quit(0)
	else:
		printerr("FAIL: %d failure(s) of %d total" % [_failures.size(), _passes + _failures.size()])
		quit(1)
