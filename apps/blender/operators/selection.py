"""Selection operators: validation issue, outliner row, outliner favorite toggle."""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import StringProperty

from ..core._shared.props_access import object_props  # type: ignore[import-not-found]
from ..core._shared.report import report_warn  # type: ignore[import-not-found]
from ..core.bpy_helpers._shared.select import (  # type: ignore[import-not-found]
    select_named_or_warn,
    select_only,
)


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
        if select_named_or_warn(self, context, self.obj_name) is None:
            return {"CANCELLED"}
        return {"FINISHED"}


class PROSCENIO_OT_select_outliner_object(bpy.types.Operator):
    """Select + activate the object clicked in the Proscenio outliner."""

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
        if select_named_or_warn(self, context, self.obj_name) is None:
            return {"CANCELLED"}
        _sync_active_index(context, "active_outliner_index", bpy.data.objects, self.obj_name)
        return {"FINISHED"}


class PROSCENIO_OT_select_bone_by_name(bpy.types.Operator):
    """Select + activate a pose bone from the Skeleton panel UIList."""

    bl_idname = "proscenio.select_bone_by_name"
    bl_label = "Proscenio: Select Bone"
    bl_description = "Selects the bone for this Skeleton-panel row in the viewport"
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        name="Armature",
        default="",
    )
    bone_name: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        default="",
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            report_warn(self, f"armature '{self.armature_name}' not found")
            return {"CANCELLED"}
        bones = getattr(armature.data, "bones", None)
        if bones is None or self.bone_name not in bones:
            report_warn(self, f"bone '{self.bone_name}' not in '{armature.name}'")
            return {"CANCELLED"}
        select_only(context, armature)
        armature.data.bones.active = bones[self.bone_name]
        if context.mode == "POSE":
            _sync_pose_bone_selection(armature, self.bone_name)
        _sync_active_index(context, "active_bone_index", bones, self.bone_name)
        return {"FINISHED"}


class PROSCENIO_OT_set_active_action(bpy.types.Operator):
    """Assign an action to the scene's primary armature from the Animation panel."""

    bl_idname = "proscenio.set_active_action"
    bl_label = "Proscenio: Set Active Action"
    bl_description = (
        "Assigns this Animation-panel row's action to the first armature "
        "in the scene so the timeline plays it"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    action_name: StringProperty(  # type: ignore[valid-type]
        name="Action",
        default="",
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        action = bpy.data.actions.get(self.action_name)
        if action is None:
            report_warn(self, f"action '{self.action_name}' not found")
            return {"CANCELLED"}
        armatures = [o for o in context.scene.objects if o.type == "ARMATURE"]
        if not armatures:
            report_warn(self, "no armature in scene to receive the action")
            return {"CANCELLED"}
        if len(armatures) > 1:
            # Mirror the writer's heuristic: warn + use the first armature only.
            report_warn(
                self,
                f"{len(armatures)} armatures in scene - assigning to '{armatures[0].name}'",
            )
        armature = armatures[0]
        if armature.animation_data is None:
            armature.animation_data_create()
        armature.animation_data.action = action
        _sync_active_index(context, "active_action_index", bpy.data.actions, self.action_name)
        return {"FINISHED"}


def _sync_pose_bone_selection(armature: bpy.types.Object, bone_name: str) -> None:
    """Set viewport selection so only ``bone_name`` is selected.

    `bones.active` drives the Properties-editor highlight; PoseBone.select
    drives the viewport bone-shape selection. Blender 4.x exposed the
    select flag on Bone too, but 5.1 moved it to PoseBone exclusively, so
    the hasattr guard stays tolerant of either layout.
    """
    if armature.pose is None:
        return
    for pose_bone in armature.pose.bones:
        wanted = pose_bone.name == bone_name
        if hasattr(pose_bone, "select"):
            pose_bone.select = wanted
        elif hasattr(pose_bone.bone, "select"):
            pose_bone.bone.select = wanted


def _sync_active_index(
    context: bpy.types.Context,
    prop_name: str,
    items: bpy.types.AnyType,
    target_name: str,
) -> None:
    """Update ``scene.proscenio.<prop_name>`` so the panel UIList highlight
    follows the row whose underlying datablock matches ``target_name``."""
    scene_props = getattr(context.scene, "proscenio", None)
    if scene_props is None or not hasattr(scene_props, prop_name):
        return
    for idx, candidate in enumerate(items):
        if candidate.name == target_name:
            setattr(scene_props, prop_name, idx)
            return


class PROSCENIO_OT_toggle_outliner_favorite(bpy.types.Operator):
    """Flip the outliner favorite flag on a target object."""

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
    PROSCENIO_OT_select_bone_by_name,
    PROSCENIO_OT_set_active_action,
    PROSCENIO_OT_toggle_outliner_favorite,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
