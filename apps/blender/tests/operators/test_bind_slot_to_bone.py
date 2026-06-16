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


def _make_legacy_bone_parented_slot(
    arm: bpy.types.Object, name: str = "legacy_slot"
) -> bpy.types.Object:
    """A slot Empty real-bone-parented the old way (parent_type == 'BONE')."""
    empty = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(empty)
    empty.parent = arm
    empty.parent_type = "BONE"
    empty.parent_bone = "arm"
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


def test_bind_refuses_when_already_bound(automesh_fixture):
    arm = _make_rig()
    empty = _make_slot(arm)
    _activate(empty)
    bpy.ops.proscenio.bind_slot_to_bone(bone_name="arm")
    # A second Bind refuses (two-click flow: Unbind first); no stacked constraint.
    result = bpy.ops.proscenio.bind_slot_to_bone(bone_name="arm")
    assert "CANCELLED" in result
    follow = [c for c in empty.constraints if c.name == "Proscenio Slot Follow"]
    assert len(follow) == 1


def test_unbind_then_bind_rebinds_without_stacking(automesh_fixture):
    arm = _make_rig()
    empty = _make_slot(arm)
    _activate(empty)
    bpy.ops.proscenio.bind_slot_to_bone(bone_name="arm")
    bpy.ops.proscenio.unbind_slot_from_bone()
    bpy.ops.proscenio.bind_slot_to_bone(bone_name="arm")
    follow = [c for c in empty.constraints if c.name == "Proscenio Slot Follow"]
    assert len(follow) == 1
    assert empty.proscenio.slot_bone == "arm"


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
    # An unknown bone is reported + cancelled the way driver.py / selection.py
    # guard a bad bone_name, not raised as a Blender traceback.
    result = bpy.ops.proscenio.bind_slot_to_bone(bone_name="ghost")
    assert "CANCELLED" in result
    assert empty.constraints.get("Proscenio Slot Follow") is None


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


def test_bind_refuses_when_bone_parented(automesh_fixture):
    arm = _make_rig()
    empty = _make_legacy_bone_parented_slot(arm)
    _activate(empty)
    # Bind never strips a hand-authored bone parent - it refuses, leaving the
    # bone parent intact, and points the user to Unbind first.
    result = bpy.ops.proscenio.bind_slot_to_bone(bone_name="arm")
    assert "CANCELLED" in result
    assert empty.parent_type == "BONE"
    assert empty.constraints.get("Proscenio Slot Follow") is None


def test_unbind_then_bind_converts_bone_parent(automesh_fixture):
    arm = _make_rig()
    empty = _make_legacy_bone_parented_slot(arm)
    _activate(empty)
    # The explicit two-click conversion: Unbind drops the bone parent, Bind adds
    # the constraint follow.
    bpy.ops.proscenio.unbind_slot_from_bone()
    assert empty.parent_type == "OBJECT"
    assert empty.parent_bone == ""
    bpy.ops.proscenio.bind_slot_to_bone(bone_name="arm")
    assert empty.parent_type == "OBJECT"
    assert empty.constraints.get("Proscenio Slot Follow") is not None
    assert empty.proscenio.slot_bone == "arm"


def test_unbind_drops_legacy_bone_parent(automesh_fixture):
    arm = _make_rig()
    empty = _make_legacy_bone_parented_slot(arm)
    _activate(empty)

    result = bpy.ops.proscenio.unbind_slot_from_bone()
    assert "FINISHED" in result
    # Unbinding a legacy slot must also drop the real bone parent, or it would
    # stay bone-driven.
    assert empty.parent_type == "OBJECT"
    assert empty.parent_bone == ""
    assert empty.constraints.get("Proscenio Slot Follow") is None
    assert empty.proscenio.slot_bone == ""


def test_slot_follow_shape_reports_each_state(automesh_fixture):
    from proscenio.core.bpy_helpers.slot import slot_follow_shape  # type: ignore[import-not-found]

    arm = _make_rig()
    free = _make_slot(arm, name="free")
    assert slot_follow_shape(free) == "none"
    _activate(free)
    bpy.ops.proscenio.bind_slot_to_bone(bone_name="arm")
    assert slot_follow_shape(free) == "constraint"

    boned = _make_legacy_bone_parented_slot(arm, name="boned")
    assert slot_follow_shape(boned) == "bone_parent"

    inert = _make_slot(arm, name="inert")
    inert.proscenio.slot_bone = "arm"
    assert slot_follow_shape(inert) == "field_inert"


def test_bone_parent_collapses_only_for_in_plane_bone(automesh_fixture):
    from proscenio.core.bpy_helpers.slot import (
        bone_parent_collapses,  # type: ignore[import-not-found]
    )

    # +Y bone points into the screen - a bone parent stays flat.
    arm_y = _make_rig()
    assert bone_parent_collapses(_make_legacy_bone_parented_slot(arm_y, name="boned_y")) is False

    # +Z bone lies in the picture plane - a bone parent collapses the quads.
    arm_z_data = bpy.data.armatures.new("rig_z")
    arm_z = bpy.data.objects.new("rig_z", arm_z_data)
    bpy.context.scene.collection.objects.link(arm_z)
    bpy.context.view_layer.objects.active = arm_z
    bpy.ops.object.mode_set(mode="EDIT")
    ebz = arm_z_data.edit_bones.new("arm")
    ebz.head = (0.0, 0.0, 0.0)
    ebz.tail = (0.0, 0.0, 1.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    assert bone_parent_collapses(_make_legacy_bone_parented_slot(arm_z, name="boned_z")) is True
