"""Authoring pipeline dispatch (SPEC 013.2 interactive-modal, T10).

Per-stage compute helpers that bridge between pure modules and the
running modal operator. Final apply_mesh pipes through build_automesh
+ Wave 13.2-sidecar reproject so existing weights survive APPLY.
"""

from __future__ import annotations

import json

import bpy
from mathutils import Vector

from ...automesh import (
    BoneSegment2D,
    binarize,
    compute_inner_loops,
    extract_outer_contour,
    interior_points_for_annulus,
    to_float_contour,
)
from ...skinning.authoring_stages import Point2D, StageOutput, StageParams
from .bridge import (
    build_automesh,
    collect_bone_segments,
    pixel_contour_to_world,
    read_alpha_grid,
)

_USER_STEINERS_KEY = "proscenio_user_steiners"

# Local imports to keep this module's top-level free of optional
# bpy-skinning helper coupling for callers that only need the
# compute_outer / compute_inner_loops_for_stage paths (e.g. headless
# overlay smoke). apply_mesh imports them at call site.


def compute_outer(
    obj: bpy.types.Object,
    image: bpy.types.Image,
    params: StageParams,
) -> list[Point2D]:
    """Run alpha walker on the active image; return outer contour in WORLD XZ.

    pixel_contour_to_world returns MESH-LOCAL XZ centered on the sprite
    origin (bmesh writer pattern). The modal's POST_VIEW overlay draws
    in world space, so we apply obj.matrix_world to land each point at
    the sprite's actual viewport position. Without this, the overlay
    renders at the world origin while the mesh sits elsewhere.
    """
    alpha_grid = read_alpha_grid(image, params.resolution)
    pixel_contour = extract_outer_contour(alpha_grid, params.alpha_threshold, params.margin_pixels)
    world_scale = 1.0 / _resolve_pixels_per_unit(bpy.context)
    source_width, source_height = image.size[0], image.size[1]
    local = pixel_contour_to_world(
        to_float_contour(pixel_contour),
        params.resolution,
        world_scale,
        source_width,
        source_height,
    )
    return _to_world_xz(obj, local)


def compute_inner_loops_for_stage(
    obj: bpy.types.Object,
    image: bpy.types.Image,
    outer: list[Point2D],
    params: StageParams,
) -> list[list[Point2D]]:
    """N concentric inner loops via pure erosion_loops.

    spacing_world is converted to spacing_px via the scene PPU + active
    resolution downscale factor.
    """
    if params.inner_loop_count <= 0:
        return []
    pixels_per_unit = _resolve_pixels_per_unit(bpy.context)
    spacing_px = max(1, int(params.inner_loop_spacing * pixels_per_unit * params.resolution))
    alpha_grid = read_alpha_grid(image, params.resolution)
    base_mask = binarize(alpha_grid, params.alpha_threshold)
    inner_pixel_contours = compute_inner_loops(
        base_mask, count=params.inner_loop_count, spacing_px=spacing_px
    )
    world_scale = 1.0 / pixels_per_unit
    source_width, source_height = image.size[0], image.size[1]
    return [
        _to_world_xz(
            obj,
            pixel_contour_to_world(
                to_float_contour(c),
                params.resolution,
                world_scale,
                source_width,
                source_height,
            ),
        )
        for c in inner_pixel_contours
    ]


def read_user_steiners(obj: bpy.types.Object) -> list[Point2D]:
    """Read obj['proscenio_user_steiners']; empty list when absent or corrupt."""
    payload = obj.get(_USER_STEINERS_KEY)
    if payload is None:
        return []
    try:
        data = json.loads(payload) if isinstance(payload, str) else list(payload)
    except (ValueError, TypeError):
        return []
    if not isinstance(data, list):
        return []
    points: list[Point2D] = []
    for item in data:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            points.append((float(item[0]), float(item[1])))
    return points


def write_user_steiners(obj: bpy.types.Object, points: list[Point2D]) -> None:
    """Persist via Custom Property as JSON string for stability."""
    obj[_USER_STEINERS_KEY] = json.dumps([[p[0], p[1]] for p in points])


def compute_all_steiners(
    outer: list[Point2D],
    inner_loops: list[list[Point2D]],
    user: list[Point2D],
    bone_segments: list[BoneSegment2D] | None,
    params: StageParams,
) -> list[Point2D]:
    """Uniform interior grid + bone density + merge user steiners.

    bone_segments comes from collect_bone_segments(picker_armature);
    elements are already ((head_x, head_z), (tail_x, tail_z)) per the
    existing helper (no extra unpacking needed).
    """
    # Use the innermost loop as the annulus "inner" boundary so the
    # uniform grid is clipped to the annulus shell; when no inner
    # loops exist, fall back to filling the full outer interior.
    inner_for_filter: list[Point2D] = inner_loops[-1] if inner_loops else []
    interior = interior_points_for_annulus(
        outer,
        inner_for_filter,
        params.interior_spacing,
        bone_segments=bone_segments,
        bone_density_radius=params.bone_radius if bone_segments else 0.0,
        bone_density_factor=params.bone_factor if bone_segments else 1,
    )
    return list(interior) + list(user)


def apply_mesh(
    obj: bpy.types.Object,
    image: bpy.types.Image,
    output: StageOutput,
    params: StageParams,
    armature: bpy.types.Object | None,
) -> dict[str, int]:
    """Final write: build_automesh + Wave 13.2-sidecar reproject."""
    # Local import: keep this module importable when the skinning
    # bpy-helpers subpackage is unavailable (e.g. unit-test stubs).
    from ..skinning import maybe_post_regen_reproject, maybe_pre_regen_snapshot

    bone_segments = collect_bone_segments(armature) if armature is not None else None
    prior_sidecar = maybe_pre_regen_snapshot(obj, armature) if armature is not None else None
    world_scale = 1.0 / _resolve_pixels_per_unit(bpy.context)
    counters = build_automesh(
        obj,
        image,
        downscale_factor=params.resolution,
        alpha_threshold=params.alpha_threshold,
        margin_pixels=params.margin_pixels,
        target_contour_vertices=params.contour_vertices,
        interior_spacing=params.interior_spacing,
        world_scale=world_scale,
        bone_segments=bone_segments,
        bone_density_radius=params.bone_radius if bone_segments else 0.0,
        bone_density_factor=params.bone_factor if bone_segments else 1,
        debug_stage="off",
        preserve_base_quad=False,
    )
    if prior_sidecar is not None and armature is not None:
        repro = maybe_post_regen_reproject(obj, armature, prior_sidecar)
        counters["reprojected"] = repro["reprojected"]
        counters["auto_seed"] = repro["auto_seed"]
    return counters


def _resolve_pixels_per_unit(context: bpy.types.Context) -> float:
    scene_props = getattr(context.scene, "proscenio", None)
    if scene_props is None:
        return 100.0
    return float(scene_props.pixels_per_unit) or 100.0


def _to_world_xz(obj: bpy.types.Object, local_points: list[Point2D]) -> list[Point2D]:
    """Transform local XZ points through obj.matrix_world; drop Y component.

    Used by stage compute helpers so the GPU overlay draws at the sprite's
    actual viewport position rather than the world origin. Y is dropped
    after transform since the Proscenio convention pins the sprite plane
    to Y=0 anyway; preserving any tiny Y component would still flatten on
    the POST_VIEW draw (which builds (x, 0, z) verts).
    """
    matrix = obj.matrix_world
    out: list[Point2D] = []
    for x, z in local_points:
        world = matrix @ Vector((x, 0.0, z))
        out.append((world.x, world.z))
    return out
