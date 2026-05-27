"""Apply a named brush curve preset to the active weight-paint brush (O4)."""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core.skinning.brush_curve_presets import PRESET_LABELS, PRESETS


class PROSCENIO_OT_set_brush_preset(bpy.types.Operator):
    bl_idname = "proscenio.set_brush_preset"
    bl_label = "Apply Brush Curve Preset"
    bl_description = "Configure the active weight-paint brush curve to a named preset"
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    preset_name: bpy.props.EnumProperty(
        name="Preset",
        items=[(name, PRESET_LABELS[name], "") for name in PRESETS],
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        ts = context.tool_settings
        return ts is not None and ts.weight_paint is not None and ts.weight_paint.brush is not None

    def execute(self, context: bpy.types.Context) -> set[str]:
        brush = context.tool_settings.weight_paint.brush
        if brush.curve is None or not brush.curve.curves:
            self.report({"WARNING"}, "Active brush has no curve mapping")
            return {"CANCELLED"}
        curve = brush.curve.curves[0]
        new_points = PRESETS[self.preset_name]
        # Truncate existing points to 2 (the min CurveMap allows) before re-adding
        while len(curve.points) > 2:
            curve.points.remove(curve.points[-1])
        # Set the first 2 points (positions exist; just update location)
        for i, (x, y) in enumerate(new_points[:2]):
            curve.points[i].location = (x, y)
        # Add the rest
        for x, y in new_points[2:]:
            curve.points.new(x, y)
        brush.curve.update()
        self.report({"INFO"}, f"Brush preset applied: {PRESET_LABELS[self.preset_name]}")
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_set_brush_preset,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
