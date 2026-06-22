"""Headless tests for the Skeleton list multi-select + cross-list highlight sync.

Runs INSIDE Blender via ``run_operator_tests.py``. Covers the spec 049 list
work that is headless-provable:

- the bone select operator's Shift/Ctrl routing (plain replaces, extend keeps,
  toggle flips) against a posed multi-bone rig, plus the active-bone-index sync;
- the cross-list deselect handlers: the Slots highlight follows the active slot
  object, and the Skeleton highlight follows the picked armature's active bone.

The multi-select radio markers and the highlight under sort/filter are GUI-only.
"""

from __future__ import annotations

import bpy


def _bone_selected(arm: bpy.types.Object, name: str) -> bool:
    """Read a pose bone's selection the version-robust way the addon does.

    5.x exposes ``PoseBone.select`` (a flag distinct from the wrapped
    ``Bone.select``); 4.2 has no ``PoseBone.select`` and the flag lives on
    ``PoseBone.bone``. Mirrors ``_get_select`` in the production
    ``bone_select`` helper so the assertions read whatever the operator wrote
    on either Blender, instead of an attribute that only one version exposes.
    """
    pose_bone = arm.pose.bones[name]
    return bool(pose_bone.select if hasattr(pose_bone, "select") else pose_bone.bone.select)


def _make_rig(name: str, bones: tuple[str, ...]) -> bpy.types.Object:
    arm_data = bpy.data.armatures.new(name + "_data")
    arm = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for i, bone_name in enumerate(bones):
        edit_bone = arm_data.edit_bones.new(bone_name)
        edit_bone.head = (float(i), 0.0, 0.0)
        edit_bone.tail = (float(i), 0.0, 1.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def _enter_pose(arm: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")


# --- bone multi-select: plain / Shift / Ctrl ------------------------------


def test_bone_plain_click_selects_only_one(automesh_fixture):
    arm = _make_rig("plain_rig", ("b0", "b1"))
    _enter_pose(arm)
    bpy.ops.proscenio.select_bone_by_name(armature_name="plain_rig", bone_name="b0")

    # A plain click on b1 (no extend/toggle) clears b0 and selects only b1.
    bpy.ops.proscenio.select_bone_by_name(armature_name="plain_rig", bone_name="b1")

    assert _bone_selected(arm, "b1") is True
    assert _bone_selected(arm, "b0") is False
    assert arm.data.bones.active.name == "b1"


def test_bone_extend_keeps_the_prior_selection(automesh_fixture):
    arm = _make_rig("ext_rig", ("b0", "b1"))
    _enter_pose(arm)
    bpy.ops.proscenio.select_bone_by_name(armature_name="ext_rig", bone_name="b0")

    # Shift-click (extend=True) adds b1 without dropping b0.
    bpy.ops.proscenio.select_bone_by_name(armature_name="ext_rig", bone_name="b1", extend=True)

    assert _bone_selected(arm, "b0") is True
    assert _bone_selected(arm, "b1") is True


def test_bone_toggle_deselects_an_already_selected_bone(automesh_fixture):
    arm = _make_rig("tog_rig", ("b0", "b1"))
    _enter_pose(arm)
    bpy.ops.proscenio.select_bone_by_name(armature_name="tog_rig", bone_name="b0")
    bpy.ops.proscenio.select_bone_by_name(armature_name="tog_rig", bone_name="b1", extend=True)

    # Ctrl-click (toggle=True) on b1, already selected, deselects only b1.
    bpy.ops.proscenio.select_bone_by_name(armature_name="tog_rig", bone_name="b1", toggle=True)

    assert _bone_selected(arm, "b1") is False
    assert _bone_selected(arm, "b0") is True


def test_bone_toggle_adds_an_unselected_bone(automesh_fixture):
    arm = _make_rig("tog2_rig", ("b0", "b1"))
    _enter_pose(arm)
    bpy.ops.proscenio.select_bone_by_name(armature_name="tog2_rig", bone_name="b0")

    # Ctrl-click on b1, not yet selected, adds it and makes it active.
    bpy.ops.proscenio.select_bone_by_name(armature_name="tog2_rig", bone_name="b1", toggle=True)

    assert _bone_selected(arm, "b0") is True
    assert _bone_selected(arm, "b1") is True
    assert arm.data.bones.active.name == "b1"


def test_bone_click_cancels_when_armature_missing(automesh_fixture):
    result = bpy.ops.proscenio.select_bone_by_name(armature_name="nope_rig", bone_name="b0")

    assert "CANCELLED" in result


def test_bone_click_syncs_active_index(automesh_fixture):
    arm = _make_rig("idx_rig", ("b0", "b1", "b2"))
    _enter_pose(arm)
    scene = bpy.context.scene
    scene.proscenio.active_bone_index = 0

    bpy.ops.proscenio.select_bone_by_name(armature_name="idx_rig", bone_name="b2")

    assert scene.proscenio.active_bone_index == 2


# --- bone_select helper ---------------------------------------------------


def test_bone_is_selected_reads_the_pose_flag(automesh_fixture):
    from proscenio.core.bpy_helpers._shared.bone_select import bone_is_selected, bone_select_only

    arm = _make_rig("read_rig", ("b0", "b1"))
    _enter_pose(arm)
    bone_select_only(arm, "b0", "POSE")

    assert bone_is_selected(arm, "b0", "POSE") is True
    assert bone_is_selected(arm, "b1", "POSE") is False


# --- cross-list highlight sync --------------------------------------------


def test_sync_bone_index_follows_active_bone(automesh_fixture):
    from proscenio.properties._handlers import sync_bone_index_to_active_bone

    arm = _make_rig("sync_rig", ("b0", "b1", "b2"))
    scene = bpy.context.scene
    scene.proscenio.active_armature = arm
    arm.data.bones.active = arm.data.bones["b2"]
    # Seed a value that differs from the target so the early-out cannot make
    # this a false pass.
    scene.proscenio.active_bone_index = 0

    sync_bone_index_to_active_bone(scene)

    assert scene.proscenio.active_bone_index == 2


def test_sync_bone_index_noop_without_picked_armature(automesh_fixture):
    from proscenio.properties._handlers import sync_bone_index_to_active_bone

    scene = bpy.context.scene
    scene.proscenio.active_armature = None
    scene.proscenio.active_bone_index = 5

    sync_bone_index_to_active_bone(scene)

    assert scene.proscenio.active_bone_index == 5


def test_sync_slots_follows_active_slot(automesh_fixture):
    from proscenio.core.outliner_view import source_index_for_name
    from proscenio.properties._handlers import sync_slots_to_active_object

    empty = bpy.data.objects.new("slotA", None)
    bpy.context.scene.collection.objects.link(empty)
    empty.proscenio.is_slot = True
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = empty
    scene = bpy.context.scene
    idx = source_index_for_name(bpy.data.objects, "slotA")
    assert idx is not None
    scene.proscenio.active_slot_index = idx + 1

    sync_slots_to_active_object(scene)

    assert scene.proscenio.active_slot_index == idx


def test_sync_slots_ignores_non_slot_active(automesh_fixture):
    from proscenio.properties._handlers import sync_slots_to_active_object

    mesh = bpy.data.objects.new("plain_mesh", bpy.data.meshes.new("m"))
    bpy.context.scene.collection.objects.link(mesh)
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = mesh
    scene = bpy.context.scene
    scene.proscenio.active_slot_index = 2

    sync_slots_to_active_object(scene)

    assert scene.proscenio.active_slot_index == 2
