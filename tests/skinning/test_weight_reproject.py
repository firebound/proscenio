"""Pure tests for weight reproject."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.skinning.sidecar_schema import SidecarEntry  # noqa: E402
from core.skinning.weight_reproject import reproject_entries  # noqa: E402


def _entry(uv: tuple[float, float], weights: dict[str, float]) -> SidecarEntry:
    return SidecarEntry(uv_anchor=uv, weights=weights, provenance="auto_seed")


def _user_entry(uv: tuple[float, float], weights: dict[str, float]) -> SidecarEntry:
    return SidecarEntry(uv_anchor=uv, weights=weights, provenance="user_paint")


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


def test_fewer_than_three_old_entries_falls_back_to_nearest():
    # 1-2 donors in range inherit the nearest donor's weights rather than
    # auto_seeding, so the user does not lose paint on chained regens.
    old = [_entry((0.0, 0.0), {"A": 1.0}), _entry((1.0, 0.0), {"A": 1.0})]
    out = reproject_entries(old, [(0.3, 0.0)], max_distance=2.0)
    assert out[0] is not None
    assert out[0].weights == {"A": 1.0}
    assert out[0].provenance == "reprojected"


def test_zero_donors_in_range_still_returns_none():
    # Only when NO donor exists in range do we fall back to caller-side
    # auto_seed (the target is truly out of mesh scope).
    old = [_entry((0.0, 0.0), {"A": 1.0}), _entry((0.1, 0.0), {"A": 1.0})]
    out = reproject_entries(old, [(10.0, 10.0)], max_distance=0.5)
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


def test_degenerate_collinear_triangle_falls_back_to_nearest():
    # When barycentric returns None (target outside the donor triangle, or
    # donors collinear so the triangle is degenerate), fall back to nearest
    # donor instead of auto_seed - otherwise weights drop at every
    # silhouette-boundary vert.
    old = [
        _entry((0.0, 0.0), {"A": 1.0}),
        _entry((0.5, 0.0), {"A": 1.0}),
        _entry((1.0, 0.0), {"A": 1.0}),
    ]
    out = reproject_entries(old, [(0.5, 0.5)], max_distance=2.0)
    assert out[0] is not None
    assert out[0].weights == {"A": 1.0}
    assert out[0].provenance == "reprojected"


def test_user_paint_carried_through_nearest_fallback():
    # When the nearest-fallback fires, the donor's user_paint provenance
    # must still propagate so artist marks survive the regen.
    old = [
        _user_entry((0.0, 0.0), {"A": 1.0}),
        _entry((0.5, 0.0), {"A": 1.0}),
        _entry((1.0, 0.0), {"A": 1.0}),
    ]
    # Target above the line -> barycentric fails -> nearest is (0,0)
    out = reproject_entries(old, [(0.0, 0.5)], max_distance=2.0)
    assert out[0] is not None
    assert out[0].provenance == "user_paint"


def test_negative_max_distance_raises():
    old = [
        _entry((0.0, 0.0), {"A": 1.0}),
        _entry((1.0, 0.0), {"A": 1.0}),
        _entry((0.0, 1.0), {"A": 1.0}),
    ]
    with pytest.raises(ValueError, match="max_distance"):
        reproject_entries(old, [(0.5, 0.5)], max_distance=-1.0)


def test_user_paint_donor_propagates_to_new_entry():
    # Any donor with user_paint must carry the marker through reproject so
    # artists do not silently lose their work on automesh regen.
    old = [
        _user_entry((0.0, 0.0), {"A": 1.0}),
        _entry((1.0, 0.0), {"A": 1.0}),
        _entry((0.0, 1.0), {"A": 1.0}),
    ]
    out = reproject_entries(old, [(0.25, 0.25)], max_distance=2.0)
    assert out[0] is not None
    assert out[0].provenance == "user_paint"


def test_all_auto_seed_donors_yield_reprojected():
    old = [
        _entry((0.0, 0.0), {"A": 1.0}),
        _entry((1.0, 0.0), {"A": 1.0}),
        _entry((0.0, 1.0), {"A": 1.0}),
    ]
    out = reproject_entries(old, [(0.25, 0.25)], max_distance=2.0)
    assert out[0] is not None
    assert out[0].provenance == "reprojected"


def test_non_finite_max_distance_raises():
    old = [
        _entry((0.0, 0.0), {"A": 1.0}),
        _entry((1.0, 0.0), {"A": 1.0}),
        _entry((0.0, 1.0), {"A": 1.0}),
    ]
    with pytest.raises(ValueError, match="max_distance"):
        reproject_entries(old, [(0.5, 0.5)], max_distance=float("inf"))
