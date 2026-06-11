"""Apply a named brush curve preset to the active weight-paint brush."""

from __future__ import annotations

from typing import ClassVar

import bpy

from ...core.skinning.brush_curve_presets import (  # type: ignore[import-not-found]
    PRESET_LABELS,
    PRESETS,
)


def _rebuild_curve_points(
    curve_map: bpy.types.CurveMap,
    points: list[tuple[float, float]],
) -> None:
    """Rebuild a CurveMap's points to exactly ``points`` (ascending x, >= 2).

    ``CurveMapPoints`` keeps a two-point floor, reallocates its backing array
    on ``remove``, and re-sorts by x on ``new`` and on every ``location``
    write. So a held point proxy goes stale across any mutation, and an
    in-place x edit can reorder the collection under the loop index - which is
    what made the previous truncate / set-in-place / new sequence fragile. The
    safe shape: trim to the floor refetching the tail each pass; pin the two
    survivors to the min and max target x (neither write can push a point past
    the other); grow the interior in ascending x; then pin every slot by index
    once the order is settled.
    """
    ordered = sorted(points)
    while len(curve_map.points) > 2:
        curve_map.points.remove(curve_map.points[-1])
    curve_map.points[0].location = ordered[0]
    curve_map.points[1].location = ordered[-1]
    for x, y in ordered[1:-1]:
        curve_map.points.new(x, y)
    for i, (x, y) in enumerate(ordered):
        curve_map.points[i].location = (x, y)


def _apply_preset_to_brush(brush: bpy.types.Brush, preset_name: str) -> tuple[bool, str]:
    """Write the named preset onto ``brush``'s falloff curve.

    Returns ``(ok, message)``. ``ok`` is False when nothing was applied (the
    brush has no distance-falloff curve, or a CurveMap mutation threw); the
    caller surfaces ``message`` as a WARNING. Split from ``execute`` so the
    full apply path - the 5.x ``curve_distance_falloff`` attribute resolution,
    the CUSTOM preset force, and the rebuild - is unit-testable without a
    tool-settings brush, which the 5.x asset system will not assign headless.
    """
    # Blender 5.x's brush refactor renamed the falloff CurveMapping from
    # ``brush.curve`` to ``brush.curve_distance_falloff`` - the old name raised
    # AttributeError on click (the never-captured report symptom).
    mapping = getattr(brush, "curve_distance_falloff", None)
    if mapping is None or not mapping.curves:
        return False, "Active brush has no distance-falloff curve"
    try:
        # The falloff is gated behind a preset enum; force CUSTOM so the written
        # points actually drive the curve rather than a built-in shape.
        if hasattr(brush, "curve_distance_falloff_preset"):
            brush.curve_distance_falloff_preset = "CUSTOM"
        _rebuild_curve_points(mapping.curves[0], PRESETS[preset_name])
        mapping.update()
    except RuntimeError as exc:
        # CurveMapPoints mutation can still throw under a live brush context;
        # degrade to a warning instead of propagating and aborting the click.
        return False, f"Could not apply brush curve preset: {exc}"
    return True, f"Brush preset applied: {PRESET_LABELS[preset_name]}"


class PROSCENIO_OT_set_brush_preset(bpy.types.Operator):
    bl_idname = "proscenio.set_brush_preset"
    bl_label = "Apply Brush Curve Preset"
    bl_description = "Configure the active weight-paint brush curve to a named preset"
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    preset_name: bpy.props.EnumProperty(  # type: ignore[valid-type]
        name="Preset",
        items=[(name, PRESET_LABELS[name], "") for name in PRESETS],
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        ts = context.tool_settings
        return ts is not None and ts.weight_paint is not None and ts.weight_paint.brush is not None

    def execute(self, context: bpy.types.Context) -> set[str]:
        brush = context.tool_settings.weight_paint.brush
        ok, message = _apply_preset_to_brush(brush, self.preset_name)
        self.report({"INFO"} if ok else {"WARNING"}, message)
        return {"FINISHED"} if ok else {"CANCELLED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_set_brush_preset,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
