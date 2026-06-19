"""Convert bone rotation mode to XYZ Euler (the Drive-from-Bone fix-up).

The export validator warns when a bone that drives a sprite is not in XYZ Euler:
Drive-from-Bone reads the bone rotation as XYZ, so a Quaternion (or non-XYZ
Euler) bone drives wrong. This operator is the one-click fix - Blender converts
the stored rotation natively when ``rotation_mode`` flips.
"""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import EnumProperty

from ...core._shared.report import report_info, report_warn  # type: ignore[import-not-found]

_EULER_MODE = "XYZ"


def _target_armature(context: bpy.types.Context) -> bpy.types.Object | None:
    """The Proscenio-picked armature, falling back to the active object."""
    scene_props = getattr(context.scene, "proscenio", None)
    picked = getattr(scene_props, "active_armature", None) if scene_props is not None else None
    if picked is not None and picked.type == "ARMATURE":
        return picked
    obj = context.active_object
    return obj if obj is not None and obj.type == "ARMATURE" else None


def _active_bone_name(armature: bpy.types.Object, context: bpy.types.Context) -> str | None:
    """Name of the armature's active bone, preferring the active pose bone."""
    active_pose_bone = getattr(context, "active_pose_bone", None)
    if active_pose_bone is not None and active_pose_bone.id_data is armature:
        return str(active_pose_bone.name)
    active_bone = getattr(getattr(armature.data, "bones", None), "active", None)
    return str(active_bone.name) if active_bone is not None else None


class PROSCENIO_OT_convert_rotation_to_euler(bpy.types.Operator):
    """Set bone rotation mode to XYZ Euler so Drive-from-Bone reads it 1:1."""

    bl_idname = "proscenio.convert_rotation_to_euler"
    bl_label = "Proscenio: Convert Rotation to Euler"
    bl_description = (
        "Set the bone rotation mode to XYZ Euler (Blender converts the stored "
        "rotation). Drive-from-Bone reads rotation as XYZ, so a Quaternion bone "
        "drives wrong - this is the one-click fix"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    scope: EnumProperty(  # type: ignore[valid-type]
        name="Scope",
        description="Convert just the active bone or every bone in the armature",
        items=(
            ("ACTIVE", "Active Bone", "Convert only the active pose bone", 0),
            ("ALL", "All Bones", "Convert every bone in the active armature", 1),
        ),
        default="ACTIVE",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _target_armature(context) is not None

    def execute(self, context: bpy.types.Context) -> set[str]:
        armature = _target_armature(context)
        if armature is None:
            report_warn(self, "no armature - pick an Active Armature in the Skeleton panel")
            return {"CANCELLED"}
        pose = getattr(armature, "pose", None)
        if pose is None:
            report_warn(self, f"armature '{armature.name}' has no pose bones")
            return {"CANCELLED"}
        if self.scope == "ACTIVE":
            bone_name = _active_bone_name(armature, context)
            if bone_name is None:
                report_warn(self, "no active bone - select one or use the All Bones scope")
                return {"CANCELLED"}
            targets = [pb for pb in pose.bones if pb.name == bone_name]
        else:
            targets = list(pose.bones)
        converted = 0
        for pose_bone in targets:
            if pose_bone.rotation_mode != _EULER_MODE:
                pose_bone.rotation_mode = _EULER_MODE
                converted += 1
        report_info(self, f"converted {converted} bone(s) to XYZ Euler")
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_convert_rotation_to_euler,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
