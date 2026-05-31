"""Pure tests for cut_geometry."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.automesh.cut_geometry import lens_polygon, perpendicular_offsets  # noqa: E402


def test_horizontal_stroke_offsets_vertical():
    # Horizontal stroke -> perp is vertical -> left = +y, right = -y
    poly = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]
    left, right = perpendicular_offsets(poly, half_width=0.5)
    assert len(left) == 3
    assert len(right) == 3
    for (lx, ly), (rx, ry), (sx, sy) in zip(left, right, poly):
        assert math.isclose(lx, sx, abs_tol=1e-6)
        assert math.isclose(rx, sx, abs_tol=1e-6)
        assert math.isclose(ly, sy + 0.5, abs_tol=1e-6)
        assert math.isclose(ry, sy - 0.5, abs_tol=1e-6)


def test_vertical_stroke_offsets_horizontal():
    poly = [(0.0, 0.0), (0.0, 1.0)]
    left, right = perpendicular_offsets(poly, half_width=0.5)
    # CCW perp of (0, 1) is (-1, 0) -> left at x=-0.5, right at x=+0.5
    assert math.isclose(left[0][0], -0.5, abs_tol=1e-6)
    assert math.isclose(right[0][0], 0.5, abs_tol=1e-6)


def test_corner_stroke_uses_averaged_tangent():
    # L-bend at (1, 0): tangent in = (1, 0), out = (0, 1), avg = (0.5, 0.5)
    poly = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    left, right = perpendicular_offsets(poly, half_width=1.0)
    # At corner i=1, perp = normalized (-0.5, 0.5) = (-1/sqrt(2), 1/sqrt(2))
    expected_lx = 1.0 + (-1.0 / math.sqrt(2)) * 1.0
    expected_ly = 0.0 + (1.0 / math.sqrt(2)) * 1.0
    assert math.isclose(left[1][0], expected_lx, abs_tol=1e-6)
    assert math.isclose(left[1][1], expected_ly, abs_tol=1e-6)


def test_too_short_polyline_raises():
    with pytest.raises(ValueError, match="polyline"):
        perpendicular_offsets([(0.0, 0.0)], half_width=1.0)


def test_negative_half_width_raises():
    with pytest.raises(ValueError, match="half_width"):
        perpendicular_offsets([(0.0, 0.0), (1.0, 0.0)], half_width=-0.1)


def test_zero_half_width_raises():
    with pytest.raises(ValueError, match="half_width"):
        perpendicular_offsets([(0.0, 0.0), (1.0, 0.0)], half_width=0.0)


def test_lens_polygon_is_closed_left_plus_right_reversed():
    left = [(0.0, 1.0), (1.0, 1.0), (2.0, 1.0)]
    right = [(0.0, -1.0), (1.0, -1.0), (2.0, -1.0)]
    lens = lens_polygon(left, right)
    assert lens == [
        (0.0, 1.0),
        (1.0, 1.0),
        (2.0, 1.0),
        (2.0, -1.0),
        (1.0, -1.0),
        (0.0, -1.0),
    ]


def test_lens_polygon_length_equals_2n():
    poly = [(float(i), 0.0) for i in range(5)]
    left, right = perpendicular_offsets(poly, half_width=0.1)
    lens = lens_polygon(left, right)
    assert len(lens) == 2 * len(poly)


def test_offsets_are_symmetric_around_stroke():
    poly = [(0.0, 0.0), (1.0, 0.0)]
    left, right = perpendicular_offsets(poly, half_width=0.25)
    for (lx, ly), (rx, ry), (sx, sy) in zip(left, right, poly):
        assert math.isclose((lx + rx) / 2, sx, abs_tol=1e-6)
        assert math.isclose((ly + ry) / 2, sy, abs_tol=1e-6)


def test_degenerate_tangent_fallback_uses_previous_perpendicular():
    # Duplicate middle point -> degenerate tangent at i=1; should use i=0's perp
    poly = [(0.0, 0.0), (0.0, 0.0), (1.0, 0.0)]
    # Should not raise; degenerate middle gets fallback offset
    left, right = perpendicular_offsets(poly, half_width=0.5)
    assert len(left) == 3
    assert len(right) == 3


def test_perpendicular_offsets_scales_with_half_width():
    """Larger half_width produces a larger perpendicular offset (T9 )."""
    poly = [(0.0, 0.0), (1.0, 0.0)]
    left_small, _ = perpendicular_offsets(poly, half_width=0.1)
    left_large, _ = perpendicular_offsets(poly, half_width=1.0)
    # Horizontal stroke -> perp is vertical; left offset is positive y
    assert abs(left_large[0][1]) > abs(left_small[0][1])
    assert math.isclose(abs(left_large[0][1]), 1.0, abs_tol=1e-6)
    assert math.isclose(abs(left_small[0][1]), 0.1, abs_tol=1e-6)
