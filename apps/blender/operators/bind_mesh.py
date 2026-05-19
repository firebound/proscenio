"""Bind mesh to picker armature via planar proximity (SPEC 013.2).

Avoids Blender's bone-heat solver by default (D4). Surfaces 5 pre-flight
diagnoses (D11) before touching geometry. Writes a WeightSidecar stub
the Wave 13.2-sidecar wave consumes for reproject.

F3 redo exposes mode + falloff_power + max_distance + use_bone_heat
opt-in. Scene PropertyGroup persistence is the panel wave's
responsibility - this operator stands alone with its F3 properties.
"""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty

from ..core.bpy_helpers.skinning import (  # type: ignore[import-not-found]
    apply_bind,
    collect_diagnoses_for_object,
)
from ..core.report import (  # type: ignore[import-not-found]
    report_error,
    report_info,
    report_warn,
)


class PROSCENIO_OT_bind_mesh_to_armature(bpy.types.Operator):
    """Bind the active mesh to the picker armature without bone-heat."""

    bl_idname = "proscenio.bind_mesh_to_armature"
    bl_label = "Proscenio: Bind Mesh to Picker Armature"
    bl_description = (
        "Bind the active mesh to the Proscenio picker armature using a "
        "planar 1/dist^power falloff. Surfaces pre-flight diagnoses (scale, "
        "normals, overlap, islands, bone bbox) before touching geometry. "
        "Writes a sidecar stub the reproject wave consumes"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    bind_init_mode: EnumProperty(  # type: ignore[valid-type]
        name="Bind mode",
        items=[
            ("PROXIMITY", "Proximity", "1/dist^power normalized (default)"),
            ("ENVELOPE", "Envelope", "Per-bone radius from Custom Property"),
            ("SINGLE_NEAREST", "Single nearest", "One bone per vert, weight 1.0"),
            ("EMPTY", "Empty", "All-zero weights (manual paint baseline)"),
        ],
        default="PROXIMITY",
    )
    falloff_power: FloatProperty(  # type: ignore[valid-type]
        name="Falloff power",
        description="Exponent for 1/dist^power (PROXIMITY only)",
        default=2.0,
        min=0.5,
        max=8.0,
    )
    max_distance: FloatProperty(  # type: ignore[valid-type]
        name="Max distance",
        description=(
            "Bones beyond this distance contribute zero. -1 = adaptive "
            "(1.5x armature bbox)"
        ),
        default=-1.0,
    )
    use_bone_heat: BoolProperty(  # type: ignore[valid-type]
        name="Use bone heat (legacy)",
        description=(
            "OPT-IN ONLY (D4) - delegate to bpy.ops.object.parent_set"
            "(ARMATURE_AUTO). Default OFF"
        ),
        default=False,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return obj is not None and obj.type == "MESH"

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            report_error(self, "active object must be a mesh")
            return {"CANCELLED"}
        if len(obj.data.vertices) == 0:
            report_error(self, "mesh has 0 verts")
            return {"CANCELLED"}

        scene_props = getattr(context.scene, "proscenio", None)
        armature = getattr(scene_props, "active_armature", None) if scene_props else None
        if armature is None or armature.type != "ARMATURE":
            report_error(self, "no picker armature set - pick one in Skeleton panel first")
            return {"CANCELLED"}
        if not any(b.use_deform for b in armature.data.bones):
            report_error(
                self,
                f"picker '{armature.name}' has no deform bones - enable deform on bones first",
            )
            return {"CANCELLED"}

        if self.use_bone_heat:
            return self._delegate_to_bone_heat(context, armature)

        findings = collect_diagnoses_for_object(obj, armature)
        errors = [f for f in findings if f.severity == "error"]
        warns = [f for f in findings if f.severity == "warn"]
        for finding in errors:
            report_error(self, f"{finding.message} - {finding.hint}")
        if errors:
            return {"CANCELLED"}
        for finding in warns:
            report_info(self, f"{finding.message} - {finding.hint}")

        try:
            counters = apply_bind(
                obj,
                armature,
                self.bind_init_mode,
                falloff_power=self.falloff_power,
                max_distance=self.max_distance,
            )
        except Exception as exc:
            report_error(self, f"bind failed: {exc}")
            return {"CANCELLED"}

        if counters["orphan_verts"] > 0:
            report_warn(
                self,
                f"{counters['orphan_verts']} verts have no bone in range - "
                "increase max_distance or move armature closer",
            )
        report_info(
            self,
            (
                f"bind: {counters['verts_bound']} verts to {counters['bones_used']} "
                f"bones ({counters['orphan_verts']} orphans). Mode={self.bind_init_mode}"
            ),
        )
        return {"FINISHED"}

    def _delegate_to_bone_heat(
        self, context: bpy.types.Context, armature: bpy.types.Object
    ) -> set[str]:
        """Legacy bone-heat opt-in path (D4). Surface raw Blender errors."""
        prior_active = context.view_layer.objects.active
        try:
            armature.select_set(True)
            context.view_layer.objects.active = armature
            bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        except RuntimeError as exc:
            report_error(self, f"bone-heat failed: {exc}")
            return {"CANCELLED"}
        finally:
            context.view_layer.objects.active = prior_active
        report_info(self, "bone-heat bind delegated to Blender (legacy path)")
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_bind_mesh_to_armature,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
