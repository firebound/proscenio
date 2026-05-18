"""Pure tests for WeightSidecar schema (SPEC 013.2 bind, Q3)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.skinning.sidecar_schema import (  # noqa: E402
    SIDECAR_VERSION,
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


def test_weight_sidecar_is_frozen():
    sidecar = WeightSidecar(
        version=1, vertex_group_names=["arm"], mesh_topology_hash="xyz", entries=[]
    )
    import pytest

    with pytest.raises(AttributeError):
        sidecar.version = 2  # type: ignore[misc]
