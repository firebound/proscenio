"""Active Sprite subpanel + helpers (SPEC 005 + 5.1.c.1 + 5.1.d.1)."""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core import validation  # type: ignore[import-not-found]
from ..core.feature_status import badge_for, status_for  # type: ignore[import-not-found]
from ._helpers import (
    _HELP_OP_IDNAME,
    _OBJECT_FRIENDLY_MODES,
    _STATUS_OP_IDNAME,
    draw_subpanel_header,
)


def _draw_sprite_frame_readout(
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


def _draw_weight_paint_disabled_hint(layout: bpy.types.UILayout) -> None:
    """Show why weight paint controls are not surfaced for sprite_frame meshes."""
    box = layout.box()
    box.label(text="weight paint not applicable to sprite_frame", icon="INFO")
    box.label(text="(Sprite2D is not deformed by bones)")


def _discover_atlas_size_for(obj: bpy.types.Object) -> tuple[int, int] | None:
    """Walk the active mesh's materials and return the first image's pixel size."""
    mesh = obj.data
    materials = getattr(mesh, "materials", None) or []
    for mat in materials:
        size = _first_tex_image_size(mat)
        if size is not None:
            return size
    return None


def _first_tex_image_size(mat: bpy.types.Material | None) -> tuple[int, int] | None:
    if mat is None or not mat.use_nodes or mat.node_tree is None:
        return None
    for node in mat.node_tree.nodes:
        if node.type != "TEX_IMAGE" or node.image is None:
            continue
        w, h = node.image.size
        if w > 0 and h > 0:
            return (int(w), int(h))
    return None


def _draw_region_box(
    layout: bpy.types.UILayout,
    props: bpy.types.AnyType,
    *,
    sprite_type: str,
) -> None:
    """Render the texture_region authoring box (5.1.c.1)."""
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


def _draw_active_sprite_body(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    obj: bpy.types.Object,
    props: bpy.types.AnyType,
) -> None:
    """Pick the body subsection by sprite_type + active mode."""
    if props.sprite_type == "sprite_frame":
        _draw_sprite_frame_body(layout, context, obj, props)
    elif context.mode == "PAINT_WEIGHT":
        _draw_weight_paint_brush(layout, context)
    else:
        _draw_polygon_body(layout, obj, props)


def _draw_sprite_frame_body(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    obj: bpy.types.Object,
    props: bpy.types.AnyType,
) -> None:
    box = layout.box()
    box.label(text="Sprite frame", icon="IMAGE_DATA")
    box.prop(props, "hframes")
    box.prop(props, "vframes")
    box.prop(props, "frame")
    box.prop(props, "centered")
    _draw_sprite_frame_readout(box, obj, props)
    _draw_preview_shader_buttons(box, obj)
    _draw_region_box(layout, props, sprite_type="sprite_frame")
    if context.mode == "PAINT_WEIGHT":
        _draw_weight_paint_disabled_hint(layout)


def _draw_preview_shader_buttons(layout: bpy.types.UILayout, obj: bpy.types.Object) -> None:
    """Render Material Preview slicer setup/remove buttons (SPEC 004 D13)."""
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
    from ..core.bpy_helpers.sprite_frame_shader import (  # type: ignore[import-not-found]
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


def _draw_polygon_body(
    layout: bpy.types.UILayout,
    obj: bpy.types.Object,
    props: bpy.types.AnyType,
) -> None:
    mesh = obj.data
    vg_count = len(getattr(obj, "vertex_groups", []) or [])
    poly_count = len(getattr(mesh, "polygons", []) or [])
    box = layout.box()
    box.label(text="Polygon", icon="MESH_DATA")
    box.label(text=f"{poly_count} polygon(s), {vg_count} vertex group(s)")
    box.operator("proscenio.reproject_sprite_uv", text="Reproject UV", icon="UV")
    box.prop(props, "material_isolated")
    _draw_region_box(layout, props, sprite_type="polygon")


def _draw_weight_paint_brush(layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
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


def _draw_driver_shortcut(
    layout: bpy.types.UILayout,
    _context: bpy.types.Context,
    props: bpy.types.AnyType,
) -> None:
    """Render the 5.1.d.1 driver-shortcut box."""
    box = layout.box()
    header = box.row(align=True)
    header.label(text="Drive from bone", icon="DRIVER")
    right = header.row()
    right.alignment = "RIGHT"
    badge = badge_for("drive_from_bone")
    status = status_for("drive_from_bone")
    op_status = right.operator(_STATUS_OP_IDNAME, text="", icon=badge.icon, emboss=False)
    op_status.band = status.value
    op = right.operator(_HELP_OP_IDNAME, text="", icon="QUESTION", emboss=False)
    op.topic = "drive_from_bone"
    box.prop(props, "driver_target", text="Target")
    box.prop(props, "driver_source_armature", text="Armature")
    box.prop(props, "driver_source_bone", text="Bone")
    box.prop(props, "driver_source_axis", text="Axis")
    box.prop(props, "driver_expression", text="Expression")
    row = box.row()
    armature = props.driver_source_armature
    has_bones = armature is not None and bool(getattr(armature.data, "bones", None))
    row.enabled = has_bones and bool(props.driver_source_bone)
    row.operator("proscenio.create_driver", text="Drive from Bone", icon="DRIVER")


class PROSCENIO_PT_active_sprite(bpy.types.Panel):
    """Per-sprite settings -- sprite type dropdown + sprite_frame metadata."""

    bl_label = "Active Sprite"
    bl_idname = "PROSCENIO_PT_active_sprite"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return False
        return context.mode in _OBJECT_FRIENDLY_MODES

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "active_sprite", "active_sprite")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        obj = context.active_object
        if obj is None:
            return

        props = getattr(obj, "proscenio", None)
        if props is None:
            layout.label(text="proscenio property group not registered", icon="ERROR")
            return

        layout.prop(props, "sprite_type")
        _draw_active_sprite_body(layout, context, obj, props)
        _draw_driver_shortcut(layout, context, props)

        for issue in validation.validate_active_sprite(obj):
            row = layout.row()
            icon = "ERROR" if issue.severity == "error" else "INFO"
            row.alert = issue.severity == "error"
            row.label(text=issue.message, icon=icon)


_classes: tuple[type, ...] = (PROSCENIO_PT_active_sprite,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
