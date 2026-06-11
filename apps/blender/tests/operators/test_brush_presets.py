"""Headless tests for the brush curve preset operator and rebuild.

Runs INSIDE Blender via ``run_operator_tests.py``. Two bugs under test:

1. Blender 5.x's brush refactor renamed the falloff CurveMapping from
   ``brush.curve`` to ``brush.curve_distance_falloff``, so the operator
   raised ``AttributeError`` on click (the report's never-captured symptom).
2. Applying a preset mutates the live ``CurveMapPoints`` collection, which
   reallocates on ``remove`` and re-sorts by x on ``new`` - so the rebuild
   must refetch proxies and insert in ascending-x order.

The tests pin the resulting point locations across the fragile truncate /
set / new sequence, including the shrink-from-many-points-back-to-two path,
and exercise the operator end to end so the renamed-attribute fix stays fixed.
"""

from __future__ import annotations

import bpy
import pytest

_PRESET_NAMES = ["HARD_EDGE", "SOFT_FALLOFF", "CREASE", "SMOOTH_BLEND"]


def _new_weight_brush() -> bpy.types.Brush:
    """A fresh weight-paint brush, or skip when this build has no falloff curve."""
    brush = bpy.data.brushes.new("proscenio_preset_test", mode="WEIGHT_PAINT")
    mapping = getattr(brush, "curve_distance_falloff", None)
    if mapping is None or not mapping.curves:
        pytest.skip("brush has no distance-falloff curve in this build")
    return brush


def _falloff(brush: bpy.types.Brush) -> bpy.types.CurveMap:
    return brush.curve_distance_falloff.curves[0]


def _locations(curve_map: bpy.types.CurveMap) -> list[tuple[float, float]]:
    return [(round(p.location[0], 6), round(p.location[1], 6)) for p in curve_map.points]


def _expected(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return [(round(x, 6), round(y, 6)) for (x, y) in points]


@pytest.mark.parametrize("preset_name", _PRESET_NAMES)
def test_preset_rebuild_lands_exact_points(automesh_fixture, preset_name):
    from proscenio.core.skinning.brush_curve_presets import (
        PRESETS,  # type: ignore[import-not-found]
    )
    from proscenio.operators.skinning.brush_preset import (  # type: ignore[import-not-found]
        _rebuild_curve_points,
    )

    brush = _new_weight_brush()
    _rebuild_curve_points(_falloff(brush), PRESETS[preset_name])
    brush.curve_distance_falloff.update()
    assert _locations(_falloff(brush)) == _expected(PRESETS[preset_name])


def test_presets_in_sequence_each_lands_exact(automesh_fixture):
    # Exercises the truncate path: shrinking from many points down to two
    # and growing back, the exact sequence the live-mutation bug corrupts.
    from proscenio.core.skinning.brush_curve_presets import (
        PRESETS,  # type: ignore[import-not-found]
    )
    from proscenio.operators.skinning.brush_preset import (  # type: ignore[import-not-found]
        _rebuild_curve_points,
    )

    brush = _new_weight_brush()
    for name in ("CREASE", "SOFT_FALLOFF", "SMOOTH_BLEND", "HARD_EDGE", "CREASE", "SOFT_FALLOFF"):
        _rebuild_curve_points(_falloff(brush), PRESETS[name])
        brush.curve_distance_falloff.update()
        assert _locations(_falloff(brush)) == _expected(PRESETS[name]), f"failed after {name}"


def test_apply_preset_to_brush_writes_falloff(automesh_fixture):
    # The full apply path (5.x curve_distance_falloff resolution + CUSTOM force
    # + rebuild) without a tool-settings brush, which the asset system will not
    # assign headless. Catches the renamed-attribute regression: the old
    # brush.curve path returned ok=False ("no distance-falloff curve") before
    # ever reaching the rebuild.
    from proscenio.core.skinning.brush_curve_presets import (
        PRESETS,  # type: ignore[import-not-found]
    )
    from proscenio.operators.skinning.brush_preset import (  # type: ignore[import-not-found]
        _apply_preset_to_brush,
    )

    brush = _new_weight_brush()
    ok, message = _apply_preset_to_brush(brush, "CREASE")
    assert ok, message
    assert _locations(_falloff(brush)) == _expected(PRESETS["CREASE"])
    if hasattr(brush, "curve_distance_falloff_preset"):
        assert brush.curve_distance_falloff_preset == "CUSTOM"
