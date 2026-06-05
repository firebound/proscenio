"""Pure tests for inner-loop erosion."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.automesh.contour import BinaryMask  # noqa: E402
from core.automesh.erosion_loops import compute_inner_loops  # noqa: E402


def _solid_square(side: int) -> BinaryMask:
    return [[True] * side for _ in range(side)]


def _solid_disc(radius: int) -> BinaryMask:
    diameter = 2 * radius + 1
    cx = cy = radius
    mask: BinaryMask = []
    for y in range(diameter):
        row = []
        for x in range(diameter):
            dx, dy = x - cx, y - cy
            row.append(dx * dx + dy * dy <= radius * radius)
        mask.append(row)
    return mask


def test_count_zero_returns_empty():
    mask = _solid_square(10)
    assert compute_inner_loops(mask, count=0, spacing_px=1) == []


def test_single_loop_smaller_than_outer():
    mask = _solid_square(20)
    loops = compute_inner_loops(mask, count=1, spacing_px=2)
    assert len(loops) == 1
    assert len(loops[0]) >= 3


def test_three_loops_each_smaller():
    mask = _solid_disc(10)
    loops = compute_inner_loops(mask, count=3, spacing_px=1)
    assert len(loops) == 3
    for i in range(len(loops) - 1):
        assert len(loops[i + 1]) <= len(loops[i])


def test_collapse_stops_early():
    mask = _solid_square(5)
    loops = compute_inner_loops(mask, count=3, spacing_px=2)
    assert len(loops) < 3


def test_negative_spacing_raises():
    import pytest

    mask = _solid_square(10)
    with pytest.raises(ValueError, match="spacing_px"):
        compute_inner_loops(mask, count=1, spacing_px=-1)
