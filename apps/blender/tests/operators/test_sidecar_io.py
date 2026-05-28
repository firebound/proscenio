"""Headless: sidecar export/import round-trip (O3)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

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


def test_sidecar_export_import_round_trip(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    original = obj["proscenio_weight_sidecar"]
    assert original is not None

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        tmp_path = Path(f.name)

    try:
        result = bpy.ops.proscenio.export_sidecar(filepath=str(tmp_path))
        assert "FINISHED" in result
        assert tmp_path.exists()

        with open(tmp_path, encoding="utf-8") as f:
            parsed = json.loads(f.read())
        # Validate all top-level schema fields are present.
        assert "entries" in parsed
        assert "version" in parsed
        assert "mesh_topology_hash" in parsed
        assert "vertex_group_names" in parsed

        # Wipe the prop then reimport.
        del obj["proscenio_weight_sidecar"]
        assert obj.get("proscenio_weight_sidecar") is None

        result = bpy.ops.proscenio.import_sidecar(filepath=str(tmp_path))
        assert "FINISHED" in result
        assert obj.get("proscenio_weight_sidecar") is not None

        # Content must survive the round-trip.
        restored = json.loads(obj["proscenio_weight_sidecar"])
        assert restored["version"] == parsed["version"]
        assert restored["mesh_topology_hash"] == parsed["mesh_topology_hash"]
        assert len(restored["entries"]) == len(parsed["entries"])
    finally:
        tmp_path.unlink(missing_ok=True)


def test_import_sidecar_rejects_invalid_json(automesh_fixture):
    _activate("hand")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("not valid json{{")
        tmp_path = Path(f.name)

    try:
        result = bpy.ops.proscenio.import_sidecar(filepath=str(tmp_path))
        assert "CANCELLED" in result
    finally:
        tmp_path.unlink(missing_ok=True)


def test_import_sidecar_rejects_missing_required_fields(automesh_fixture):
    _activate("hand")

    bad_payload = json.dumps({"entries": []})  # missing version + mesh_topology_hash
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(bad_payload)
        tmp_path = Path(f.name)

    try:
        result = bpy.ops.proscenio.import_sidecar(filepath=str(tmp_path))
        assert "CANCELLED" in result
    finally:
        tmp_path.unlink(missing_ok=True)


def test_export_poll_false_without_sidecar(automesh_fixture):
    """Export operator must be unavailable when no sidecar is set."""
    obj = _activate("hand")
    # Ensure no sidecar exists.
    if obj.get("proscenio_weight_sidecar") is not None:
        del obj["proscenio_weight_sidecar"]
    # poll() returns False, so invoking the op raises RuntimeError.
    with pytest.raises(RuntimeError):
        bpy.ops.proscenio.export_sidecar(filepath="irrelevant.json")
