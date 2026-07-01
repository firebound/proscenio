from __future__ import annotations

import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.automesh.stroke_geometry import (  # noqa: E402
    apply_pen_axis_lock,
    chaikin_smooth,
    contour_ring_from_pen,
    contour_ring_from_pen_edges,
    subdivide_polyline_edges,
)


def test_apply_pen_axis_lock_x_keeps_last_world_z():
    # "x" (horizontal) lock: keep the new X, snap Z to the last vert's Z.
    assert apply_pen_axis_lock((5.0, 9.0), (1.0, 2.0), "x") == (5.0, 2.0)


def test_apply_pen_axis_lock_z_keeps_last_world_x():
    # "z" (vertical) lock: keep the new Z, snap X to the last vert's X.
    assert apply_pen_axis_lock((5.0, 9.0), (1.0, 2.0), "z") == (1.0, 9.0)


def test_apply_pen_axis_lock_empty_axis_passes_through():
    assert apply_pen_axis_lock((5.0, 9.0), (1.0, 2.0), "") == (5.0, 9.0)


def test_apply_pen_axis_lock_no_last_vert_passes_through():
    assert apply_pen_axis_lock((5.0, 9.0), None, "x") == (5.0, 9.0)


def test_subdivide_polyline_edges_per_edge_counts():
    # Open polyline, edge 0 gets 2 verts, edge 1 gets 0 (spec 070 per-edge).
    pts = [(0.0, 0.0), (3.0, 0.0), (3.0, 3.0)]
    out = subdivide_polyline_edges(pts, [2, 0])
    assert len(out) == 5  # 3 anchors + 2 on edge 0 + 0 on edge 1
    assert out[0] == (0.0, 0.0)
    assert out[3] == (3.0, 0.0)  # second anchor after the 2 inserted


def test_subdivide_polyline_edges_missing_counts_default_zero():
    pts = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]
    assert subdivide_polyline_edges(pts, []) == pts  # no counts -> unchanged


def test_contour_ring_per_edge_subdivides_each_edge_independently():
    # Triangle, wrap edge subdivided too (closed loop confirmed on first vert).
    pts = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0)]
    ring = contour_ring_from_pen_edges(pts, [1, 0, 2])
    # edge0 +1, edge1 +0, wrap edge2 +2 -> 3 anchors + 3 inserted = 6.
    assert len(ring) == 6


def test_contour_ring_per_edge_drops_closing_dup_and_guards_min_verts():
    closed = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 0.0)]
    ring = contour_ring_from_pen_edges(closed, [0, 0, 0])
    assert ring == [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0)]  # dup dropped, no subdiv
    assert contour_ring_from_pen_edges([(0.0, 0.0), (1.0, 0.0)], [0]) is None


def test_contour_ring_drops_closing_duplicate():
    # The close-on-first-vert click leaves the first vert duplicated at the end;
    # the ring drops it (no subdivision -> verts unchanged otherwise).
    pts = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 0.0)]
    ring = contour_ring_from_pen(pts, subdivisions=0)
    assert ring == [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]


def test_contour_ring_keeps_open_loop_unchanged():
    # An already-open ring (no trailing duplicate) is kept as-is.
    pts = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    assert contour_ring_from_pen(pts, subdivisions=0) == pts


def test_contour_ring_too_few_points_returns_none():
    assert contour_ring_from_pen([(0.0, 0.0), (1.0, 0.0)], subdivisions=0) is None
    # A degenerate close (only the duplicated first vert left) is also too few.
    assert contour_ring_from_pen([(0.0, 0.0), (0.0, 0.0)], subdivisions=0) is None


def test_contour_ring_subdivides_each_edge():
    # subdivisions=1 inserts one midpoint per open edge of the 3-vert ring (the
    # closing edge stays implicit, so 3 verts -> 3 + 2 inserted = 5).
    pts = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 0.0)]
    ring = contour_ring_from_pen(pts, subdivisions=1)
    assert ring is not None
    assert ring[0] == (0.0, 0.0)
    assert (1.0, 0.0) in ring  # midpoint of the first edge
    assert len(ring) == 5


def test_chaikin_zero_iters_returns_input_unchanged():
    pts = [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)]
    assert chaikin_smooth(pts, iters=0) == pts


def test_chaikin_one_iter_subdivides_each_segment_into_two():
    pts = [(0.0, 0.0), (1.0, 0.0)]
    out = chaikin_smooth(pts, iters=1)
    # First + last endpoints preserved; one segment -> 2 new mid points
    # at 1/4 and 3/4 -> total 4 points (start, q1, q3, end)
    assert len(out) == 4
    assert out[0] == (0.0, 0.0)
    assert out[-1] == (1.0, 0.0)
    assert math.isclose(out[1][0], 0.25)
    assert math.isclose(out[2][0], 0.75)


def test_chaikin_two_iters_smooths_zigzag_toward_centroid():
    # symmetric zigzag; after smoothing peaks pull toward midline (y=0)
    pts = [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0), (3.0, 1.0), (4.0, 0.0)]
    out = chaikin_smooth(pts, iters=2)
    max_y = max(p[1] for p in out)
    assert max_y < 1.0  # original peaks were 1.0; smoothed must be lower
    assert max_y > 0.3  # but not flattened entirely


