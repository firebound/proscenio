"""Headless operator tests for the bind_mesh operator (the weight-paint productivity follow-up)."""

from __future__ import annotations

import json

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


def test_bind_happy_path(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    # No explicit mode - exercise the BONE_HEAT default landing from PG
    result = bpy.ops.proscenio.bind_mesh_to_armature()
    assert "FINISHED" in result
    group_names = {g.name for g in obj.vertex_groups}
    assert {"wrist", "palm", "fingertip"} <= group_names


def test_bind_diagnose_unapplied_scale_aborts(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    obj.scale = (2.0, 2.0, 2.0)
    # bpy.ops raises RuntimeError when an operator reports {"ERROR"} and
    # returns {"CANCELLED"}. The message carries the diagnose hint.
    with pytest.raises(RuntimeError, match="unapplied scale"):
        bpy.ops.proscenio.bind_mesh_to_armature(bind_init_mode="PROXIMITY")
    assert "wrist" not in {g.name for g in obj.vertex_groups}


def test_bind_diagnose_bones_outside_bbox_warns_but_proceeds(automesh_fixture):
    _activate("hand")
    rig = bpy.data.objects["automesh.hand_rig"]
    rig.location.x = 100.0
    _set_picker("automesh.hand_rig")
    result = bpy.ops.proscenio.bind_mesh_to_armature(bind_init_mode="PROXIMITY")
    assert "FINISHED" in result


def test_bind_preserves_base_sprite_group_on_rerun(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    if "proscenio_base_sprite" not in obj.vertex_groups:
        obj.vertex_groups.new(name="proscenio_base_sprite")
    bpy.ops.proscenio.bind_mesh_to_armature(bind_init_mode="PROXIMITY")
    assert "proscenio_base_sprite" in {g.name for g in obj.vertex_groups}
    bpy.ops.proscenio.bind_mesh_to_armature(bind_init_mode="SINGLE_NEAREST")
    assert "proscenio_base_sprite" in {g.name for g in obj.vertex_groups}


def test_bind_writes_populated_sidecar(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()  # BONE_HEAT is the default mode
    payload = obj.get("proscenio_weight_sidecar")
    assert payload is not None
    sidecar = json.loads(payload)
    assert sidecar["version"] == 1
    assert "wrist" in sidecar["vertex_group_names"]
    assert len(sidecar["entries"]) == len(obj.data.vertices)
    for entry in sidecar["entries"]:
        assert entry["provenance"] == "auto_seed"
        assert "uv_anchor" in entry
        assert isinstance(entry["weights"], dict)


def test_bind_explicit_proximity_still_works(automesh_fixture):
    """Power-user fallback path: explicit PROXIMITY still computes weights."""
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    result = bpy.ops.proscenio.bind_mesh_to_armature(bind_init_mode="PROXIMITY")
    assert "FINISHED" in result
    assert {"wrist", "palm", "fingertip"} <= {g.name for g in obj.vertex_groups}


def test_bind_single_nearest_one_bone_per_vert(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature(bind_init_mode="SINGLE_NEAREST")
    bone_names = {"wrist", "palm", "fingertip"}
    for vert in obj.data.vertices:
        full_weights = [
            g.weight
            for g in vert.groups
            if obj.vertex_groups[g.group].name in bone_names and g.weight > 0.5
        ]
        assert len(full_weights) == 1
