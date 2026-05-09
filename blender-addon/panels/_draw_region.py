"""Texture region authoring box (SPEC 005 5.1.c.1).

Shared between the sprite_frame and polygon body draws -- both need
the auto / manual mode toggle and the four region floats. Pulled into
its own helper module by SPEC 009 wave 9.10.
"""

from __future__ import annotations

import bpy


def draw_box(
    layout: bpy.types.UILayout,
    props: bpy.types.AnyType,
    *,
    sprite_type: str,
) -> None:
    """Render the texture_region authoring box."""
    box = layout.box()
    box.label(text="Texture region", icon="UV_DATA")
    box.prop(props, "region_mode", text="")
    if props.region_mode == "manual":
        row = box.row(align=True)
        row.prop(props, "region_x")
        row.prop(props, "region_y")
        row = box.row(align=True)
        row.prop(props, "region_w")
        row.prop(props, "region_h")
        if sprite_type == "polygon":
            box.operator("proscenio.snap_region_to_uv", text="Snap to UV bounds", icon="UV")
    else:
        hint = (
            "computed from UV bounds at export"
            if sprite_type == "polygon"
            else "omitted at export -- full atlas used"
        )
        box.label(text=hint, icon="INFO")
