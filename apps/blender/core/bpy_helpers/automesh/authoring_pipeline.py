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
from ...skinning.authoring_stages import Point2D, StageOutput, StageParams, Stroke
from .bridge import (
    build_automesh,
    collect_bone_segments,
    pixel_contour_to_world,
    read_alpha_grid,
)

_USER_STEINERS_KEY = "proscenio_user_steiners"
_USER_STROKES_KEY = "proscenio_user_strokes"

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
        if not (isinstance(item, (list, tuple)) and len(item) == 2):
            continue
        try:
            x = float(item[0])
            z = float(item[1])
        except (TypeError, ValueError):
            continue
        points.append((x, z))
    return points


def write_user_steiners(obj: bpy.types.Object, points: list[Point2D]) -> None:
    """Persist via Custom Property as JSON string for stability."""
    obj[_USER_STEINERS_KEY] = json.dumps([[p[0], p[1]] for p in points])


def read_user_strokes(obj: bpy.types.Object) -> list[Stroke]:
    """Read obj['proscenio_user_strokes']; backward compat with legacy
    proscenio_user_steiners flat list (treated as kind='point' strokes).
    """
    payload = obj.get(_USER_STROKES_KEY)
    if payload is not None:
        try:
            data = json.loads(payload) if isinstance(payload, str) else list(payload)
        except (ValueError, TypeError):
            return []
        return _parse_strokes(data)
    # Legacy fallback: flat list of points -> wrap each as kind='point'
    legacy_points = read_user_steiners(obj)
    return [{"kind": "point", "points": [p]} for p in legacy_points]


def write_user_strokes(obj: bpy.types.Object, strokes: list[Stroke]) -> None:
    obj[_USER_STROKES_KEY] = json.dumps(
        [{"kind": s["kind"], "points": [[p[0], p[1]] for p in s["points"]]} for s in strokes]
    )


def _parse_strokes(data: object) -> list[Stroke]:
    if not isinstance(data, list):
        return []
    out: list[Stroke] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        if kind not in ("point", "stroke"):
            continue
        raw_pts = item.get("points")
        if not isinstance(raw_pts, list):
            continue
        pts: list[tuple[float, float]] = []
        for raw_pt in raw_pts:
            if not (isinstance(raw_pt, (list, tuple)) and len(raw_pt) == 2):
                continue
            try:
                pts.append((float(raw_pt[0]), float(raw_pt[1])))
            except (TypeError, ValueError):
                continue
        out.append({"kind": kind, "points": pts})
    return out


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
    """Final write: build_automesh + Wave 13.2-sidecar reproject.

    Forwards `output.user_steiners` to build_automesh's `extra_steiners`
    kwarg (PR #60) so the points the artist clicked during Stage 3
    (USER_STEINERS) land in the final mesh as additional CDT constraints.
    Without this wire the modal's Stage 3 placements were preview-only.

    output.inner_loops are NOT yet honored - build_automesh's
    _triangulate_into_bmesh accepts a single inner contour; multi-inner
    support is the next extension step (Wave 13.3 polish).
    """
    # Local import: keep this module importable when the skinning
    # bpy-helpers subpackage is unavailable (e.g. unit-test stubs).
    from ..skinning import maybe_post_regen_reproject, maybe_pre_regen_snapshot

    bone_segments = collect_bone_segments(armature) if armature is not None else None
    prior_sidecar = maybe_pre_regen_snapshot(obj, armature) if armature is not None else None
    world_scale = 1.0 / _resolve_pixels_per_unit(bpy.context)
    # output.user_steiners are stored in WORLD XZ (overlay draws in world
    # space). build_automesh's interior_points list is in MESH-LOCAL XZ
    # (matches outer_world's space - misleadingly named, see
    # pixel_contour_to_world docstring). Apply matrix_world.inverted()
    # to convert before forwarding, otherwise _merge_extra_steiners
    # filters them out via point_in_polygon(world_pt, local_polygon)
    # whenever obj.location != world origin.
    extra_steiners = _world_steiners_to_local(obj, output.user_steiners)
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
        extra_steiners=extra_steiners,
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


