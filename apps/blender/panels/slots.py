"""Slots panel - project slot list + Create Slot; Active Slot detail subpanel.

The parent lists every slot Empty in the scene (each row clickable to
select it) and hosts Create Slot, so the list never vanishes when the
active object is not a slot (the audit's disappearing-panel bug). The
Active Slot subpanel polls on the active object being a slot Empty and
carries the attachment detail + Add Selected Mesh. The subpanel's status
badge + help button land with the header-convention pass (a later phase);
the parent keeps the existing ``slot_system`` badge.
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core import validation  # type: ignore[import-not-found]
from ._helpers import draw_subpanel_header


def _is_slot(obj: bpy.types.Object) -> bool:
    """True when ``obj`` is an Empty flagged as a Proscenio slot."""
    if obj.type != "EMPTY":
        return False
    props = getattr(obj, "proscenio", None)
    return props is not None and bool(getattr(props, "is_slot", False))


def _attachment_kind_for(mesh_obj: bpy.types.Object) -> str:
    """Read the kind ("mesh" / "sprite") of a slot attachment mesh."""
    props = getattr(mesh_obj, "proscenio", None)
    if props is None:
        return "mesh"
    return str(getattr(props, "element_type", "mesh"))


def _attachment_icon_for(kind: str) -> str:
    return "MESH_DATA" if kind == "mesh" else "IMAGE_DATA"


class PROSCENIO_PT_slots(bpy.types.Panel):
    """Slots - the project slot list + Create Slot."""

    bl_label = "Slots"
    bl_idname = "PROSCENIO_PT_slots"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 3
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "slot_system", "slot_system")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        active = context.active_object
        slots = sorted((o for o in context.scene.objects if _is_slot(o)), key=lambda o: o.name)
        if not slots:
            layout.label(text="no slots yet - select meshes and Create Slot", icon="INFO")
        else:
            col = layout.column(align=True)
            for slot in slots:
                row = col.row(align=True)
                op = row.operator(
                    "proscenio.select_slot",
                    text=slot.name,
                    icon="LINK_BLEND",
                    depress=slot is active,
                )
                op.slot_name = slot.name
                n_children = sum(1 for c in slot.children if c.type == "MESH")
                row.label(text=str(n_children), icon="OUTLINER_OB_MESH")
        layout.separator()
        layout.operator("proscenio.create_slot", text="Create Slot", icon="ADD")


class PROSCENIO_PT_active_slot(bpy.types.Panel):
    """Active Slot subpanel - attachment detail + Add Selected Mesh.

    Polls on the active object being a slot Empty; the parent Slots panel
    stays visible regardless so the list + Create Slot never vanish.
    """

    bl_label = "Active Slot"
    bl_idname = "PROSCENIO_PT_active_slot"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_slots"
    bl_order = 0

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return obj is not None and _is_slot(obj)

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "active_slot", "active_slot")

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


_classes: tuple[type, ...] = (
    PROSCENIO_PT_slots,
    PROSCENIO_PT_active_slot,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
