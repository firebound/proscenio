"""Unit tests for the sprite-frame grid clamp.

Pure pytest, no Blender. The frame property update callback delegates the
bound to ``clamp_frame_index``; these pin the [0, hframes*vframes-1] range.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core._shared.sprite_grid import clamp_frame_index  # noqa: E402


def test_in_range_frame_is_unchanged() -> None:
    assert clamp_frame_index(3, 2, 3) == 3  # grid 2x3 = 6 cells, max index 5


def test_over_range_frame_clamps_to_last_cell() -> None:
    assert clamp_frame_index(99, 2, 3) == 5  # 2*3 - 1


def test_shrinking_the_grid_pulls_the_frame_in() -> None:
    # frame 5 was valid on a 2x3 grid; on a 1x1 grid the only cell is 0.
    assert clamp_frame_index(5, 1, 1) == 0


def test_negative_frame_clamps_to_zero() -> None:
    assert clamp_frame_index(-4, 4, 4) == 0


def test_single_cell_grid_clamps_everything_to_zero() -> None:
    assert clamp_frame_index(7, 1, 1) == 0


def test_last_valid_index_is_kept() -> None:
    assert clamp_frame_index(15, 4, 4) == 15  # 4*4 - 1
