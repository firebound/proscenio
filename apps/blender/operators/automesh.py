"""Automesh operator: PNG sprite -> deformable annulus mesh (SPEC 013).

Wave 13.1 first cut. Resolves the upstream half of skinning that
SPEC 003 already shipped on the export side. Turns a sprite plane
with an image texture (or a `[mesh]`-tagged Photoshop import) into
an annulus mesh whose density follows the picker armature's bones.

Decision map (see SPEC 013 STUDY):
- D1: alpha-trace one-shot, pure-Python alpha walker (no OpenCV).
- D2: annulus topology (outer dilate + inner erode + triangle_fill).
- D3: ``proscenio_base_sprite`` vertex group preserves UV-pinned base.
- D15: density-under-bones ON when picker has armature, OFF otherwise.

Operator is ``REGISTER, UNDO`` so F3 redo can iterate parameters
without re-clicking. Defaults read from
``scene.proscenio.skinning``; F3 redo exposes inline overrides.
"""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import (
    BoolProperty,
    FloatProperty,
    IntProperty,
)

from ..core.bpy_helpers.automesh_bmesh import (
    build_automesh,
    collect_bone_segments,
)
from ..core.report import report_error, report_info, report_warn


def _resolve_image(obj: bpy.types.Object) -> bpy.types.Image | None:
    """Find the first image texture in the mesh's material slots.

    Walks the active material's node tree for a ``TEX_IMAGE`` node;
    if none, falls back to the first material on the mesh that has
    one. Returns ``None`` when the mesh has no image-textured
    material - the operator pre-flight reports an actionable error
    in that case.
    """
    materials = list(obj.data.materials) if obj.data else []
    for material in materials:
        if material is None or not material.use_nodes:
            continue
        for node in material.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image is not None:
                return node.image
    return None


def _resolve_pixels_per_unit(context: bpy.types.Context) -> float:
    """Read the scene's pixels-per-unit, fall back to 100 when unset."""
    scene_props = getattr(context.scene, "proscenio", None)
    if scene_props is None:
        return 100.0
    return float(scene_props.pixels_per_unit) or 100.0


class PROSCENIO_OT_automesh_from_sprite(bpy.types.Operator):
    """Generate a deformable annulus mesh from the active sprite's alpha."""

    bl_idname = "proscenio.automesh_from_sprite"
    bl_label = "Proscenio: Automesh from Sprite"
    bl_description = (
        "Build a deformable annulus mesh from the active sprite's image "
        "alpha channel. Pure-Python contour walker (no OpenCV dependency) "
        "+ Laplacian smoothing + arc-length resampling + bone-aware "
        "interior density when an active armature is set. Re-runs preserve "
        "the original UV-pinned quad via the proscenio_base_sprite vertex "
        "group"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    resolution: FloatProperty(  # type: ignore[valid-type]
        name="Resolution",
        description=("Image downscale factor for the contour walker (1.0 = full, 0.25 = quarter)"),
        default=0.25,
        min=0.01,
        max=1.0,
    )
    alpha_threshold: IntProperty(  # type: ignore[valid-type]
        name="Alpha threshold",
        default=127,
        min=0,
        max=255,
    )
    margin_pixels: IntProperty(  # type: ignore[valid-type]
        name="Margin (px)",
        default=5,
        min=0,
        max=100,
    )
    contour_vertices: IntProperty(  # type: ignore[valid-type]
        name="Contour vertices",
        default=64,
        min=8,
        max=512,
    )
    interior_spacing: FloatProperty(  # type: ignore[valid-type]
        name="Interior spacing",
        default=0.1,
        min=0.001,
        soft_max=2.0,
    )
    density_under_bones: BoolProperty(  # type: ignore[valid-type]
        name="Density under bones",
        default=True,
    )
    bone_radius: FloatProperty(  # type: ignore[valid-type]
        name="Bone radius",
        default=0.5,
        min=0.01,
        soft_max=5.0,
    )
    bone_factor: IntProperty(  # type: ignore[valid-type]
        name="Bone density factor",
        default=2,
        min=1,
        max=8,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return obj is not None and obj.type == "MESH"

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        # Pull defaults from the scene PG so F3 redo + button click
        # both reflect the user's panel settings.
        scene_props = getattr(context.scene, "proscenio", None)
        if scene_props is not None:
            skinning = getattr(scene_props, "skinning", None)
            if skinning is not None:
                self.resolution = float(skinning.automesh_resolution)
                self.alpha_threshold = int(skinning.automesh_alpha_threshold)
                self.margin_pixels = int(skinning.automesh_margin_pixels)
                self.contour_vertices = int(skinning.automesh_contour_vertices)
                self.interior_spacing = float(skinning.automesh_interior_spacing)
                self.density_under_bones = bool(skinning.automesh_density_under_bones)
                self.bone_radius = float(skinning.automesh_bone_radius)
                self.bone_factor = int(skinning.automesh_bone_factor)
        return self.execute(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            report_error(self, "active object must be a mesh")
            return {"CANCELLED"}

        image = _resolve_image(obj)
        if image is None:
            report_error(
                self,
                "active mesh has no image texture - add a material with a "
                "TEX_IMAGE node first, or use an automesh-able imported sprite",
            )
            return {"CANCELLED"}

        if image.size[0] <= 0 or image.size[1] <= 0:
            report_error(
                self,
                f"image '{image.name}' has zero size - reload or pick a real texture",
            )
            return {"CANCELLED"}

        if max(image.size) > 4096:
            report_warn(
                self,
                f"image '{image.name}' is large ({image.size[0]}x{image.size[1]}) - "
                "consider lowering resolution to keep automesh fast",
            )

        bone_segments = None
        if self.density_under_bones:
            scene_props = getattr(context.scene, "proscenio", None)
            picker = getattr(scene_props, "active_armature", None) if scene_props else None
            if picker is not None and picker.type == "ARMATURE":
                segments = collect_bone_segments(picker)
                if segments:
                    bone_segments = segments
                else:
                    report_info(
                        self,
                        f"picker armature '{picker.name}' has no deform bones - "
                        "automesh falls back to uniform density",
                    )
            else:
                report_info(
                    self,
                    "no picker armature - automesh uses uniform interior density "
                    "(pick an armature in the Skeleton panel for density-under-bones)",
                )

        world_scale = 1.0 / _resolve_pixels_per_unit(context)

        try:
            counters = build_automesh(
                obj,
                image,
                downscale_factor=self.resolution,
                alpha_threshold=self.alpha_threshold,
                margin_pixels=self.margin_pixels,
                target_contour_vertices=self.contour_vertices,
                interior_spacing=self.interior_spacing,
                world_scale=world_scale,
                bone_segments=bone_segments,
                bone_density_radius=self.bone_radius if bone_segments else 0.0,
                bone_density_factor=self.bone_factor if bone_segments else 1,
            )
        except ValueError as exc:
            report_error(self, f"automesh failed: {exc}")
            return {"CANCELLED"}

        report_info(
            self,
            (
                f"automesh built: {counters['outer_verts']} outer + "
                f"{counters['inner_verts']} inner + "
                f"{counters['interior_verts']} interior = "
                f"{counters['total_verts']} total, "
                f"{counters['total_faces']} faces"
            ),
        )
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_automesh_from_sprite,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
