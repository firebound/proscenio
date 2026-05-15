"""Operator that fills ``scene.proscenio.active_armature`` from the panel.

The Skeleton subpanel renders this as a one-click button next to the
picker when the picker is empty but armatures exist in the scene.
Writing the PointerProperty from a panel button is safe (operator
context, not panel ``draw``) where a draw-time write would raise
``AttributeError: Writing to ID classes in this context is not
allowed``.
"""

from typing import ClassVar

import bpy
from bpy.props import StringProperty

from ..core.report import report_warn  # type: ignore[import-not-found]


class PROSCENIO_OT_set_active_armature(bpy.types.Operator):
    """Set the Proscenio active armature pointer to a named scene object."""

    bl_idname = "proscenio.set_active_armature"
    bl_label = "Proscenio: Use Armature"
    bl_description = (
        "Pick this armature as the explicit Proscenio target so every "
        "skeleton operation (Quick Armature, IK toggle, pose helpers) "
        "writes into it"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        name="Armature name",
        default="",
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not self.armature_name:
            report_warn(self, "no armature name supplied")
            return {"CANCELLED"}
        obj = bpy.data.objects.get(self.armature_name)
        if obj is None:
            report_warn(self, f"object '{self.armature_name}' not found")
            return {"CANCELLED"}
        if obj.type != "ARMATURE":
            report_warn(self, f"'{self.armature_name}' is not an armature")
            return {"CANCELLED"}
        scene_props = getattr(context.scene, "proscenio", None)
        if scene_props is None:
            report_warn(self, "Proscenio scene properties not available")
            return {"CANCELLED"}
        scene_props.active_armature = obj
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_set_active_armature,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
