"""Unit tests for SPEC 012.2 Quick Armature pure-math helpers.

bpy-free. Covers chord resolution (D10), grid snap (D12), axis lock
(D11), and naming (D2 + D15) primitives consumed by
``apps/blender/operators/quick_armature.py``.

Run from the repo root:

    pytest tests/test_quick_armature_math.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.quick_armature_math import (  # noqa: E402  - sys.path setup above
    DEFAULT_NAME_PREFIX,
    apply_axis_lock,
    format_bone_name,
    resolve_press_mode,
    sanitize_prefix,
    snap_world_point_xz,
)


class TestResolvePressMode:
    """D10: invert default chord vocabulary (chain by default)."""

    def test_default_chain_no_modifier_chains_connected(self) -> None:
        assert resolve_press_mode(shift_held=False, default_chain=True) == (True, True)

    def test_default_chain_with_shift_starts_new_root(self) -> None:
        assert resolve_press_mode(shift_held=True, default_chain=True) == (False, False)

    def test_legacy_no_modifier_starts_new_root(self) -> None:
        assert resolve_press_mode(shift_held=False, default_chain=False) == (False, False)

    def test_legacy_with_shift_chains_unconnected(self) -> None:
        assert resolve_press_mode(shift_held=True, default_chain=False) == (True, False)


class TestSnapWorldPointXz:
    """D12: snap X / Z to nearest grid increment; preserve Y."""

    def test_snap_to_unit_grid(self) -> None:
        assert snap_world_point_xz((1.4, 0.0, 2.7), 1.0) == (1.0, 0.0, 3.0)

    def test_snap_to_half_unit_grid(self) -> None:
        assert snap_world_point_xz((1.4, 0.0, 2.7), 0.5) == (1.5, 0.0, 2.5)

    def test_y_is_preserved(self) -> None:
        assert snap_world_point_xz((1.0, 7.5, 2.0), 1.0)[1] == pytest.approx(7.5)

    def test_zero_increment_is_no_op(self) -> None:
        point = (1.234, 5.678, 9.0)
        assert snap_world_point_xz(point, 0.0) == point

    def test_negative_increment_is_no_op(self) -> None:
        point = (1.234, 5.678, 9.0)
        assert snap_world_point_xz(point, -1.0) == point

    def test_negative_coords_round_to_nearest(self) -> None:
        assert snap_world_point_xz((-1.4, 0.0, -2.7), 1.0) == (-1.0, 0.0, -3.0)


class TestApplyAxisLock:
    """D11: clamp the non-locked component of tail to head's value."""

    def test_lock_x_keeps_x_free_clamps_y_z(self) -> None:
        head = (1.0, 0.0, 5.0)
        tail = (3.0, 7.0, 8.0)
        assert apply_axis_lock(head, tail, "X") == (3.0, 0.0, 5.0)

    def test_lock_z_clamps_x_keeps_z_free(self) -> None:
        head = (1.0, 0.0, 5.0)
        tail = (3.0, 7.0, 8.0)
        assert apply_axis_lock(head, tail, "Z") == (1.0, 0.0, 8.0)

    def test_no_lock_returns_tail_unchanged(self) -> None:
        head = (1.0, 0.0, 5.0)
        tail = (3.0, 7.0, 8.0)
        assert apply_axis_lock(head, tail, None) == tail


class TestSanitizePrefix:
    def test_strips_leading_trailing_whitespace(self) -> None:
        assert sanitize_prefix("  def  ") == "def"

    def test_empty_falls_back_to_default(self) -> None:
        assert sanitize_prefix("") == DEFAULT_NAME_PREFIX

    def test_whitespace_only_falls_back_to_default(self) -> None:
        assert sanitize_prefix("   ") == DEFAULT_NAME_PREFIX

    def test_none_falls_back_to_default(self) -> None:
        assert sanitize_prefix(None) == DEFAULT_NAME_PREFIX

    def test_passes_through_non_default(self) -> None:
        assert sanitize_prefix("ctrl") == "ctrl"


class TestFormatBoneName:
    def test_pads_index_to_three_digits(self) -> None:
        assert format_bone_name("def", 0) == "def.000"
        assert format_bone_name("def", 7) == "def.007"
        assert format_bone_name("def", 42) == "def.042"

    def test_index_above_999_overflows(self) -> None:
        # Documented behaviour: padding floor is 3, larger indices grow.
        assert format_bone_name("def", 1000) == "def.1000"
