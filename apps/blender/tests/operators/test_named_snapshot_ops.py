"""Headless tests for the named weight-snapshot operators.

Runs INSIDE Blender via ``run_operator_tests.py``. Covers the spec 049 named
save points: save the current weights under a name, then restore them by name
after the weights are mutated. The rolling-auto cap is covered purely in
``tests/skinning/test_named_snapshots.py``.
"""

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


def _first_wrist_weight(obj: bpy.types.Object) -> float:
    wrist = obj.vertex_groups["wrist"]
    for vert in obj.data.vertices:
        for elem in vert.groups:
            if elem.group == wrist.index and elem.weight > 0.0:
                return float(elem.weight)
    return 0.0


def _bound_hand() -> bpy.types.Object:
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    return obj


def test_save_then_restore_named_snapshot(automesh_fixture):
    obj = _bound_hand()
    original = _first_wrist_weight(obj)
    assert original > 0.0

    result = bpy.ops.proscenio.save_weight_snapshot(snapshot_name="pose-a")
    assert "FINISHED" in result

    # Mutate: zero the wrist group on every vert.
    wrist = obj.vertex_groups["wrist"]
    for vert in obj.data.vertices:
        wrist.add([vert.index], 0.0, "REPLACE")
    assert abs(_first_wrist_weight(obj)) < 1e-9

    result = bpy.ops.proscenio.restore_named_snapshot(snapshot_name="pose-a")
    assert "FINISHED" in result
    assert abs(_first_wrist_weight(obj) - original) < 1e-3


def test_saved_snapshot_is_listed(automesh_fixture):
    from proscenio.core.bpy_helpers.skinning import read_snapshots

    obj = _bound_hand()
    bpy.ops.proscenio.save_weight_snapshot(snapshot_name="pose-a")

    listed = read_snapshots(obj)
    assert [(s.name, s.kind) for s in listed] == [("pose-a", "manual")]


def test_restore_unknown_name_cancels(automesh_fixture):
    _bound_hand()
    with pytest.raises(RuntimeError, match="no snapshot named"):
        bpy.ops.proscenio.restore_named_snapshot(snapshot_name="does-not-exist")


def test_save_empty_name_cancels(automesh_fixture):
    _bound_hand()
    with pytest.raises(RuntimeError, match="name cannot be empty"):
        bpy.ops.proscenio.save_weight_snapshot(snapshot_name="   ")
