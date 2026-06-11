"""Headless: sidecar export/import round-trip."""

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


def _vert_has_weight(obj: bpy.types.Object, idx: int) -> bool:
    for vg in obj.vertex_groups:
        try:
            if vg.weight(idx) > 1e-6:
                return True
        except RuntimeError:
            continue
    return False


def test_import_applies_live_weights_when_topology_matches(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    assert len(obj.vertex_groups) > 0

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        tmp_path = Path(f.name)
    try:
        assert "FINISHED" in bpy.ops.proscenio.export_sidecar(filepath=str(tmp_path))
        # Wipe the live weights so a successful import must re-create them.
        obj.vertex_groups.clear()
        assert len(obj.vertex_groups) == 0

        assert "FINISHED" in bpy.ops.proscenio.import_sidecar(filepath=str(tmp_path))
        # Topology is unchanged, so import reapplied the snapshot onto live groups.
        assert len(obj.vertex_groups) > 0, "import did not re-create vertex groups"
        wrote_live_weights = any(_vert_has_weight(obj, v.index) for v in obj.data.vertices)
        assert wrote_live_weights, "import did not write live weights"
    finally:
        tmp_path.unlink(missing_ok=True)


def test_import_stores_only_when_topology_mismatches(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        tmp_path = Path(f.name)
    try:
        assert "FINISHED" in bpy.ops.proscenio.export_sidecar(filepath=str(tmp_path))
        # Tamper the topology hash so the live mesh no longer matches.
        data = json.loads(tmp_path.read_text(encoding="utf-8"))
        data["mesh_topology_hash"] = "mismatch-not-the-real-hash"
        tmp_path.write_text(json.dumps(data), encoding="utf-8")
        # Wipe live weights; a stored-only import must NOT re-create them.
        obj.vertex_groups.clear()

        assert "FINISHED" in bpy.ops.proscenio.import_sidecar(filepath=str(tmp_path))
        # CP stored the tampered payload, but the live weights stay untouched.
        stored = json.loads(obj["proscenio_weight_sidecar"])
        assert stored["mesh_topology_hash"] == "mismatch-not-the-real-hash"
        assert len(obj.vertex_groups) == 0, "stored-only import wrongly applied weights"
    finally:
        tmp_path.unlink(missing_ok=True)
