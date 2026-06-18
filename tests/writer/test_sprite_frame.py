"""Pure-pytest unit tests for the sprite-frame wrap helper.

The conftest bpy/mathutils stand-ins let the writer module import so the
pure frame-index math runs without Blender.
"""

from __future__ import annotations

from blender.exporters.godot.writer import sprite_frame_animations as sfa


def test_wrap_in_range_is_unchanged() -> None:
    assert sfa._wrap_frame(2, 3) == 2
    assert sfa._wrap_frame(0, 3) == 0
    assert sfa._wrap_frame(3, 3) == 3


def test_wrap_positive_overflow_wraps_like_blender() -> None:
    # hframes*vframes = 4 (max_frame 3): Blender's MODULO shows 4 -> 0, 5 -> 1.
    assert sfa._wrap_frame(4, 3) == 0
    assert sfa._wrap_frame(5, 3) == 1
    assert sfa._wrap_frame(8, 3) == 0


def test_wrap_negative_is_non_negative() -> None:
    # Python modulo keeps the result in [0, max_frame]; -1 lands on the last cell.
    assert sfa._wrap_frame(-1, 3) == 3
    assert sfa._wrap_frame(-4, 3) == 0


def test_wrap_single_cell_grid_is_always_zero() -> None:
    # max_frame 0 -> one cell; every index collapses to 0 (no div-by-zero).
    assert sfa._wrap_frame(7, 0) == 0
    assert sfa._wrap_frame(-3, 0) == 0
