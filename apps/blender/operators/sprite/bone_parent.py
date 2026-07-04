"""Sprite bone-parent operators: rigid attach the active sprite to a bone, and clear.

The non-slot way to pin a rigid Sprite2D to a single bone. Authors a real
``parent_type == "BONE"`` parent keep-transform (no jump to the bone tail) via
the shared bpy helper; the exporter reads it through ``resolve_sprite_bone``.
The bind picker is a prop_search bone dropdown in a props dialog, prefilled from
the active pose bone; execute parents from ``bone_name`` so headless tests pass
it directly.
"""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import StringProperty

from ...core._shared.props_access import element_type_of  # type: ignore[import-not-found]
from ...core._shared.report import report_info, report_warn  # type: ignore[import-not-found]
from ...core.bpy_helpers.i18n import iface
from ...core.bpy_helpers.sprite import (  # type: ignore[import-not-found]
    clear_bone_parent_keep_world,
    current_bone_parent,
    parent_to_bone_keep_world,
    resolve_sprite_armature,
)


def _is_sprite_element(obj: bpy.types.Object | None) -> bool:
    """True when ``obj`` is a MESH whose element_type is "sprite"."""
    return obj is not None and obj.type == "MESH" and element_type_of(obj) == "sprite"


class PROSCENIO_OT_parent_sprite_to_bone(bpy.types.Operator):
    """Rigid-attach the active sprite to a bone (keep-transform bone parent)."""

    bl_idname = "proscenio.parent_sprite_to_bone"
    bl_label = "Proscenio: Parent Sprite to Bone"
    bl_description = (
        "Make the active sprite follow a single bone as a rigid attachment: a "
        "bone parent authored keep-transform so the sprite stays put instead of "
        "jumping to the bone tail. Exports as a Sprite2D parented to that Bone2D. "
        "For a bone in the picture plane the sprite rotates with the bone rest - "
        "use a slot for a flat follow"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    bone_name: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        description="Bone the sprite rigidly follows",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if not _is_sprite_element(obj):
            return False
        if current_bone_parent(obj):
            return False
        return resolve_sprite_armature(context, obj) is not None

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        active_bone = getattr(context, "active_pose_bone", None)
        if active_bone is not None:
            self.bone_name = active_bone.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: bpy.types.Context) -> None:
        obj = context.active_object
        armature = resolve_sprite_armature(context, obj) if obj is not None else None
        if armature is None:
            self.layout.label(text=iface("no armature to parent to"), icon="ERROR")
            return
        self.layout.prop_search(self, "bone_name", armature.data, "bones", text="Bone")

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        if not _is_sprite_element(obj):
            report_warn(self, "active object is not a sprite element")
            return {"CANCELLED"}
        armature = resolve_sprite_armature(context, obj)
        if armature is None:
            report_warn(self, "no armature found for this sprite")
            return {"CANCELLED"}
        if not self.bone_name:
            report_warn(self, "pick a bone for the sprite to follow")
            return {"CANCELLED"}
        if self.bone_name not in armature.data.bones:
            report_warn(self, f"bone '{self.bone_name}' not in armature '{armature.name}'")
            return {"CANCELLED"}
        context.view_layer.update()
        parent_to_bone_keep_world(obj, armature, str(self.bone_name))
        report_info(self, f"sprite '{obj.name}' follows bone '{self.bone_name}'")
        return {"FINISHED"}


class PROSCENIO_OT_clear_sprite_bone_parent(bpy.types.Operator):
    """Remove the active sprite's bone parent, keeping its on-screen position."""

    bl_idname = "proscenio.clear_sprite_bone_parent"
    bl_label = "Proscenio: Clear Sprite Bone Parent"
    bl_description = (
        "Stop the active sprite following a bone: drops the bone parent and "
        "leaves the sprite unparented at the same position, ready to re-parent "
        "or attach to a slot"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return _is_sprite_element(obj) and bool(current_bone_parent(obj))

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        if not _is_sprite_element(obj) or not current_bone_parent(obj):
            return {"CANCELLED"}
        clear_bone_parent_keep_world(obj)
        report_info(self, f"sprite '{obj.name}' no longer follows a bone")
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_parent_sprite_to_bone,
    PROSCENIO_OT_clear_sprite_bone_parent,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