def _world_steiners_to_local(
    obj: bpy.types.Object, world_points: list[Point2D]
) -> list[Point2D] | None:
    """Inverse of _to_world_xz; converts user-Steiner world XZ to mesh-local XZ.

    Returns None for empty input so apply_mesh's `extra_steiners=` arg
    stays None (build_automesh treats None as "no extras"). When obj sits
    at world origin without rotation/scale, world == local and this is
    a no-op transform.
    """
    if not world_points:
        return None
    inv = obj.matrix_world.inverted()
    out: list[Point2D] = []
    for x, z in world_points:
        local = inv @ Vector((x, 0.0, z))
        out.append((local.x, local.z))
    return out


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


def _strokes_to_cdt_inputs(
    obj: bpy.types.Object,
    strokes: list[Stroke],
    outer_world_local: list[Point2D],
    outer_base_index: int,
    interior_base_index: int,
    interior_spacing: float,
) -> tuple[list[Point2D], list[tuple[int, int]]]:
    """Convert Stage 3 strokes to (extra_steiners_local, extra_edges).

    For each stroke:
    - kind='point': append point as single Steiner; no edges.
    - kind='stroke': append all resampled verts as Steiners. Build edges
      between consecutive Steiners. If endpoint snaps to an outer vert
      (within interior_spacing * 1.5), DROP that endpoint from extras
      and emit an edge from the next stroke vert to the outer vert
      index (outer_base_index + snap_index).

    Indices in the returned edges:
    - Non-snapped stroke verts get indices >= interior_base_index (allocated
      in append order)
    - Snapped endpoints reference outer_base_index + snap_index

    Coordinates are in MESH-LOCAL XZ (apply matrix_world.inverted()
    to each stroke point first; existing _world_steiners_to_local
    pattern).
    """
    from .stroke_geometry import snap_endpoint  # local to keep top clean
    inv = obj.matrix_world.inverted()
    extras_local: list[Point2D] = []
    edges: list[tuple[int, int]] = []

    def to_local(p: Point2D) -> Point2D:
        v = inv @ Vector((p[0], 0.0, p[1]))
        return (v.x, v.z)

    snap_radius = interior_spacing * 1.5

    for stroke in strokes:
        if stroke["kind"] == "point":
            for p in stroke["points"]:
                extras_local.append(to_local(p))
            continue
        # stroke kind
        pts_local = [to_local(p) for p in stroke["points"]]
        if not pts_local:
            continue
        # snap endpoints to outer
        start_snap = snap_endpoint(pts_local[0], outer_world_local, snap_radius)
        end_snap = snap_endpoint(pts_local[-1], outer_world_local, snap_radius)
        # decide which inner indices are stroke-allocated
        inner_pts = list(pts_local)
        if start_snap is not None and inner_pts:
            inner_pts = inner_pts[1:]
        if end_snap is not None and inner_pts:
            inner_pts = inner_pts[:-1]
        # allocate indices for the inner stroke verts
        allocated_start = interior_base_index + len(extras_local)
        allocated_indices = list(range(allocated_start, allocated_start + len(inner_pts)))
        extras_local.extend(inner_pts)
        # build edge sequence
        node_indices: list[int] = []
        if start_snap is not None:
            node_indices.append(outer_base_index + start_snap)
        node_indices.extend(allocated_indices)
        if end_snap is not None:
            node_indices.append(outer_base_index + end_snap)
        # skip strokes that collapsed entirely (both endpoints snapped to same outer)
        if len(node_indices) < 2:
            continue
        for i in range(len(node_indices) - 1):
            edges.append((node_indices[i], node_indices[i + 1]))
    return extras_local, edges
