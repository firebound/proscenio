"""Slot bone-follow operators: bind the active slot to a bone, and unbind.

Authors the object-parent + Child Of follow via the shared bpy helper so the
Blender view matches the Godot runtime. The bind picker is a prop_search bone
dropdown in a props dialog; execute binds from ``bone_name`` so headless tests
pass it directly.
"""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import StringProperty

from ...core._shared.report import report_info, report_warn  # type: ignore[import-not-found]
from ...core.bpy_helpers.slot import (  # type: ignore[import-not-found]
    bind_slot_to_bone,
    resolve_slot_armature,
    slot_follow_shape,
    unbind_slot_from_bone,
)
from ...core.slot.slot_emit import is_slot_empty  # type: ignore[import-not-found]
from ...core.validation import slot_parent_bone  # type: ignore[import-not-found]

_FOLLOW_VIA = {"constraint": "the Proscenio constraint", "bone_parent": "a bone parent"}


def _already_following(empty: bpy.types.Object) -> str:
    """The user-facing 'via X' phrase when the slot already follows, else ""."""
    return _FOLLOW_VIA.get(slot_follow_shape(empty), "")


class PROSCENIO_OT_bind_slot_to_bone(bpy.types.Operator):
    """Make the active slot follow a bone (object-parent + Child Of)."""

    bl_idname = "proscenio.bind_slot_to_bone"
    bl_label = "Proscenio: Bind Slot to Bone"
    bl_description = (
        "Make the active slot follow a bone in Blender the way it already does "
        "in Godot: keeps the Empty object-parented and adds a Child Of "
        "constraint whose inverse cancels the bone rest, staying flat for any "
        "bone orientation. Hand bone-parenting the Empty (Ctrl+P > Bone) also "
        "exports, but only for bones pointing into the screen. If the slot "
        "already follows, Unbind first (moving a bound slot needs a rebind)"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    bone_name: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        description="Bone the slot follows",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        empty = context.active_object
        if not is_slot_empty(empty):
            return False
        return resolve_slot_armature(context, empty) is not None

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        empty = context.active_object
        via = _already_following(empty)
        if via:
            report_warn(self, f"slot already follows via {via} - Unbind first, then Bind")
            return {"CANCELLED"}
        active_bone = getattr(context, "active_pose_bone", None)
        if active_bone is not None:
            self.bone_name = active_bone.name
        elif not self.bone_name:
            self.bone_name = slot_parent_bone(empty)
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: bpy.types.Context) -> None:
        empty = context.active_object
        armature = resolve_slot_armature(context, empty)
        if armature is None:
            self.layout.label(text="no armature to follow", icon="ERROR")
            return
        self.layout.prop_search(self, "bone_name", armature.data, "bones", text="Bone")

    def execute(self, context: bpy.types.Context) -> set[str]:
        empty = context.active_object
        via = _already_following(empty)
        if via:
            report_warn(self, f"slot already follows via {via} - Unbind first, then Bind")
            return {"CANCELLED"}
        armature = resolve_slot_armature(context, empty)
        if armature is None:
            report_warn(self, "no armature found for this slot")
            return {"CANCELLED"}
        if not self.bone_name:
            report_warn(self, "pick a bone for the slot to follow")
            return {"CANCELLED"}
        if self.bone_name not in armature.data.bones:
            report_warn(self, f"bone '{self.bone_name}' not in armature '{armature.name}'")
            return {"CANCELLED"}
        context.view_layer.update()
        bind_slot_to_bone(empty, armature, str(self.bone_name))
        report_info(self, f"slot '{empty.name}' follows bone '{self.bone_name}'")
        return {"FINISHED"}


class PROSCENIO_OT_unbind_slot_from_bone(bpy.types.Operator):
    """Remove the active slot's bone-follow and clear slot_bone."""

    bl_idname = "proscenio.unbind_slot_from_bone"
    bl_label = "Proscenio: Unbind Slot from Bone"
    bl_description = (
        "Stop the active slot following a bone: removes the Proscenio Child Of "
        "constraint or a hand-authored bone parent (whichever it uses) and "
        "clears slot_bone, leaving the Empty object-parented and inert"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        empty = context.active_object
        return is_slot_empty(empty) and slot_parent_bone(empty) != ""

    def execute(self, context: bpy.types.Context) -> set[str]:
        empty = context.active_object
        unbind_slot_from_bone(empty)
        report_info(self, f"slot '{empty.name}' no longer follows a bone")
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_bind_slot_to_bone,
    PROSCENIO_OT_unbind_slot_from_bone,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
