"""Unit tests for the draw-order -> Y layout math (bpy-free; runs without Blender)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.draw_order import y_location_from_draw_order  # noqa: E402


def test_y_location_scales_order_by_spacing():
    assert y_location_from_draw_order(3, 0.5) == 1.5


def test_y_location_zero_order_is_origin():
    assert y_location_from_draw_order(0, 0.5) == 0.0


def test_y_location_negative_order_fans_the_other_way():
    assert y_location_from_draw_order(-2, 0.25) == -0.5
