@tool
extends SceneTree

# Headless coverage for the spec 080 sprite rest transform.
#
# A sprite element that carries `position` / `rotation` / `scale` (the
# document's absolute skeleton-space rest transform) must render at exactly
# that pose no matter what it parents under - a Bone2D with a non-trivial
# cumulative rest, a slot anchor, or the skeleton root. A legacy document
# without `position` keeps the old identity-local placement. A rigid
# bone-parented mesh keeps its identity local transform (its vertices are
# baked bone-local by the writer).
#
# Run from the apps/godot project root:
#
#     godot --headless --script res://tests/test_sprite_rest_transform.gd

const SkeletonBuilder := preload("res://addons/proscenio/builders/skeleton_builder.gd")
const SlotBuilder := preload("res://addons/proscenio/builders/slot_builder.gd")
const SpriteBuilder := preload("res://addons/proscenio/builders/sprite_builder.gd")
const MeshBuilder := preload("res://addons/proscenio/builders/mesh_builder.gd")
const ProscenioDocumentRes := preload(
	"res://addons/proscenio/schema_bindings/proscenio_document.gd"
)

var _failures: Array[String] = []
var _passes: int = 0  # gdlint: ignore=unused-private-class-variable


func _initialize() -> void:
	_run_rest_transform_checks()
	_finish()


# A rotated `root` (-90deg, a +Z spine) with a `child` offset along it - the
# child's cumulative rest is position (0, -20), rotation -90deg. Before spec
# 080 every sprite under `child` inherited that pose wholesale.
func _document() -> ProscenioDocumentRes:
	return (
		ProscenioDocumentRes
		. from_dict(
			{
				"name": "rest_probe",
				"skeleton":
				{
					"bones":
					[
						{
							"name": "root",
							"position": [0.0, 40.0],
							"rotation": -1.5707963,
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
				"slots":
				[{"name": "s.slot", "bone": "child", "attachments": ["s.badge"], "default": ""}],
				"elements":
				[
					{
						"type": "sprite",
						"name": "badge",
						"bone": "child",
						"position": [10.0, -50.0],
						"rotation": 0.35,
						"scale": [2.0, 3.0],
						"hframes": 1,
						"vframes": 1,
						"frame": 0,
						"centered": true,
					},
					{
						"type": "sprite",
						"name": "old_way",
						"bone": "child",
						"hframes": 1,
						"vframes": 1,
						"frame": 0,
						"centered": true,
					},
					{
						"type": "sprite",
						"name": "s.badge",
						"bone": "child",
						"position": [25.0, 5.0],
						"hframes": 1,
						"vframes": 1,
						"frame": 0,
						"centered": true,
					},
					{
						"type": "mesh",
						"name": "plank",
						"bone": "child",
						"texture_region": [0.0, 0.0, 1.0, 1.0],
						"polygon": [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0]],
						"uv": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]],
					},
				],
			}
		)
	)


func _run_rest_transform_checks() -> void:
	var document := _document()
	var skeleton := SkeletonBuilder.build(document.skeleton)
	var character := Node2D.new()
	character.name = "char"
	get_root().add_child(character)
	character.add_child(skeleton)

	var slot_map := SlotBuilder.build(skeleton, document.slots)
	SpriteBuilder.attach_elements(skeleton, document.elements, null, slot_map, "")
	MeshBuilder.attach_elements(skeleton, document.elements, null, slot_map, "")

	var child_bone: Node = skeleton.find_child("child", true, false)
	_assert_true(child_bone != null, "skeleton: child bone built")

	# A document rest transform renders at exactly that pose despite the
	# bone's cumulative -90deg rest.
	var badge: Sprite2D = skeleton.find_child("badge", true, false)
	_assert_true(badge != null, "badge: built")
	if badge != null:
		_assert_true(badge.get_parent() == child_bone, "badge: parented under its Bone2D")
		_assert_near(badge.global_position.x, 10.0, "badge: global x is the document rest x")
		_assert_near(badge.global_position.y, -50.0, "badge: global y is the document rest y")
		_assert_near(badge.global_rotation, 0.35, "badge: global rotation is the document rest")
		_assert_near(badge.global_scale.x, 2.0, "badge: global scale x is the document rest")
		_assert_near(badge.global_scale.y, 3.0, "badge: global scale y is the document rest")

	# A legacy document (no `position`) keeps the identity-local placement:
	# the sprite sits on the bone and inherits its cumulative rest.
	var old_way: Sprite2D = skeleton.find_child("old_way", true, false)
	_assert_true(old_way != null, "old_way: built")
	if old_way != null:
		_assert_true(old_way.get_parent() == child_bone, "old_way: parented under its Bone2D")
		_assert_true(old_way.transform == Transform2D.IDENTITY, "old_way: identity local kept")
		_assert_near(old_way.global_position.x, 0.0, "old_way: sits on the bone head x")
		_assert_near(old_way.global_position.y, -20.0, "old_way: sits on the bone head y")

	# Slot routing: the anchor already cancels the bone rest, so the same
	# formula must land the sprite at its absolute rest, not double-cancel.
	var slotted: Sprite2D = skeleton.find_child("s_badge", true, false)
	_assert_true(slotted != null, "slotted: built")
	if slotted != null:
		var anchor: Node = skeleton.find_child("s_slot", true, false)
		_assert_true(slotted.get_parent() == anchor, "slotted: routed under the slot anchor")
		_assert_near(slotted.global_position.x, 25.0, "slotted: global x is the document rest x")
		_assert_near(slotted.global_position.y, 5.0, "slotted: global y is the document rest y")

	# A rigid bone-parented mesh bakes its vertices bone-local, so its node
	# must keep the identity local transform (no rest-cancel).
	var plank: Polygon2D = skeleton.find_child("plank", true, false)
	_assert_true(plank != null, "plank: built")
	if plank != null:
		_assert_true(plank.get_parent() == child_bone, "plank: parented under its Bone2D")
		_assert_true(plank.transform == Transform2D.IDENTITY, "plank: identity local kept")


func _assert_near(actual: float, expected: float, label: String) -> void:
	if abs(actual - expected) < 0.01:
		_passes += 1
		print("  ok  %s" % label)
	else:
		_fail("%s - expected %.3f, got %.3f" % [label, expected, actual])


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
		print("test_sprite_rest_transform: all %d checks passed" % _passes)
		quit(0)
	else:
		for failure: String in _failures:
			printerr("  - %s" % failure)
		printerr("test_sprite_rest_transform: %d failure(s)" % _failures.size())
		quit(1)
