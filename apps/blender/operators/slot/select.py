"""Slot selection operator - click a row in the Slots list to select it."""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import StringProperty

from ...core._shared.report import report_warn  # type: ignore[import-not-found]
from ...core.bpy_helpers._shared.select import select_only  # type: ignore[import-not-found]


class PROSCENIO_OT_select_slot(bpy.types.Operator):
    """Select + activate a slot Empty from the Slots panel list.

    Clicking a slot row should make it the active object so the Active
    Slot subpanel surfaces its attachments. Without this operator the row
    would only be a label.
    """

    bl_idname = "proscenio.select_slot"
    bl_label = "Proscenio: Select Slot"
    bl_description = (
        "Select and activate this slot so its attachments show in the Active Slot subpanel"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER"}

    slot_name: StringProperty(  # type: ignore[valid-type]
        name="Slot name",
        default="",
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = bpy.data.objects.get(self.slot_name)
        props = getattr(obj, "proscenio", None) if obj is not None else None
        if obj is None or obj.type != "EMPTY" or not getattr(props, "is_slot", False):
            report_warn(self, f"slot '{self.slot_name}' not found")
            return {"CANCELLED"}
        select_only(context, obj)
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_select_slot,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
