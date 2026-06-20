"""Headless: Bake IK to Keyframes restores the pre-bake bone selection.

Runs INSIDE Blender via ``run_operator_tests.py``. The bake scopes ``nla.bake``
to the IK chain by selecting only those bones; it now snapshots and restores the
artist's selection afterwards instead of leaving the chain-only selection behind.
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


def test_bake_ik_restores_selection(automesh_fixture: None) -> None:
    from proscenio.operators.armature.authoring_ik import _get_bone_select, _set_bone_select

    rig = _enter_pose_with_active_bone("automesh.hand_rig", "fingertip")
    try:
        assert "FINISHED" in bpy.ops.proscenio.toggle_ik_chain()

        # Select every bone so the snapshot differs from the chain-only set the
        # bake selects internally - that difference is what proves restoration.
        for pose_bone in rig.pose.bones:
            _set_bone_select(pose_bone, True)
        before = {pb.name for pb in rig.pose.bones if _get_bone_select(pb)}

        result = bpy.ops.proscenio.bake_ik_chain()
        assert "FINISHED" in result

        after = {pb.name for pb in rig.pose.bones if _get_bone_select(pb)}
        assert after == before, "bake left the chain-only selection instead of restoring"
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")
