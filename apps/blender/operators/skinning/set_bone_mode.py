"""Operator to flip per-bone SOFT/HARD mode from the panel UI (O1).

Writes into ``obj['proscenio_bone_modes']`` JSON Custom Property via
``bone_modes.write_bone_modes``. Missing entry = bind operator default.
Registered as ``proscenio.set_bone_mode``; used by the bind sub-box
per-bone toggle rows in the Skinning panel.
"""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import EnumProperty, StringProperty

from ...core.skinning.bone_modes import (  # type: ignore[import-not-found]
    read_bone_modes,
    write_bone_modes,
)


class PROSCENIO_OT_set_bone_mode(bpy.types.Operator):
    """Override the bind mode for a single bone."""

    bl_idname = "proscenio.set_bone_mode"
    bl_label = "Set Bone Mode"
    bl_description = (
        "Override the bind mode for a single bone (SOFT=proximity falloff, HARD=single-nearest)"
    )
    bl_options: ClassVar[set[str]] = {"INTERNAL", "REGISTER", "UNDO"}

    bone_name: StringProperty(  # type: ignore[valid-type]
        name="Bone Name",
        default="",
    )
    mode: EnumProperty(  # type: ignore[valid-type]
        name="Mode",
        items=[
            ("SOFT", "Soft", "Proximity falloff"),
            ("HARD", "Hard", "Single-nearest"),
        ],
        default="SOFT",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return obj is not None and obj.type == "MESH"

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return {"CANCELLED"}
        modes = dict(read_bone_modes(obj))
        modes[self.bone_name] = self.mode
        write_bone_modes(obj, modes)
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_set_bone_mode,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
