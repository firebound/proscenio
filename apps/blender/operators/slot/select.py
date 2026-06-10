"""Slot selection operator - click a row in the Slots list to select it."""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import StringProperty

from ...core.bpy_helpers._shared.select import (  # type: ignore[import-not-found]
    select_named_or_warn,
)
from ...core.slot.slot_emit import is_slot_empty  # type: ignore[import-not-found]


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
        obj = select_named_or_warn(
            self,
            context,
            self.slot_name,
            not_found_message=f"slot '{self.slot_name}' not found",
            predicate=is_slot_empty,
        )
        return {"CANCELLED"} if obj is None else {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_select_slot,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
