"""Pure tests for weight reproject (SPEC 013.2 sidecar, T3)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.skinning.sidecar_schema import SidecarEntry  # noqa: E402
from core.skinning.weight_reproject import reproject_entries  # noqa: E402


def _entry(uv: tuple[float, float], weights: dict[str, float]) -> SidecarEntry:
    return SidecarEntry(uv_anchor=uv, weights=weights, provenance="auto_seed")


def test_identical_topology_passes_through_with_reprojected_tag():
    old = [
        _entry((0.0, 0.0), {"A": 1.0}),
        _entry((1.0, 0.0), {"B": 1.0}),
        _entry((0.0, 1.0), {"A": 0.5, "B": 0.5}),
    ]
    new_anchors = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    out = reproject_entries(old, new_anchors, max_distance=2.0)
    assert len(out) == 3
    for entry in out:
        assert entry is not None
        assert entry.provenance == "reprojected"
    # exact-match anchors interpolate as themselves
    assert math.isclose(out[0].weights["A"], 1.0, abs_tol=1e-3)
    assert math.isclose(out[1].weights["B"], 1.0, abs_tol=1e-3)


def test_centroid_of_triangle_averages_three_anchors():
    old = [
        _entry((0.0, 0.0), {"A": 1.0}),
        _entry((1.0, 0.0), {"B": 1.0}),
        _entry((0.0, 1.0), {"C": 1.0}),
    ]
    centroid = (1.0 / 3.0, 1.0 / 3.0)
    out = reproject_entries(old, [centroid], max_distance=2.0)
    assert out[0] is not None
    for bone in ("A", "B", "C"):
        assert math.isclose(out[0].weights[bone], 1.0 / 3.0, abs_tol=1e-3)


def test_far_anchor_falls_back_to_none():
    old = [
        _entry((0.0, 0.0), {"A": 1.0}),
        _entry((0.1, 0.0), {"A": 1.0}),
        _entry((0.0, 0.1), {"A": 1.0}),
    ]
    out = reproject_entries(old, [(10.0, 10.0)], max_distance=0.5)
    assert out == [None]


def test_fewer_than_three_old_entries_returns_none():
    # Caller is expected to fall back to auto_seed.
    old = [_entry((0.0, 0.0), {"A": 1.0}), _entry((1.0, 0.0), {"A": 1.0})]
    out = reproject_entries(old, [(0.5, 0.0)], max_distance=2.0)
    assert out == [None]


def test_single_bone_weight_preserved_under_interpolation():
    old = [
        _entry((0.0, 0.0), {"only": 1.0}),
        _entry((1.0, 0.0), {"only": 1.0}),
        _entry((0.0, 1.0), {"only": 1.0}),
    ]
    out = reproject_entries(old, [(0.25, 0.25)], max_distance=2.0)
    assert out[0] is not None
    assert math.isclose(out[0].weights["only"], 1.0, abs_tol=1e-3)


def test_degenerate_collinear_triangle_returns_none():
    # 3 collinear neighbors -> barycentric undefined -> caller auto_seeds
    old = [
        _entry((0.0, 0.0), {"A": 1.0}),
        _entry((0.5, 0.0), {"A": 1.0}),
        _entry((1.0, 0.0), {"A": 1.0}),
    ]
    # Target ABOVE the line - no triangle contains it
    out = reproject_entries(old, [(0.5, 0.5)], max_distance=2.0)
    assert out == [None]
