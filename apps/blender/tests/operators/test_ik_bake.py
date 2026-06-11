"""Headless end-to-end test for the IK bake gate + Bake IK operator.

Runs INSIDE Blender via ``run_operator_tests.py``. Builds the constrained
chain through the shipped Toggle IK wiring, animates only the control target
(the silent-wrong-export hazard), confirms the export validator trips on the
unbaked chain, bakes it through the one-click operator, and confirms the gate
clears and the chain bones now carry keyframes. The validator's pure rule logic
is unit-tested in ``tests/test_validation_export.py``.
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


def _bone_has_fcurve(rig: bpy.types.Object, bone_name: str) -> bool:
    from proscenio.core._shared.action_fcurves import (
        action_fcurves,  # type: ignore[import-not-found]
    )

    action = rig.animation_data.action
    needle = f'pose.bones["{bone_name}"]'
    return any(str(fc.data_path).startswith(needle) for fc in action_fcurves(action))


def _has_bake_error(scene: bpy.types.Scene) -> bool:
    from proscenio.core.validation.export import validate_export  # type: ignore[import-not-found]

    return any(i.severity == "error" and "Bake IK" in i.message for i in validate_export(scene))


def test_unbaked_ik_chain_trips_then_bake_clears_it(automesh_fixture):
    rig = _enter_pose_with_active_bone("automesh.hand_rig", "fingertip")
    try:
        bpy.ops.proscenio.toggle_ik_chain()
        target_name = rig.pose.bones["fingertip"].constraints["Proscenio IK"].subtarget

        # Animate only the IK control target across two frames - the chain bones
        # themselves stay unkeyed, which the writer would export as flat bones.
        target = rig.pose.bones[target_name]
        target.location = (0.0, 0.0, 0.0)
        target.keyframe_insert(data_path="location", frame=1)
        target.location = (0.2, 0.0, 0.3)
        target.keyframe_insert(data_path="location", frame=10)
        assert not _bone_has_fcurve(rig, "fingertip"), "chain bone keyed before bake"

        assert _has_bake_error(bpy.context.scene), "gate did not trip on the unbaked chain"

        rig.data.bones.active = rig.data.bones["fingertip"]
        bpy.ops.proscenio.bake_ik_chain()

        assert _bone_has_fcurve(rig, "fingertip"), "bake left the chain bone unkeyed"
        assert not _has_bake_error(bpy.context.scene), "gate still trips after baking"
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")
