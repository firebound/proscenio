"""Slot attachment operators (SPEC 004): add attachment, set default."""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import StringProperty

from ...core.report import report_info, report_warn  # type: ignore[import-not-found]


class PROSCENIO_OT_add_slot_attachment(bpy.types.Operator):
    """Re-parent the active mesh into the active slot Empty (SPEC 004)."""

    bl_idname = "proscenio.add_slot_attachment"
    bl_label = "Proscenio: Add Slot Attachment"
    bl_description = "Re-parent the selected mesh as a child of the active slot Empty"
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        empty = context.active_object
        if empty is None or empty.type != "EMPTY":
            return False
        props = getattr(empty, "proscenio", None)
        if props is None or not bool(getattr(props, "is_slot", False)):
            return False
        return any(obj.type == "MESH" and obj is not empty for obj in context.selected_objects)

    def execute(self, context: bpy.types.Context) -> set[str]:
        empty = context.active_object
        meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if not meshes:
            report_warn(self, "no MESH objects selected")
            return {"CANCELLED"}
        for mesh in meshes:
            world = mesh.matrix_world.copy()
            mesh.parent = empty
            mesh.parent_type = "OBJECT"
            mesh.matrix_parent_inverse = empty.matrix_world.inverted()
            mesh.matrix_world = world
        report_info(self, f"added {len(meshes)} attachment(s) to slot '{empty.name}'")
        return {"FINISHED"}


class PROSCENIO_OT_set_slot_default(bpy.types.Operator):
    """Mark the named attachment as the slot's default (SPEC 004 D2)."""

    bl_idname = "proscenio.set_slot_default"
    bl_label = "Proscenio: Set Slot Default"
    bl_description = "Make this attachment the slot's default visible child at scene load"
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    attachment_name: StringProperty(  # type: ignore[valid-type]
        name="Attachment name",
        description="Name of the mesh child to flag as default",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        empty = context.active_object
        if empty is None or empty.type != "EMPTY":
            return False
        props = getattr(empty, "proscenio", None)
        return props is not None and bool(getattr(props, "is_slot", False))

    def execute(self, context: bpy.types.Context) -> set[str]:
        empty = context.active_object
        props = empty.proscenio
        children_names = {child.name for child in empty.children if child.type == "MESH"}
        if self.attachment_name not in children_names:
            report_warn(
                self,
                f"'{self.attachment_name}' is not a child of slot '{empty.name}'",
            )
            return {"CANCELLED"}
        props.slot_default = self.attachment_name
        report_info(self, f"slot '{empty.name}' default = '{self.attachment_name}'")
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_add_slot_attachment,
    PROSCENIO_OT_set_slot_default,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
