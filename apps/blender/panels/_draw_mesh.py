"""Mesh body draw for the Active Mesh subpanel.

Mesh mode block: poly count, vertex group count, reproject UV
button, isolated material toggle, shared region box.
"""

from __future__ import annotations

import bpy


def draw_body(
    layout: bpy.types.UILayout,
    obj: bpy.types.Object,
    props: bpy.types.AnyType,
) -> None:
    """Mesh body block - drawn inside the Active Mesh subpanel."""
    mesh = obj.data
    vg_count = len(getattr(obj, "vertex_groups", []) or [])
    poly_count = len(getattr(mesh, "polygons", []) or [])
    layout.label(text=f"{poly_count} polygon(s), {vg_count} vertex group(s)")
    layout.operator("proscenio.reproject_sprite_uv", text="Reproject UV", icon="UV")
    layout.prop(props, "material_isolated")
    layout.prop(props, "exclude_from_atlas")
