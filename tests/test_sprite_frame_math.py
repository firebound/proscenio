"""Unit tests for the SPEC 004 D13 sprite_frame preview cell math.

Pure pytest, no Blender. Covers the bpy-free helpers in
``core.sprite_frame_math`` that compute the per-cell UV slicing math;
the bpy graph builder in ``core.bpy_helpers.sprite_frame_shader`` is
exercised manually on the doll fixture.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.sprite_frame_math import (  # noqa: E402
    cell_offset_x,
    cell_offset_y,
    cell_size,
)


def test_cell_size_4x1_yields_quarter_width() -> None:
    w, h = cell_size(hframes=4, vframes=1)
    assert w == pytest.approx(0.25)
    assert h == pytest.approx(1.0)


def test_cell_size_2x2_yields_half_each() -> None:
    w, h = cell_size(hframes=2, vframes=2)
    assert w == pytest.approx(0.5)
    assert h == pytest.approx(0.5)


def test_cell_size_zero_falls_back_to_unit() -> None:
    """Defensive: validation surfaces the user error separately, but the
    shader graph never divides by zero."""
    assert cell_size(hframes=0, vframes=0) == (1.0, 1.0)
    assert cell_size(hframes=-3, vframes=-1) == (1.0, 1.0)


def test_cell_offset_x_walks_columns() -> None:
    # 4-wide grid: frame 0 -> col 0, frame 1 -> col 1, ...
    assert cell_offset_x(0, hframes=4) == pytest.approx(0.0)
    assert cell_offset_x(1, hframes=4) == pytest.approx(0.25)
    assert cell_offset_x(2, hframes=4) == pytest.approx(0.5)
    assert cell_offset_x(3, hframes=4) == pytest.approx(0.75)


def test_cell_offset_x_wraps_modulo_hframes() -> None:
    """Frame index past the end of a row wraps - lets the y-offset advance."""
    assert cell_offset_x(4, hframes=4) == pytest.approx(0.0)
    assert cell_offset_x(5, hframes=4) == pytest.approx(0.25)


def test_cell_offset_y_top_to_bottom() -> None:
    """Frame 0 sits at the top of the atlas; subsequent rows step down."""
    # 4x2 grid. Frames 0-3 = row 0 (top); frames 4-7 = row 1 (bottom).
    assert cell_offset_y(0, hframes=4, vframes=2) == pytest.approx(0.5)
    assert cell_offset_y(3, hframes=4, vframes=2) == pytest.approx(0.5)
    assert cell_offset_y(4, hframes=4, vframes=2) == pytest.approx(0.0)
    assert cell_offset_y(7, hframes=4, vframes=2) == pytest.approx(0.0)


def test_cell_offset_y_single_row_pins_top() -> None:
    """A 4x1 sheet: every frame sits at the bottom UV origin (Blender's V=0)
    because there is only one row spanning the full height."""
    for f in range(4):
        assert cell_offset_y(f, hframes=4, vframes=1) == pytest.approx(0.0)


def test_cell_offset_y_wraps_when_frame_exceeds_grid() -> None:
    """frame >= hframes*vframes wraps via modulo on rows - defensive,
    matches the validation pass which surfaces the out-of-range error
    but does not block the shader from rendering something."""
    # 2x2 grid, frame 4 wraps to row 0
    assert cell_offset_y(4, hframes=2, vframes=2) == pytest.approx(0.5)


def test_cell_offset_x_zero_hframes_falls_back_to_unit() -> None:
    """Defensive fallback: hframes=0 is treated as 1 so column = 0."""
    assert cell_offset_x(5, hframes=0) == pytest.approx(0.0)


def test_cell_offset_y_zero_dims_falls_back_to_top() -> None:
    assert cell_offset_y(5, hframes=0, vframes=0) == pytest.approx(0.0)
