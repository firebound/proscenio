"""bpy-bound bridge for SPEC 013 automesh.

bpy-bound. Imports ``bpy`` + ``bmesh`` at module top. Lives in
``core/bpy_helpers/``.

Wraps the pure-Python pipeline from ``core.alpha_contour`` +
``core.automesh_geometry`` + ``core.automesh_density`` with the
bits that need real Blender data:

* Read ``bpy.types.Image.pixels`` (flat float RGBA array) into the
  int alpha grid the pure helpers consume - with downscale + clip
  + alpha-only extraction.
* Convert pixel-coordinate contours to world XZ units on the Y=0
  picture plane (Proscenio convention, SPEC 012 D11 axis lock).
* Build a ``bmesh.types.BMesh``: add the outer + inner contour
  vertices + interior Steiner points, lay down the cyclic edge
  pairs from :func:`core.automesh_geometry.build_annulus_edge_pairs`,
  call ``bmesh.ops.triangle_fill`` to triangulate the annulus.
* Preserve the original quad's 4 corner vertices via the
  ``proscenio_base_sprite`` vertex group (SPEC 013 D3) so re-runs
  only remove generated geometry, never the user-UV-pinned base.
* Write the resulting bmesh back to the active object's mesh.

The bridge does not own UX (no operator semantics, no panel
calls). Operator + panel live in their own modules and call
:func:`run_automesh` with already-resolved parameters.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

import bmesh

from ...automesh import (
    AlphaGrid,
    BoneSegment2D,
    Contour2D,
    arc_length_resample,
    extract_contours,
    filter_points_too_close_to_boundary,
    find_best_inner_rotation,
    interior_points_for_annulus,
    laplacian_smooth,
    point_in_polygon,
    to_float_contour,
)
from .base_sprite import (
    delete_non_base_geometry,
    initialize_base_sprite_group,
    remove_base_sprite_verts,
)
from .cdt import build_mesh_via_delaunay, delete_faces_inside_holes
from .debug import (
    clear_debug_objects,
    emit_bridges_debug,
    emit_contour_debug,
    emit_points_debug,
)
from .uv import stamp_uvs

if TYPE_CHECKING:
    from bpy.types import Bone, Image, Object


_SMOOTH_ITERATIONS = 3
"""Laplacian smoothing passes applied to each raw pixel contour
before triangulation. Three passes is the COA Tools 2 default and
empirically the sweet spot between staircase suppression and
silhouette drift."""


DebugStage = Literal[
    "off",
    "raw_contours",
    "smoothed",
    "resampled",
    "interior_points",
    "bridges",
    "fill_no_interior",
    "final",
]
"""Debug stages the operator can stop at + visualize.

Each non-``off`` stage runs the pipeline up to that point, emits
a companion wireframe object via ``automesh_debug``, and returns
early (no bmesh write into the active sprite). The user can step
through stages to pinpoint which step produced bad output.

