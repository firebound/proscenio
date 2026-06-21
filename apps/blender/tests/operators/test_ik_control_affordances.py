"""Headless tests for the Rigify-style control-bone affordances (spec 056 call 5).

Runs INSIDE Blender via ``run_operator_tests.py``. When Toggle IK creates a
control bone it groups the bone into a reused "Proscenio Controls" bone
collection and tints it with a theme color, so the control reads as a control
rather than a deform bone in the viewport. The custom shape is deferred.
"""

from __future__ import annotations

import bpy


def _enter_pose_with_active_bone(rig_name: str, bone_name: str) -> bpy.types.Object:
    rig = bpy.data.objects[rig_name]
    bpy.context.view_layer.objects.active = rig
    for other in bpy.context.selected_objects:
        other.select_set(False)
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    rig.data.bones.active = rig.data.bones[bone_name]
    return rig


def test_control_bone_joins_controls_collection_with_theme(automesh_fixture: None) -> None:
    from proscenio.operators.armature.authoring_ik import (
        _CONTROLS_COLLECTION,
        _CONTROLS_THEME,
    )

    rig = _enter_pose_with_active_bone("automesh.hand_rig", "fingertip")
    try:
        assert "FINISHED" in bpy.ops.proscenio.toggle_ik_chain()
        control_name = rig.pose.bones["fingertip"].constraints["Proscenio IK"].subtarget

        collection = rig.data.collections.get(_CONTROLS_COLLECTION)
        assert collection is not None, "Proscenio Controls collection was not created"
        member_names = {b.name for b in collection.bones}
        assert control_name in member_names, "control bone not assigned to the collection"

        bone = rig.data.bones[control_name]
        assert bone.color.palette == _CONTROLS_THEME, "control bone was not theme-tinted"
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")


def test_controls_collection_is_reused_across_chains(automesh_fixture: None) -> None:
    from proscenio.operators.armature.authoring_ik import _CONTROLS_COLLECTION

    rig = _enter_pose_with_active_bone("automesh.hand_rig", "fingertip")
    try:
        bpy.ops.proscenio.toggle_ik_chain()
        rig.data.bones.active = rig.data.bones["palm"]
        bpy.ops.proscenio.toggle_ik_chain()
        matches = [c for c in rig.data.collections if c.name == _CONTROLS_COLLECTION]
        assert len(matches) == 1, "a second chain created a duplicate controls collection"
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")
