@tool
extends SceneTree

# Headless coverage for slot anchoring under a transformed bone chain.
#
# A bone-attached slot must sit at the SKELETON ORIGIN at rest: its mesh / sprite
# attachments are baked in absolute screen space, so the slot Node2D has to
# cancel the bone's full cumulative rest transform (not just its parent-local
# rest) and let only the bone's pose delta move the attachments. Bone2D's
# get_skeleton_rest() returns the parent-local rest in this Godot version, so a
# slot under a bone whose parent is rotated landed at the wrong place (the
# mixed_feature face slot drifted off to the side).
#
# Run from the apps/godot project root:
#
#     godot --headless --script res://tests/test_slot_anchor.gd

const SkeletonBuilder := preload("res://addons/proscenio/builders/skeleton_builder.gd")
const SlotBuilder := preload("res://addons/proscenio/builders/slot_builder.gd")
const ProscenioDocumentRes := preload(
	"res://addons/proscenio/schema_bindings/proscenio_document.gd"
)

var _failures: Array[String] = []
var _passes: int = 0  # gdlint: ignore=unused-private-class-variable


func _initialize() -> void:
	_run_anchor_check()
	_finish()


# A rotated `root` (-90deg, like a +Z spine root) with a child bone offset along
# it, and a slot anchored to the child. The child's cumulative rest is non-
# trivial, so a parent-local-only cancel would misplace the slot.
func _skeleton_document() -> ProscenioDocumentRes:
	return (
		ProscenioDocumentRes
		. from_dict(
			{
				"name": "anchor_probe",
				"skeleton":
				{
					"bones":
					[
						{
							"name": "root",
							"position": [0.0, 40.0],
							"rotation": -1.5708,
							"length": 40.0
						},
						{
							"name": "child",
							"parent": "root",
							"position": [60.0, 0.0],
							"rotation": 0.0,
							"length": 30.0,
						},
					]
				},
				"slots": [{"name": "s.slot", "bone": "child", "attachments": [], "default": ""}],
			}
		)
	)


func _run_anchor_check() -> void:
	var document := _skeleton_document()
	var skeleton := SkeletonBuilder.build(document.skeleton)
	var character := Node2D.new()
	character.name = "char"
	get_root().add_child(character)
	character.add_child(skeleton)

	SlotBuilder.build(skeleton, document.slots)

	var slot: Node2D = skeleton.find_child("s_slot", true, false)
	if slot == null:
		_fail("anchor: slot node 's_slot' not built")
		return
	# At rest the slot must land on the skeleton origin so absolute-baked
	# attachments render where they were authored.
	var gp := slot.global_position
	_assert_near(gp.x, 0.0, "anchor: slot global x at skeleton origin")
	_assert_near(gp.y, 0.0, "anchor: slot global y at skeleton origin")


func _assert_near(actual: float, expected: float, label: String) -> void:
	if abs(actual - expected) < 0.01:
		_passes += 1
		print("  ok  %s" % label)
	else:
		_fail("%s - expected %.3f, got %.3f" % [label, expected, actual])


func _fail(msg: String) -> void:
	_failures.append(msg)
	push_error("FAIL: %s" % msg)


func _finish() -> void:
	if _failures.is_empty():
		print("test_slot_anchor: all %d checks passed" % _passes)
		quit(0)
	else:
		for failure: String in _failures:
			printerr("  - %s" % failure)
		printerr("test_slot_anchor: %d failure(s)" % _failures.size())
		quit(1)