def test_chaikin_preserves_endpoints_at_all_iter_counts():
    pts = [(5.0, 5.0), (6.0, 6.0), (7.0, 5.0)]
    for iters in (1, 2, 3, 5):
        out = chaikin_smooth(pts, iters=iters)
        assert out[0] == (5.0, 5.0)
        assert out[-1] == (7.0, 5.0)


def test_chaikin_single_point_returns_single_point():
    assert chaikin_smooth([(1.0, 2.0)], iters=2) == [(1.0, 2.0)]


def test_chaikin_two_points_with_zero_iters_returns_input():
    assert chaikin_smooth([(0.0, 0.0), (1.0, 0.0)], iters=0) == [(0.0, 0.0), (1.0, 0.0)]


from core.automesh.stroke_geometry import resample_polyline  # noqa: E402


def test_resample_straight_line_at_spacing():
    # 10-unit line, spacing 1.0 -> 11 points (endpoints inclusive)
    out = resample_polyline([(0.0, 0.0), (10.0, 0.0)], spacing=1.0)
    assert len(out) == 11
    for i, (x, y) in enumerate(out):
        assert math.isclose(x, float(i))
        assert math.isclose(y, 0.0)


def test_resample_preserves_endpoints():
    out = resample_polyline([(0.0, 0.0), (3.0, 4.0)], spacing=1.0)
    assert out[0] == (0.0, 0.0)
    assert math.isclose(out[-1][0], 3.0)
    assert math.isclose(out[-1][1], 4.0)


def test_resample_single_point_returns_single_point():
    assert resample_polyline([(2.0, 3.0)], spacing=1.0) == [(2.0, 3.0)]


def test_resample_empty_returns_empty():
    assert resample_polyline([], spacing=1.0) == []


def test_resample_zero_or_negative_spacing_raises():
    import pytest

    with pytest.raises(ValueError, match="spacing"):
        resample_polyline([(0.0, 0.0), (1.0, 0.0)], spacing=0.0)
    with pytest.raises(ValueError, match="spacing"):
        resample_polyline([(0.0, 0.0), (1.0, 0.0)], spacing=-0.1)


def test_resample_path_shorter_than_spacing_returns_endpoints_only():
    out = resample_polyline([(0.0, 0.0), (0.3, 0.0)], spacing=1.0)
    assert out == [(0.0, 0.0), (0.3, 0.0)]


def test_resample_zigzag_yields_uniform_arc_length_spacing():
    pts = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (2.0, 1.0)]  # L-bend, total len 3
    out = resample_polyline(pts, spacing=1.0)
    # 4 points expected (0, 1, 2, 3 arc-length)
    assert len(out) == 4


from core.automesh.stroke_geometry import snap_endpoint  # noqa: E402


def test_snap_returns_none_when_no_candidate_in_range():
    assert snap_endpoint((0.0, 0.0), [(5.0, 5.0), (10.0, 10.0)], max_dist=1.0) is None


def test_snap_returns_nearest_index_when_in_range():
    candidates = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]
    # query closer to candidate index 1
    assert snap_endpoint((1.1, 0.0), candidates, max_dist=0.5) == 1


def test_snap_returns_first_on_tie():
    candidates = [(1.0, 0.0), (-1.0, 0.0)]  # both 1 unit away from origin
    # tie-break: lowest index
    assert snap_endpoint((0.0, 0.0), candidates, max_dist=2.0) == 0


def test_snap_empty_candidates_returns_none():
    assert snap_endpoint((0.0, 0.0), [], max_dist=1.0) is None


def test_snap_negative_max_dist_raises():
    import pytest

    with pytest.raises(ValueError, match="max_dist"):
        snap_endpoint((0.0, 0.0), [(1.0, 0.0)], max_dist=-1.0)


from core.automesh.stroke_geometry import subdivide_polyline  # noqa: E402


def test_subdivide_zero_returns_input():
    pts = [(0.0, 0.0), (1.0, 0.0)]
    assert subdivide_polyline(pts, 0) == pts


def test_subdivide_one_inserts_midpoint_per_edge():
    out = subdivide_polyline([(0.0, 0.0), (1.0, 0.0)], 1)
    assert out == [(0.0, 0.0), (0.5, 0.0), (1.0, 0.0)]


def test_subdivide_two_inserts_two_evenly_spaced_per_edge():
    out = subdivide_polyline([(0.0, 0.0), (3.0, 0.0)], 2)
    assert [round(p[0], 3) for p in out] == [0.0, 1.0, 2.0, 3.0]


def test_subdivide_multi_edge_preserves_original_verts():
    pts = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    out = subdivide_polyline(pts, 1)
    assert out[0] == (0.0, 0.0)
    assert out[2] == (1.0, 0.0)
    assert out[-1] == (1.0, 1.0)
    assert len(out) == 5  # 2 edges, +1 mid each


def test_subdivide_single_point_or_empty_unchanged():
    assert subdivide_polyline([(2.0, 2.0)], 3) == [(2.0, 2.0)]
    assert subdivide_polyline([], 3) == []


def test_subdivide_negative_count_treated_as_zero():
    pts = [(0.0, 0.0), (1.0, 0.0)]
    assert subdivide_polyline(pts, -2) == pts
