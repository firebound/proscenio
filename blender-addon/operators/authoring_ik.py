"""IK chain toggle authoring shortcut (SPEC 005.1.b)."""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import IntProperty

from ..core.report import report_info  # type: ignore[import-not-found]

_IK_CONSTRAINT_NAME = "Proscenio IK"


class PROSCENIO_OT_toggle_ik_chain(bpy.types.Operator):
    """Toggle a Proscenio-owned IK constraint on the active pose bone."""

    bl_idname = "proscenio.toggle_ik_chain"
    bl_label = "Proscenio: Toggle IK"
    bl_description = (
        "Adds an IK constraint named 'Proscenio IK' to the active pose bone "
        "(chain length 2). Click again to remove it. Hand-added constraints "
        "are left untouched."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    chain_length: IntProperty(  # type: ignore[valid-type]
        name="Chain length",
        default=2,
        min=0,
        soft_max=8,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context.mode != "POSE":
            return False
        bone = getattr(context, "active_pose_bone", None)
        return bone is not None

    def execute(self, context: bpy.types.Context) -> set[str]:
        bone = context.active_pose_bone
        existing = bone.constraints.get(_IK_CONSTRAINT_NAME)
        if existing is not None:
            bone.constraints.remove(existing)
            report_info(self, f"removed IK from '{bone.name}'")
            return {"FINISHED"}

        ik = bone.constraints.new(type="IK")
        ik.name = _IK_CONSTRAINT_NAME
        ik.chain_count = self.chain_length
        report_info(
            self,
            f"added IK to '{bone.name}' (chain={self.chain_length}); set the target manually.",
        )
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_toggle_ik_chain,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
