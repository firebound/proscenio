"""Unit tests for SPEC 013 automesh interior-density helpers.

bpy-free. Exercises point-in-polygon, distance-to-segment, uniform
grid generation, annulus clipping, and bone-aware subdivision -
the math the bpy bridge feeds into ``bmesh.ops.triangle_fill``
between the outer + inner contours.

Run from the repo root:

    pytest tests/test_automesh_density.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.automesh_density import (  # noqa: E402  - sys.path setup above
    BoneSegment2D,
    Point2D,
    bone_aware_subdivision,
    bounding_box,
    distance_to_segment,
    filter_inside_annulus,
    interior_points_for_annulus,
    point_in_polygon,
    uniform_interior_grid,
)


def _square(size: float) -> list[Point2D]:
    return [(0.0, 0.0), (size, 0.0), (size, size), (0.0, size)]


def _centered_square(center: Point2D, half_size: float) -> list[Point2D]:
    cx, cy = center
    return [
        (cx - half_size, cy - half_size),
        (cx + half_size, cy - half_size),
        (cx + half_size, cy + half_size),
        (cx - half_size, cy + half_size),
    ]


class TestBoundingBox:
    def test_square_box(self) -> None:
        assert bounding_box(_square(10.0)) == (0.0, 0.0, 10.0, 10.0)

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            bounding_box([])

    def test_negative_coords_supported(self) -> None:
        assert bounding_box([(-2.0, -3.0), (1.0, 4.0)]) == (-2.0, -3.0, 1.0, 4.0)


class TestPointInPolygon:
    def test_center_inside_square(self) -> None:
        assert point_in_polygon((5.0, 5.0), _square(10.0)) is True

    def test_outside_below_left(self) -> None:
        assert point_in_polygon((-1.0, -1.0), _square(10.0)) is False

    def test_outside_above_right(self) -> None:
        assert point_in_polygon((11.0, 11.0), _square(10.0)) is False

    def test_short_polygon_returns_false(self) -> None:
        assert point_in_polygon((0.0, 0.0), [(0.0, 0.0), (1.0, 1.0)]) is False

    def test_concave_l_shape(self) -> None:
        # L shape: long vertical bar + foot
        l_shape = [
            (0.0, 0.0), (3.0, 0.0), (3.0, 1.0),
            (1.0, 1.0), (1.0, 5.0), (0.0, 5.0),
        ]
        assert point_in_polygon((0.5, 0.5), l_shape) is True
        assert point_in_polygon((0.5, 4.0), l_shape) is True
        # Concave bite (outside the L body)
        assert point_in_polygon((2.5, 4.0), l_shape) is False


class TestDistanceToSegment:
    def test_point_on_segment_zero_distance(self) -> None:
        d = distance_to_segment((5.0, 0.0), ((0.0, 0.0), (10.0, 0.0)))
        assert d == pytest.approx(0.0)

    def test_perpendicular_distance(self) -> None:
        d = distance_to_segment((5.0, 3.0), ((0.0, 0.0), (10.0, 0.0)))
        assert d == pytest.approx(3.0)

    def test_projection_falls_before_start(self) -> None:
        # Projection at x=-2 maps outside [0, 1], so distance = to A.
        d = distance_to_segment((-2.0, 0.0), ((0.0, 0.0), (10.0, 0.0)))
        assert d == pytest.approx(2.0)

    def test_projection_falls_after_end(self) -> None:
        # Projection past B, distance = to B.
        d = distance_to_segment((15.0, 4.0), ((0.0, 0.0), (10.0, 0.0)))
        assert d == pytest.approx(math.hypot(5.0, 4.0))

    def test_zero_length_segment_falls_back_to_point_distance(self) -> None:
        d = distance_to_segment((3.0, 4.0), ((0.0, 0.0), (0.0, 0.0)))
        assert d == pytest.approx(5.0)


class TestUniformInteriorGrid:
    def test_negative_spacing_raises(self) -> None:
        with pytest.raises(ValueError, match="spacing must be > 0"):
            uniform_interior_grid((0.0, 0.0, 10.0, 10.0), -1.0)

    def test_grid_dimensions_match_bbox_and_spacing(self) -> None:
        # 10x10 bbox with spacing 2 -> 5x5 = 25 grid points.
        out = uniform_interior_grid((0.0, 0.0, 10.0, 10.0), 2.0)
        assert len(out) == 25

    def test_grid_points_lie_inside_bbox(self) -> None:
        bbox = (0.0, 0.0, 10.0, 10.0)
        out = uniform_interior_grid(bbox, 2.0)
        min_x, min_y, max_x, max_y = bbox
        for x, y in out:
            assert min_x <= x <= max_x
            assert min_y <= y <= max_y

    def test_zero_area_bbox_returns_empty(self) -> None:
        assert uniform_interior_grid((0.0, 0.0, 0.0, 5.0), 1.0) == []
        assert uniform_interior_grid((0.0, 0.0, 5.0, 0.0), 1.0) == []


class TestFilterInsideAnnulus:
    def test_no_outer_returns_empty(self) -> None:
        assert filter_inside_annulus([(1.0, 1.0)], [], []) == []

    def test_no_inner_keeps_inside_outer(self) -> None:
        candidates = [(5.0, 5.0), (-1.0, 5.0), (11.0, 5.0)]
        out = filter_inside_annulus(candidates, _square(10.0), [])
        assert out == [(5.0, 5.0)]

    def test_annulus_excludes_inner_hole(self) -> None:
        # Outer 0..10 square, inner 4..6 hole. Only ring is interior.
        outer = _square(10.0)
        inner = _centered_square((5.0, 5.0), 1.0)
        candidates = [
            (5.0, 5.0),  # center of inner -> excluded
            (2.0, 5.0),  # ring -> kept
            (5.0, 2.0),  # ring -> kept
            (-1.0, 5.0),  # outside outer -> excluded
        ]
        out = filter_inside_annulus(candidates, outer, inner)
        assert (5.0, 5.0) not in out
        assert (-1.0, 5.0) not in out
        assert (2.0, 5.0) in out
        assert (5.0, 2.0) in out


class TestBoneAwareSubdivision:
    def test_negative_radius_raises(self) -> None:
        with pytest.raises(ValueError, match="influence_radius"):
            bone_aware_subdivision([], [], -1.0, 2)

    def test_subdivision_factor_below_one_raises(self) -> None:
        with pytest.raises(ValueError, match="subdivision_factor"):
            bone_aware_subdivision([], [], 1.0, 0)

    def test_factor_one_returns_unchanged(self) -> None:
        base: list[Point2D] = [(1.0, 1.0), (2.0, 2.0)]
        bones: list[BoneSegment2D] = [((0.0, 0.0), (5.0, 5.0))]
        out = bone_aware_subdivision(base, bones, 10.0, 1)
        assert out == base

    def test_no_bones_returns_unchanged(self) -> None:
        base: list[Point2D] = [(1.0, 1.0), (2.0, 2.0)]
        out = bone_aware_subdivision(base, [], 5.0, 4)
        assert out == base

    def test_points_far_from_bone_not_subdivided(self) -> None:
        base: list[Point2D] = [(100.0, 100.0)]
        bones: list[BoneSegment2D] = [((0.0, 0.0), (1.0, 0.0))]
        out = bone_aware_subdivision(base, bones, 5.0, 4)
        assert out == base

    def test_points_near_bone_are_densified(self) -> None:
        base: list[Point2D] = [(0.5, 0.5)]
        bones: list[BoneSegment2D] = [((0.0, 0.0), (10.0, 0.0))]
        out = bone_aware_subdivision(base, bones, 5.0, 4)
        # factor=4 means 3 extras per influenced point.
        assert len(out) == 4


class TestInteriorPointsForAnnulus:
    def test_empty_outer_returns_empty(self) -> None:
        assert interior_points_for_annulus([], [], 1.0) == []

    def test_zero_spacing_raises(self) -> None:
        with pytest.raises(ValueError, match="spacing must be > 0"):
            interior_points_for_annulus(_square(10.0), [], 0.0)

    def test_uniform_density_without_bones(self) -> None:
        # 10x10 outer, 2x2 inner hole, spacing 2 -> grid 5x5 = 25,
        # minus the 1 point landing inside the hole.
        outer = _square(10.0)
        inner = _centered_square((5.0, 5.0), 1.0)
        out = interior_points_for_annulus(outer, inner, 2.0)
        # The center point (5, 5) falls inside the hole and is filtered.
        assert all(not (4.0 <= x <= 6.0 and 4.0 <= y <= 6.0) for x, y in out)

    def test_no_inner_falls_back_to_outer_only(self) -> None:
        outer = _square(10.0)
        out = interior_points_for_annulus(outer, [], 5.0)
        # 10x10 bbox at spacing 5 -> 2x2 = 4 candidates, all inside outer.
        assert len(out) == 4

    def test_bones_with_factor_one_no_extra_density(self) -> None:
        outer = _square(10.0)
        bones: list[BoneSegment2D] = [((0.0, 5.0), (10.0, 5.0))]
        uniform = interior_points_for_annulus(outer, [], 2.0)
        with_bones = interior_points_for_annulus(
            outer, [], 2.0, bone_segments=bones,
            bone_density_radius=5.0, bone_density_factor=1,
        )
        assert len(with_bones) == len(uniform)

    def test_bones_with_factor_two_adds_density(self) -> None:
        outer = _square(20.0)
        bones: list[BoneSegment2D] = [((0.0, 10.0), (20.0, 10.0))]
        uniform = interior_points_for_annulus(outer, [], 4.0)
        with_bones = interior_points_for_annulus(
            outer, [], 4.0, bone_segments=bones,
            bone_density_radius=6.0, bone_density_factor=2,
        )
        assert len(with_bones) > len(uniform)
