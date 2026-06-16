"""Headless tests for the slot bone-follow operators.

Runs INSIDE Blender via ``run_operator_tests.py``. Builds a one-bone armature
+ an object-parented slot Empty, then drives bind/unbind through bpy.ops and
asserts the constraint, the slot_bone field, and the rest/posed follow.
"""

from __future__ import annotations

import bpy
import pytest


def _make_rig(bone: str = "arm") -> bpy.types.Object:
    arm_data = bpy.data.armatures.new("rig")
    arm = bpy.data.objects.new("rig", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones.new(bone)
    eb.head = (0.0, 0.0, 0.0)
    eb.tail = (0.0, 1.0, 0.0)  # +Y, into the screen (in-plane convention)
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def _make_slot(arm: bpy.types.Object, name: str = "weapon") -> bpy.types.Object:
    empty = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(empty)
    empty.parent = arm
    empty.parent_type = "OBJECT"
    empty.location = (0.0, 1.0, 0.0)  # at the bone tail
    empty.proscenio.is_slot = True
    child = bpy.data.objects.new(name + "_att", bpy.data.meshes.new("att"))
    bpy.context.scene.collection.objects.link(child)
    child.parent = empty
    child.parent_type = "OBJECT"
    bpy.context.view_layer.objects.active = empty
    bpy.context.view_layer.update()
    return empty


def _activate(obj: bpy.types.Object) -> None:
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def test_bind_adds_named_constraint_and_writes_field(automesh_fixture):
    arm = _make_rig()
    empty = _make_slot(arm)
    _activate(empty)

    result = bpy.ops.proscenio.bind_slot_to_bone(bone_name="arm")
    assert "FINISHED" in result

    con = empty.constraints.get("Proscenio Slot Follow")
    assert con is not None and con.type == "CHILD_OF"
    assert con.target is arm and con.subtarget == "arm"
    assert empty.proscenio.slot_bone == "arm"
    assert empty["proscenio_slot_bone"] == "arm"
    assert empty.parent_type == "OBJECT"  # never bone-parented


def test_bind_keeps_slot_at_rest_then_follows_pose(automesh_fixture):
    arm = _make_rig()
    empty = _make_slot(arm)
    _activate(empty)
    before = empty.matrix_world.translation.copy()

    bpy.ops.proscenio.bind_slot_to_bone(bone_name="arm")
    bpy.context.view_layer.update()
    # ``matrix_world.translation`` aliases the live world matrix, so snapshot it
    # before posing or the next view_layer.update() mutates it in place and the
    # follow delta below reads as zero.
    at_rest = empty.matrix_world.translation.copy()
    assert (at_rest - before).length == pytest.approx(0.0, abs=1e-4), "moved at rest"

    # Pose the bone; the slot must ride the delta.
    arm.pose.bones["arm"].rotation_mode = "XYZ"
    arm.pose.bones["arm"].rotation_euler = (0.5, 0.0, 0.0)
    bpy.context.view_layer.update()
    posed = empty.matrix_world.translation
    assert (posed - at_rest).length > 1e-3, "slot did not follow the posed bone"


def test_rebind_does_not_stack_constraints(automesh_fixture):
    arm = _make_rig()
    empty = _make_slot(arm)
    _activate(empty)
    bpy.ops.proscenio.bind_slot_to_bone(bone_name="arm")
    bpy.ops.proscenio.bind_slot_to_bone(bone_name="arm")
    follow = [c for c in empty.constraints if c.name == "Proscenio Slot Follow"]
    assert len(follow) == 1


def test_unbind_removes_constraint_and_clears_field(automesh_fixture):
    arm = _make_rig()
    empty = _make_slot(arm)
    _activate(empty)
    bpy.ops.proscenio.bind_slot_to_bone(bone_name="arm")

    result = bpy.ops.proscenio.unbind_slot_from_bone()
    assert "FINISHED" in result
    assert empty.constraints.get("Proscenio Slot Follow") is None
    assert empty.proscenio.slot_bone == ""
    assert "proscenio_slot_bone" not in empty


def test_bind_unknown_bone_cancels(automesh_fixture):
    arm = _make_rig()
    empty = _make_slot(arm)
    _activate(empty)
    with pytest.raises(RuntimeError, match="no bone"):
        bpy.ops.proscenio.bind_slot_to_bone(bone_name="ghost")


def test_create_slot_pose_bone_uses_follow_not_bone_parent(automesh_fixture):
    arm = _make_rig()
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    arm.data.bones.active = arm.data.bones["arm"]

    result = bpy.ops.proscenio.create_slot()
    assert "FINISHED" in result
    bpy.ops.object.mode_set(mode="OBJECT")

    empty = bpy.context.view_layer.objects.active
    assert empty.proscenio.is_slot is True
    # The migrated path object-parents + follows; it never bone-parents.
    assert empty.parent is arm
    assert empty.parent_type == "OBJECT"
    assert empty.constraints.get("Proscenio Slot Follow") is not None
    assert empty.proscenio.slot_bone == "arm"
    # Anchored at the bone tail (world (0,1,0)).
    bpy.context.view_layer.update()
    tail = empty.matrix_world.translation
    assert tail.y == pytest.approx(1.0, abs=1e-4)
