"""Headless tests for the automesh sidecar hook."""

from __future__ import annotations

import json

import bpy


def _activate(name: str) -> bpy.types.Object:
    obj = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    return obj


def _set_picker(name: str) -> None:
    bpy.context.scene.proscenio.active_armature = bpy.data.objects[name]


def _set_preserve(value: bool) -> None:
    bpy.context.scene.proscenio.skinning.preserve_on_regen = value


def _read_sidecar(obj: bpy.types.Object) -> dict:
    payload = obj.get("proscenio_weight_sidecar")
    assert payload is not None
    return json.loads(payload)


def test_automesh_regen_with_preserve_on_reprojects(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    _set_preserve(True)
    # Bind first so the sidecar has populated entries to snapshot.
    bpy.ops.proscenio.bind_mesh_to_armature()
    pre = _read_sidecar(obj)
    assert len(pre["entries"]) > 0
    # Regen with a different resolution to force topology change.
    bpy.ops.proscenio.automesh_from_alpha(resolution=0.5)
    post = _read_sidecar(obj)
    # Post-regen sidecar must have entries equal to new vert count.
    assert len(post["entries"]) == len(obj.data.vertices)
    provenances = {entry["provenance"] for entry in post["entries"]}
    assert "reprojected" in provenances or "auto_seed" in provenances


def test_automesh_regen_with_preserve_off_skips_hook(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    _set_preserve(True)
    bpy.ops.proscenio.bind_mesh_to_armature()
    pre_hash = _read_sidecar(obj)["mesh_topology_hash"]
    # Turn the auto-flow off, then regen with a forcing parameter change.
    _set_preserve(False)
    bpy.ops.proscenio.automesh_from_alpha(resolution=0.5)
    post = _read_sidecar(obj)
    # With preserve OFF, hook is no-op: sidecar stays from BEFORE the regen
    # (the operator did not re-stamp; topology hash points to OLD topology).
    assert post["mesh_topology_hash"] == pre_hash
