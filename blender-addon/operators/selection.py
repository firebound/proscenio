"""Selection operators: validation issue, outliner row, outliner favorite toggle."""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import StringProperty

from ..core.props_access import object_props  # type: ignore[import-not-found]
from ..core.report import report_warn  # type: ignore[import-not-found]
from ..core.select import select_only  # type: ignore[import-not-found]


class PROSCENIO_OT_select_issue_object(bpy.types.Operator):
    """Select the object referenced by a validation issue and make it active."""

    bl_idname = "proscenio.select_issue_object"
    bl_label = "Proscenio: Select Issue Object"
    bl_description = "Selects and activates the object that the issue refers to"
    bl_options: ClassVar[set[str]] = {"REGISTER"}

    obj_name: StringProperty(  # type: ignore[valid-type]
        name="Object name",
        default="",
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not self.obj_name:
            report_warn(self, "issue has no object name")
            return {"CANCELLED"}
        obj = bpy.data.objects.get(self.obj_name)
        if obj is None:
            report_warn(self, f"object '{self.obj_name}' not found")
            return {"CANCELLED"}
        select_only(context, obj)
        return {"FINISHED"}


class PROSCENIO_OT_select_outliner_object(bpy.types.Operator):
    """Select + activate the object clicked in the Proscenio outliner (5.1.d.4)."""

    bl_idname = "proscenio.select_outliner_object"
    bl_label = "Proscenio: Select Outliner Object"
    bl_description = "Selects and activates the object represented by this outliner row"
    bl_options: ClassVar[set[str]] = {"REGISTER"}

    obj_name: StringProperty(  # type: ignore[valid-type]
        name="Object name",
        default="",
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not self.obj_name:
            return {"CANCELLED"}
        obj = bpy.data.objects.get(self.obj_name)
        if obj is None:
            report_warn(self, f"object '{self.obj_name}' not found")
            return {"CANCELLED"}
        select_only(context, obj)
        return {"FINISHED"}


class PROSCENIO_OT_toggle_outliner_favorite(bpy.types.Operator):
    """Flip the outliner favorite flag on a target object (5.1.d.4)."""

    bl_idname = "proscenio.toggle_outliner_favorite"
    bl_label = "Proscenio: Toggle Outliner Favorite"
    bl_description = (
        "Pin / unpin this object in the Proscenio outliner. "
        "Pinned objects survive the 'Favorites only' filter."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    obj_name: StringProperty(  # type: ignore[valid-type]
        name="Object name",
        default="",
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        if not self.obj_name:
            return {"CANCELLED"}
        obj = bpy.data.objects.get(self.obj_name)
        if obj is None:
            return {"CANCELLED"}
        props = object_props(obj)
        if props is None:
            report_warn(self, "PropertyGroup not registered on this object")
            return {"CANCELLED"}
        props.is_outliner_favorite = not bool(props.is_outliner_favorite)
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_select_issue_object,
    PROSCENIO_OT_select_outliner_object,
    PROSCENIO_OT_toggle_outliner_favorite,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
