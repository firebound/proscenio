from __future__ import annotations

import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.automesh.stroke_geometry import chaikin_smooth  # noqa: E402


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
