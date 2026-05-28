"""Pure tests for brush curve preset data (O4)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.skinning.brush_curve_presets import PRESET_LABELS, PRESETS  # noqa: E402


def test_all_presets_have_at_least_two_points():
    for name, points in PRESETS.items():
        assert len(points) >= 2, f"preset {name} needs >=2 points"


def test_all_presets_endpoints_in_unit_range():
    for name, points in PRESETS.items():
        for x, y in points:
            assert 0.0 <= x <= 1.0, f"preset {name} x out of range: {x}"
            assert 0.0 <= y <= 1.0, f"preset {name} y out of range: {y}"


def test_all_presets_start_at_x_zero_end_at_x_one():
    for name, points in PRESETS.items():
        assert points[0][0] == 0.0, f"preset {name} first x must be 0.0"
        assert points[-1][0] == 1.0, f"preset {name} last x must be 1.0"


def test_label_exists_for_each_preset():
    for name in PRESETS:
        assert name in PRESET_LABELS
        assert PRESET_LABELS[name].strip(), f"preset {name} has empty label"
