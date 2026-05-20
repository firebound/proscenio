"""Bind mesh to picker armature (SPEC 013.2).

Defaults to Blender's bone-heat solver (D4). Surfaces 5 pre-flight
diagnoses (D11) before touching geometry. Writes a WeightSidecar stub
the Wave 13.2-sidecar wave consumes for reproject.

F3 redo exposes bind_init_mode enum (BONE_HEAT default, PROXIMITY/ENVELOPE/
SINGLE_NEAREST/EMPTY fallbacks) + falloff_power + max_distance.
Scene PropertyGroup persistence (panel) reads into invoke() so panel
+ F3 both reflect persisted settings.
"""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import EnumProperty, FloatProperty

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
    """Bind the active mesh to the picker armature."""

    bl_idname = "proscenio.bind_mesh_to_armature"
    bl_label = "Proscenio: Bind Mesh to Picker Armature"
    bl_description = (
        "Bind the active mesh to the Proscenio picker armature. Default mode "
        "delegates to Blender's bone heat (best for 2D pickers); Proscenio's "
        "planar proximity / envelope / single-nearest / empty modes are "
        "available as F3-redo fallbacks. Surfaces 5 pre-flight diagnoses + "
        "writes a sidecar stub the reproject wave consumes"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    bind_init_mode: EnumProperty(  # type: ignore[valid-type]
        name="Bind mode",
        items=[
            (
                "BONE_HEAT",
                "Bone Heat (Blender native)",
                "Delegate to Blender's Parent w/ Auto Weights (default)",
            ),
            (
                "PROXIMITY",
                "Proximity (1/d^p)",
                "Per-bone 1/distance^falloff_power normalized (Proscenio fallback)",
            ),
            (
                "ENVELOPE",
                "Envelope",
                "Per-bone radius from bone Custom Property",
            ),
            (
                "SINGLE_NEAREST",
                "Single nearest",
                "One bone per vert, weight 1.0",
            ),
            (
                "EMPTY",
                "Empty",
                "All-zero baseline for manual paint",
            ),
        ],
        default="BONE_HEAT",
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
            "Bones beyond this distance contribute zero (PROXIMITY only). "
            "-1 = adaptive (1.5x armature bbox)"
        ),
        default=-1.0,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return obj is not None and obj.type == "MESH"

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        scene_props = getattr(context.scene, "proscenio", None)
        skinning = getattr(scene_props, "skinning", None) if scene_props else None
        if skinning is not None:
            self.bind_init_mode = str(skinning.bind_init_mode)
            self.falloff_power = float(skinning.bind_falloff_power)
            self.max_distance = float(skinning.bind_max_distance)
        return self.execute(context)

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

        # D11 contract: ALL bind paths run pre-flight diagnoses.
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
        except RuntimeError as exc:
            if self.bind_init_mode == "BONE_HEAT":
                report_error(
                    self,
                    f"bone-heat failed: {exc}. Try mode=PROXIMITY as fallback "
                    "(Skinning panel > Bind mode dropdown)",
                )
            else:
                report_error(self, f"bind failed: {exc}")
            return {"CANCELLED"}
        except Exception as exc:
            report_error(self, f"bind failed: {exc}")
            return {"CANCELLED"}

        if counters["orphan_verts"] > 0:
            report_warn(
                self,
                f"{counters['orphan_verts']} verts have no bone in range - "
                "increase max_distance or move armature closer",
            )
        if counters["groups_wiped"] > 0:
            report_info(
                self,
                f"removed {counters['groups_wiped']} non-base vertex group(s) before bind",
            )
        report_info(
            self,
            (
                f"bind: {counters['verts_bound']} verts to {counters['bones_used']} "
                f"bones ({counters['orphan_verts']} orphans). Mode={self.bind_init_mode}"
            ),
        )
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_bind_mesh_to_armature,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
