"""Headless: Bake Current Pose keys only the bone's active rotation channel.

Runs INSIDE Blender via ``run_operator_tests.py``. The bake used to insert
keyframes on both ``rotation_quaternion`` and ``rotation_euler`` regardless of
the bone's ``rotation_mode``, leaving a dead fcurve on the unused channel that
fights the live one on playback. It now bakes only the channel the mode uses.
"""

from __future__ import annotations

import bpy


def test_rotation_data_path_matches_mode() -> None:
    from proscenio.operators.pose_library import _rotation_data_path

    assert _rotation_data_path("QUATERNION") == "rotation_quaternion"
    assert _rotation_data_path("AXIS_ANGLE") == "rotation_axis_angle"
    assert _rotation_data_path("XYZ") == "rotation_euler"
    assert _rotation_data_path("ZYX") == "rotation_euler"


def test_bake_keys_only_the_matching_rotation_channel(automesh_fixture: None) -> None:
    rig = bpy.data.objects["automesh.hand_rig"]
    bpy.context.view_layer.objects.active = rig
    for other in bpy.context.selected_objects:
        other.select_set(False)
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    try:
        for pose_bone in rig.pose.bones:
            pose_bone.rotation_mode = "XYZ"
        result = bpy.ops.proscenio.bake_current_pose()
        assert "FINISHED" in result

        from proscenio.core._shared.action_fcurves import action_fcurves

        action = rig.animation_data.action
        paths = {fc.data_path for fc in action_fcurves(action)}
        assert any(p.endswith(".rotation_euler") for p in paths), "no euler channel baked"
        assert not any(".rotation_quaternion" in p for p in paths), "dead quaternion fcurve baked"
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")
