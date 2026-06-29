"""Pure tests for the ADD-island mask union (spec 070): fill_polygon_into_mask
+ extract_outer_contour_with_islands. No bpy - exercises the contour math that
makes an overlapping island MERGE with the silhouette instead of grafting."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.automesh.contour import (  # noqa: E402
    extract_outer_contour,
    extract_outer_contour_with_islands,
    fill_polygon_into_mask,
)


def _empty_mask(w: int, h: int) -> list[list[bool]]:
    return [[False] * w for _ in range(h)]


def test_fill_polygon_sets_interior_cells():
    mask = _empty_mask(10, 10)
    # A 4x4 square (cells 2..5 on both axes).
    fill_polygon_into_mask(mask, [(2.0, 2.0), (6.0, 2.0), (6.0, 6.0), (2.0, 6.0)])
    assert mask[3][3] is True  # interior
    assert mask[5][5] is True
    assert mask[0][0] is False  # outside
    assert mask[8][8] is False


def test_fill_polygon_ignores_degenerate():
    mask = _empty_mask(5, 5)
    fill_polygon_into_mask(mask, [(1.0, 1.0), (3.0, 1.0)])  # 2 verts
    assert all(not cell for row in mask for cell in row)


def test_fill_polygon_clips_out_of_bounds():
    mask = _empty_mask(6, 6)
    # Square spilling past the right/bottom edges - must clip, not raise.
    fill_polygon_into_mask(mask, [(3.0, 3.0), (20.0, 3.0), (20.0, 20.0), (3.0, 20.0)])
    assert mask[4][4] is True
    assert mask[5][5] is True  # last in-bounds cell


def _solid_block_alpha(
    w: int, h: int, x0: int, x1: int, y0: int, y1: int
) -> list[list[int]]:
    """Alpha grid (0/255) with a solid foreground block [x0,x1) x [y0,y1)."""
    grid = [[0] * w for _ in range(h)]
    for y in range(y0, y1):
        for x in range(x0, x1):
            grid[y][x] = 255
    return grid


def test_island_overlapping_silhouette_merges_into_one_larger_contour():
    """An island overlapping the alpha block yields ONE contour enclosing the
    union - wider than the bare silhouette (the merge, not a detour)."""
    alpha = _solid_block_alpha(40, 40, 5, 20, 10, 30)  # block x in [5,20)
    bare = extract_outer_contour(alpha, threshold=127, dilate_px=0)
    # Island overlapping the block's right edge and poking further right.
    island = [(15.0, 14.0), (30.0, 14.0), (30.0, 26.0), (15.0, 26.0)]
    merged = extract_outer_contour_with_islands(alpha, 127, 0, [island])
    bare_max_x = max(x for x, _ in bare)
    merged_max_x = max(x for x, _ in merged)
    assert merged_max_x > bare_max_x, "island did not grow the silhouette rightward"
    # One contour (a single closed loop), not two.
    assert len(merged) >= len(bare)


def test_detached_island_is_dropped_not_traced():
    """A fully detached ADD island is ignored (spec 070: ADD must overlap). Without
    the connectivity guard trace_contour could walk the detached island instead of
    the real silhouette; the merged contour must equal the bare one."""
    alpha = _solid_block_alpha(40, 40, 4, 14, 4, 14)  # block top-left
    bare = extract_outer_contour(alpha, 127, 0)
    detached = [(25.0, 25.0), (35.0, 25.0), (35.0, 35.0), (25.0, 35.0)]  # far away
    merged = extract_outer_contour_with_islands(alpha, 127, 0, [detached])
    assert merged == bare


def test_no_islands_matches_plain_extract():
    alpha = _solid_block_alpha(30, 30, 4, 18, 6, 22)
    assert extract_outer_contour_with_islands(
        alpha, 127, 0, []
    ) == extract_outer_contour(alpha, 127, 0)
