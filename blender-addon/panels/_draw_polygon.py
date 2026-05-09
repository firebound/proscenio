"""Polygon body + weight paint draws (SPEC 005 + 5.1.b).

Polygon mode block: poly count, vertex group count, reproject UV
button, isolated material toggle, shared region box. Plus the inline
weight-paint brush mirror used when the user is in PAINT_WEIGHT mode.

Pulled out of ``panels/active_sprite.py`` by SPEC 009 wave 9.10.
"""

from __future__ import annotations

import bpy

from . import _draw_region


def draw_body(
    layout: bpy.types.UILayout,
    obj: bpy.types.Object,
    props: bpy.types.AnyType,
) -> None:
    """Polygon body block."""
    mesh = obj.data
    vg_count = len(getattr(obj, "vertex_groups", []) or [])
    poly_count = len(getattr(mesh, "polygons", []) or [])
    box = layout.box()
    box.label(text="Polygon", icon="MESH_DATA")
    box.label(text=f"{poly_count} polygon(s), {vg_count} vertex group(s)")
    box.operator("proscenio.reproject_sprite_uv", text="Reproject UV", icon="UV")
    box.prop(props, "material_isolated")
    _draw_region.draw_box(layout, props, sprite_type="polygon")


def draw_weight_paint(layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
    """Mirror Blender's weight-paint brush controls inline (5.1.b)."""
    box = layout.box()
    box.label(text="Weight paint", icon="BRUSH_DATA")
    tool_settings = context.tool_settings
    wp = getattr(tool_settings, "weight_paint", None)
    brush = getattr(wp, "brush", None) if wp is not None else None
    if brush is None:
        box.label(text="no active brush", icon="INFO")
        return
    ups = tool_settings.unified_paint_settings
    box.prop(ups, "use_unified_size", text="Unified size")
    box.prop(ups if ups.use_unified_size else brush, "size", slider=True)
    box.prop(ups, "use_unified_strength", text="Unified strength")
    box.prop(ups if ups.use_unified_strength else brush, "strength", slider=True)
    box.prop(ups if ups.use_unified_weight else brush, "weight", slider=True)
    box.prop(brush, "use_auto_normalize", text="Auto-normalize")
