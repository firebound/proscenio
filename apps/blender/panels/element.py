"""Element panel + per-kind subpanels.

The Element panel hosts the isolated element-type selector and surfaces
validation issues for the active element. The body splits into
accordion subpanels: Active Mesh / Active Sprite (one shows per
``element_type``), plus the shared Texture Region and Drive from Bone
subpanels. Per-kind body draws live in ``_draw_mesh`` / ``_draw_sprite``,
the shared region box in ``_draw_region``, the driver shortcut in
``_draw_driver_shortcut``. Every subpanel carries a status badge + help
button via ``draw_header_preset``.
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core import validation  # type: ignore[import-not-found]
from . import _draw_driver_shortcut, _draw_mesh, _draw_region, _draw_sprite
from ._helpers import draw_subpanel_header


def _active_mesh_props(context: bpy.types.Context) -> bpy.types.AnyType | None:
    """Return the active MESH object's Proscenio props, or None."""
    obj = context.active_object
    if obj is None or obj.type != "MESH":
        return None
    return getattr(obj, "proscenio", None)


class PROSCENIO_PT_element(bpy.types.Panel):
    """Per-element settings - element-type selector; the body lives in subpanels."""

    bl_label = "Element"
    bl_idname = "PROSCENIO_PT_element"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 2
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "element", "active_element")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            layout.label(text="select a mesh or sprite element", icon="INFO")
            return
        props = getattr(obj, "proscenio", None)
        if props is None:
            layout.label(text="proscenio property group not registered", icon="ERROR")
            return
        if context.mode == "PAINT_WEIGHT":
            col = layout.column()
            col.enabled = False
            col.prop(props, "element_type")
            layout.label(text="element type is locked in Weight Paint mode", icon="INFO")
            return
        layout.prop(props, "element_type")
        for issue in validation.validate_active_element(obj):
            row = layout.row()
            icon = "ERROR" if issue.severity == "error" else "INFO"
            row.alert = issue.severity == "error"
            row.label(text=issue.message, icon=icon)


class PROSCENIO_PT_active_mesh(bpy.types.Panel):
    """Active Mesh body - the Polygon2D fields of the selected mesh element."""

    bl_label = "Active Mesh"
    bl_idname = "PROSCENIO_PT_active_mesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_element"
    bl_order = 0

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        props = _active_mesh_props(context)
        return props is not None and props.element_type == "mesh"

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "active_mesh", "active_mesh")

    def draw(self, context: bpy.types.Context) -> None:
        obj = context.active_object
        _draw_mesh.draw_body(self.layout, obj, obj.proscenio)


class PROSCENIO_PT_active_sprite(bpy.types.Panel):
    """Active Sprite body - the Sprite2D frame fields of the selected sprite element."""

    bl_label = "Active Sprite"
    bl_idname = "PROSCENIO_PT_active_sprite"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_element"
    bl_order = 0

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        props = _active_mesh_props(context)
        return props is not None and props.element_type == "sprite"

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "active_sprite", "active_sprite")

    def draw(self, context: bpy.types.Context) -> None:
        obj = context.active_object
        _draw_sprite.draw_body(self.layout, obj, obj.proscenio)


class PROSCENIO_PT_texture_region(bpy.types.Panel):
    """Texture Region subpanel - auto/manual region for the active element."""

    bl_label = "Texture Region"
    bl_idname = "PROSCENIO_PT_texture_region"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_element"
    bl_order = 1
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_mesh_props(context) is not None

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "texture_region", "texture_region")

    def draw(self, context: bpy.types.Context) -> None:
        props = context.active_object.proscenio
        _draw_region.draw_box(self.layout, props, element_type=props.element_type)


class PROSCENIO_PT_drive_from_bone(bpy.types.Panel):
    """Drive from Bone subpanel - bone-to-element driver shortcut."""

    bl_label = "Drive from Bone"
    bl_idname = "PROSCENIO_PT_drive_from_bone"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_element"
    bl_order = 2
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_mesh_props(context) is not None

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "drive_from_bone", "drive_from_bone")

    def draw(self, context: bpy.types.Context) -> None:
        _draw_driver_shortcut.draw_box(self.layout, context.active_object.proscenio)


_classes: tuple[type, ...] = (
    PROSCENIO_PT_element,
    PROSCENIO_PT_active_mesh,
    PROSCENIO_PT_active_sprite,
    PROSCENIO_PT_texture_region,
    PROSCENIO_PT_drive_from_bone,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
