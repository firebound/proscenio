"""Unit tests for the Quick Armature pure-math helpers.

bpy-free. Covers chord resolution, grid snap, axis lock, and naming
primitives consumed by
``apps/blender/operators/quick_armature.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.armature.quick_armature_math import (  # noqa: E402  - sys.path setup above
    PREVIEW_COLOR,
    PREVIEW_COLOR_DISCONNECTED,
    PREVIEW_COLOR_INVALID,
    PREVIEW_COLOR_UNPARENTED,
    DEFAULT_NAME_PREFIX,
    apply_axis_lock,
    axis_guideline_endpoints,
    format_bone_name,
    preview_color_for,
    resolve_pick,
    resolve_press_mode,
    resolve_press_mode_label,
    sanitize_prefix,
    snap_world_point_xz,
)


class TestPreviewColorFor:
    def test_off_canvas_is_invalid_red(self) -> None:
        assert preview_color_for(cursor_in_canvas=False, press_mode="connected") == (
            PREVIEW_COLOR_INVALID
        )

    def test_unparented_is_cyan(self) -> None:
        assert preview_color_for(cursor_in_canvas=True, press_mode="unparented") == (
            PREVIEW_COLOR_UNPARENTED
        )

    def test_disconnected_is_yellow(self) -> None:
        assert preview_color_for(cursor_in_canvas=True, press_mode="disconnected") == (
            PREVIEW_COLOR_DISCONNECTED
        )

    def test_connected_is_the_default_orange(self) -> None:
        assert (
            preview_color_for(cursor_in_canvas=True, press_mode="connected")
            == PREVIEW_COLOR
        )


class TestAxisGuidelineEndpoints:
    def test_x_axis_spans_horizontally_through_head(self) -> None:
        assert axis_guideline_endpoints((1.0, 2.0, 3.0), "X", 10.0) == (
            (-9.0, 2.0, 3.0),
            (11.0, 2.0, 3.0),
        )

    def test_z_axis_spans_in_depth_through_head(self) -> None:
        assert axis_guideline_endpoints((1.0, 2.0, 3.0), "Z", 10.0) == (
            (1.0, 2.0, -7.0),
            (1.0, 2.0, 13.0),
        )

    def test_no_lock_returns_none(self) -> None:
        assert axis_guideline_endpoints((1.0, 2.0, 3.0), None, 10.0) is None


class TestResolvePressMode:
    """Chord vocabulary aligned with Blender bone parenting."""

    def test_default_chain_no_modifier_returns_connected(self) -> None:
        assert resolve_press_mode(shift_held=False, default_chain=True) == (True, True)

    def test_default_chain_with_shift_returns_unparented(self) -> None:
        assert resolve_press_mode(shift_held=True, default_chain=True) == (False, False)

    def test_alt_held_returns_disconnected(self) -> None:
        assert resolve_press_mode(
            shift_held=False, alt_held=True, default_chain=True
        ) == (True, False)

    def test_alt_with_shift_still_disconnected(self) -> None:
        # Alt wins over Shift; user explicitly asked for parented + free head.
        assert resolve_press_mode(
            shift_held=True, alt_held=True, default_chain=True
        ) == (True, False)

    def test_legacy_no_modifier_returns_unparented(self) -> None:
        assert resolve_press_mode(shift_held=False, default_chain=False) == (
            False,
            False,
        )

    def test_legacy_with_shift_returns_disconnected(self) -> None:
        # Legacy chord: Shift = parent + use_connect=False.
        assert resolve_press_mode(shift_held=True, default_chain=False) == (True, False)


class TestResolvePressModeLabel:
    """Same chord matrix returned as Blender-aligned labels."""

    def test_default_no_modifier_is_connected(self) -> None:
        assert (
            resolve_press_mode_label(
                shift_held=False, alt_held=False, default_chain=True
            )
            == "connected"
        )

    def test_default_shift_is_unparented(self) -> None:
        assert (
            resolve_press_mode_label(
                shift_held=True, alt_held=False, default_chain=True
            )
            == "unparented"
        )

    def test_alt_label_is_disconnected(self) -> None:
        assert (
            resolve_press_mode_label(
                shift_held=False, alt_held=True, default_chain=True
            )
            == "disconnected"
        )

    def test_legacy_no_modifier_is_unparented(self) -> None:
        assert (
            resolve_press_mode_label(
                shift_held=False, alt_held=False, default_chain=False
            )
            == "unparented"
        )

    def test_legacy_shift_is_disconnected(self) -> None:
        assert (
            resolve_press_mode_label(
                shift_held=True, alt_held=False, default_chain=False
            )
            == "disconnected"
        )


class TestSnapWorldPointXz:
    """Snap X / Z to nearest grid increment; preserve Y."""

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
    """Clamp the non-locked component of tail to head's value."""

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


class TestResolvePick:
    """Reparent hit-test: nearest bone tail within a world radius, by name.

    The pure core of viewport pick-parent - the operator projects the cursor
    and each bone tail to the Y=0 XZ plane, then this resolves which bone tip
    (if any) the click landed on. Returns the bone name on a hit, ``None`` on
    a miss (cursor in empty space), so the operator can no-op with feedback.
    """

    def test_cursor_near_a_tip_picks_that_bone(self) -> None:
        tips = [("boneA", (0.0, 0.0)), ("boneB", (5.0, 0.0)), ("boneC", (0.0, 5.0))]
        # Cursor sits a hair from boneB's tail.
        assert resolve_pick((5.05, 0.02), tips, radius=0.5) == "boneB"

    def test_cursor_in_empty_space_picks_nothing(self) -> None:
        tips = [("boneA", (0.0, 0.0)), ("boneB", (5.0, 0.0))]
        # Cursor far from every tail (beyond the radius) -> no reparent.
        assert resolve_pick((50.0, 50.0), tips, radius=0.5) is None

    def test_no_tips_picks_nothing(self) -> None:
        assert resolve_pick((0.0, 0.0), [], radius=0.5) is None

    def test_picks_the_nearest_when_two_are_in_radius(self) -> None:
        tips = [("near", (0.1, 0.0)), ("far", (0.4, 0.0))]
        assert resolve_pick((0.0, 0.0), tips, radius=1.0) == "near"

    def test_tie_keeps_the_first(self) -> None:
        tips = [("first", (1.0, 0.0)), ("second", (-1.0, 0.0))]
        # Equidistant from the origin; the lower index wins (nearest_index uses
        # strict <), so the first-listed bone is chosen.
        assert resolve_pick((0.0, 0.0), tips, radius=2.0) == "first"

    def test_on_the_radius_boundary_counts_as_a_hit(self) -> None:
        tips = [("edge", (1.0, 0.0))]
        # Exactly at the radius: nearest_index caps with <=, so this hits.
        assert resolve_pick((0.0, 0.0), tips, radius=1.0) == "edge"
