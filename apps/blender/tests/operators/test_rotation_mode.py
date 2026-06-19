"""Headless tests for Convert rotation to Euler.

Runs INSIDE Blender via ``run_operator_tests.py``. Drive-from-Bone reads bone
rotation as XYZ Euler; this operator is the one-click fix that flips a bone's
``rotation_mode`` to XYZ (Blender converts the stored rotation). Covers both
scopes: the active bone only, and every bone in the armature.
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


def test_convert_active_bone_to_euler(automesh_fixture):
    rig = _enter_pose_with_active_bone("automesh.hand_rig", "fingertip")
    try:
        rig.pose.bones["fingertip"].rotation_mode = "QUATERNION"
        result = bpy.ops.proscenio.convert_rotation_to_euler(scope="ACTIVE")
        assert "FINISHED" in result
        assert rig.pose.bones["fingertip"].rotation_mode == "XYZ"
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")


def test_convert_active_bone_leaves_siblings_untouched(automesh_fixture):
    rig = _enter_pose_with_active_bone("automesh.hand_rig", "fingertip")
    try:
        for pose_bone in rig.pose.bones:
            pose_bone.rotation_mode = "QUATERNION"
        bpy.ops.proscenio.convert_rotation_to_euler(scope="ACTIVE")
        assert rig.pose.bones["fingertip"].rotation_mode == "XYZ"
        others = [pb for pb in rig.pose.bones if pb.name != "fingertip"]
        assert others, "fixture should have more than one bone for this assertion"
        assert all(pb.rotation_mode == "QUATERNION" for pb in others)
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")


def test_convert_all_bones_to_euler(automesh_fixture):
    rig = _enter_pose_with_active_bone("automesh.hand_rig", "fingertip")
    try:
        for pose_bone in rig.pose.bones:
            pose_bone.rotation_mode = "QUATERNION"
        result = bpy.ops.proscenio.convert_rotation_to_euler(scope="ALL")
        assert "FINISHED" in result
        assert all(pb.rotation_mode == "XYZ" for pb in rig.pose.bones)
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")
