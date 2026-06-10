"""Bind mesh to picker armature.

Defaults to Blender's bone-heat solver. Surfaces 5 pre-flight
diagnoses before touching geometry. Writes a WeightSidecar stub
the reproject step consumes.

F3 redo exposes bind_init_mode enum (BONE_HEAT default, PROXIMITY/ENVELOPE/
SINGLE_NEAREST/EMPTY fallbacks) + falloff_power + max_distance.
Scene PropertyGroup persistence (panel) reads into invoke() so panel
+ F3 both reflect persisted settings.
"""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import EnumProperty, FloatProperty

from ...core._shared.props_access import (  # type: ignore[import-not-found]
    active_armature,
    scene_skinning,
)
from ...core._shared.report import (  # type: ignore[import-not-found]
    report_error,
    report_info,
    report_warn,
)
from ...core.bpy_helpers.skinning import (  # type: ignore[import-not-found]
    apply_bind,
    collect_diagnoses_for_object,
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
        "writes a sidecar stub the reproject step consumes"
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
        if active_armature(context) is None:
            return False
        return any(o.type == "MESH" for o in context.selected_objects) or (
            context.active_object is not None and context.active_object.type == "MESH"
        )

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        skinning = scene_skinning(context)
        if skinning is not None:
            self.bind_init_mode = str(skinning.bind_init_mode)
            self.falloff_power = float(skinning.bind_falloff_power)
            self.max_distance = float(skinning.bind_max_distance)
        return self.execute(context)

    def _bind_single(
        self,
        mesh_obj: bpy.types.Object,
        armature: bpy.types.Object,
    ) -> dict[str, int]:
        """Run pre-flight diagnoses and apply_bind for one mesh object.

        Returns the counters dict from apply_bind. Raises RuntimeError or
        Exception on failure so the caller can track per-mesh results.
        Emits per-finding reports directly to self.
        """
        if len(mesh_obj.data.vertices) == 0:
            raise ValueError("mesh has 0 verts")

        # Contract: ALL bind paths run pre-flight diagnoses.
        findings = collect_diagnoses_for_object(mesh_obj, armature)
        errors = [f for f in findings if f.severity == "error"]
        warns = [f for f in findings if f.severity == "warn"]
        for finding in errors:
            report_error(self, f"[{mesh_obj.name}] {finding.message} - {finding.hint}")
        if errors:
            raise RuntimeError(f"{len(errors)} pre-flight error(s); see above")
        for finding in warns:
            report_warn(self, f"[{mesh_obj.name}] {finding.message} - {finding.hint}")

        try:
            counters = apply_bind(
                mesh_obj,
                armature,
                self.bind_init_mode,
                falloff_power=self.falloff_power,
                max_distance=self.max_distance,
            )
        except RuntimeError as exc:
            if self.bind_init_mode == "BONE_HEAT":
                raise RuntimeError(
                    f"bone-heat failed: {exc}. Try mode=PROXIMITY as fallback "
                    "(Skinning panel > Bind mode dropdown)"
                ) from exc
            raise

        if counters["orphan_verts"] > 0:
            report_warn(
                self,
                f"[{mesh_obj.name}] {counters['orphan_verts']} verts have no bone in range - "
                "increase max_distance or move armature closer",
            )
        if counters["groups_wiped"] > 0:
            report_info(
                self,
                f"[{mesh_obj.name}] removed {counters['groups_wiped']} "
                "non-base vertex group(s) before bind",
            )
        report_info(
            self,
            (
                f"[{mesh_obj.name}] bind: {counters['verts_bound']} verts to "
                f"{counters['bones_used']} bones ({counters['orphan_verts']} orphans). "
                f"Mode={self.bind_init_mode}"
            ),
        )
        # apply_bind returns dict[str, Any] (counters); narrow to declared type
        return {str(k): int(v) for k, v in counters.items()}

    def execute(self, context: bpy.types.Context) -> set[str]:
        armature = active_armature(context)
        if armature is None:
            report_error(self, "no picker armature set - pick one in Skeleton panel first")
            return {"CANCELLED"}
        if not any(b.use_deform for b in armature.data.bones):
            report_error(
                self,
                f"picker '{armature.name}' has no deform bones - enable deform on bones first",
            )
            return {"CANCELLED"}

        # Collect all selected MESH objects; fall back to active when nothing
        # is formally selected (e.g. F3-invoked with no selection box).
        targets = [o for o in context.selected_objects if o.type == "MESH"]
        if not targets:
            active = context.active_object
            if active is not None and active.type == "MESH":
                targets = [active]
        if not targets:
            report_error(self, "no mesh objects selected")
            return {"CANCELLED"}

        successes = 0
        failures: list[tuple[str, str]] = []
        for mesh_obj in targets:
            try:
                self._bind_single(mesh_obj, armature)
                successes += 1
            except Exception as exc:
                failures.append((mesh_obj.name, str(exc)))

        for name, err in failures:
            report_warn(self, f"bind failed for '{name}': {err}")

        report_info(self, f"bound {successes} mesh(es)")
        return {"FINISHED"} if successes else {"CANCELLED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_bind_mesh_to_armature,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
