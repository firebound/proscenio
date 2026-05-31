"""Headless tests for Edit Weights modal (the paint work)."""

from __future__ import annotations

import bpy
import pytest


def _activate(name: str) -> bpy.types.Object:
    obj = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    return obj


def _set_picker(name: str) -> None:
    bpy.context.scene.proscenio.active_armature = bpy.data.objects[name]


def test_invoke_aborts_without_sidecar(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    # Do NOT bind - sidecar absent. The operator's poll() gate refuses
    # the call before invoke even fires, which surfaces as a poll-failed
    # RuntimeError from bpy.ops. Either way, the abort guarantee is the
    # same: no mode transition, no side effects on the active object.
    assert bpy.ops.proscenio.edit_weights.poll() is False
    with pytest.raises(RuntimeError, match=r"poll|sidecar|context"):
        bpy.ops.proscenio.edit_weights("INVOKE_DEFAULT")
    assert obj.mode != "WEIGHT_PAINT"


def test_invoke_enters_weight_paint_with_preset_applied(automesh_fixture):
    obj = _activate("hand")
    armature = bpy.data.objects["automesh.hand_rig"]
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    # Headless Blender cannot run modal operators end-to-end: bpy.ops
    # rejects INVOKE_DEFAULT for modals with "Invalid operator call"
    # (no event loop) and direct class instantiation of bpy.types.Operator
    # subclasses is forbidden ("bpy_struct.__new__ expected a single
    # argument"). Replicate the invoke setup block to verify its observable
    # side effects: mode == WEIGHT_PAINT and 2D-safe brush preset applied
    # (use_frontface off). The modal lifecycle proper is covered by manual
    # testing.
    from proscenio.core.bpy_helpers.skinning import (  # type: ignore[import-not-found]
        apply_paint_preset,
        read_mirror_flag,
    )

    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    if armature.mode != "POSE":
        bpy.ops.object.mode_set(mode="POSE")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if obj.mode != "WEIGHT_PAINT":
        bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    apply_paint_preset(bpy.context, mirror_x=read_mirror_flag(armature))
    assert obj.mode == "WEIGHT_PAINT"
    brush = bpy.context.tool_settings.weight_paint.brush
    assert bool(getattr(brush, "use_frontface", True)) is False


def test_stroke_flips_provenance_to_user_paint(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    # Drive the operator's stroke logic via the underlying class
    # rather than firing events (which the headless framework cannot pump).
    from proscenio.core.bpy_helpers.skinning import (
        StrokeDiffTracker,  # type: ignore[import-not-found]
    )
    from proscenio.core.skinning.sidecar_schema import from_json  # type: ignore[import-not-found]

    sidecar_before = from_json(obj["proscenio_weight_sidecar"])
    tracker = StrokeDiffTracker(obj, sidecar_before)
    obj.vertex_groups.active_index = obj.vertex_groups["wrist"].index
    tracker.snapshot_active_vg()
    # Mutate weights on the wrist group to simulate a stroke
    wrist = obj.vertex_groups["wrist"]
    target_verts = [v.index for v in obj.data.vertices[:5]]
    for vert_idx in target_verts:
        wrist.add([vert_idx], 0.42, "REPLACE")
    touched = tracker.flip_touched_after_stroke()
    assert touched >= 1
    sidecar_after = from_json(obj["proscenio_weight_sidecar"])
    user_paint_count = sum(1 for e in sidecar_after.entries if e.provenance == "user_paint")
    assert user_paint_count >= 1


def test_session_capture_restore_round_trip(automesh_fixture):
    obj = _activate("hand")
    armature = bpy.data.objects["automesh.hand_rig"]
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    from proscenio.core.bpy_helpers.skinning import (  # type: ignore[import-not-found]
        capture_session,
        restore_session,
        snapshot_bone_visibility,
        snapshot_paint_preset,
    )

    prior_mode = obj.mode
    prior_preset = snapshot_paint_preset(bpy.context)
    prior_visibility = snapshot_bone_visibility(armature)
    session = capture_session(
        bpy.context, obj, armature, prior_preset, prior_visibility, overlay_flag=False
    )
    # Mutate: switch to WEIGHT_PAINT
    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    assert obj.mode == "WEIGHT_PAINT"
    restore_session(bpy.context, session)
    assert obj.mode == prior_mode


def test_panel_button_present_when_sidecar_populated(automesh_fixture):
    _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    # The panel draw runs in the UI layer; we only assert the operator is
    # registered + poll-passes for the active obj.
    assert bpy.ops.proscenio.edit_weights.poll() is True
