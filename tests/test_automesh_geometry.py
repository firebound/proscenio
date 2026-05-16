"""Unit tests for SPEC 013 automesh geometry pipeline.

bpy-free. Exercises the Laplacian smoothing + arc-length resample +
annulus edge construction consumed by
``core/bpy_helpers/automesh_bmesh.py``.

Run from the repo root:

    pytest tests/test_automesh_geometry.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.automesh_geometry import (  # noqa: E402  - sys.path setup above
    Contour2D,
    arc_length_resample,
    build_annulus_edge_pairs,
    laplacian_smooth,
    perimeter_length,
    relax_contour,
    to_float_contour,
)


def _square_contour(size: float = 10.0) -> Contour2D:
    """Axis-aligned square contour for predictable arithmetic."""
    return [(0.0, 0.0), (size, 0.0), (size, size), (0.0, size)]


def _staircase_contour() -> Contour2D:
    """Pixel-staircase that smoothing should round."""
    return [
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, 1.0),
        (2.0, 1.0),
        (2.0, 2.0),
        (3.0, 2.0),
        (3.0, 3.0),
        (0.0, 3.0),
    ]


class TestToFloatContour:
    def test_lifts_ints_to_floats(self) -> None:
        out = to_float_contour([(1, 2), (3, 4)])
        assert out == [(1.0, 2.0), (3.0, 4.0)]
        assert all(isinstance(x, float) and isinstance(y, float) for x, y in out)


class TestLaplacianSmooth:
    def test_negative_iterations_raise(self) -> None:
        with pytest.raises(ValueError, match=">= 0"):
            laplacian_smooth([(0.0, 0.0)], -1)

    def test_zero_iterations_returns_copy(self) -> None:
        contour = _square_contour()
        out = laplacian_smooth(contour, 0)
        assert out == contour
        assert out is not contour

    def test_single_vertex_returns_unchanged(self) -> None:
        out = laplacian_smooth([(1.0, 2.0)], 5)
        assert out == [(1.0, 2.0)]

    def test_square_smooths_toward_center(self) -> None:
        # Square centered at (5, 5), after smoothing every vertex moves
        # toward the centroid.
        contour = _square_contour(10.0)
        smoothed = laplacian_smooth(contour, 1)
        cx, cy = 5.0, 5.0
        for original, new in zip(contour, smoothed):
            dist_before = math.hypot(original[0] - cx, original[1] - cy)
            dist_after = math.hypot(new[0] - cx, new[1] - cy)
            assert dist_after < dist_before

    def test_staircase_smooths_corners(self) -> None:
        staircase = _staircase_contour()
        smoothed = laplacian_smooth(staircase, 3)
        # Every input corner had integer coords; smoothing should have
        # produced sub-integer offsets everywhere.
        for x, y in smoothed:
            assert not (x.is_integer() and y.is_integer())


class TestPerimeterLength:
    def test_square_perimeter(self) -> None:
        assert perimeter_length(_square_contour(10.0)) == pytest.approx(40.0)

    def test_empty_contour_zero(self) -> None:
        assert perimeter_length([]) == 0.0

    def test_single_vertex_zero(self) -> None:
        assert perimeter_length([(1.0, 2.0)]) == 0.0


class TestArcLengthResample:
    def test_target_below_three_raises(self) -> None:
        with pytest.raises(ValueError, match="target_count must be >= 3"):
            arc_length_resample(_square_contour(), 2)

    def test_short_contour_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 3 vertices"):
            arc_length_resample([(0.0, 0.0), (1.0, 1.0)], 8)

    def test_zero_perimeter_raises(self) -> None:
        # Dedupe collapses the 3 identical points to 1 before the
        # perimeter check, so the raised error names the dedupe path
        # rather than "zero perimeter". Both express the same intent:
        # degenerate contour refused.
        with pytest.raises(ValueError, match="collapses to <3|zero perimeter"):
            arc_length_resample([(1.0, 1.0), (1.0, 1.0), (1.0, 1.0)], 8)

    def test_output_count_matches_target(self) -> None:
        contour = _square_contour(10.0)
        out = arc_length_resample(contour, 16)
        assert len(out) == 16

    def test_spacing_is_uniform(self) -> None:
        # 16-point sample of a 40-unit perimeter -> 2.5 units per step.
        out = arc_length_resample(_square_contour(10.0), 16)
        expected_step = 40.0 / 16
        for index in range(len(out)):
            x0, y0 = out[index]
            x1, y1 = out[(index + 1) % len(out)]
            distance = math.hypot(x1 - x0, y1 - y0)
            assert distance == pytest.approx(expected_step, abs=1e-9)

    def test_upsample_doubles_density(self) -> None:
        # 4-vertex square upsampled to 32 -> 8 samples per original edge.
        out = arc_length_resample(_square_contour(8.0), 32)
        assert len(out) == 32

    def test_first_sample_is_first_vertex(self) -> None:
        out = arc_length_resample(_square_contour(10.0), 8)
        assert out[0] == pytest.approx((0.0, 0.0))


class TestRelaxContour:
    def test_negative_smooth_iterations_raise(self) -> None:
        with pytest.raises(ValueError, match="smooth_iterations"):
            relax_contour([(0, 0), (1, 0), (1, 1)], -1, 8)

    def test_target_below_three_raises(self) -> None:
        with pytest.raises(ValueError, match="target_vertex_count"):
            relax_contour([(0, 0), (1, 0), (1, 1)], 3, 2)

    def test_short_input_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 3 points"):
            relax_contour([(0, 0), (1, 0)], 3, 8)

    def test_pipeline_outputs_requested_count(self) -> None:
        # 8-pixel staircase smoothed + resampled to 32 verts.
        pixel = [
            (0, 0),
            (1, 0),
            (1, 1),
            (2, 1),
            (2, 2),
            (3, 2),
            (3, 3),
            (0, 3),
        ]
        out = relax_contour(pixel, smooth_iterations=3, target_vertex_count=32)
        assert len(out) == 32


class TestBuildAnnulusEdgePairs:
    def test_outer_below_three_raises(self) -> None:
        with pytest.raises(ValueError, match="outer_count must be >= 3"):
            build_annulus_edge_pairs(2, 0)

    def test_inner_two_raises(self) -> None:
        with pytest.raises(ValueError, match="inner_count must be 0 or >= 3"):
            build_annulus_edge_pairs(4, 2)

    def test_inner_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="inner_count must be >= 0"):
            build_annulus_edge_pairs(4, -1)

    def test_outer_only_cyclic_edges(self) -> None:
        edges = build_annulus_edge_pairs(4, 0)
        assert edges == [(0, 1), (1, 2), (2, 3), (3, 0)]

    def test_annulus_has_two_disjoint_loops(self) -> None:
        edges = build_annulus_edge_pairs(4, 3)
        # 4 outer + 3 inner = 7 edges.
        assert len(edges) == 7
        # Outer loop indices 0-3, inner loop indices 4-6.
        outer = [(0, 1), (1, 2), (2, 3), (3, 0)]
        inner = [(4, 5), (5, 6), (6, 4)]
        assert edges == outer + inner

    def test_no_bridge_edges_between_loops(self) -> None:
        # triangle_fill in bmesh produces the annulus; bridges would
        # confuse the Delaunay triangulator.
        edges = build_annulus_edge_pairs(6, 4)
        for start, end in edges:
            same_loop = (start < 6 and end < 6) or (start >= 6 and end >= 6)
            assert same_loop, f"unexpected bridge edge {(start, end)}"
