@tool
extends SceneTree

# Walks the real Blender-baked goldens (synced into res://examples/ by
# scripts/godot/sync_fixtures.py) and asserts the builders produce a sane node
# tree. This is the writer -> builder end-to-end guard: test_importer.gd walks
# hand-authored edge-case fixtures, but those drifted from the baked output and
# masked real bugs. The checks below pin the four that slipped through:
#
#   - mixed_feature carries the chained 5-bone rig incl. the `mouth_anchor`
#     bone (renamed so it does not collide with the `mouth` sprite element);
#   - a bone-attached slot anchors at the skeleton origin (cumulative rest);
#   - the spine bob plays vertically, not sideways (parent-local anim delta);
#   - the mouth_drive sprite_frame track wraps out-of-range frames (not clamp).
#
# Run from the apps/godot project root (after sync_fixtures.py):
#
#     godot --headless --script res://tests/test_golden_scenes.gd

const SkeletonBuilder := preload("res://addons/proscenio/builders/skeleton_builder.gd")
const SlotBuilder := preload("res://addons/proscenio/builders/slot_builder.gd")
const MeshBuilder := preload("res://addons/proscenio/builders/mesh_builder.gd")
const SpriteBuilder := preload("res://addons/proscenio/builders/sprite_builder.gd")
const AnimationBuilder := preload("res://addons/proscenio/builders/animation_builder.gd")
const ProscenioDocumentRes := preload(
	"res://addons/proscenio/schema_bindings/proscenio_document.gd"
)

var _failures: Array[String] = []
var _passes: int = 0  # gdlint: ignore=unused-private-class-variable


func _initialize() -> void:
	_run_mixed_feature_checks()
	_run_mouth_drive_checks()
	_finish()


func _build(golden_path: String) -> Node2D:
	var file := FileAccess.open(golden_path, FileAccess.READ)
	if file == null:
		return null
	var json := JSON.new()
	if json.parse(file.get_as_text()) != OK or typeof(json.data) != TYPE_DICTIONARY:
		return null
	var data: Dictionary = json.data
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


func _run_mixed_feature_checks() -> void:
	var character := _build("res://examples/mixed_feature/mixed_feature.proscenio")
	if character == null:
		_fail("mixed: could not load golden")
		return
	var skeleton: Skeleton2D = character.get_node("Skeleton2D")

	# Five chained bones, including the renamed anchor (was `mouth`, which
	# collided with the sprite element of the same name).
	var bone_names := PackedStringArray()
	for bone: Node in _descendants(skeleton, "Bone2D"):
		bone_names.append(String(bone.name))
	bone_names.sort()
	_assert_eq(", ".join(bone_names), "head, jaw, mouth_anchor, root, spine", "mixed: bone names")

	# Skinned body is a SIBLING of the skeleton, two bone weights, two faces.
	var rig_root: Node = skeleton.get_parent()
	var body: Node = rig_root.find_child("body", true, false)
	_assert_true(body is Polygon2D and body.get_parent() == rig_root, "mixed: body skinned sibling")

	# The mouth sprite resolves (no bone/sprite name collision).
	var mouth: Node = skeleton.find_child("mouth", true, false)
	_assert_true(mouth is Sprite2D, "mixed: mouth is Sprite2D")

	# The bone-attached face slot anchors at the skeleton origin so the absolute-
	# baked attachments render where authored (cumulative-rest fix).
	var slot: Node = skeleton.find_child("face_slot", true, false)
	_assert_true(slot is Node2D, "mixed: face_slot present")
	if slot is Node2D:
		var gp: Vector2 = (slot as Node2D).global_position
		_assert_near(gp.x, 0.0, "mixed: face_slot at skeleton origin x")
		_assert_near(gp.y, 0.0, "mixed: face_slot at skeleton origin y")

	# The spine bob plays VERTICALLY (parent-local anim-delta fix): sampling the
	# bob peak displaces the spine on screen Y, not X.
	var player: AnimationPlayer = character.get_node("AnimationPlayer")
	var spine := skeleton.find_child("spine", true, false) as Node2D
	if player.has_animation("mixed_anim") and spine != null:
		var rest := spine.global_position
		player.play("mixed_anim")
		player.seek(0.458333, true)
		var delta := spine.global_position - rest
		_assert_true(
			absf(delta.y) > absf(delta.x) * 5.0, "mixed: spine bob is vertical not sideways"
		)


func _run_mouth_drive_checks() -> void:
	var character := _build("res://examples/mouth_drive/mouth_drive.proscenio")
	if character == null:
		_fail("mouth_drive: could not load golden")
		return
	var player: AnimationPlayer = character.get_node("AnimationPlayer")
	_assert_true(player.has_animation("mouth_drive_anim"), "mouth_drive: anim present")
	if not player.has_animation("mouth_drive_anim"):
		return
	var anim := player.get_animation("mouth_drive_anim")
	# Find the sprite_frame value track on the mouth and read its keyed frames.
	var frames: Array[int] = []
	for ti in anim.get_track_count():
		var path := str(anim.track_get_path(ti))
		if anim.track_get_type(ti) == Animation.TYPE_VALUE and path.ends_with(":frame"):
			for ki in anim.track_get_key_count(ti):
				# track_get_key_value returns Variant; the frame keys are floats.
				var value: float = anim.track_get_key_value(ti, ki)
				frames.append(int(value))
	# Out-of-range driver values wrap (4->0, 5->1) to match Blender's preview,
	# instead of clamping to 3 and collapsing the motion to a stub.
	_assert_eq(
		str(frames),
		str([2, 1, 0, 3, 0, 2, 3, 0, 1, 0, 3, 2]),
		"mouth_drive: sprite frames wrap (not clamp)",
	)


func _descendants(node: Node, type_name: String) -> Array:
	var out: Array = []
	for child in node.get_children():
		if child.is_class(type_name):
			out.append(child)
		out.append_array(_descendants(child, type_name))
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


func _assert_near(actual: float, expected: float, label: String) -> void:
	if absf(actual - expected) < 0.01:
		_passes += 1
		print("  ok  %s" % label)
	else:
		_fail("%s - expected %.3f, got %.3f" % [label, expected, actual])


func _fail(msg: String) -> void:
	_failures.append(msg)
	push_error("FAIL: %s" % msg)


func _finish() -> void:
	if _failures.is_empty():
		print("test_golden_scenes: all %d checks passed" % _passes)
		quit(0)
	else:
		for failure: String in _failures:
			printerr("  - %s" % failure)
		printerr("test_golden_scenes: %d failure(s)" % _failures.size())
		quit(1)
