"""Pure tests for build_sidecar_from_vgroup_data (M1)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))


def test_build_sidecar_from_uv_and_weights_dict():
    from core.skinning.weight_snapshot import build_sidecar_from_vgroup_data  # noqa: E402
    uvs = [(0.0, 0.0), (0.5, 0.5), (1.0, 1.0)]
    weights_per_vert = [
        {"bone_a": 1.0},
        {"bone_a": 0.5, "bone_b": 0.5},
        {"bone_b": 1.0},
    ]
    sidecar = build_sidecar_from_vgroup_data(uvs, weights_per_vert)
    assert len(sidecar.entries) == 3
    assert sidecar.entries[0].provenance == "auto_seed"
    assert sidecar.entries[1].weights == {"bone_a": 0.5, "bone_b": 0.5}


def test_empty_inputs_return_empty_sidecar():
    from core.skinning.weight_snapshot import build_sidecar_from_vgroup_data  # noqa: E402
    sidecar = build_sidecar_from_vgroup_data([], [])
    assert sidecar.entries == []


def test_mismatched_lengths_truncate_to_shorter():
    from core.skinning.weight_snapshot import build_sidecar_from_vgroup_data  # noqa: E402
    uvs = [(0.0, 0.0), (0.5, 0.5)]
    weights = [{"a": 1.0}]
    sidecar = build_sidecar_from_vgroup_data(uvs, weights)
    assert len(sidecar.entries) == 1
