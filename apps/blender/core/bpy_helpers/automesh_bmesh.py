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

import contextlib
from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

import bmesh

from ..alpha_contour import (
    AlphaGrid,
    extract_contour_pair,
)
from ..automesh_density import (
    BoneSegment2D,
    interior_points_for_annulus,
)
from ..automesh_geometry import (
    Contour2D,
    arc_length_resample,
    find_best_inner_rotation,
    laplacian_smooth,
    to_float_contour,
)
from .automesh_debug import (
    clear_debug_objects,
    emit_bridges_debug,
    emit_contour_debug,
    emit_points_debug,
)

if TYPE_CHECKING:
    from bpy.types import Bone, Image, Object


BASE_SPRITE_GROUP_NAME = "proscenio_base_sprite"
"""Vertex group flagged on the original 4 quad corners so automesh
regen knows which verts to preserve. Lifted from COA Tools 2's
``coa_base_sprite`` pattern per SPEC 013 D3."""


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


def read_alpha_grid(image: Image, downscale_factor: float) -> AlphaGrid:
    """Read an image's alpha channel into a downscaled int grid.

    ``downscale_factor`` matches the COA Tools 2 ``resolution``
    knob: 1.0 = full image resolution, 0.5 = half each axis (quarter
    pixel count), 0.25 = eighth pixel count. Downscale before
    contour tracing because pure-Python morphology + tracing scale
    quadratically with pixel count; the silhouette is recoverable
    from ~256x256 even for HD sprites.

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
    for target_y in range(target_h):
        source_y = min(int(target_y / downscale_factor), source_h - 1)
        row = grid[target_y]
        for target_x in range(target_w):
            source_x = min(int(target_x / downscale_factor), source_w - 1)
            alpha_index = (source_y * source_w + source_x) * 4 + 3
            row[target_x] = int(pixels[alpha_index] * 255)
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
    return [(x * factor - half_w, half_h - y * factor) for (x, y) in contour]


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


def _initialize_base_sprite_group(obj: Object) -> tuple[int, bool]:
    """Ensure ``proscenio_base_sprite`` exists; flag current verts only on first run.

    Returns ``(group_index, is_fresh)``. ``is_fresh`` is True when the
    group did not exist before this call - meaning every vertex
    currently on the mesh is part of the original UV-pinned base + we
    flag them all so the regen-delete step preserves them.

    On subsequent runs (group already present) we do NOT re-flag the
    current verts. The previously-generated automesh geometry already
    sits in the mesh; flagging it now would promote it to "base" and
    the next ``_delete_non_base_geometry`` call would skip it,
    causing the mesh to accumulate vertices unbounded across reruns
    (regression caught in PR #51 review).
    """
    group = obj.vertex_groups.get(BASE_SPRITE_GROUP_NAME)
    if group is not None:
        return group.index, False
    group = obj.vertex_groups.new(name=BASE_SPRITE_GROUP_NAME)
    mesh = obj.data
    indices = list(range(len(mesh.vertices)))
    if indices:
        group.add(indices, 1.0, "REPLACE")
    return group.index, True


def _delete_non_base_geometry(obj: Object, group_index: int) -> None:
    """Remove every vertex NOT in the base-sprite group from the mesh.

    Used as the first step of a regen so the original 4 quad
    corners survive while everything automesh generated is wiped.
    Goes through bmesh because plain ``mesh.vertices`` does not
    support per-vertex removal cleanly.
    """
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    deform_layer = bm.verts.layers.deform.verify()
    to_remove = [
        vert
        for vert in bm.verts
        if group_index not in vert[deform_layer] or vert[deform_layer].get(group_index, 0.0) <= 0.0
    ]
    bmesh.ops.delete(bm, geom=to_remove, context="VERTS")
    bm.to_mesh(mesh)
    bm.free()


def _point_in_triangle_xz(
    px: float,
    pz: float,
    ax: float,
    az: float,
    bx: float,
    bz: float,
    cx: float,
    cz: float,
) -> bool:
    """Half-plane test for a point against an XZ triangle.

    Returns True for the closed triangle (boundary included). Pure
    math, no numpy. Used by :func:`_insert_interior_points` to find
    which triangle of the just-triangulated annulus contains each
    Steiner point before splitting that triangle around the point.
    """

    def sign(p1x: float, p1z: float, p2x: float, p2z: float, p3x: float, p3z: float) -> float:
        return (p1x - p3x) * (p2z - p3z) - (p2x - p3x) * (p1z - p3z)

    d1 = sign(px, pz, ax, az, bx, bz)
    d2 = sign(px, pz, bx, bz, cx, cz)
    d3 = sign(px, pz, cx, cz, ax, az)
    has_neg = d1 < 0.0 or d2 < 0.0 or d3 < 0.0
    has_pos = d1 > 0.0 or d2 > 0.0 or d3 > 0.0
    return not (has_neg and has_pos)


def _insert_interior_points(
    bm: bmesh.types.BMesh,
    interior_points: list[tuple[float, float]],
) -> int:
    """Split annulus triangles to incorporate Steiner points.

    For each ``(x, z)`` in ``interior_points``, locate the triangle
    in the bmesh whose XZ projection contains the point + split it
    into three triangles fanned around a new center vertex created
    at ``(x, 0.0, z)``. Returns the count of successfully inserted
    points (some may fall outside every triangle due to float drift
    or annulus boundary inconsistency - those are silently skipped
    so the operator never raises mid-build).
    """
    inserted = 0
    bm.faces.ensure_lookup_table()
    for px, pz in interior_points:
        target_face = None
        for face in bm.faces:
            if len(face.verts) != 3:
                continue
            v0, v1, v2 = face.verts
            if _point_in_triangle_xz(px, pz, v0.co.x, v0.co.z, v1.co.x, v1.co.z, v2.co.x, v2.co.z):
                target_face = face
                break
        if target_face is None:
            continue
        v0, v1, v2 = list(target_face.verts)
        new_vert = bm.verts.new((px, 0.0, pz))
        bm.faces.remove(target_face)
        try:
            bm.faces.new((v0, v1, new_vert))
            bm.faces.new((v1, v2, new_vert))
            bm.faces.new((v2, v0, new_vert))
            inserted += 1
        except ValueError:
            # bm.faces.new raises ValueError when the face already
            # exists. Defensive: skip the duplicate; the new vert
            # remains as a loose vertex in this rare path (less
            # bad than crashing the operator).
            pass
        bm.faces.ensure_lookup_table()
    return inserted


def _build_annulus_strip(
    bm: bmesh.types.BMesh,
    outer_verts: list[bmesh.types.BMVert],
    inner_verts: list[bmesh.types.BMVert],
    bridge_offset: int,
) -> None:
    """Build N cells of 2 triangles each across the outer/inner ring.

    Cell i connects outer[i], outer[(i+1) % N], inner[i + offset],
    inner[(i+1) % N + offset] - 4 verts forming a trapezoid. Each
    trapezoid splits into two triangles along the outer[i+1]->
    inner[i + offset] diagonal. Result: 2N triangles forming a
    clean strip annulus, no orientation ambiguity, no triangulator
    misdetection of the inner ring as a fillable face.

    Defensive: ``bm.faces.new`` raises ``ValueError`` if the face
    already exists or if verts are collinear. We swallow + continue
    so a single bad cell does not abort the whole strip.
    """
    n = len(outer_verts)
    if n == 0 or n != len(inner_verts):
        return
    normalized_offset = bridge_offset % n
    for i in range(n):
        next_i = (i + 1) % n
        inner_curr = (i + normalized_offset) % n
        inner_next = (next_i + normalized_offset) % n
        # Triangle 1: outer[i] -> outer[next_i] -> inner[inner_curr]
        # Triangle 2: outer[next_i] -> inner[inner_next] -> inner[inner_curr]
        with contextlib.suppress(ValueError):
            bm.faces.new((outer_verts[i], outer_verts[next_i], inner_verts[inner_curr]))
        with contextlib.suppress(ValueError):
            bm.faces.new((outer_verts[next_i], inner_verts[inner_next], inner_verts[inner_curr]))


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
_STAGE_BY_INDEX: dict[int, DebugStage] = {value: key for key, value in _STAGE_INDEX.items()}


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
    alpha_grid = read_alpha_grid(image, downscale_factor)
    # margin_pixels is expressed in SOURCE image pixels so the user's
    # mental model matches what they author in Photoshop / Pillow.
    # The contour walker operates on the downscaled grid, so we scale
    # the dilate/erode kernel size by downscale_factor to keep the
    # effective margin invariant. Without this, margin=5 + downscale=
    # 0.25 dilates 5 cells of a 50x50 grid = 20 source pixels = way
    # more aggressive than the user expects (regression caught in
    # smoke validation).
    grid_margin = max(0, round(margin_pixels * downscale_factor))
    outer_pixels, inner_pixels = extract_contour_pair(alpha_grid, alpha_threshold, grid_margin)
    if len(outer_pixels) < 3:
        raise ValueError(
            "automesh outer contour too short - try lowering the alpha "
            "threshold or increasing the resolution"
        )

    source_width, source_height = image.size[0], image.size[1]
    outer_world_raw = pixel_contour_to_world(
        to_float_contour(outer_pixels),
        downscale_factor,
        world_scale,
        source_width,
        source_height,
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

    if debug_stage == "raw_contours":
        emit_contour_debug(obj, "raw_contours", outer_world_raw, inner_world_raw)
        return _debug_stage_report("raw_contours", len(outer_world_raw), len(inner_world_raw))

    outer_smoothed = laplacian_smooth(outer_world_raw, _SMOOTH_ITERATIONS)
    inner_smoothed = (
        laplacian_smooth(inner_world_raw, _SMOOTH_ITERATIONS) if inner_world_raw else []
    )

    if debug_stage == "smoothed":
        emit_contour_debug(obj, "smoothed", outer_smoothed, inner_smoothed)
        return _debug_stage_report("smoothed", len(outer_smoothed), len(inner_smoothed))

    outer_world = arc_length_resample(outer_smoothed, target_contour_vertices)
    # Inner contour uses the SAME vertex count as outer so the
    # annulus can be triangulated as a clean strip of trapezoids
    # via radial bridge edges (see build_annulus_edge_pairs).
    inner_world: Contour2D = (
        arc_length_resample(inner_smoothed, target_contour_vertices) if inner_smoothed else []
    )

    if debug_stage == "resampled":
        emit_contour_debug(obj, "resampled", outer_world, inner_world)
        return _debug_stage_report("resampled", len(outer_world), len(inner_world))

    interior_points = interior_points_for_annulus(
        outer_world,
        inner_world,
        interior_spacing,
        bone_segments=bone_segments,
        bone_density_radius=bone_density_radius,
        bone_density_factor=bone_density_factor,
    )

    if debug_stage == "interior_points":
        emit_points_debug(obj, "interior_points", interior_points)
        return _debug_stage_report(
            "interior_points",
            len(outer_world),
            len(inner_world),
            interior_count=len(interior_points),
        )

    # Bridge offset = inner rotation that minimizes total radial
    # bridge length, so the strip triangulation gets clean nearly-
    # parallel sides instead of crossing the annulus diagonally.
    bridge_offset = find_best_inner_rotation(outer_world, inner_world)

    if debug_stage == "bridges":
        emit_bridges_debug(obj, "bridges", outer_world, inner_world, bridge_offset)
        return _debug_stage_report(
            "bridges", len(outer_world), len(inner_world), bridge_offset=bridge_offset
        )

    base_group_index, _is_fresh = _initialize_base_sprite_group(obj)
    _delete_non_base_geometry(obj, base_group_index)

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    outer_verts = [bm.verts.new((x, 0.0, y)) for (x, y) in outer_world]
    inner_verts = [bm.verts.new((x, 0.0, y)) for (x, y) in inner_world]
    bm.verts.ensure_lookup_table()

    if inner_verts and len(outer_verts) == len(inner_verts):
        # Annulus strip: build N cells of 2 triangles each directly.
        # bmesh.ops.triangle_fill with both loops + bridges in same
        # orientation mis-detected the inner ring as a fillable face
        # and fan-triangulated the hole (regression caught in smoke
        # validation; visible as spiky verticals crossing the annulus
        # center). Manual quad-split has no orientation ambiguity:
        # we know exactly which pairs of outer / inner verts belong
        # to each cell after find_best_inner_rotation aligned them.
        _build_annulus_strip(bm, outer_verts, inner_verts, bridge_offset)
    else:
        # Fallback for thin silhouettes with no inner ring: fill the
        # outer loop as a single n-gon polygon, then triangulate via
        # bmesh.ops.triangulate. No bridges involved so the
        # orientation issue does not occur.
        outer_edges = [
            bm.edges.new((outer_verts[i], outer_verts[(i + 1) % len(outer_verts)]))
            for i in range(len(outer_verts))
        ]
        bmesh.ops.triangle_fill(
            bm,
            edges=outer_edges,
            use_beauty=True,
            use_dissolve=False,
        )

    if debug_stage == "fill_no_interior":
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        return _debug_stage_report(
            "fill_no_interior",
            len(outer_world),
            len(inner_world),
            total_verts=len(mesh.vertices),
            total_faces=len(mesh.polygons),
        )

    # Insert interior Steiner points into the just-triangulated annulus
    # (D15 density-under-bones). triangle_fill leaves loose verts
    # disconnected, so a naive ``bm.verts.new`` for each interior
    # point produced dangling vertices that never appeared in the
    # final triangulation (regression caught in PR #51 review).
    # We triangulate the annulus first, then for each interior point
    # locate the containing triangle and split it into three new
    # triangles around a new center vertex.
    interior_inserted = _insert_interior_points(bm, interior_points)

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    return {
        "outer_verts": len(outer_verts),
        "inner_verts": len(inner_verts),
        "interior_verts": interior_inserted,
        "total_verts": len(mesh.vertices),
        "total_faces": len(mesh.polygons),
    }
