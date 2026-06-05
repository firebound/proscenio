"""Headless tests for restore_weight_snapshot operator."""

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


def test_restore_after_paint_reverts_to_snapshot(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    original = _first_wrist_weight(obj)
    assert original > 0.0
    # Mutate: zero out the wrist group on every vert.
    wrist = obj.vertex_groups["wrist"]
    for vert in obj.data.vertices:
        wrist.add([vert.index], 0.0, "REPLACE")
    assert abs(_first_wrist_weight(obj)) < 1e-9
    result = bpy.ops.proscenio.restore_weight_snapshot()
    assert "FINISHED" in result
    restored = _first_wrist_weight(obj)
    assert abs(restored - original) < 1e-3


def test_restore_with_stale_topology_aborts(automesh_fixture):
    _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    # Turn off preserve so regen does NOT update the snapshot hash.
    bpy.context.scene.proscenio.skinning.preserve_on_regen = False
    bpy.ops.proscenio.automesh_from_sprite(resolution=0.5)
    # The stored sidecar still points to the OLD topology hash.
    with pytest.raises(RuntimeError, match="topology changed"):
        bpy.ops.proscenio.restore_weight_snapshot()
