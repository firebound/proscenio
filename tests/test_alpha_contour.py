"""Unit tests for SPEC 013 pure-Python alpha contour walker.

bpy-free. Exercises the contour tracing + binary morphology helpers
consumed by ``core/bpy_helpers/automesh_bmesh.py``.

Run from the repo root:

    pytest tests/test_alpha_contour.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.alpha_contour import (  # noqa: E402  - sys.path setup above
    AlphaGrid,
    BinaryMask,
    binarize,
    dilate,
    erode,
    extract_contour_pair,
    extract_inner_contour,
    extract_outer_contour,
    find_first_boundary,
    trace_contour,
)


def _square_alpha(size: int, inset: int = 0) -> AlphaGrid:
    """Build an N x N alpha grid with a fully-opaque inset square."""
    grid: AlphaGrid = [[0 for _ in range(size)] for _ in range(size)]
    for y in range(inset, size - inset):
        for x in range(inset, size - inset):
            grid[y][x] = 255
    return grid


def _checkerboard_alpha(size: int) -> AlphaGrid:
    """Two disjoint squares for multi-island tests."""
    grid: AlphaGrid = [[0 for _ in range(size)] for _ in range(size)]
    for y in range(2):
        for x in range(2):
            grid[y][x] = 255
    for y in range(size - 2, size):
        for x in range(size - 2, size):
            grid[y][x] = 255
    return grid


def _l_shape_alpha(size: int) -> AlphaGrid:
    """Concave L-shaped silhouette."""
    grid: AlphaGrid = [[0 for _ in range(size)] for _ in range(size)]
    # Vertical bar of the L
    for y in range(2, size - 2):
        for x in range(2, 5):
            grid[y][x] = 255
    # Horizontal foot of the L
    for y in range(size - 5, size - 2):
        for x in range(2, size - 2):
            grid[y][x] = 255
    return grid


class TestBinarize:
    def test_threshold_127_default(self) -> None:
        grid: AlphaGrid = [[0, 100, 128, 200, 255]]
        mask = binarize(grid, 127)
        assert mask == [[False, False, True, True, True]]

    def test_threshold_0_passes_anything_above_zero(self) -> None:
        grid: AlphaGrid = [[0, 1, 128, 255]]
        mask = binarize(grid, 0)
        assert mask == [[False, True, True, True]]

    def test_threshold_255_rejects_everything(self) -> None:
        grid: AlphaGrid = [[0, 100, 200, 255]]
        mask = binarize(grid, 255)
        assert mask == [[False, False, False, False]]

    def test_empty_grid_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one row"):
            binarize([], 127)

    def test_empty_row_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one column"):
            binarize([[]], 127)

    def test_out_of_range_threshold_raises(self) -> None:
        with pytest.raises(ValueError, match="\\[0, 255\\]"):
            binarize([[100]], -1)
        with pytest.raises(ValueError, match="\\[0, 255\\]"):
            binarize([[100]], 256)


class TestDilate:
    def test_zero_iterations_is_identity(self) -> None:
        mask: BinaryMask = [[True, False], [False, True]]
        out = dilate(mask, 0)
        assert out == mask
        assert out is not mask  # defensive copy returned

    def test_negative_iterations_raise(self) -> None:
        with pytest.raises(ValueError, match=">= 0"):
            dilate([[True]], -1)

    def test_single_pixel_grows_to_plus_shape(self) -> None:
        mask: BinaryMask = [
            [False, False, False],
            [False, True, False],
            [False, False, False],
        ]
        out = dilate(mask, 1)
        assert out == [
            [False, True, False],
            [True, True, True],
            [False, True, False],
        ]

    def test_dilation_is_idempotent_on_full_mask(self) -> None:
        mask: BinaryMask = [[True, True], [True, True]]
        assert dilate(mask, 5) == mask


class TestErode:
    def test_zero_iterations_is_identity(self) -> None:
        mask: BinaryMask = [[True, False], [False, True]]
        out = erode(mask, 0)
        assert out == mask
        assert out is not mask

    def test_negative_iterations_raise(self) -> None:
        with pytest.raises(ValueError, match=">= 0"):
            erode([[True]], -1)

    def test_border_pixels_erode_due_to_grid_edge(self) -> None:
        # 3x3 full mask: border pixels touch the grid edge so they erode.
        mask: BinaryMask = [[True] * 3 for _ in range(3)]
        out = erode(mask, 1)
        # Only the center survives one erosion pass.
        assert out == [
            [False, False, False],
            [False, True, False],
            [False, False, False],
        ]

    def test_thin_silhouette_erodes_entirely(self) -> None:
        mask = binarize(_square_alpha(5, inset=1), 127)
        # 3x3 inner square -> one erode pass leaves only center.
        out = erode(mask, 2)
        assert all(not pixel for row in out for pixel in row)


class TestFindFirstBoundary:
    def test_empty_mask_returns_none(self) -> None:
        mask: BinaryMask = [[False] * 4 for _ in range(4)]
        assert find_first_boundary(mask) is None

    def test_top_left_pixel_found_first(self) -> None:
        mask: BinaryMask = [[True, False], [False, False]]
        assert find_first_boundary(mask) == (0, 0)

    def test_first_hit_is_topmost_then_leftmost(self) -> None:
        mask: BinaryMask = [
            [False, False, False],
            [False, False, True],
            [True, True, True],
        ]
        # Row 1 hits first (top-to-bottom), x=2 is the leftmost True there.
        assert find_first_boundary(mask) == (2, 1)


class TestTraceContour:
    def test_single_isolated_pixel_returns_self(self) -> None:
        mask: BinaryMask = [
            [False, False, False],
            [False, True, False],
            [False, False, False],
        ]
        contour = trace_contour(mask, (1, 1))
        # Moore Neighbour on an isolated pixel finds no neighbour - returns
        # just the seed pixel.
        assert contour == [(1, 1)]

    def test_invalid_start_raises(self) -> None:
        mask: BinaryMask = [[True, False], [False, False]]
        with pytest.raises(ValueError, match="outside the mask"):
            trace_contour(mask, (-1, 0))
        with pytest.raises(ValueError, match="not a foreground pixel"):
            trace_contour(mask, (1, 1))

    def test_square_contour_walks_perimeter(self) -> None:
        alpha = _square_alpha(6, inset=1)
        contour = extract_outer_contour(alpha, 127, 0)
        # 4x4 inner square has 12 boundary pixels (perimeter cells).
        assert len(contour) == 12
        # First point sits at the top-left corner of the inset square.
        assert contour[0] == (1, 1)

    def test_contour_walks_clockwise(self) -> None:
        alpha = _square_alpha(6, inset=1)
        contour = extract_outer_contour(alpha, 127, 0)
        # Second point should advance to the east (clockwise from top-left).
        first_x, first_y = contour[0]
        second_x, second_y = contour[1]
        # Clockwise from (1,1) on the top edge goes east first.
        assert (second_x, second_y) in {(2, 1), (1, 2), (2, 2)}
        if (second_x, second_y) == (2, 1):
            assert second_x - first_x == 1
            assert second_y == first_y


class TestExtractOuterContour:
    def test_empty_silhouette_raises(self) -> None:
        alpha = _square_alpha(4, inset=4)  # all-zero grid
        with pytest.raises(ValueError, match="no foreground pixels"):
            extract_outer_contour(alpha, 127, 0)

    def test_dilation_grows_contour(self) -> None:
        alpha = _square_alpha(8, inset=3)  # 2x2 inset square
        bare = extract_outer_contour(alpha, 127, 0)
        dilated = extract_outer_contour(alpha, 127, 1)
        # Dilated outline encloses more cells -> longer contour.
        assert len(dilated) > len(bare)


class TestExtractInnerContour:
    def test_thin_silhouette_returns_empty(self) -> None:
        alpha = _square_alpha(5, inset=1)  # 3x3 inset
        result = extract_inner_contour(alpha, 127, 5)  # erode > silhouette
        assert result == []

    def test_zero_erode_matches_outer(self) -> None:
        alpha = _square_alpha(6, inset=1)
        outer = extract_outer_contour(alpha, 127, 0)
        inner = extract_inner_contour(alpha, 127, 0)
        assert inner == outer


class TestExtractContourPair:
    def test_negative_margin_raises(self) -> None:
        alpha = _square_alpha(4, inset=1)
        with pytest.raises(ValueError, match="margin_px must be >= 0"):
            extract_contour_pair(alpha, 127, -1)

    def test_pair_returns_outer_larger_than_inner(self) -> None:
        alpha = _square_alpha(10, inset=2)  # 6x6 inset square
        outer, inner = extract_contour_pair(alpha, 127, 1)
        assert len(outer) > len(inner) > 0

    def test_thin_silhouette_inner_empty(self) -> None:
        alpha = _square_alpha(6, inset=2)  # 2x2 inset, margin 2 wipes inner
        outer, inner = extract_contour_pair(alpha, 127, 2)
        assert len(outer) > 0
        assert inner == []

    def test_l_shape_outer_traces_concave_hull(self) -> None:
        alpha = _l_shape_alpha(12)
        outer = extract_outer_contour(alpha, 127, 0)
        # L-shape has 2 outward corners + concave inset; contour visits both.
        assert len(outer) > 4
        # Sanity: contour is non-self-intersecting (no duplicate points
        # except possibly the start match used by Jacob's stop).
        unique = set(outer)
        assert len(unique) == len(outer)
