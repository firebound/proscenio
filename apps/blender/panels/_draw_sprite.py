"""Sprite-frame body draw (slot panel + region readout).

Renders the sprite-frame metadata block: hframes / vframes / frame /
centered, the atlas+region readout, the preview-shader setup buttons,
and the shared region authoring box.
"""

from __future__ import annotations

import bpy

from ..core._shared.material_images import (  # type: ignore[import-not-found]
    iter_material_images,
)


def draw_body(
    layout: bpy.types.UILayout,
    obj: bpy.types.Object,
    props: bpy.types.AnyType,
) -> None:
    """Sprite-frame body block - drawn inside the Active Sprite subpanel."""
    layout.prop(props, "hframes")
    layout.prop(props, "vframes")
    layout.prop(props, "frame")
    layout.prop(props, "centered")
    _draw_readout(layout, obj, props)
    _draw_preview_shader_buttons(layout, obj)


def _draw_readout(
    box: bpy.types.UILayout,
    obj: bpy.types.Object,
    props: bpy.types.AnyType,
) -> None:
    """Show atlas + region + frame size info for a sprite_frame mesh."""
    atlas_size = _discover_atlas_size_for(obj)
    if atlas_size is None:
        box.label(text="atlas: not linked in material", icon="INFO")
        return
    aw, ah = atlas_size
    box.label(text=f"atlas: {aw}x{ah} px", icon="IMAGE_DATA")
    if props.region_mode == "manual":
        rw_px = max(1, round(props.region_w * aw))
        rh_px = max(1, round(props.region_h * ah))
        box.label(text=f"region: {rw_px}x{rh_px} px (manual)")
    else:
        rw_px, rh_px = aw, ah
        box.label(text=f"region: {rw_px}x{rh_px} px (full atlas)")
    hf = max(1, int(props.hframes))
    vf = max(1, int(props.vframes))
    fw = rw_px // hf
    fh = rh_px // vf
    box.label(text=f"frame: {fw}x{fh} px ({hf}x{vf} grid)")


def _discover_atlas_size_for(obj: bpy.types.Object) -> tuple[int, int] | None:
    """Walk the object's materials and return the first valid image's pixel size."""
    for image in iter_material_images(obj):
        w, h = image.size
        if w > 0 and h > 0:
            return (int(w), int(h))
    return None


def _draw_preview_shader_buttons(layout: bpy.types.UILayout, obj: bpy.types.Object) -> None:
    """Render Material Preview slicer setup/remove buttons."""
    has_slicer = _material_has_slicer(obj)
    row = layout.row(align=True)
    setup = row.row()
    setup.enabled = not has_slicer
    setup.operator(
        "proscenio.setup_sprite_frame_preview",
        text="Setup Preview",
        icon="SHADERFX",
    )
    remove = row.row()
    remove.enabled = has_slicer
    remove.operator(
        "proscenio.remove_sprite_frame_preview",
        text="Remove Preview",
        icon="X",
    )


def _material_has_slicer(obj: bpy.types.Object) -> bool:
    """True when any of the mesh's materials carries the SpriteFrameSlicer node."""
    from ..core.bpy_helpers.spritesheet.spritesheet_shader import (  # type: ignore[import-not-found]
        SLICER_GROUP_NAME,
    )

    materials = getattr(obj.data, "materials", None) or []
    for mat in materials:
        if mat is None or not getattr(mat, "use_nodes", False):
            continue
        nt = getattr(mat, "node_tree", None)
        if nt is None:
            continue
        for node in nt.nodes:
            if node.type == "GROUP" and getattr(node.node_tree, "name", "") == SLICER_GROUP_NAME:
                return True
    return False
