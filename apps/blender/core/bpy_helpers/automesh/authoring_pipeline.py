"""Authoring pipeline dispatch (SPEC 013.2 interactive-modal, T10).

Per-stage compute helpers that bridge between pure modules and the
running modal operator. Final apply_mesh pipes through build_automesh
+ Wave 13.2-sidecar reproject so existing weights survive APPLY.
"""

from __future__ import annotations

import json
from collections.abc import Callable

import bpy
from mathutils import Vector

from ...automesh import (
    BoneSegment2D,
    arc_length_resample,
    binarize,
    compute_inner_loops,
    extract_outer_contour,
    interior_points_for_annulus,
    point_in_polygon,
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
_USER_OUTER_STROKES_KEY = "proscenio_user_outer_strokes"

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


def read_user_outer_strokes(obj: bpy.types.Object) -> list[Stroke]:
    """Read obj['proscenio_user_outer_strokes']; empty list when absent or corrupt.

    Reserved for Stage 2 (USER_OUTER). Capture logic comes in T6/T7; this
    helper is scaffolded here so the persistence key is registered and
    round-trip tests can verify it before capture is wired.
    """
    payload = obj.get(_USER_OUTER_STROKES_KEY)
    if payload is None:
        return []
    try:
        data = json.loads(payload) if isinstance(payload, str) else list(payload)
    except (ValueError, TypeError):
        return []
    return _parse_strokes(data)


def write_user_outer_strokes(obj: bpy.types.Object, strokes: list[Stroke]) -> None:
    """Persist Stage 2 (USER_OUTER) strokes as JSON string."""
    obj[_USER_OUTER_STROKES_KEY] = json.dumps(
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
        if kind not in ("point", "stroke", "cut"):
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

    Stage 3 strokes (output.user_strokes) become:
    - extra_steiners: resampled vert positions (mesh-local XZ)
    - extra_edges: constraint segments between consecutive stroke verts
      + endpoint snaps to outer contour verts

    Without this wire, Stage 3 strokes are preview-only.

    NOTE: pre-computes outer_world via compute_outer + matches build_automesh's
    internal `arc_length_resample(outer, target_contour_vertices)` so the
    snap-candidate count + interior_base_index match what build_automesh
    will produce. Without the resample match the indices would reference
    the raw walker output (~200 verts) while build_automesh ships a
    resampled outer (~64 verts), corrupting extra_edges. compute_outer is
    ~50ms; the extra resample is a few ms; APPLY is once per modal session.
    A future refactor could thread outer_world into build_automesh to avoid
    the double run entirely.
    """
    from ...automesh.outer_splice import splice_extend_strokes
    from ..skinning import maybe_post_regen_reproject, maybe_pre_regen_snapshot

    bone_segments = collect_bone_segments(armature) if armature is not None else None
    prior_sidecar = maybe_pre_regen_snapshot(obj, armature) if armature is not None else None
    world_scale = 1.0 / _resolve_pixels_per_unit(bpy.context)
    # Pre-compute outer for snap candidates + index layout.
    # CRITICAL: match build_automesh's internal arc_length_resample so the
    # index counts agree (raw walker output vs resampled outer differ).
    outer_world_raw = compute_outer(obj, image, params)

    # Split Stage 2 strokes by intent:
    # - kind="stroke" on user_outer_strokes = EXTEND (splice into outer).
    # - kind="cut" on user_outer_strokes = CUT (flows through existing cut pipeline).
    outer_extends: list[list[Point2D]] = []
    outer_cuts: list[Stroke] = []
    for s in output.user_outer_strokes:
        if s["kind"] == "stroke":
            outer_extends.append(list(s["points"]))
        else:
            outer_cuts.append(s)

    # Splice extend strokes into the raw walker outer (world XZ) pre-resample
    # so smoothing + resample applies uniformly to the extended polyline.
    outer_override_local: list[Point2D] | None = None
    if outer_extends:
        spliced_world = splice_extend_strokes(outer_world_raw, outer_extends)
        if spliced_world is not outer_world_raw:
            # Re-resample the spliced outer to params.contour_vertices (mesh-local)
            # matching what build_automesh does internally for the walker output.
            spliced_local_raw = [_world_to_local_xz(obj, p) for p in spliced_world]
            outer_override_local = list(
                arc_length_resample(spliced_local_raw, params.contour_vertices)
            )
            print(
                f"[apply_mesh] extend splice: {len(outer_extends)} stroke(s) applied; "
                f"raw outer {len(outer_world_raw)} -> spliced {len(spliced_world)} verts "
                f"-> resampled {len(outer_override_local)} mesh-local verts"
            )
        else:
            # All extend strokes were fully inside or outside - WARN each fully-outside one.
            for i, _stroke in enumerate(outer_extends):
                print(
                    f"[apply_mesh] WARNING: outer extend stroke {i} entirely outside "
                    f"silhouette or fully inside - cannot splice, stroke ignored"
                )

    # Use the spliced+resampled outer as outer_world_local when available;
    # otherwise fall back to the standard resample of the raw walker outer.
    if outer_override_local is not None:
        outer_world_local = outer_override_local
    else:
        outer_world_local_raw = [_world_to_local_xz(obj, p) for p in outer_world_raw]
        outer_world_local = list(
            arc_length_resample(outer_world_local_raw, params.contour_vertices)
        )

    outer_base_index = 0
    interior_base_index = len(outer_world_local)
    if params.inner_loop_count > 0:
        inner_loops = compute_inner_loops_for_stage(obj, image, outer_world_raw, params)
        if inner_loops:
            # build_automesh resamples the innermost loop to contour_vertices too
            interior_base_index += params.contour_vertices
    # Cut strokes from Stage 2 + all Stage 4 strokes flow through the standard cut pipeline.
    cut_and_interior_strokes: list[Stroke] = outer_cuts + list(output.user_strokes)
    extras_local, extra_edges, stroke_verts_dropped, cut_lenses = _strokes_to_cdt_inputs(
        obj,
        cut_and_interior_strokes,
        outer_world_local,
        outer_base_index=outer_base_index,
        interior_base_index=interior_base_index,
        interior_spacing=params.interior_spacing,
        inner_world_local=None,  # FUTURE: pass inner contour when inner_loops path is unified
        holes_world_local=None,  # FUTURE: pass hole contours; deferred to follow-up
    )
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
        outer_override=outer_override_local,
        extra_steiners=extras_local if extras_local else None,
        extra_edges=extra_edges if extra_edges else None,
        cut_lenses_local=cut_lenses if cut_lenses else None,
    )
    if stroke_verts_dropped > 0:
        counters["stroke_verts_dropped"] = stroke_verts_dropped
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


def _world_to_local_xz(obj: bpy.types.Object, world_pt: Point2D) -> Point2D:
    inv = obj.matrix_world.inverted()
    local = inv @ Vector((world_pt[0], 0.0, world_pt[1]))
    return (local.x, local.z)


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


def _to_local_xz(obj: bpy.types.Object) -> Callable[[Point2D], Point2D]:
    """Build a world-XZ -> mesh-local-XZ projector closed over obj.matrix_world.inverted()."""
    inv = obj.matrix_world.inverted()

    def project(p: Point2D) -> Point2D:
        v = inv @ Vector((p[0], 0.0, p[1]))
        return (v.x, v.z)

    return project


def _vert_inside_silhouette(
    point: Point2D,
    outer: list[Point2D],
    inner: list[Point2D] | None,
    holes: list[list[Point2D]] | None,
) -> bool:
    """Return True if point is inside the valid fill region.

    Valid region: inside outer polygon, outside inner polygon (if any),
    outside all hole polygons (if any). Mirrors the filter logic in
    _merge_extra_steiners but applied pre-index-allocation so indices
    in extra_edges stay consistent with the surviving extras list.
    """
    if not point_in_polygon(point, outer):
        return False
    if inner and point_in_polygon(point, inner):
        return False
    return not (holes and any(point_in_polygon(point, hole) for hole in holes))


def _emit_point_extras(
    points: list[Point2D],
    project: Callable[[Point2D], Point2D],
    extras_local: list[Point2D],
    outer: list[Point2D] | None = None,
    inner: list[Point2D] | None = None,
    holes: list[list[Point2D]] | None = None,
) -> int:
    """Append kind='point' stroke verts to extras (no edges).

    When outer is provided, silhouette-filters each vert before appending.
    Returns count of dropped verts.
    """
    dropped = 0
    for p in points:
        local = project(p)
        if outer is not None and not _vert_inside_silhouette(local, outer, inner, holes):
            dropped += 1
            continue
        extras_local.append(local)
    return dropped


def _build_stroke_node_indices(
    pts_local: list[Point2D],
    outer_world_local: list[Point2D],
    outer_base_index: int,
    interior_base_index: int,
    extras_local: list[Point2D],
    snap_radius: float,
    silhouette_outer: list[Point2D] | None = None,
    silhouette_inner: list[Point2D] | None = None,
    silhouette_holes: list[list[Point2D]] | None = None,
) -> tuple[list[int], int]:
    """For one kind='stroke' polyline, append surviving inner verts to
    extras_local and return (node_index_sequence, dropped_count).

    Endpoint snapping: when start or end falls within snap_radius of an
    outer contour vert, the stroke vert is DROPPED and the edge references
    the outer vert's index directly (avoids a duplicate co-located vert).

    Silhouette filter (AS-AM1): before allocating CDT indices, each inner
    vert is tested via _vert_inside_silhouette. Dropped verts are excluded
    from extras_local AND from the node index sequence. Edges are only
    emitted between consecutive SURVIVING positions, so a dropped middle
    vert splits the polyline into two independent edge runs (no edge spans
    the gap). Dropped endpoints likewise skip snap index allocation.
    """
    from ...automesh.stroke_geometry import snap_endpoint

    if not pts_local:
        return [], 0

    # Determine which verts survive the silhouette filter.
    # None mask = no filter (callers that don't pass silhouette_outer).
    def _keep(p: Point2D) -> bool:
        if silhouette_outer is None:
            return True
        return _vert_inside_silhouette(p, silhouette_outer, silhouette_inner, silhouette_holes)

    survivors_mask = [_keep(p) for p in pts_local]
    dropped = sum(1 for m in survivors_mask if not m)

    # Endpoint snap uses first/last SURVIVING positions.
    first_alive = next((i for i, m in enumerate(survivors_mask) if m), None)
    last_alive = next((i for i, m in reversed(list(enumerate(survivors_mask))) if m), None)

    if first_alive is None:
        # Every vert dropped - nothing to emit.
        return [], dropped

    start_snap = snap_endpoint(pts_local[first_alive], outer_world_local, snap_radius)
    end_snap = snap_endpoint(pts_local[last_alive], outer_world_local, snap_radius)

    # Allocate extras indices for inner surviving verts only.
    # A vert is "inner" if it is not snapped away (first/last alive that snapped).
    skip_first = start_snap is not None
    skip_last = end_snap is not None

    node_indices: list[int] = []
    if start_snap is not None:
        node_indices.append(outer_base_index + start_snap)

    for i, (pt, alive) in enumerate(zip(pts_local, survivors_mask, strict=False)):
        is_first_alive = i == first_alive and skip_first
        is_last_alive = i == last_alive and skip_last
        if is_first_alive or is_last_alive:
            # This position is claimed by the snap index; skip allocation.
            continue
        if not alive:
            # Dropped vert - no index pushed. The gap means _edges_from_node_indices
            # will not emit an edge spanning this position (the two surviving
            # neighbours are not consecutive in node_indices).
            continue
        idx = interior_base_index + len(extras_local)
        extras_local.append(pt)
        node_indices.append(idx)

    if end_snap is not None:
        node_indices.append(outer_base_index + end_snap)

    return node_indices, dropped


def _edges_from_node_indices(node_indices: list[int]) -> list[tuple[int, int]]:
    """Consecutive-pair edges, skipping self-edges (a == b).

    Self-edges happen when both endpoints snap to the same outer vert AND
    no inner stroke verts survive between them - CDT rejects self-edges
    and may destabilize, so emit nothing.
    """
    out: list[tuple[int, int]] = []
    for i in range(len(node_indices) - 1):
        a = node_indices[i]
        b = node_indices[i + 1]
        if a == b:
            continue
        out.append((a, b))
    return out


def _strokes_to_cdt_inputs(
    obj: bpy.types.Object,
    strokes: list[Stroke],
    outer_world_local: list[Point2D],
    outer_base_index: int,
    interior_base_index: int,
    interior_spacing: float,
    inner_world_local: list[Point2D] | None = None,
    holes_world_local: list[list[Point2D]] | None = None,
) -> tuple[list[Point2D], list[tuple[int, int]], int, list[list[Point2D]]]:
    """Convert Stage 3 strokes to (extra_steiners_local, extra_edges, dropped_count, cut_lenses).

    For each stroke:
    - kind='point': append point as single Steiner; no edges.
    - kind='stroke': append all resampled verts as Steiners. Build edges
      between consecutive Steiners. If endpoint snaps to an outer vert
      (within interior_spacing * 1.5), DROP that endpoint from extras
      and emit an edge from the next stroke vert to the outer vert
      index (outer_base_index + snap_index).
    - kind='cut': build 2 parallel offset polylines perpendicular to the
      stroke at each sample (each at +/- cut_half from the stroke centre).
      Both loops become CDT constraint edges with start/end caps closing
      the lens. The lens polygon (left_loop + right_loop reversed) is
      appended to cut_lenses for post-CDT face-prune.

    Silhouette filter (AS-AM1): each vert is tested BEFORE index allocation.
    Verts outside outer_world_local, inside inner_world_local, or inside any
    hole are dropped. extra_edges indices only reference surviving verts so
    stale indices never reach the CDT. dropped_count accumulates across all
    strokes and is surfaced to the operator for a WARNING report.

    Indices in the returned edges:
    - Non-snapped stroke verts get indices >= interior_base_index (allocated
      in append order among survivors only)
    - Snapped endpoints reference outer_base_index + snap_index

    Coordinates are in MESH-LOCAL XZ (apply matrix_world.inverted()
    to each stroke point first; existing _world_steiners_to_local
    pattern).

    cut_lenses (4th return value): list of lens polygons (each a list of
    Point2D) generated by kind='cut' strokes. Passed to build_automesh
    for post-CDT face-prune. Empty when no cut strokes exist.
    """
    from ...automesh.cut_geometry import lens_polygon, perpendicular_offsets

    project = _to_local_xz(obj)
    extras_local: list[Point2D] = []
    edges: list[tuple[int, int]] = []
    total_dropped = 0
    cut_lenses: list[list[Point2D]] = []
    snap_radius = interior_spacing * 1.5
    # cut_half: half of the cut width; T5 hardcodes to 15% of interior_spacing
    # (i.e. cut_width = interior_spacing * 0.3, half = * 0.15). T9 promotes
    # to a UI slider.
    cut_half = interior_spacing * 0.15

    for stroke in strokes:
        if stroke["kind"] == "point":
            dropped = _emit_point_extras(
                stroke["points"],
                project,
                extras_local,
                outer=outer_world_local,
                inner=inner_world_local,
                holes=holes_world_local,
            )
            total_dropped += dropped
            continue

        if stroke["kind"] == "cut":
            pts_local = [project(p) for p in stroke["points"]]
            # Silhouette-filter samples before building offset loops.
            surviving = [
                p
                for p in pts_local
                if _vert_inside_silhouette(
                    p, outer_world_local, inner_world_local, holes_world_local
                )
            ]
            dropped = len(pts_local) - len(surviving)
            total_dropped += dropped
            if len(surviving) < 2:
                continue
            left_loop, right_loop = perpendicular_offsets(surviving, half_width=cut_half)
            # Allocate CDT indices for both loops into extras_local.
            left_start = interior_base_index + len(extras_local)
            extras_local.extend(left_loop)
            right_start = interior_base_index + len(extras_local)
            extras_local.extend(right_loop)
            n_left = len(left_loop)
            n_right = len(right_loop)  # always == n_left
            # Left loop constraint edges (open polyline - not cyclic).
            for i in range(n_left - 1):
                edges.append((left_start + i, left_start + i + 1))
            # Right loop constraint edges (open polyline).
            for i in range(n_right - 1):
                edges.append((right_start + i, right_start + i + 1))
            # Cap edges: connect the two loops at start and end to close the lens.
            edges.append((left_start, right_start))
            edges.append((left_start + n_left - 1, right_start + n_right - 1))
            # Stash the lens polygon for post-CDT face-prune (orthogonal to
            # alpha-hole prune; processed separately in _triangulate_into_bmesh).
            cut_lenses.append(lens_polygon(left_loop, right_loop))
            continue

        # kind == "stroke"
        pts_local = [project(p) for p in stroke["points"]]
        if not pts_local:
            continue
        node_indices, dropped = _build_stroke_node_indices(
            pts_local,
            outer_world_local,
            outer_base_index,
            interior_base_index,
            extras_local,
            snap_radius,
            silhouette_outer=outer_world_local,
            silhouette_inner=inner_world_local,
            silhouette_holes=holes_world_local,
        )
        total_dropped += dropped
        if len(node_indices) < 2:
            continue
        edges.extend(_edges_from_node_indices(node_indices))
    return extras_local, edges, total_dropped, cut_lenses
