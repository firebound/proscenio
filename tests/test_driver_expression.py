"""Unit tests for the bone-channel -> property driver expression builder.

bpy-free. The builder turns the Drive-from-Bone two-range UI (an input
bone-channel range and an output target-value range) into a clamped
linear-map driver expression string. It replaces the raw ``var`` default
that mapped radians straight onto a 0..N frame range, so negative rotation
clamped to 0 and the flagship driver looked broken on first contact.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.armature.driver_expression import build_driver_expression  # noqa: E402


def _eval(expr: str, var: float) -> float:
    """Evaluate a built driver expression with ``var`` bound, Blender-style.

    Blender exposes ``min``/``max`` (and the ``math`` module) in the driver
    namespace; mirror just the pieces these expressions use.
    """
    return float(eval(expr, {"__builtins__": {}}, {"var": var, "min": min, "max": max}))


class TestLinearMapInsideBand:
    def test_unit_range_is_identity_at_midpoint(self) -> None:
        expr = build_driver_expression(0.0, 1.0, 0.0, 1.0)
        assert _eval(expr, 0.5) == pytest.approx(0.5)

    def test_unit_range_maps_endpoints(self) -> None:
        expr = build_driver_expression(0.0, 1.0, 0.0, 10.0)
        assert _eval(expr, 0.0) == pytest.approx(0.0)
        assert _eval(expr, 1.0) == pytest.approx(10.0)


class TestClamping:
    def test_below_input_range_holds_at_output_low(self) -> None:
        expr = build_driver_expression(0.0, 1.0, 0.0, 1.0)
        assert _eval(expr, -1.0) == pytest.approx(0.0)

    def test_above_input_range_holds_at_output_high(self) -> None:
        expr = build_driver_expression(0.0, 1.0, 0.0, 1.0)
        assert _eval(expr, 2.0) == pytest.approx(1.0)


class TestNegativeSpanningDefault:
    """The recorded first-contact failure: negative rotation clamped to 0."""

    def test_centre_maps_to_output_midpoint(self) -> None:
        expr = build_driver_expression(-1.5708, 1.5708, 0.0, 1.0)
        assert _eval(expr, 0.0) == pytest.approx(0.5, abs=1e-4)

    def test_slight_negative_rotation_is_not_clamped_to_zero(self) -> None:
        expr = build_driver_expression(-1.5708, 1.5708, 0.0, 1.0)
        value = _eval(expr, -0.1)
        assert value > 0.0, "negative rotation still clamps to 0 - the original bug"
        assert value == pytest.approx(0.5 + (-0.1) / 3.1416, abs=1e-4)

    def test_negative_extreme_reaches_output_low(self) -> None:
        expr = build_driver_expression(-1.5708, 1.5708, 0.0, 1.0)
        assert _eval(expr, -1.5708) == pytest.approx(0.0, abs=1e-4)


class TestInvertedOutputRange:
    def test_descending_output_maps_endpoints(self) -> None:
        expr = build_driver_expression(0.0, 1.0, 1.0, 0.0)
        assert _eval(expr, 0.0) == pytest.approx(1.0)
        assert _eval(expr, 1.0) == pytest.approx(0.0)

    def test_descending_output_clamps_within_sorted_band(self) -> None:
        expr = build_driver_expression(0.0, 1.0, 1.0, 0.0)
        assert _eval(expr, 2.0) == pytest.approx(0.0)
        assert _eval(expr, -1.0) == pytest.approx(1.0)


class TestDegenerateInputRange:
    def test_zero_width_input_returns_constant_output_min(self) -> None:
        expr = build_driver_expression(1.0, 1.0, 0.3, 0.9)
        assert _eval(expr, 0.0) == pytest.approx(0.3)
        assert _eval(expr, 5.0) == pytest.approx(0.3)
