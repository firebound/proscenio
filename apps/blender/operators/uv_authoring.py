"""UV authoring operators: Reproject UV, Snap region to UV bounds."""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core._shared.props_access import object_props  # type: ignore[import-not-found]
from ..core._shared.region import compute_region_from_uvs  # type: ignore[import-not-found]
from ..core._shared.report import report_info, report_warn  # type: ignore[import-not-found]
from ..core.bpy_helpers._shared.mesh_uvs import (  # type: ignore[import-not-found]
    collect_mesh_loop_uvs,
    planar_uv_from_positions,
)


class PROSCENIO_OT_reproject_sprite_uv(bpy.types.Operator):
    """Re-unwrap the active mesh's UVs with a deterministic planar projection.

    Maps each loop's vertex position onto the mesh's dominant plane: for the
    standard XZ picture-plane quad, U follows X and V follows Z, normalized
    over the bounding box - the same mapping the PSD importer and the fixtures
    author. Unlike Smart UV Project (whose face-normal frame rotated and
    mirrored an XZ quad), it never disturbs a hand-authored orientation, and
    it runs entirely in Object Mode with no mode toggle or selection change.
    """

    bl_idname = "proscenio.reproject_sprite_uv"
    bl_label = "Proscenio: Reproject UV"
    bl_description = (
        "Re-projects the active mesh's UVs with a deterministic planar "
        "projection (U follows X, V follows Z for a picture-plane mesh) so the "
        "texture lines up after vertex edits without rotating or mirroring the "
        "layout. Active object only."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return False
        # Reads mesh.vertices[].co, which is the BMesh-stale pre-edit copy in
        # Edit Mode; Object Mode only so the projection sees live geometry.
        return bool(context.mode == "OBJECT")

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        mesh = obj.data
        if not mesh.loops:
            report_warn(self, f"'{obj.name}' has no geometry to project")
            return {"CANCELLED"}
        # Resolve the layer only after the guard, so a cancel never mutates the
        # datablock (no stray UVMap, no empty undo step). A freshly created
        # layer is loop-length; an active layer can be shorter than the loop
        # count in a partially-initialized mesh (the same short-data state
        # collect_mesh_loop_uvs guards), so fall back to a new layer and bail if
        # it is still short rather than indexing past the end of uv_layer.data.
        loop_count = len(mesh.loops)
        uv_layer = mesh.uv_layers.active
        if uv_layer is None or len(uv_layer.data) < loop_count:
            uv_layer = mesh.uv_layers.new(name="UVMap")
        if len(uv_layer.data) < loop_count:
            report_warn(self, f"'{obj.name}' has inconsistent UV data; recreate UVs and retry")
            return {"CANCELLED"}

        positions = [tuple(mesh.vertices[loop.vertex_index].co) for loop in mesh.loops]
        uvs = planar_uv_from_positions(positions)
        for loop_index, (u, v) in enumerate(uvs):
            uv_layer.data[loop_index].uv = (u, v)
        mesh.update()

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
