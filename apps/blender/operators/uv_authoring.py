"""UV authoring operators: Reproject UV, Snap region to UV bounds (SPEC 005.1.b/c)."""

from __future__ import annotations

import contextlib
from typing import ClassVar

import bpy
from bpy.props import FloatProperty

from ..core.props_access import object_props  # type: ignore[import-not-found]
from ..core.report import report_info, report_warn  # type: ignore[import-not-found]


class PROSCENIO_OT_reproject_sprite_uv(bpy.types.Operator):
    """Re-unwrap the active mesh's UVs against its first image-textured material.

    Known limitation (tests/BUGS_FOUND.md): bpy.ops.uv.smart_project picks
    a projection from face normals. For quads in the XZ picture plane the
    normal points -Y; the operator can rotate/mirror the result relative
    to whatever the build_blend.py author hand-tuned. Use only on meshes
    whose UVs were never authored by hand, or restore from the pre_pack
    snapshot afterwards.
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
        # Re-projection toggles Edit Mode on the active mesh; starting from
        # Edit Mode would leak state from the user's in-progress selection.
        return context.mode == "OBJECT"

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        prior_mode = context.mode
        prior_active = context.view_layer.objects.active
        prior_selection = [o for o in context.scene.objects if o.select_get()]

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
            for other in context.scene.objects:
                other.select_set(False)
            for o in prior_selection:
                o.select_set(True)
            if prior_active is not None:
                context.view_layer.objects.active = prior_active

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
        # mesh.uv_layers.active.data is empty while the mesh is in Edit
        # Mode (BMesh owns the loop data instead); execute() would raise
        # IndexError when reading uv_layer.data[li].
        return context.mode == "OBJECT"

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

        xs: list[float] = []
        ys: list[float] = []
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                u = uv_layer.data[li].uv
                xs.append(float(u.x))
                ys.append(1.0 - float(u.y))

        if not xs:
            report_warn(self, f"'{obj.name}' has no UV data")
            return {"CANCELLED"}

        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        props.region_x = x_min
        props.region_y = y_min
        props.region_w = x_max - x_min
        props.region_h = y_max - y_min
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
