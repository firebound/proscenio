"""Pure tests for WeightSidecar schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.skinning.sidecar_schema import (  # noqa: E402
    SIDECAR_VERSION,
    SidecarEntry,
    WeightSidecar,
    build_minimal_stub,
    compute_topology_hash,
    from_json,
    to_json,
)


def test_topology_hash_sensitive_to_vert_count():
    a = compute_topology_hash(4, [[0, 1, 2]])
    b = compute_topology_hash(5, [[0, 1, 2]])
    assert a != b


def test_topology_hash_sensitive_to_face_indices():
    a = compute_topology_hash(3, [[0, 1, 2]])
    b = compute_topology_hash(3, [[0, 2, 1]])
    assert a != b


def test_topology_hash_stable_for_same_input():
    a = compute_topology_hash(10, [[0, 1, 2], [1, 2, 3]])
    b = compute_topology_hash(10, [[0, 1, 2], [1, 2, 3]])
    assert a == b


def test_build_minimal_stub_has_empty_entries():
    sidecar = build_minimal_stub(["wrist", "palm"], "deadbeef")
    assert sidecar.version == SIDECAR_VERSION
    assert sidecar.vertex_group_names == ["wrist", "palm"]
    assert sidecar.mesh_topology_hash == "deadbeef"
    assert sidecar.entries == []
    assert isinstance(sidecar.entries, list)


def test_json_round_trip_preserves_all_fields():
    sidecar = build_minimal_stub(["A", "B"], "abc123")
    payload = to_json(sidecar)
    parsed = json.loads(payload)
    assert parsed["version"] == SIDECAR_VERSION
    assert parsed["vertex_group_names"] == ["A", "B"]
    restored = from_json(payload)
    assert restored == sidecar


def test_from_json_rejects_wrong_version():
    payload = json.dumps(
        {
            "version": 999,
            "vertex_group_names": [],
            "mesh_topology_hash": "x",
            "entries": [],
        }
    )
    import pytest

    with pytest.raises(ValueError):
        from_json(payload)


def test_from_json_rejects_bad_json():
    import pytest

    with pytest.raises(ValueError, match="invalid sidecar JSON"):
        from_json("{not-json")


def test_from_json_rejects_non_object_root():
    import pytest

    with pytest.raises(ValueError, match="must be a JSON object"):
        from_json("[1, 2, 3]")


def test_from_json_rejects_missing_topology_hash():
    import pytest

    payload = json.dumps({"version": 1, "vertex_group_names": [], "entries": []})
    with pytest.raises(ValueError, match="missing mesh_topology_hash"):
        from_json(payload)


def test_entry_round_trip_via_to_json_from_json():
    sidecar = WeightSidecar(
        version=1,
        vertex_group_names=["wrist", "palm"],
        mesh_topology_hash="abc",
        entries=[
            SidecarEntry(
                uv_anchor=(0.5, 0.5),
                weights={"wrist": 0.8, "palm": 0.2},
                provenance="auto_seed",
            ),
            SidecarEntry(
                uv_anchor=(0.1, 0.9),
                weights={"wrist": 1.0},
                provenance="reprojected",
            ),
        ],
    )
    payload = to_json(sidecar)
    restored = from_json(payload)
    assert restored == sidecar
    assert restored.entries[0].provenance == "auto_seed"
    assert restored.entries[1].weights == {"wrist": 1.0}


def test_from_json_rejects_unknown_provenance():
    import pytest

    payload = json.dumps(
        {
            "version": 1,
            "vertex_group_names": [],
            "mesh_topology_hash": "x",
            "entries": [
                {"uv_anchor": [0.0, 0.0], "weights": {}, "provenance": "alien"}
            ],
        }
    )
    with pytest.raises(ValueError, match="provenance"):
        from_json(payload)


def test_weight_sidecar_is_frozen():
    sidecar = WeightSidecar(
        version=1, vertex_group_names=["arm"], mesh_topology_hash="xyz", entries=[]
    )
    import pytest

    with pytest.raises(AttributeError):
        sidecar.version = 2  # type: ignore[misc]
