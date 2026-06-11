"""Headless tests for the Drive-from-Bone operator's range-based expression.

Runs INSIDE Blender via ``run_operator_tests.py``. The pure linear-map builder
is covered in ``tests/test_driver_expression.py``; here the operator must route
the two ranges through that builder onto a real driver fcurve, honour the
Advanced toggle that keeps a hand-written expression verbatim, and mirror the
ranges back to the PropertyGroup for the redo panel.
"""

from __future__ import annotations

import bpy
import pytest


def _activate(name: str) -> bpy.types.Object:
    obj = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    return obj


def _driver_fcurve(obj: bpy.types.Object, data_path: str) -> bpy.types.FCurve | None:
    if obj.animation_data is None:
        return None
    return obj.animation_data.drivers.find(data_path)


def _eval_driver(expr: str, var: float) -> float:
    """Evaluate a stored driver expression, Blender-style (var + min/max bound).

    String-equality against a Python-double rebuild is brittle: the operator's
    FloatProperty rounds the range inputs to float32, so the embedded literals
    differ from a float64 ``repr``. Assert behaviour instead.
    """
    return float(eval(expr, {"__builtins__": {}}, {"var": var, "min": min, "max": max}))


def test_create_driver_builds_range_expression(automesh_fixture):
    obj = _activate("hand")
    result = bpy.ops.proscenio.create_driver(
        armature_name="automesh.hand_rig",
        bone_name="wrist",
        target_property="region_x",
        source_axis="ROT_Y",
        advanced=False,
        in_min=-1.5708,
        in_max=1.5708,
        out_min=0.0,
        out_max=1.0,
    )
    assert "FINISHED" in result
    fcurve = _driver_fcurve(obj, "proscenio.region_x")
    assert fcurve is not None
    expr = fcurve.driver.expression
    assert expr != "var", "operator stored the raw passthrough, not the built map"
    # Behaviour of the built map: centre maps to mid-output and a slightly
    # negative rotation no longer clamps to 0 (the recorded first-contact bug).
    assert _eval_driver(expr, 0.0) == pytest.approx(0.5, abs=1e-3)
    assert _eval_driver(expr, -1.5708) == pytest.approx(0.0, abs=1e-3)
    assert _eval_driver(expr, 1.5708) == pytest.approx(1.0, abs=1e-3)
    assert _eval_driver(expr, -0.1) > 0.0
    target = fcurve.driver.variables[0].targets[0]
    assert target.id is bpy.data.objects["automesh.hand_rig"]
    assert target.bone_target == "wrist"


def test_create_driver_advanced_keeps_raw_expression(automesh_fixture):
    obj = _activate("hand")
    result = bpy.ops.proscenio.create_driver(
        armature_name="automesh.hand_rig",
        bone_name="palm",
        target_property="region_y",
        source_axis="ROT_Y",
        advanced=True,
        expression="var * 2.0",
    )
    assert "FINISHED" in result
    fcurve = _driver_fcurve(obj, "proscenio.region_y")
    assert fcurve is not None
    assert fcurve.driver.expression == "var * 2.0"


def test_create_driver_mirrors_ranges_to_props(automesh_fixture):
    from proscenio.core._shared.props_access import object_props  # type: ignore[import-not-found]

    obj = _activate("hand")
    bpy.ops.proscenio.create_driver(
        armature_name="automesh.hand_rig",
        bone_name="wrist",
        target_property="region_x",
        source_axis="ROT_Y",
        advanced=False,
        in_min=-1.0,
        in_max=1.0,
        out_min=0.2,
        out_max=0.8,
    )
    props = object_props(obj)
    assert props.driver_in_min == pytest.approx(-1.0)
    assert props.driver_in_max == pytest.approx(1.0)
    assert props.driver_out_min == pytest.approx(0.2)
    assert props.driver_out_max == pytest.approx(0.8)
    assert props.driver_advanced is False
