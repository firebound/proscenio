"""Texture region authoring box (the authoring panel).

Shared between the sprite and mesh body draws - both need
the auto / manual mode toggle and the four region floats. Pulled into
its own helper module by the code-modularity work.
"""

from __future__ import annotations

import bpy


def draw_box(
    layout: bpy.types.UILayout,
    props: bpy.types.AnyType,
    *,
    element_type: str,
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
        if element_type == "mesh":
            box.operator("proscenio.snap_region_to_uv", text="Snap to UV bounds", icon="UV")
    else:
        hint = (
            "computed from UV bounds at export"
            if element_type == "mesh"
            else "omitted at export - full atlas used"
        )
        box.label(text=hint, icon="INFO")
