"""Pose library + bake-current-pose operators (SPEC 005.1.a/d.2)."""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import StringProperty

from ..core.report import report_error, report_info, report_warn  # type: ignore[import-not-found]


def _default_pose_asset_name(armature: bpy.types.Object, context: bpy.types.Context) -> str:
    """Compose ``<action>.<frame>`` or ``<armature>.<frame>`` for the asset name."""
    frame = int(context.scene.frame_current)
    anim_data = getattr(armature, "animation_data", None)
    action = getattr(anim_data, "action", None) if anim_data is not None else None
    if action is not None and action.name:
        return f"{action.name}.{frame}"
    return f"{armature.name}.{frame}"


class PROSCENIO_OT_save_pose_asset(bpy.types.Operator):
    """Save the current pose to the Asset Browser (SPEC 005.1.d.2)."""

    bl_idname = "proscenio.save_pose_asset"
    bl_label = "Proscenio: Save Pose to Library"
    bl_description = (
        "Bundle the current armature pose into a Pose Library asset so it shows "
        "up in the Asset Browser. Wraps Blender's poselib.create_pose_asset."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    pose_name: StringProperty(  # type: ignore[valid-type]
        name="Pose name",
        description=(
            "Asset name. Empty string falls back to '<action>.<frame>' or '<armature>.<frame>'."
        ),
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        active = context.active_object
        if active is None or active.type != "ARMATURE":
            return False
        return bool(context.mode == "POSE")

    def execute(self, context: bpy.types.Context) -> set[str]:
        armature = context.active_object
        if armature is None or armature.type != "ARMATURE":
            report_error(self, "no active armature")
            return {"CANCELLED"}
        if not armature.pose or not armature.pose.bones:
            report_warn(self, "armature has no pose bones")
            return {"CANCELLED"}
        if not hasattr(bpy.ops.poselib, "create_pose_asset"):
            report_error(
                self,
                "bpy.ops.poselib.create_pose_asset not available "
                "(Blender < 3.5 or pose library disabled).",
            )
            return {"CANCELLED"}
        library = _first_writable_asset_library()
        if library is None:
            report_error(
                self,
                "no writable asset library configured. Add one in "
                "Preferences > File Paths > Asset Libraries with a path "
                "Blender can write to, then retry.",
            )
            return {"CANCELLED"}

        pose_name = self.pose_name or _default_pose_asset_name(armature, context)
        # asset_library_reference is required since Blender 4.x+ when
        # calling create_pose_asset programmatically; default '' falls
        # back to "" and Blender refuses with "Unexpected library type".
        # Pass the first writable user library's name (matches the
        # ENUM identifier convention).
        try:
            bpy.ops.poselib.create_pose_asset(
                pose_name=pose_name,
                asset_library_reference=library.name,
            )
        except (RuntimeError, TypeError) as exc:
            report_error(self, f"pose library refused: {exc}")
            return {"CANCELLED"}

        report_info(
            self,
            f"saved pose asset '{pose_name}' to '{library.name}'",
        )
        return {"FINISHED"}


def _first_writable_asset_library() -> bpy.types.UserAssetLibrary | None:
    """Return the first Asset Library with a writable on-disk path, or None.

    Blender 4.x ships without default writable Pose Libraries, so
    poselib.create_pose_asset fails with "Unexpected library type" until
    the user adds one in Preferences > File Paths > Asset Libraries.
    Returning the entry (not just a bool) lets the caller pass its name
    as ``asset_library_reference`` - required by the operator since 4.x
    even when only one library is configured. The poll path lets the
    operator stay clickable; the precheck surfaces the missing setup
    with an actionable hint instead of the cryptic poselib error.
    """
    import os

    libs = getattr(bpy.context.preferences.filepaths, "asset_libraries", None)
    if libs is None:
        return None
    for lib in libs:
        path = str(getattr(lib, "path", ""))
        if path and os.path.isdir(path) and os.access(path, os.W_OK):
            return lib
    return None


class PROSCENIO_OT_bake_current_pose(bpy.types.Operator):
    """Insert keyframes for every Bone2D's transform at the current frame."""

    bl_idname = "proscenio.bake_current_pose"
    bl_label = "Proscenio: Bake Current Pose"
    bl_description = (
        "Inserts a location/rotation/scale keyframe on every pose bone of the "
        "first armature in the scene at the playhead. Requires Pose Mode."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        active = context.active_object
        if active is None or active.type != "ARMATURE":
            return False
        return bool(context.mode == "POSE")

    def execute(self, context: bpy.types.Context) -> set[str]:
        armature = context.active_object
        frame = context.scene.frame_current
        bones = armature.pose.bones
        if not bones:
            report_warn(self, "armature has no pose bones")
            return {"CANCELLED"}
        for bone in bones:
            for path in ("location", "rotation_quaternion", "rotation_euler", "scale"):
                if hasattr(bone, path):
                    bone.keyframe_insert(data_path=path, frame=frame)
        report_info(self, f"baked pose at frame {frame} for {len(bones)} bone(s)")
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_save_pose_asset,
    PROSCENIO_OT_bake_current_pose,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
