"""Read/write tool_settings.weight_paint preset.

Maps PaintPresetSnapshot fields onto the live bpy brush + unified
paint settings. Symmetric snapshot/apply so the modal can restore
the prior brush state on exit.
"""

from __future__ import annotations

import bpy

from ...skinning.paint_preset_2d import PaintPresetSnapshot, build_target_preset

_MIRROR_FLAG_KEY = "proscenio_mirror_x"


def snapshot_paint_preset(context: bpy.types.Context) -> PaintPresetSnapshot:
    """Read tool_settings.weight_paint + active brush into a snapshot."""
    ts = context.tool_settings.weight_paint
    brush = ts.brush
    return PaintPresetSnapshot(
        use_front_faces=bool(getattr(brush, "use_frontface", True)),
        use_normal=bool(getattr(brush, "use_projected", False)),
        use_accumulate=bool(getattr(brush, "use_accumulate", False)),
        use_pressure_size=bool(getattr(brush, "use_pressure_size", False)),
        use_pressure_strength=bool(getattr(brush, "use_pressure_strength", False)),
        use_x_mirror=bool(getattr(ts, "use_symmetry_x", False)),
        brush_radius=int(getattr(brush, "size", 24)),
        brush_strength=float(getattr(brush, "strength", 0.5)),
    )


def apply_paint_preset(context: bpy.types.Context, *, mirror_x: bool) -> None:
    """Write the 2D preset onto tool_settings + active brush."""
    target = build_target_preset(mirror_x=mirror_x)
    _write_preset(context, target)


def restore_paint_preset(context: bpy.types.Context, snapshot: PaintPresetSnapshot) -> None:
    """Reapply the prior snapshot onto tool_settings + active brush."""
    _write_preset(context, snapshot)


def _write_preset(context: bpy.types.Context, preset: PaintPresetSnapshot) -> None:
    ts = context.tool_settings.weight_paint
    brush = ts.brush
    if hasattr(brush, "use_frontface"):
        brush.use_frontface = preset.use_front_faces
    if hasattr(brush, "use_projected"):
        brush.use_projected = preset.use_normal
    if hasattr(brush, "use_accumulate"):
        brush.use_accumulate = preset.use_accumulate
    if hasattr(brush, "use_pressure_size"):
        brush.use_pressure_size = preset.use_pressure_size
    if hasattr(brush, "use_pressure_strength"):
        brush.use_pressure_strength = preset.use_pressure_strength
    if hasattr(ts, "use_symmetry_x"):
        ts.use_symmetry_x = preset.use_x_mirror
    if hasattr(brush, "size"):
        brush.size = preset.brush_radius
    if hasattr(brush, "strength"):
        brush.strength = preset.brush_strength


def read_mirror_flag(armature: bpy.types.Object) -> bool:
    """Picker rig's X-mirror Custom Property; default False when absent."""
    return bool(armature.get(_MIRROR_FLAG_KEY, False))
