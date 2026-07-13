"""Element bone-follow operators: bind the active rigid element to a bone.

The non-slot way to pin a rigid element (a Sprite2D sprite, or an unskinned
mesh) to a single bone. Constraint-first (spec 080 D4): Bind authors
object-parent + a ``Child Of`` whose inverse cancels the bone REST via the
shared bone-follow core - the same one-click, non-destructive flow as Bind
Slot to Bone, and one mental model across elements and slots. A raw
``parent_type == "BONE"`` parent (Ctrl+P > Bone, keep-transform) remains a
supported power-user fallback the exporter reads; Convert upgrades it to the
constraint in place. The exporter resolves the followed bone through
``resolve_sprite_bone`` (constraint first, then the raw parent, then the
first vertex group).
"""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import StringProperty

from ...core._shared.bone_follow_resolve import (  # type: ignore[import-not-found]
    ELEMENT_FOLLOW_CONSTRAINT,
)
from ...core._shared.props_access import element_type_of  # type: ignore[import-not-found]
from ...core._shared.report import report_info, report_warn  # type: ignore[import-not-found]
from ...core.bpy_helpers._shared.bone_follow import (  # type: ignore[import-not-found]
    bind_to_bone_rest,
    follow_shape,
    unbind_keep_world,
)
from ...core.bpy_helpers.i18n import iface
from ...core.bpy_helpers.sprite import (  # type: ignore[import-not-found]
    resolve_sprite_armature,
)

_POSED_BIND_WARNING = (
    "bone '{bone}' is posed - the follow cancels the REST (what Godot "
    "reproduces), so the element snapped to its rest-relative spot"
)


def _is_rigid_element(obj: bpy.types.Object | None) -> bool:
    """True for a MESH element that binds as a rigid whole: a sprite, or a
    mesh with no vertex groups (a skinned mesh binds via weights instead)."""
    if obj is None or obj.type != "MESH":
        return False
    element_type = element_type_of(obj)
    if element_type == "sprite":
        return True
    return element_type == "mesh" and not obj.vertex_groups


def _element_shape(obj: bpy.types.Object) -> str:
    return follow_shape(obj, ELEMENT_FOLLOW_CONSTRAINT)


class PROSCENIO_OT_parent_sprite_to_bone(bpy.types.Operator):
    """Bind the active rigid element to a bone (object-parent + Child Of)."""

    bl_idname = "proscenio.parent_sprite_to_bone"
    bl_label = "Proscenio: Bind Element to Bone"
    bl_description = (
        "Make the active element follow a single bone the way a slot does: "
        "keeps the object-parent and adds a Child Of constraint whose inverse "
        "cancels the bone rest, so the element stays where it was authored "
        "and only the bone's pose moves it - for any bone orientation. "
        "Hand bone-parenting (Ctrl+P > Bone, keep-transform) also exports, "
        "as a power-user fallback"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    bone_name: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        description="Bone the element rigidly follows",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if not _is_rigid_element(obj):
            return False
        if _element_shape(obj) != "none":
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
            self.layout.label(text=iface("no armature to bind to"), icon="ERROR")
            return
        self.layout.prop_search(self, "bone_name", armature.data, "bones", text="Bone")

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        if not _is_rigid_element(obj):
            report_warn(self, "active object is not a rigid element (sprite or unskinned mesh)")
            return {"CANCELLED"}
        if _element_shape(obj) != "none":
            report_warn(self, "element already follows a bone - Clear first, then Bind")
            return {"CANCELLED"}
        armature = resolve_sprite_armature(context, obj)
        if armature is None:
            report_warn(self, "no armature found for this element")
            return {"CANCELLED"}
        if not self.bone_name:
            report_warn(self, "pick a bone for the element to follow")
            return {"CANCELLED"}
        if self.bone_name not in armature.data.bones:
            report_warn(self, f"bone '{self.bone_name}' not in armature '{armature.name}'")
            return {"CANCELLED"}
        context.view_layer.update()
        posed = bind_to_bone_rest(obj, armature, str(self.bone_name), ELEMENT_FOLLOW_CONSTRAINT)
        if posed:
            report_warn(self, _POSED_BIND_WARNING.format(bone=self.bone_name))
        report_info(self, f"element '{obj.name}' follows bone '{self.bone_name}'")
        return {"FINISHED"}


class PROSCENIO_OT_convert_element_follow(bpy.types.Operator):
    """Upgrade a raw bone parent to the Proscenio constraint follow in place."""

    bl_idname = "proscenio.convert_element_follow"
    bl_label = "Proscenio: Convert to Constraint Follow"
    bl_description = (
        "Replace this element's raw bone parent with the Proscenio Child Of "
        "follow, keeping the same bone and the on-screen position - the "
        "one-click migration to the constraint-first binding model"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return _is_rigid_element(obj) and _element_shape(obj) == "bone_parent"

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        if not _is_rigid_element(obj) or _element_shape(obj) != "bone_parent":
            return {"CANCELLED"}
        armature = obj.parent
        bone_name = str(obj.parent_bone)
        if armature is None or getattr(armature, "type", None) != "ARMATURE":
            report_warn(self, "bone parent has no armature parent to bind against")
            return {"CANCELLED"}
        if bone_name not in armature.data.bones:
            report_warn(self, f"bone '{bone_name}' not in armature '{armature.name}'")
            return {"CANCELLED"}
        context.view_layer.update()
        # bind drops the raw parent keep-world before wiring the constraint,
        # so the element never double-drives and never moves on screen.
        posed = bind_to_bone_rest(obj, armature, bone_name, ELEMENT_FOLLOW_CONSTRAINT)
        if posed:
            report_warn(self, _POSED_BIND_WARNING.format(bone=bone_name))
        report_info(self, f"element '{obj.name}' now follows '{bone_name}' via the constraint")
        return {"FINISHED"}


class PROSCENIO_OT_clear_sprite_bone_parent(bpy.types.Operator):
    """Remove the active element's bone follow, keeping its on-screen position."""

    bl_idname = "proscenio.clear_sprite_bone_parent"
    bl_label = "Proscenio: Clear Bone Follow"
    bl_description = (
        "Stop the active element following a bone: removes the Proscenio "
        "Child Of constraint or a raw bone parent (whichever it uses) and "
        "leaves the element at the same position, ready to re-bind or attach "
        "to a slot"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return _is_rigid_element(obj) and _element_shape(obj) != "none"

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        if not _is_rigid_element(obj) or _element_shape(obj) == "none":
            return {"CANCELLED"}
        unbind_keep_world(obj, ELEMENT_FOLLOW_CONSTRAINT)
        report_info(self, f"element '{obj.name}' no longer follows a bone")
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_parent_sprite_to_bone,
    PROSCENIO_OT_convert_element_follow,
    PROSCENIO_OT_clear_sprite_bone_parent,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
