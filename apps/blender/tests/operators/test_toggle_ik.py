"""Headless tests for Toggle IK target wiring.

Runs INSIDE Blender via ``run_operator_tests.py``. The shipped toggle inserted
a targetless IK constraint that solved only while grabbing the constrained
bone; it must now create and wire a control target so the chain solves
standalone, and remove that control cleanly when toggled off without touching
the deform skeleton.
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


def test_toggle_on_wires_a_target(automesh_fixture):
    rig = _enter_pose_with_active_bone("automesh.hand_rig", "fingertip")
    try:
        result = bpy.ops.proscenio.toggle_ik_chain()
        assert "FINISHED" in result
        ik = rig.pose.bones["fingertip"].constraints.get("Proscenio IK")
        assert ik is not None
        assert ik.target is rig
        assert ik.subtarget != "", "constraint left targetless - solves only while grabbed"
        assert ik.subtarget in rig.data.bones, "target control bone was not created"
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")


def test_toggle_off_removes_constraint_and_target(automesh_fixture):
    rig = _enter_pose_with_active_bone("automesh.hand_rig", "fingertip")
    try:
        bpy.ops.proscenio.toggle_ik_chain()
        target_name = rig.pose.bones["fingertip"].constraints["Proscenio IK"].subtarget
        assert target_name in rig.data.bones
        bpy.ops.proscenio.toggle_ik_chain()
        assert rig.pose.bones["fingertip"].constraints.get("Proscenio IK") is None
        assert target_name not in rig.data.bones, "target control bone left behind on toggle off"
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")


def test_toggle_target_bone_is_non_deforming(automesh_fixture):
    rig = _enter_pose_with_active_bone("automesh.hand_rig", "fingertip")
    try:
        bpy.ops.proscenio.toggle_ik_chain()
        target_name = rig.pose.bones["fingertip"].constraints["Proscenio IK"].subtarget
        assert rig.data.bones[target_name].use_deform is False, "target would deform bound meshes"
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")
