"""Headless: non-deform control bones never reach the Godot export.

Runs INSIDE Blender via ``run_operator_tests.py``. The Toggle IK wiring creates
a non-deform ``.IK`` control bone; the export is a deform skeleton for
``Polygon2D`` skinning, so that control must be absent from both the skeleton
``bones[]`` and from every animation track (spec 056, decision 4A - the general
``use_deform=False`` filter). The pure projection-level guards are unit-tested in
``tests/writer/test_skeleton.py`` and ``tests/writer/test_animations.py``; this
proves the whole ``export()`` path drops the control end to end.
"""

from __future__ import annotations

import json
from pathlib import Path

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


def test_control_bone_absent_from_skeleton_and_tracks(
    automesh_fixture: None, tmp_path: Path
) -> None:
    from proscenio.exporters.godot import writer

    rig = _enter_pose_with_active_bone("automesh.hand_rig", "fingertip")
    try:
        assert "FINISHED" in bpy.ops.proscenio.toggle_ik_chain()
        control_name = rig.pose.bones["fingertip"].constraints["Proscenio IK"].subtarget
        assert control_name in rig.data.bones, "test precondition: control bone created"
        assert rig.data.bones[control_name].use_deform is False

        # Animate the control so it would emit an animation track if not filtered.
        control = rig.pose.bones[control_name]
        control.location = (0.0, 0.0, 0.0)
        inserted_first = control.keyframe_insert(data_path="location", frame=1)
        assert inserted_first, "test precondition: control keyframe inserted"
        control.location = (0.2, 0.0, 0.3)
        inserted_second = control.keyframe_insert(data_path="location", frame=10)
        assert inserted_second, "test precondition: control keyframe inserted"
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")

    out = tmp_path / "leak.proscenio"
    writer.export(out, pixels_per_unit=100.0)
    doc = json.loads(out.read_text(encoding="utf-8"))

    skeleton_names = [b["name"] for b in doc["skeleton"]["bones"]]
    assert control_name not in skeleton_names, "control bone leaked into skeleton bones[]"
    assert "fingertip" in skeleton_names, "deform chain bone wrongly dropped"

    track_targets = {
        track["target"] for anim in doc.get("animations", []) for track in anim["tracks"]
    }
    assert control_name not in track_targets, "control bone leaked into an animation track"


def test_excluded_deform_bone_absent_from_export(automesh_fixture: None, tmp_path: Path) -> None:
    # A deform bone the rigger pinned off the export (proscenio.exclude_from_export
    # via the Skeleton list toggle) must drop from both the skeleton and any
    # animation track, exactly like a non-deform control - the rig-helper path.
    from proscenio.exporters.godot import writer

    rig = _enter_pose_with_active_bone("automesh.hand_rig", "fingertip")
    try:
        assert rig.data.bones["fingertip"].use_deform is True, "test precondition: deform bone"
        rig.data.bones["fingertip"].proscenio.exclude_from_export = True

        tip = rig.pose.bones["fingertip"]
        tip.location = (0.0, 0.0, 0.0)
        assert tip.keyframe_insert(data_path="location", frame=1)
        tip.location = (0.2, 0.0, 0.3)
        assert tip.keyframe_insert(data_path="location", frame=10)
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")

    out = tmp_path / "excluded.proscenio"
    writer.export(out, pixels_per_unit=100.0)
    doc = json.loads(out.read_text(encoding="utf-8"))

    skeleton_names = [b["name"] for b in doc["skeleton"]["bones"]]
    assert "fingertip" not in skeleton_names, "excluded deform bone leaked into skeleton bones[]"

    track_targets = {
        track["target"] for anim in doc.get("animations", []) for track in anim["tracks"]
    }
    assert "fingertip" not in track_targets, "excluded deform bone leaked into an animation track"
