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

from ..addon_prefs import y_location_spacing  # type: ignore[import-not-found]
from ..core import validation  # type: ignore[import-not-found]
from ..core.bpy_helpers.i18n import iface
from . import (
    _draw_bone_attach,
    _draw_driver_shortcut,
    _draw_mesh,
    _draw_region,
    _draw_sprite,
)
from ._helpers import (
    _active_mesh_props,
    _is_mesh_element,
    draw_issue_row,
    draw_subpanel_header,
)

# Below this N-panel width the Element header drops the active-object name and
# keeps just "Element" (a custom draw_header label cannot truncate, so the name
# is dropped wholesale rather than left to vanish mid-word). Mirrors the
# Skeleton header. GUI-tunable.
_ELEMENT_HEADER_NAME_MIN_WIDTH = 220


class PROSCENIO_PT_element(bpy.types.Panel):
    """Per-element settings - element-type selector; the body lives in subpanels."""

    # bl_label blank: the full "Element: <name>" title is drawn in draw_header
    # (Blender renders draw_header LEFT of bl_label), matching the Skeleton
    # header so the active element name reads in the header, not a body row.
    bl_label = ""
    bl_idname = "PROSCENIO_PT_element"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 2
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header(self, context: bpy.types.Context) -> None:
        obj = context.active_object
        name = obj.name if (obj is not None and obj.type == "MESH") else None
        region = getattr(context, "region", None)
        width = getattr(region, "width", 9999)
        if name and width >= _ELEMENT_HEADER_NAME_MIN_WIDTH:
            self.layout.label(text=f"Element: {name}")
        else:
            self.layout.label(text=iface("Element"))

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "element", "active_element")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            layout.label(text=iface("select a mesh or sprite element"), icon="INFO")
            return
        props = getattr(obj, "proscenio", None)
        if props is None:
            layout.label(text=iface("proscenio property group not registered"), icon="ERROR")
            return
        if context.mode == "PAINT_WEIGHT":
            col = layout.column()
            col.enabled = False
            col.prop(props, "element_type")
            layout.label(text=iface("element type is locked in Weight Paint mode"), icon="INFO")
            return
        if obj.get("proscenio_type") is None:
            # Hand-authored mesh with no element data yet: offer one-click adopt
            # with a smart Mesh/Sprite default before showing the element fields.
            box = layout.box()
            box.label(text=iface("hand-authored mesh - not a Proscenio element yet"), icon="INFO")
            box.operator(
                "proscenio.incorporate_element", text="Incorporate as Element", icon="IMPORT"
            )
        layout.prop(props, "element_type")
        layout.prop(props, "y_draw_order")
        if obj.get("proscenio_import_origin") is not None:
            # Imported from a PSD manifest: offer a one-click re-import of just
            # this Element from its source entry (siblings untouched).
            layout.operator(
                "proscenio.reimport_element", text="Re-import from PSD", icon="FILE_REFRESH"
            )
        if props.element_type == "mesh" and obj.get("proscenio_import_placement") is not None:
            # Spec 071: revert a generated mesh back to its original imported plane.
            # PSD-imported mesh elements only (the placement tag is the rebuild
            # source); the operator raises a destructive-action confirm.
            layout.operator("proscenio.revert_to_plane", text="Revert to Plane", icon="LOOP_BACK")
        for issue in validation.validate_active_element(
            obj, layer_spacing=y_location_spacing(context)
        ):
            draw_issue_row(layout, issue)


class PROSCENIO_PT_active_mesh(bpy.types.Panel):
    """Active Mesh body - the Polygon2D fields of the selected mesh element."""

    bl_label = "Active Mesh"
    bl_idname = "PROSCENIO_PT_active_mesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_element"
    bl_order = 0
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _is_mesh_element(context)

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "active_mesh", "active_mesh")

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
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        props = _active_mesh_props(context)
        return props is not None and props.element_type == "sprite"

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "active_sprite", "active_sprite")

    def draw(self, context: bpy.types.Context) -> None:
        obj = context.active_object
        _draw_sprite.draw_body(self.layout, obj, obj.proscenio)


class PROSCENIO_PT_attach_to_bone(bpy.types.Panel):
    """Attach to Bone subpanel - rigid bone parent for a sprite (the non-slot path)."""

    bl_label = "Attach to Bone"
    bl_idname = "PROSCENIO_PT_attach_to_bone"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_element"
    bl_order = 1
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        props = _active_mesh_props(context)
        return props is not None and props.element_type == "sprite"

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "sprite_bone_parent", "sprite_bone_parent")

    def draw(self, context: bpy.types.Context) -> None:
        _draw_bone_attach.draw_body(self.layout, context, context.active_object)


class PROSCENIO_PT_texture_region(bpy.types.Panel):
    """Texture Region subpanel - auto/manual region for the active element."""

    bl_label = "Texture Region"
    bl_idname = "PROSCENIO_PT_texture_region"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_element"
    bl_order = 2
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_mesh_props(context) is not None

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "texture_region", "texture_region")

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
    bl_order = 3
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_mesh_props(context) is not None

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "drive_from_bone", "drive_from_bone")

    def draw(self, context: bpy.types.Context) -> None:
        _draw_driver_shortcut.draw_box(self.layout, context.active_object)


_classes: tuple[type, ...] = (
    PROSCENIO_PT_element,
    PROSCENIO_PT_active_mesh,
    PROSCENIO_PT_active_sprite,
    PROSCENIO_PT_attach_to_bone,
    PROSCENIO_PT_texture_region,
    PROSCENIO_PT_drive_from_bone,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
