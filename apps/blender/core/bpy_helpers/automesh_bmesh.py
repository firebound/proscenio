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
from typing import TYPE_CHECKING

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
    build_annulus_edge_pairs,
    laplacian_smooth,
)

if TYPE_CHECKING:
    from bpy.types import Image, Object


BASE_SPRITE_GROUP_NAME = "proscenio_base_sprite"
"""Vertex group flagged on the original 4 quad corners so automesh
regen knows which verts to preserve. Lifted from COA Tools 2's
``coa_base_sprite`` pattern per SPEC 013 D3."""


_SMOOTH_ITERATIONS = 3
"""Laplacian smoothing passes applied to each raw pixel contour
before triangulation. Three passes is the COA Tools 2 default and
empirically the sweet spot between staircase suppression and
silhouette drift."""


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
) -> Contour2D:
    """Convert pixel-coordinate contour to world XZ units.

    Pixel coordinates are (image-space x, image-space y). World
    coordinates are (world X, world Z) on the Y=0 picture plane.
    Image Y grows downward in raster space; world Z grows upward in
    Blender's right-handed system - so the conversion flips Y to
    Z with a sign change. ``world_scale`` converts pixel units to
    world units (typically ``1 / pixels_per_unit`` from the scene
    PG so the imported sprite matches its rendered scale).
    """
    if downscale_factor <= 0.0:
        raise ValueError(f"downscale_factor must be > 0, got {downscale_factor}")
    if world_scale <= 0.0:
        raise ValueError(f"world_scale must be > 0, got {world_scale}")
    factor = world_scale / downscale_factor
    return [(x * factor, -y * factor) for (x, y) in contour]


def collect_bone_segments(
    armature_obj: Object,
) -> list[BoneSegment2D]:
    """Extract bone segments as XZ-plane pairs from an armature.

    Walks ``armature_obj.data.edit_bones`` (or ``bones`` when not in
    Edit Mode) and emits ``((head_x, head_z), (tail_x, tail_z))`` for
    each deform-flagged bone. Y components are dropped since
    Proscenio bones live on the Y=0 picture plane per SPEC 012
    convention.
    """
    armature_data = armature_obj.data
    bones: Sequence = (
        armature_data.edit_bones
        if hasattr(armature_data, "edit_bones") and armature_data.edit_bones
        else armature_data.bones
    )
    segments: list[BoneSegment2D] = []
    for bone in bones:
        head = bone.head
        tail = bone.tail
        if not bone.use_deform:
            continue
        segments.append(((head.x, head.z), (tail.x, tail.z)))
    return segments


def _ensure_base_sprite_group(obj: Object) -> int:
    """Return the index of the ``proscenio_base_sprite`` group, creating it.

    Convenience for the regen path: when an existing mesh has no
    base-sprite group (legacy or fresh import), we create one and
    flag the current vertices as the base before generating new
    geometry. Idempotent.
    """
    group = obj.vertex_groups.get(BASE_SPRITE_GROUP_NAME)
    if group is None:
        group = obj.vertex_groups.new(name=BASE_SPRITE_GROUP_NAME)
    return group.index


def _flag_existing_verts_as_base(obj: Object, group_index: int) -> None:
    """Add every current vertex to the base-sprite group at weight 1.0."""
    mesh = obj.data
    indices = list(range(len(mesh.vertices)))
    if indices:
        obj.vertex_groups[group_index].add(indices, 1.0, "REPLACE")


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
) -> dict[str, int]:
    """Generate the annulus mesh on ``obj`` from ``image`` alpha.

    Replaces any previously generated automesh geometry while
    preserving vertices flagged in the ``proscenio_base_sprite``
    group (D3). Returns counters the operator surfaces in the
    INFO report: ``{"outer_verts", "inner_verts", "interior_verts",
    "total_verts", "total_faces"}``.

    Raises ``ValueError`` when the alpha silhouette is empty or
    the image cannot be sampled - the operator pre-flight catches
    these before getting here so the user sees an actionable
    message rather than a stack trace.
    """
    alpha_grid = read_alpha_grid(image, downscale_factor)
    outer_pixels, inner_pixels = extract_contour_pair(alpha_grid, alpha_threshold, margin_pixels)
    if len(outer_pixels) < 3:
        raise ValueError(
            "automesh outer contour too short - try lowering the alpha "
            "threshold or increasing the resolution"
        )

    outer_world_raw = pixel_contour_to_world(outer_pixels, downscale_factor, world_scale)
    outer_world = arc_length_resample(
        laplacian_smooth(outer_world_raw, _SMOOTH_ITERATIONS),
        target_contour_vertices,
    )

    inner_world: Contour2D = []
    if len(inner_pixels) >= 3:
        inner_world_raw = pixel_contour_to_world(inner_pixels, downscale_factor, world_scale)
        # Inner contour uses ~half the outer vertex count so the
        # ring of triangles between loops has reasonable aspect ratio.
        inner_target = max(3, target_contour_vertices // 2)
        inner_world = arc_length_resample(
            laplacian_smooth(inner_world_raw, _SMOOTH_ITERATIONS),
            inner_target,
        )

    interior_points = interior_points_for_annulus(
        outer_world,
        inner_world,
        interior_spacing,
        bone_segments=bone_segments,
        bone_density_radius=bone_density_radius,
        bone_density_factor=bone_density_factor,
    )

    base_group_index = _ensure_base_sprite_group(obj)
    _flag_existing_verts_as_base(obj, base_group_index)
    _delete_non_base_geometry(obj, base_group_index)

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    outer_verts = [bm.verts.new((x, 0.0, y)) for (x, y) in outer_world]
    inner_verts = [bm.verts.new((x, 0.0, y)) for (x, y) in inner_world]
    interior_verts = [bm.verts.new((x, 0.0, y)) for (x, y) in interior_points]
    bm.verts.ensure_lookup_table()

    boundary_verts = outer_verts + inner_verts
    edge_pairs = build_annulus_edge_pairs(len(outer_verts), len(inner_verts))
    bmesh_edges = []
    for start_index, end_index in edge_pairs:
        edge = bm.edges.new((boundary_verts[start_index], boundary_verts[end_index]))
        bmesh_edges.append(edge)

    bmesh.ops.triangle_fill(
        bm,
        edges=bmesh_edges,
        use_beauty=True,
        use_dissolve=False,
    )

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    return {
        "outer_verts": len(outer_verts),
        "inner_verts": len(inner_verts),
        "interior_verts": len(interior_verts),
        "total_verts": len(mesh.vertices),
        "total_faces": len(mesh.polygons),
    }
