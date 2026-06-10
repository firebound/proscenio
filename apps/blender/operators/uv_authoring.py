"""UV authoring operators: Reproject UV, Snap region to UV bounds."""

from __future__ import annotations

import contextlib
from typing import ClassVar

import bpy
from bpy.props import FloatProperty

from ..core._shared.props_access import object_props  # type: ignore[import-not-found]
from ..core._shared.region import compute_region_from_uvs  # type: ignore[import-not-found]
from ..core._shared.report import report_info, report_warn  # type: ignore[import-not-found]
from ..core.bpy_helpers._shared.mesh_uvs import (  # type: ignore[import-not-found]
    collect_mesh_loop_uvs,
)
from ..core.bpy_helpers._shared.select import (  # type: ignore[import-not-found]
    preserve_selection,
)


class PROSCENIO_OT_reproject_sprite_uv(bpy.types.Operator):
    """Re-unwrap the active mesh's UVs against its first image-textured material.

    Known limitation: smart_project derives the projection from face
    normals. For XZ-picture-plane quads the normal points -Y, so it can
    rotate/mirror the result relative to a hand-authored layout. Use only
    on meshes whose UVs were never hand-authored, or restore from the
    pre_pack snapshot afterwards.
    """

    bl_idname = "proscenio.reproject_sprite_uv"
    bl_label = "Proscenio: Reproject UV"
    bl_description = (
        "Re-projects the active mesh's UVs (Smart UV Project) so the texture "
        "lines up after vertex edits. Active object only. May rotate / "
        "mirror UVs relative to hand-authored layouts."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    angle_limit: FloatProperty(  # type: ignore[valid-type]
        name="Angle limit",
        description="Smart UV Project angle limit (radians)",
        default=1.15192,
        min=0.0,
        max=3.14159,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return False
        # Toggles Edit Mode internally; starting in Edit Mode leaks the
        # user's in-progress selection. Object Mode only.
        return bool(context.mode == "OBJECT")

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        prior_mode = context.mode

        # preserve_selection restores selection + active; the inner finally
        # only handles the Edit-Mode toggle below.
        with preserve_selection(context):
            try:
                for other in context.scene.objects:
                    other.select_set(False)
                obj.select_set(True)
                context.view_layer.objects.active = obj
                if prior_mode != "EDIT_MESH":
                    bpy.ops.object.mode_set(mode="EDIT")
                bpy.ops.mesh.select_all(action="SELECT")
                bpy.ops.uv.smart_project(angle_limit=self.angle_limit)
            finally:
                if prior_mode != "EDIT_MESH":
                    with contextlib.suppress(RuntimeError):
                        bpy.ops.object.mode_set(mode="OBJECT")

        report_info(self, f"reprojected UVs on '{obj.name}'")
        return {"FINISHED"}


class PROSCENIO_OT_snap_region_to_uv(bpy.types.Operator):
    """Copy current UV bounds into the manual region_x/y/w/h fields."""

    bl_idname = "proscenio.snap_region_to_uv"
    bl_label = "Proscenio: Snap region to UV bounds"
    bl_description = (
        "Reads the active mesh's UV bounds and writes them into the manual "
        "region fields. Use this to seed manual mode with the current auto value."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return False
        # uv_layer.data is empty under BMesh in Edit Mode; Object Mode only.
        return bool(context.mode == "OBJECT")

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        props = object_props(obj)
        if props is None:
            report_warn(self, "PropertyGroup not registered on this object")
            return {"CANCELLED"}

        mesh = obj.data
        uv_layer = mesh.uv_layers.active
        if uv_layer is None or not mesh.polygons or len(uv_layer.data) == 0:
            report_warn(self, f"'{obj.name}' has no UV layer or no polygons")
            return {"CANCELLED"}

        # Flip v into Godot/region space, then reuse the auto-mode bounds
        # computation so Snap seeds the exact value the writer would emit.
        uvs_godot = [[u, 1.0 - v] for u, v in collect_mesh_loop_uvs(mesh)]
        if not uvs_godot:
            report_warn(self, f"'{obj.name}' has no UV data")
            return {"CANCELLED"}

        props.region_x, props.region_y, props.region_w, props.region_h = compute_region_from_uvs(
            uvs_godot
        )
        report_info(
            self,
            f"snapped region to UV bounds "
            f"({props.region_x:.4f}, {props.region_y:.4f}, "
            f"{props.region_w:.4f}, {props.region_h:.4f})",
        )
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_reproject_sprite_uv,
    PROSCENIO_OT_snap_region_to_uv,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
