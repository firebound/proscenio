"""Active Slot subpanel + helpers (SPEC 004)."""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core import validation  # type: ignore[import-not-found]
from ._helpers import draw_subpanel_header


def _attachment_kind_for(mesh_obj: bpy.types.Object) -> str:
    """Read the kind ("polygon" / "sprite_frame") of a slot attachment mesh."""
    props = getattr(mesh_obj, "proscenio", None)
    if props is None:
        return "polygon"
    return str(getattr(props, "sprite_type", "polygon"))


def _attachment_icon_for(kind: str) -> str:
    return "MESH_DATA" if kind == "polygon" else "IMAGE_DATA"


class PROSCENIO_PT_active_slot(bpy.types.Panel):
    """Slot authoring - visible when the active Empty is flagged as a slot (SPEC 004)."""

    bl_label = "Active Slot"
    bl_idname = "PROSCENIO_PT_active_slot"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None or obj.type != "EMPTY":
            return False
        props = getattr(obj, "proscenio", None)
        if props is None:
            return False
        return bool(getattr(props, "is_slot", False))

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "slot_system", "slot_system")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        empty = context.active_object
        if empty is None:
            return
        props = empty.proscenio
        children = sorted(
            (c for c in empty.children if c.type == "MESH"),
            key=lambda c: c.name,
        )

        col = layout.column()
        col.label(text=f"Slot '{empty.name}'", icon="LINK_BLEND")
        col.label(
            text=f"bone: {empty.parent_bone or '(unparented)'}",
            icon="BONE_DATA",
        )

        layout.separator()
        layout.label(text=f"Attachments ({len(children)}):", icon="OUTLINER_OB_MESH")
        if not children:
            row = layout.row()
            row.alert = True
            row.label(text="empty slot - add child meshes", icon="INFO")

        current_default = props.slot_default or (children[0].name if children else "")
        for child in children:
            row = layout.row(align=True)
            is_default = child.name == current_default
            icon = "SOLO_ON" if is_default else "SOLO_OFF"
            op = row.operator(
                "proscenio.set_slot_default",
                text="",
                icon=icon,
                emboss=is_default,
            )
            op.attachment_name = child.name
            row.label(text=child.name)
            kind = _attachment_kind_for(child)
            row.label(text=kind, icon=_attachment_icon_for(kind))

        layout.separator()
        row = layout.row()
        row.operator(
            "proscenio.add_slot_attachment",
            text="Add Selected Mesh",
            icon="ADD",
        )

        for issue in validation.validate_active_slot(empty):
            row = layout.row()
            icon = "ERROR" if issue.severity == "error" else "INFO"
            row.alert = issue.severity == "error"
            row.label(text=issue.message, icon=icon)


_classes: tuple[type, ...] = (PROSCENIO_PT_active_slot,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
