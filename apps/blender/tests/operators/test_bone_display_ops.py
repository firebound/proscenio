"""Headless tests for the spec 069 bone-display + Rig UI operators.

Runs INSIDE Blender via ``run_operator_tests.py``. Exercises the real operators
against a built rig with bone collections, asserting the business effect:

- the per-bone favorite and Relative Parenting toggles flip the real bone state
  (and prove ``Bone.use_relative_parent`` is writable on the data bone, the lock
  the design rests on);
- ``select_bone_collection`` selects exactly the collection's bones;
- ``color_bone_collection`` applies a palette to every bone in the collection;
- ``toggle_bone_export`` flips the per-bone export-exclusion flag.
"""

from __future__ import annotations

import bpy


def _make_rig(name: str) -> bpy.types.Object:
    """A 3-bone rig: root -> spine (connected child) -> tip (disconnected child)."""
    arm_data = bpy.data.armatures.new(name + "_data")
    arm = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    root = arm_data.edit_bones.new("root")
    root.head = (0.0, 0.0, 0.0)
    root.tail = (0.0, 0.0, 1.0)
    spine = arm_data.edit_bones.new("spine")
    spine.head = (0.0, 0.0, 1.0)
    spine.tail = (0.0, 0.0, 2.0)
    spine.parent = root
    spine.use_connect = True
    tip = arm_data.edit_bones.new("tip")
    tip.head = (0.5, 0.0, 2.0)
    tip.tail = (0.5, 0.0, 3.0)
    tip.parent = spine
    tip.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def _collection_with(arm: bpy.types.Object, name: str, bone_names: tuple[str, ...]):
    """Create a bone collection and assign the named bones to it."""
    collection = arm.data.collections.new(name)
    for bone_name in bone_names:
        collection.assign(arm.data.bones[bone_name])
    return collection


def _enter_pose(arm: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")


def _bone_selected(arm: bpy.types.Object, name: str) -> bool:
    pose_bone = arm.pose.bones[name]
    return bool(pose_bone.select if hasattr(pose_bone, "select") else pose_bone.bone.select)


# --- per-bone favorite ---------------------------------------------------


def test_toggle_bone_favorite_flips_the_flag(automesh_fixture):
    arm = _make_rig("fav_rig")
    assert arm.data.bones["spine"].proscenio.is_favorite is False

    bpy.ops.proscenio.toggle_bone_favorite(armature_name="fav_rig", bone_name="spine")
    assert arm.data.bones["spine"].proscenio.is_favorite is True

    bpy.ops.proscenio.toggle_bone_favorite(armature_name="fav_rig", bone_name="spine")
    assert arm.data.bones["spine"].proscenio.is_favorite is False


def test_toggle_bone_favorite_cancels_for_missing_bone(automesh_fixture):
    _make_rig("fav_rig2")
    result = bpy.ops.proscenio.toggle_bone_favorite(armature_name="fav_rig2", bone_name="nope")
    assert "CANCELLED" in result


# --- per-bone export exclusion -------------------------------------------


def test_toggle_bone_export_flips_exclude_flag(automesh_fixture):
    arm = _make_rig("exp_rig")
    assert arm.data.bones["spine"].proscenio.exclude_from_export is False

    bpy.ops.proscenio.toggle_bone_export(armature_name="exp_rig", bone_name="spine")
    assert arm.data.bones["spine"].proscenio.exclude_from_export is True

    bpy.ops.proscenio.toggle_bone_export(armature_name="exp_rig", bone_name="spine")
    assert arm.data.bones["spine"].proscenio.exclude_from_export is False


def test_toggle_bone_export_cancels_for_missing_bone(automesh_fixture):
    _make_rig("exp_rig2")
    result = bpy.ops.proscenio.toggle_bone_export(armature_name="exp_rig2", bone_name="nope")
    assert "CANCELLED" in result


# --- relative parenting toggle (data-bone write access) --------------------


def test_toggle_relative_parent_flips_use_relative_parent(automesh_fixture):
    # Proves Bone.use_relative_parent is writable on the data bone in Object
    # mode - the design's whole premise for making this a one-click toggle.
    arm = _make_rig("rel_rig")
    assert arm.data.bones["tip"].use_relative_parent is False

    bpy.ops.proscenio.toggle_bone_relative_parent(armature_name="rel_rig", bone_name="tip")
    assert arm.data.bones["tip"].use_relative_parent is True

    bpy.ops.proscenio.toggle_bone_relative_parent(armature_name="rel_rig", bone_name="tip")
    assert arm.data.bones["tip"].use_relative_parent is False


# --- Rig UI: select a whole collection ------------------------------------


def test_select_bone_collection_selects_its_bones(automesh_fixture):
    arm = _make_rig("sel_rig")
    _collection_with(arm, "Arm", ("spine", "tip"))
    _enter_pose(arm)
    # Seed a selection outside the collection so the replace semantics are real.
    bpy.ops.proscenio.select_bone_by_name(armature_name="sel_rig", bone_name="root")

    bpy.ops.proscenio.select_bone_collection(armature_name="sel_rig", collection_name="Arm")

    assert _bone_selected(arm, "spine") is True
    assert _bone_selected(arm, "tip") is True
    assert _bone_selected(arm, "root") is False


def test_select_bone_collection_cancels_for_empty_collection(automesh_fixture):
    arm = _make_rig("sel_rig2")
    arm.data.collections.new("Empty")
    _enter_pose(arm)
    result = bpy.ops.proscenio.select_bone_collection(
        armature_name="sel_rig2", collection_name="Empty"
    )
    assert "CANCELLED" in result


# --- per-collection color ------------------------------------------------


def test_color_bone_collection_applies_palette_to_all(automesh_fixture):
    arm = _make_rig("color_rig")
    _collection_with(arm, "Arm", ("spine", "tip"))

    bpy.ops.proscenio.color_bone_collection(
        armature_name="color_rig", collection_name="Arm", palette="THEME03"
    )

    assert arm.data.bones["spine"].color.palette == "THEME03"
    assert arm.data.bones["tip"].color.palette == "THEME03"
    # A bone outside the collection is untouched.
    assert arm.data.bones["root"].color.palette == "DEFAULT"


def test_color_bone_collection_reaches_nested_children(automesh_fixture):
    # A parent collection that holds bones only in its children must still
    # resolve them - the reported "collection 'arms' has no bones" regression.
    arm = _make_rig("nested_rig")
    parent = arm.data.collections.new("arms")
    child = arm.data.collections.new("arm.L", parent=parent)
    child.assign(arm.data.bones["spine"])
    child.assign(arm.data.bones["tip"])

    result = bpy.ops.proscenio.color_bone_collection(
        armature_name="nested_rig", collection_name="arms", palette="THEME05"
    )

    assert "FINISHED" in result
    assert arm.data.bones["spine"].color.palette == "THEME05"
    assert arm.data.bones["tip"].color.palette == "THEME05"