``final`` matches ``off`` behavior except it clears any prior
debug companions for the sprite so reruns leave the scene clean.
"""


def _max_alpha_in_block(
    pixels: list[float],
    source_w: int,
    sx_start: int,
    sx_end: int,
    sy_start: int,
    sy_end: int,
) -> int:
    """Max alpha (0-255) over the source pixel rectangle ``[sx, sy)``.

    Inner loop of the conservative MAX downsample. Lifted into its
    own helper to keep ``read_alpha_grid`` itself a flat loop.
    """
    max_alpha = 0
    for sy in range(sy_start, sy_end):
        for sx in range(sx_start, sx_end):
            alpha = int(pixels[(sy * source_w + sx) * 4 + 3] * 255)
            if alpha > max_alpha:
                max_alpha = alpha
    return max_alpha


def read_alpha_grid(image: Image, downscale_factor: float) -> AlphaGrid:
    """Read an image's alpha channel into a downscaled int grid.

    ``downscale_factor`` matches the COA Tools 2 ``resolution``
    knob: 1.0 = full image resolution, 0.5 = half each axis (quarter
    pixel count), 0.25 = eighth pixel count. Downscale before
    contour tracing because pure-Python morphology + tracing scale
    quadratically with pixel count; the silhouette is recoverable
    from ~256x256 even for HD sprites.

    Conservative MAX downsample: each target cell = MAX alpha
    across all source pixels mapping to it (not NEAREST single
    sample). NEAREST would lose boundary pixels when the sampled
    source cell happens to be background while neighbors are
    foreground - silhouette shrinks inward by up to 1 downsampled
    cell (= 4 source pixels at downscale=0.25). MAX guarantees the
    silhouette expands by AT MOST 1 downsampled cell outward, acting
    as a built-in 1-pixel safety margin without the explicit margin
    setting. Caught in PR #51 smoke as "mesh boundary cuts inside
    the alpha" (user demand: never cut alpha).

    Y-flip on read: Blender ``image.pixels[]`` is stored bottom-up
    (OpenGL convention - ``pixels[0]`` is the visual BOTTOM-LEFT of
    the PIL-saved PNG). Downstream code treats ``grid[0]`` as the
    visual TOP (PIL convention), so the source-Y index is flipped
    on read. Without the flip the mesh silhouette ends up upside-
    down relative to the texture rendered on the sprite plane.

    Out-of-range ``downscale_factor`` raises ``ValueError`` so the
    operator's pre-flight surfaces a clear error message.
    """
    if not 0.0 < downscale_factor <= 1.0:
        raise ValueError(f"downscale_factor must be in (0, 1], got {downscale_factor}")
    source_w, source_h = image.size[0], image.size[1]
    if source_w <= 0 or source_h <= 0:
        raise ValueError(f"image has zero size ({source_w}x{source_h})")
    pixels = list(image.pixels[:])
    target_w = max(1, int(source_w * downscale_factor))
    target_h = max(1, int(source_h * downscale_factor))
    grid: AlphaGrid = [[0] * target_w for _ in range(target_h)]
    block_size = max(1, round(1.0 / downscale_factor))
    for target_y in range(target_h):
        flipped_target_y = target_h - 1 - target_y
        sy_start = min(int(flipped_target_y / downscale_factor), source_h - 1)
        sy_end = min(sy_start + block_size, source_h)
        row = grid[target_y]
        for target_x in range(target_w):
            sx_start = min(int(target_x / downscale_factor), source_w - 1)
            sx_end = min(sx_start + block_size, source_w)
            row[target_x] = _max_alpha_in_block(
                pixels, source_w, sx_start, sx_end, sy_start, sy_end
            )
    return grid


def pixel_contour_to_world(
    contour: Contour2D,
    downscale_factor: float,
    world_scale: float,
    source_width: int,
    source_height: int,
) -> Contour2D:
    """Convert pixel-coordinate contour to mesh-local XZ units.

    Pixel coordinates are (image-space x, image-space y) in the
    downscaled grid that the alpha walker produced. Output
    coordinates are mesh-local (X, Z) centered on the sprite's
    origin, ready to be written into the bmesh - when Blender then
    applies the object's location the contour lands aligned with
    the textured plane.

    Image Y grows downward in raster space; world Z grows upward in
    Blender's right-handed system - the conversion flips Y to Z
    with a sign change. ``world_scale`` converts pixel units to
    world units (typically ``1 / pixels_per_unit`` from the scene
    PG so the imported sprite matches its rendered scale).

    The centering subtracts half the sprite extent from each axis
    so pixel (0, 0) lands at mesh-local (-half_w, +half_h) - the
    top-left corner of a centered quad - rather than (0, 0). Without
    this the generated annulus sat in the bottom-right quadrant of
    the textured plane (regression caught during smoke validation).
    ``source_width`` / ``source_height`` are the original image
    dimensions (NOT the downscaled grid dimensions), matching how
    the textured plane was sized at fixture-author time.
    """
    if downscale_factor <= 0.0:
        raise ValueError(f"downscale_factor must be > 0, got {downscale_factor}")
    if world_scale <= 0.0:
        raise ValueError(f"world_scale must be > 0, got {world_scale}")
    if source_width <= 0 or source_height <= 0:
        raise ValueError(f"source dimensions must be positive, got {source_width}x{source_height}")
    factor = world_scale / downscale_factor
    half_w = source_width * world_scale / 2.0
    half_h = source_height * world_scale / 2.0
    # Place verts at the CENTER of each boundary cell, not the
    # left-top corner. The corner convention biased margins by side:
    # left/top got OUTWARD vert placement (margin), right/bottom got
    # INWARD placement (CUT into alpha). User caught this as "top
    # generous + bottom cuts" - asymmetric coverage.
    # Centering moves the vert half-cell inward from corner so all
    # 4 sides get symmetric ~half-cell-of-dilation margin.
    half_cell = factor / 2.0
    return [
        (x * factor - half_w + half_cell, half_h - y * factor - half_cell) for (x, y) in contour
    ]


def collect_bone_segments(
    armature_obj: Object,
) -> list[BoneSegment2D]:
    """Extract bone segments as world-space XZ-plane pairs.

    Walks ``armature_obj.data.edit_bones`` (or ``bones`` when not in
    Edit Mode) and emits ``((head_x, head_z), (tail_x, tail_z))`` for
    each deform-flagged bone. Y components are dropped since
    Proscenio bones live on the Y=0 picture plane per SPEC 012
    convention.

    Head / tail are transformed by ``armature_obj.matrix_world`` so
    the segments live in the same world space as the sprite contours
    that the density helper compares them against. Without this, the
    density-under-bones path silently misaligns whenever the armature
    has any object-level transform (location, rotation, scale) - the
    sprite's contour points are world-space, the bones would be in
    armature-local space, and they'd never line up.
    """
    armature_data = armature_obj.data
    matrix_world = armature_obj.matrix_world
    bones: Sequence[Bone] = (
        armature_data.edit_bones
        if hasattr(armature_data, "edit_bones") and armature_data.edit_bones
        else armature_data.bones
    )
    segments: list[BoneSegment2D] = []
    for bone in bones:
        if not bone.use_deform:
            continue
        head_world = matrix_world @ bone.head
        tail_world = matrix_world @ bone.tail
        segments.append(((head_world.x, head_world.z), (tail_world.x, tail_world.z)))
    return segments


def _debug_stage_report(
    stage: DebugStage,
    outer_count: int,
    inner_count: int,
    interior_count: int = 0,
    bridge_offset: int | None = None,
    total_verts: int | None = None,
    total_faces: int | None = None,
) -> dict[str, int]:
    """Build the counter dict the operator surfaces after a debug stop.

    Reuses the same key shape as the normal ``build_automesh``
    return so the operator's INFO formatter has one code path,
    plus a ``debug_stage`` marker the operator surfaces in the
    user-facing report.
    """
    report: dict[str, int] = {
        "outer_verts": outer_count,
        "inner_verts": inner_count,
        "interior_verts": interior_count,
        "total_verts": total_verts if total_verts is not None else 0,
        "total_faces": total_faces if total_faces is not None else 0,
    }
    # Encode stage label by stuffing the enum index - keeps the
    # dict[str, int] signature so existing call sites stay typed.
    # Operator reads the literal string back via _STAGE_INDEX.
    report["_debug_stage_index"] = _STAGE_INDEX[stage]
    if bridge_offset is not None:
        report["bridge_offset"] = bridge_offset
    return report


_STAGE_INDEX: dict[DebugStage, int] = {
    "off": 0,
    "raw_contours": 1,
    "smoothed": 2,
    "resampled": 3,
    "interior_points": 4,
    "bridges": 5,
    "fill_no_interior": 6,
    "final": 7,
}
# Reverse map - the operator uses this to decode the integer index
# the bridge stashes in the counters dict back into a human-readable
# stage label for the INFO report. Looks unused from inside this
# module (CodeQL flagged it) but is part of the bridge's public
# surface; deleting it breaks the operator import.
_STAGE_BY_INDEX: dict[int, DebugStage] = {value: key for key, value in _STAGE_INDEX.items()}


def _log_begin(
    obj: Object,
    image: Image,
    downscale_factor: float,
    alpha_threshold: int,
    margin_pixels: int,
    target_contour_vertices: int,
    interior_spacing: float,
    bone_segments: list[BoneSegment2D] | None,
    debug_stage: DebugStage,
) -> None:
    print(
        f"[automesh] === BEGIN obj={obj.name} image={image.name} "
        f"{image.size[0]}x{image.size[1]} downscale={downscale_factor} "
        f"alpha_threshold={alpha_threshold} margin_pixels={margin_pixels} "
        f"contour_vertices={target_contour_vertices} "
        f"interior_spacing={interior_spacing} "
        f"density_under_bones={'yes' if bone_segments else 'no'} "
        f"debug_stage={debug_stage}"
    )


def _read_alpha_and_extract_contours(
    image: Image,
    downscale_factor: float,
    alpha_threshold: int,
    margin_pixels: int,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]], list[list[tuple[int, int]]]]:
    """Read alpha grid + extract outer / inner / hole pixel contours.

    Encapsulates the alpha-grid read + contour extraction with the
    margin scaling rule (source-pixel margin -> downscaled-grid
    kernel size). Raises ``ValueError`` when the outer contour is
    too short to triangulate.
    """
    alpha_grid = read_alpha_grid(image, downscale_factor)
    grid_h = len(alpha_grid)
    grid_w = len(alpha_grid[0]) if grid_h else 0
    nonzero = sum(1 for row in alpha_grid for px in row if px > 0)
    above_thr = sum(1 for row in alpha_grid for px in row if px > alpha_threshold)
    print(
        f"[automesh] alpha_grid {grid_w}x{grid_h} cells "
        f"nonzero={nonzero} above_threshold({alpha_threshold})={above_thr}"
    )
    # margin_pixels is expressed in SOURCE image pixels so the user's
    # mental model matches what they author in Photoshop / Pillow.
    # Scale by downscale_factor so margin=5 + downscale=0.25 still
    # corresponds to ~5 source pixels and not 5 grid cells (= 20
    # source pixels). Regression caught in PR #51 smoke.
    grid_margin = max(0, round(margin_pixels * downscale_factor))
    outer_pixels, inner_pixels, hole_pixels = extract_contours(
        alpha_grid, alpha_threshold, grid_margin
    )
    # SPEC 013 D2 amendment: hole contours feed CDT as additional
    # constraint loops so the mesh excludes alpha holes. Proscenio
    # differentiates from Spine + COA Tools 2 here - both refuse
    # to support holes.
    print(
        f"[automesh] contour_pair grid_margin={grid_margin} "
        f"outer_pixels={len(outer_pixels)} inner_pixels={len(inner_pixels)} "
        f"holes={len(hole_pixels)} ({[len(h) for h in hole_pixels]})"
    )
    if len(outer_pixels) < 3:
        raise ValueError(
            "automesh outer contour too short - try lowering the alpha "
            "threshold or increasing the resolution"
        )
    return outer_pixels, inner_pixels, hole_pixels


def _to_world_space(
    outer_pixels: list[tuple[int, int]],
    inner_pixels: list[tuple[int, int]],
    hole_pixels: list[list[tuple[int, int]]],
    downscale_factor: float,
    world_scale: float,
    source_width: int,
    source_height: int,
) -> tuple[Contour2D, Contour2D, list[Contour2D]]:
    """Convert all pixel-space contours to world-space."""
    outer_world_raw = pixel_contour_to_world(
        to_float_contour(outer_pixels),
        downscale_factor,
        world_scale,
        source_width,
        source_height,
    )
    if outer_world_raw:
        xs = [p[0] for p in outer_world_raw]
        ys = [p[1] for p in outer_world_raw]
        print(
            f"[automesh] outer_world_raw bbox "
            f"x=[{min(xs):.4f},{max(xs):.4f}] z=[{min(ys):.4f},{max(ys):.4f}] "
            f"first={outer_world_raw[0]} last={outer_world_raw[-1]}"
        )
    inner_world_raw: Contour2D = []
    if len(inner_pixels) >= 3:
        inner_world_raw = pixel_contour_to_world(
            to_float_contour(inner_pixels),
            downscale_factor,
            world_scale,
            source_width,
            source_height,
        )
    holes_world_raw: list[Contour2D] = [
        pixel_contour_to_world(
            to_float_contour(h),
            downscale_factor,
            world_scale,
            source_width,
            source_height,
        )
        for h in hole_pixels
        if len(h) >= 3
    ]
    return outer_world_raw, inner_world_raw, holes_world_raw


def _smooth_and_resample(
    outer_world_raw: Contour2D,
    inner_world_raw: Contour2D,
    holes_world_raw: list[Contour2D],
    target_contour_vertices: int,
) -> tuple[Contour2D, Contour2D, list[Contour2D]]:
    """Apply Laplacian smoothing (inner only) + arc-length resample.

    Outer + holes skip smoothing because Laplacian shrinks convex
    corners inward by ~1 px per pass, which would cut alpha at the
    silhouette / bleed mesh over transparent at hole edges.
    Inner contour smooths because it is the eroded version of the
    silhouette and the inward shrink is desired there.

    Hole target vert count scales as outer/4 with a minimum of 8 so
    tiny holes still produce reasonable triangles.
    """
    outer_smoothed = outer_world_raw
    inner_smoothed = (
        laplacian_smooth(inner_world_raw, _SMOOTH_ITERATIONS) if inner_world_raw else []
    )
    outer_world = arc_length_resample(outer_smoothed, target_contour_vertices)
    inner_world: Contour2D = (
        arc_length_resample(inner_smoothed, target_contour_vertices) if inner_smoothed else []
    )
    hole_target = max(8, target_contour_vertices // 4)
    holes_world: list[Contour2D] = [
        arc_length_resample(raw, hole_target) for raw in holes_world_raw
    ]
    print(
        f"[automesh] resampled outer={len(outer_world)} inner={len(inner_world)} "
        f"holes_total_verts={sum(len(h) for h in holes_world)} "
        f"target={target_contour_vertices}"
    )
    return outer_world, inner_world, holes_world


def _compute_steiner_points(
    outer_world: Contour2D,
    inner_world: Contour2D,
    holes_world: list[Contour2D],
    interior_spacing: float,
    bone_segments: list[BoneSegment2D] | None,
    bone_density_radius: float,
    bone_density_factor: int,
    exclude_zones: list[tuple[float, float, float]] | None = None,
) -> list[tuple[float, float]]:
    """Generate + filter Steiner interior points.

    Three-step funnel:

    1. ``interior_points_for_annulus`` produces a candidate grid
       (uniform OR bone-clustered when picker armature is set).
       ``inner_world`` is passed so the helper skips points inside
       the inner ring when the user opted into the annulus topology
       (margin_pixels > 0); without it, points inside the ring
       would survive into CDT only to become loose verts after the
       inner ring's hole exclusion (regression flagged in PR #52
       review). When ``inner_world`` is empty (margin_pixels = 0,
       default), the helper treats the whole outer interior as fair
       game - unchanged behavior.
    2. Points falling inside any detected alpha hole are dropped -
       CDT excludes the hole region, so a Steiner there would
       become a loose vertex with no incident face.
    3. Points within half-spacing of any boundary vert are dropped
       to avoid CDT phantom-vert duplication.
    """
    interior_points = interior_points_for_annulus(
        outer_world,
        inner_world,
        interior_spacing,
        bone_segments=bone_segments,
        bone_density_radius=bone_density_radius,
        bone_density_factor=bone_density_factor,
        exclude_zones=exclude_zones,
    )
    if holes_world:
        before_hole_filter = len(interior_points)
        interior_points = [
            point
            for point in interior_points
            if not any(point_in_polygon(point, hole) for hole in holes_world)
        ]
        print(
            f"[automesh] interior_points dropped_inside_holes="
            f"{before_hole_filter - len(interior_points)} "
            f"(of {before_hole_filter})"
        )
    boundary_for_filter = list(outer_world) + list(inner_world)
    min_separation = max(interior_spacing * 0.5, 1e-3)
    before_filter = len(interior_points)
    interior_points = filter_points_too_close_to_boundary(
        interior_points, boundary_for_filter, min_separation
    )
    print(
        f"[automesh] interior_points generated={before_filter} "
        f"kept_after_filter={len(interior_points)} "
        f"min_separation={min_separation:.4f}"
    )
    return interior_points


def _merge_extra_steiners(
    auto_interior: list[tuple[float, float]],
    extra_steiners: list[tuple[float, float]],
    outer_world: Contour2D,
    inner_world: Contour2D,
    holes_world: list[Contour2D],
) -> list[tuple[float, float]]:
    """Merge user-placed Steiner points into the auto-computed interior.

    Filters extras the same way `_compute_steiner_points` filters the
    auto grid: drop anything outside the outer silhouette, drop anything
    inside the inner annulus ring (excluded from CDT fill, so a vert
    there would become a loose vertex with no incident face), drop
    anything inside an alpha hole. Skips the half-spacing boundary
    check because the user explicitly placed these (they may want a
    point near the silhouette edge for joint-cover deformation control).

    Used by the interactive modal authoring operator to forward the
    points the artist clicked during Stage 3 (USER_STEINERS) into the
    final mesh at Stage 5 (APPLY).
    """
    accepted: list[tuple[float, float]] = []
    late_dropped = 0
    for point in extra_steiners:
        if not point_in_polygon(point, outer_world):
            late_dropped += 1
            continue
        if inner_world and point_in_polygon(point, inner_world):
            late_dropped += 1
            continue
        if any(point_in_polygon(point, hole) for hole in holes_world):
            late_dropped += 1
            continue
        accepted.append(point)
    if late_dropped:
        print(
            f"[automesh] WARNING: _merge_extra_steiners dropped {late_dropped} late-stage "
            f"vert(s) - caller should pre-filter (see AS-AM1)"
        )
    return list(auto_interior) + accepted


def _apply_rip_to_bmesh(
    bm: bmesh.types.BMesh,
    rip_edge_pairs: list[tuple[int, int]],
    input_to_bm: dict[int, bmesh.types.BMVert],
) -> None:
    """Resolve rip-edge pairs to bmesh edges and call split_edges.

    For each ``(a_idx, b_idx)`` in ``rip_edge_pairs``, look up the BMVert
    for each input index in ``input_to_bm``, then find the BMEdge connecting
    them via ``bm.edges.get``. Collected edges are passed to
    ``bmesh.ops.split_edges`` which duplicates the shared verts at each edge
    so the two sides become topologically independent (Blender V / Rip
    Vertices behavior). No mesh area is removed.

    Cut-margin perpendicular translation is deferred to v2: in v1 the split
    produces co-located duplicate verts (margin=0 always). The UI slider
    (authoring_cut_margin) is wired in StageParams but unused in this path.
    """
    bm.edges.ensure_lookup_table()
    rip_bmesh_edges: list[bmesh.types.BMEdge] = []
    for a_idx, b_idx in rip_edge_pairs:
        bv_a = input_to_bm.get(a_idx)
        bv_b = input_to_bm.get(b_idx)
        if bv_a is None or bv_b is None:
            continue
        edge = bm.edges.get((bv_a, bv_b))
        if edge is not None:
            rip_bmesh_edges.append(edge)
    if not rip_bmesh_edges:
        print("[automesh] rip: no matching edges found in bmesh for rip_edge_pairs")
        return
    bmesh.ops.split_edges(bm, edges=rip_bmesh_edges)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    print(f"[automesh] rip_split applied to {len(rip_bmesh_edges)} edge(s)")


def _triangulate_into_bmesh(
    obj: Object,
    outer_world: Contour2D,
    inner_world: Contour2D,
    interior_points: list[tuple[float, float]],
    holes_world: list[Contour2D],
    extra_edges: list[tuple[int, int]] | None = None,
    cut_lenses: list[list[tuple[float, float]]] | None = None,
    rip_edge_pairs: list[tuple[int, int]] | None = None,
) -> tuple[int, object]:
    """Run CDT into a bmesh + apply hole-face post-prune + optional rip.

    Returns ``(base_group_index, bm)`` so the orchestrator can
    decide whether to commit the bmesh (final path) or write +
    free without finalize (debug fill_no_interior).

    Three independent post-CDT passes run in sequence:
    1. Alpha-hole prune: faces whose centroid falls inside any alpha
       hole contour (holes_world). Unchanged from pre-AS-AM7 behaviour.
    2. Cut-lens prune: faces whose centroid falls inside any cut lens
       polygon (cut_lenses from Stage 2 outer kind='cut' strokes).
       Orthogonal to pass 1 - different polygon sets, same helper.
    3. Rip pass: Stage 4 kind='cut' strokes: split_edges on the bmesh
       edges that materialized the stroke constraint. Verts are
       duplicated so each side deforms independently; NO mesh area
       is removed (AS-AM7-REV behavior).
    """
    base_group_index, _is_fresh = initialize_base_sprite_group(obj)
    delete_non_base_geometry(obj, base_group_index)
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    _face_count, input_to_bm = build_mesh_via_delaunay(
        bm,
        outer_world,
        inner_world,
        interior_points,
        holes_world,
        extra_edges=extra_edges,
    )
    if holes_world:
        # CDT's automatic hole detection is unreliable against the
        # bridge's Y-flip orientation flow; the centroid post-prune
        # is the deterministic fallback (see cdt.py).
        delete_faces_inside_holes(bm, holes_world)
    if cut_lenses:
        # Separate pass: remove faces inside cut-stroke lens polygons.
        # Intentionally kept apart from the alpha-hole pass so the two
        # polygon sets never interfere with each other.
        n_pruned = delete_faces_inside_holes(bm, cut_lenses)
        print(
            f"[automesh] cut_lens_prune removed {n_pruned} face(s) "
            f"across {len(cut_lenses)} lens(es)"
        )
    if rip_edge_pairs:
        # Stage 4 kind='cut' rip pass: split_edges on constraint-materialized
        # edges. Uses input_to_bm from build_mesh_via_delaunay to resolve
        # input indices to BMVerts without coordinate searching.
        _apply_rip_to_bmesh(bm, rip_edge_pairs, input_to_bm)
    return base_group_index, bm


def _finalize_mesh(
    obj: Object,
    bm: object,
    base_group_index: int,
    source_width: int,
    source_height: int,
    world_scale: float,
    preserve_base_quad: bool,
) -> None:
    """Commit bmesh to mesh + stamp UVs + drop base sprite verts."""
    mesh = obj.data
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))  # type: ignore[attr-defined]
    bm.to_mesh(mesh)  # type: ignore[attr-defined]
    bm.free()  # type: ignore[attr-defined]
    stamp_uvs(mesh, source_width, source_height, world_scale)
    if not preserve_base_quad:
        remove_base_sprite_verts(obj, base_group_index)
    mesh.update()
    print(f"[automesh] === END mesh now has {len(mesh.vertices)} verts, {len(mesh.polygons)} faces")


def build_automesh(
    obj: Object,
    image: Image,
    *,
    downscale_factor: float,
    alpha_threshold: int,
    margin_pixels: int,
    target_contour_vertices: int,
    interior_spacing: float,
    world_scale: float,
    bone_segments: list[BoneSegment2D] | None = None,
    bone_density_radius: float = 0.0,
    bone_density_factor: int = 1,
    debug_stage: DebugStage = "off",
    preserve_base_quad: bool = False,
    outer_override: list[tuple[float, float]] | None = None,
    extra_steiners: list[tuple[float, float]] | None = None,
    extra_edges: list[tuple[int, int]] | None = None,
    cut_lenses_local: list[list[tuple[float, float]]] | None = None,
    rip_edge_pairs: list[tuple[int, int]] | None = None,
) -> dict[str, int]:
    """Generate the annulus mesh on ``obj`` from ``image`` alpha.

    Replaces any previously generated automesh geometry while
    preserving vertices flagged in the ``proscenio_base_sprite``
    group (D3). Returns counters the operator surfaces in the
    INFO report: ``{"outer_verts", "inner_verts", "interior_verts",
    "total_verts", "total_faces"}``.

    When ``debug_stage`` is non-``off``, the pipeline runs up to
    that stage, emits a companion wireframe object into the
    ``Proscenio.Debug`` collection, then returns early without
    touching the active mesh. The counters dict carries
    ``{"debug_stage": <name>, "debug_outer_verts": N, ...}`` so
    the operator surfaces the snapshot in the INFO report.

    Raises ``ValueError`` when the alpha silhouette is empty or
    the image cannot be sampled - the operator pre-flight catches
    these before getting here so the user sees an actionable
    message rather than a stack trace.
    """
    if debug_stage in ("off", "final"):
        clear_debug_objects(obj)
    _log_begin(
        obj,
        image,
        downscale_factor,
        alpha_threshold,
        margin_pixels,
        target_contour_vertices,
        interior_spacing,
        bone_segments,
        debug_stage,
    )

    outer_pixels, inner_pixels, hole_pixels = _read_alpha_and_extract_contours(
        image, downscale_factor, alpha_threshold, margin_pixels
    )
    source_width, source_height = image.size[0], image.size[1]
    outer_world_raw, inner_world_raw, holes_world_raw = _to_world_space(
        outer_pixels,
        inner_pixels,
        hole_pixels,
        downscale_factor,
        world_scale,
        source_width,
        source_height,
    )
    if debug_stage == "raw_contours":
        emit_contour_debug(obj, "raw_contours", outer_world_raw, inner_world_raw)
        return _debug_stage_report("raw_contours", len(outer_world_raw), len(inner_world_raw))

    outer_world, inner_world, holes_world = _smooth_and_resample(
        outer_world_raw, inner_world_raw, holes_world_raw, target_contour_vertices
    )
    # AS-AM10: when apply_mesh has already spliced + resampled the outer contour
    # (extend strokes), use that override directly instead of the walker output.
    # Inner contour + holes still derive from the alpha walker unchanged.
    if outer_override is not None:
        outer_world = list(outer_override)
        print(
            f"[automesh] outer_override applied: {len(outer_world)} verts "
            f"(replaces walker-resampled outer)"
        )
    if debug_stage == "smoothed":
        # Smoothed = post-Laplacian, pre-resample. Snapshot the
        # intermediate state by re-running Laplacian without resample.
        outer_smoothed = outer_world_raw
        inner_smoothed = (
            laplacian_smooth(inner_world_raw, _SMOOTH_ITERATIONS) if inner_world_raw else []
        )
        emit_contour_debug(obj, "smoothed", outer_smoothed, inner_smoothed)
        return _debug_stage_report("smoothed", len(outer_smoothed), len(inner_smoothed))
    if debug_stage == "resampled":
        emit_contour_debug(obj, "resampled", outer_world, inner_world)
        return _debug_stage_report("resampled", len(outer_world), len(inner_world))

    exclude_zones: list[tuple[float, float, float]] | None = None
    if extra_steiners:
        exclude_zones = [(p[0], p[1], interior_spacing * 0.5) for p in extra_steiners]
    interior_points = _compute_steiner_points(
        outer_world,
        inner_world,
        holes_world,
        interior_spacing,
        bone_segments,
        bone_density_radius,
        bone_density_factor,
        exclude_zones=exclude_zones,
    )
    if extra_steiners:
        interior_points = _merge_extra_steiners(
            interior_points, extra_steiners, outer_world, inner_world, holes_world
        )
    if debug_stage == "interior_points":
        emit_points_debug(obj, "interior_points", interior_points)
        return _debug_stage_report(
            "interior_points",
            len(outer_world),
            len(inner_world),
            interior_count=len(interior_points),
        )

    bridge_offset = find_best_inner_rotation(outer_world, inner_world)
    if debug_stage == "bridges":
        emit_bridges_debug(obj, "bridges", outer_world, inner_world, bridge_offset)
        return _debug_stage_report(
            "bridges", len(outer_world), len(inner_world), bridge_offset=bridge_offset
        )

    base_group_index, bm = _triangulate_into_bmesh(
        obj,
        outer_world,
        inner_world,
        interior_points,
        holes_world,
        extra_edges=extra_edges,
        cut_lenses=cut_lenses_local,
        rip_edge_pairs=rip_edge_pairs,
    )
    if debug_stage == "fill_no_interior":
        mesh = obj.data
        bm.to_mesh(mesh)  # type: ignore[attr-defined]
        bm.free()  # type: ignore[attr-defined]
        mesh.update()
        return _debug_stage_report(
            "fill_no_interior",
            len(outer_world),
            len(inner_world),
            total_verts=len(mesh.vertices),
            total_faces=len(mesh.polygons),
        )

    _finalize_mesh(
        obj, bm, base_group_index, source_width, source_height, world_scale, preserve_base_quad
    )
    mesh = obj.data
    return {
        "outer_verts": len(outer_world),
        "inner_verts": len(inner_world),
        # Interior count = Steiner points that survived hole + boundary
        # filters. The Delaunay pass may absorb / merge some near-
        # boundary; len(interior_points) is the input count, not the
        # final mesh count - good enough for the INFO report.
        "interior_verts": len(interior_points),
        "total_verts": len(mesh.vertices),
        "total_faces": len(mesh.polygons),
    }
