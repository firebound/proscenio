"""Constrained Delaunay triangulation + hole-face prune (the weight-paint-automesh spec).

Wraps ``mathutils.geometry.delaunay_2d_cdt`` for the automesh
bridge: produces the bmesh triangulation that covers the alpha
silhouette + Steiner interior points, then prunes any face whose
centroid lies inside a detected alpha hole.

CDT's nested-loop hole detection is unreliable against the
bridge's Y-flip orientation flow; the centroid post-process is
the deterministic fallback (cheaper than fighting the CDT
winding / epsilon settings to make output_type=2 work end-to-end).
"""

from __future__ import annotations

import bmesh
import mathutils

from ...automesh import point_in_polygon


def delete_faces_inside_holes(
    bm: bmesh.types.BMesh,
    holes_world: list[list[tuple[float, float]]],
) -> int:
    """Delete every BMFace whose XZ centroid lies inside any hole loop.

    Loose verts + edges left behind by the face deletion are also
    cleaned: drop any edge without an incident face, then any vert
    without an incident edge, so the result is a clean cutout
    (without this cleanup the hole boundary's constraint edges +
    the CDT-internal edges spanning the hole region remain as
    wireframe "spokes" crossing the cutout in viewport - regression
    caught in PR #51 smoke).

    Returns the count of faces removed.
    """
    if not holes_world:
        return 0
    bm.faces.ensure_lookup_table()
    to_remove: list[bmesh.types.BMFace] = []
    for face in bm.faces:
        verts = face.verts
        if not verts:
            continue
        n = len(verts)
        cx = sum(v.co.x for v in verts) / n
        cz = sum(v.co.z for v in verts) / n
        for hole in holes_world:
            if point_in_polygon((cx, cz), hole):
                to_remove.append(face)
                break
    if to_remove:
        bmesh.ops.delete(bm, geom=to_remove, context="FACES_ONLY")
        loose_edges = [e for e in bm.edges if len(e.link_faces) == 0]
        if loose_edges:
            bmesh.ops.delete(bm, geom=loose_edges, context="EDGES")
        loose_verts = [v for v in bm.verts if len(v.link_edges) == 0]
        if loose_verts:
            bmesh.ops.delete(bm, geom=loose_verts, context="VERTS")
    return len(to_remove)


def _cyclic_loop_edges(start_index: int, count: int) -> list[tuple[int, int]]:
    """Build the N edges that close a closed loop of ``count`` verts.

    Verts are assumed to be laid out contiguously in some flat coord
    array starting at ``start_index``. Cyclic = last edge wraps to
    the start.
    """
    return [(start_index + i, start_index + (i + 1) % count) for i in range(count)]


def _build_cdt_inputs(
    outer_world: list[tuple[float, float]],
    inner_world: list[tuple[float, float]],
    interior_points: list[tuple[float, float]],
    holes: list[list[tuple[float, float]]],
    extra_edges: list[tuple[int, int]] | None = None,
) -> tuple[list[tuple[float, float]], list[tuple[int, int]]]:
    """Assemble the ``(coords, constraint_edges)`` CDT inputs.

    Layout in the flat coord array:
    ``outer + inner + interior + each_hole_in_order``.
    Constraint edges close each contour loop in place.

    ``extra_edges`` is appended verbatim - indices must be valid against
    the final coord array (caller maps indices when stroke verts live in
    `interior_points` and snap endpoints reference `outer_world`).
    """
    outer_count = len(outer_world)
    inner_count = len(inner_world)
    all_coords: list[tuple[float, float]] = (
        list(outer_world) + list(inner_world) + list(interior_points)
    )
    edges_constraint = _cyclic_loop_edges(0, outer_count)
    if inner_count >= 3:
        edges_constraint.extend(_cyclic_loop_edges(outer_count, inner_count))
    hole_offset = len(all_coords)
    for hole in holes:
        if len(hole) < 3:
            continue
        all_coords.extend(hole)
        edges_constraint.extend(_cyclic_loop_edges(hole_offset, len(hole)))
        hole_offset += len(hole)
    if extra_edges:
        edges_constraint.extend(extra_edges)
    return all_coords, edges_constraint


def _commit_cdt_faces(
    bm: bmesh.types.BMesh,
    out_verts: list[tuple[float, float]],
    out_faces: list[list[int]],
) -> int:
    """Materialize CDT-output verts + faces into the bmesh.

    Returns the count of faces successfully created.

    ``bm.faces.new`` raises ``ValueError`` on degenerate / duplicate-edge
    faces; we swallow and log up to 5 per call so the operator never aborts
    mid-build.
    """
    bm_verts = [bm.verts.new((v[0], 0.0, v[1])) for v in out_verts]
    bm.verts.ensure_lookup_table()
    added = 0
    failed = 0
    for face in out_faces:
        try:
            bm.faces.new([bm_verts[i] for i in face])
            added += 1
        except ValueError as exc:
            failed += 1
            if failed <= 5:
                print(f"[automesh] face skipped ({exc}): indices={face}")
    if failed:
        print(f"[automesh] {failed} faces failed creation ({added} succeeded)")
    return added


def build_mesh_via_delaunay(
    bm: bmesh.types.BMesh,
    outer_world: list[tuple[float, float]],
    inner_world: list[tuple[float, float]],
    interior_points: list[tuple[float, float]],
    holes_world: list[list[tuple[float, float]]] | None = None,
    extra_edges: list[tuple[int, int]] | None = None,
) -> int:
    """Single-pass Constrained Delaunay Triangulation for the entire mesh.

    Replaces the prior 3-pass pipeline (manual annulus strip +
    inner-area fill + Steiner insertion) with one
    ``mathutils.geometry.delaunay_2d_cdt`` call configured to:

    - Treat outer + inner cyclic edges as hard constraints (must
      appear in the output).
    - Auto-detect the inner ring AND every hole loop as HOLEs via
      ``output_type=2`` (CDT_INSIDE_WITH_HOLES) when present, so the
      interior of the inner ring + every alpha hole is correctly
      excluded from triangulation.
    - Include Steiner interior points as additional verts from the
      start so they participate in the Delaunay rather than being
      fan-split into an existing fan triangulation afterwards.
    - Produce BMesh-valid output (no degenerate / self-intersecting
      faces, no edge duplicates) so bm.faces.new always succeeds
      without "this edge exists" exceptions.

    Returns the count of faces added to the bmesh.

    Delaunay output_type enum (BLI_delaunay_2d.h):
        0 CDT_FULL                                 - convex hull triangulation
        1 CDT_INSIDE                                - triangles enclosed by constraints
        2 CDT_INSIDE_WITH_HOLES                     - like 1 + auto-detect holes
        3 CDT_CONSTRAINTS                           - ONLY constraint edges (no fill)
        4 CDT_CONSTRAINTS_VALID_BMESH               - like 3 + bmesh-valid
        5 CDT_CONSTRAINTS_VALID_BMESH_WITH_HOLES    - like 4 + holes

    PR #51 smoke caught the bug: we were using 4 / 5 which omit
    interior triangulation entirely. Use 1 / 2 to get the full
    Delaunay fill of the constrained region.
    """
    if len(outer_world) < 3:
        return 0
    holes = list(holes_world) if holes_world else []
    all_coords, edges_constraint = _build_cdt_inputs(
        outer_world, inner_world, interior_points, holes, extra_edges=extra_edges
    )
    output_type = 2 if (len(inner_world) >= 3 or holes) else 1
    result = mathutils.geometry.delaunay_2d_cdt(
        all_coords,
        edges_constraint,
        [],
        output_type,
        1e-6,
        True,
    )
    out_verts, _out_edges, out_faces, _orig_v, _orig_e, _orig_f = result
    print(
        f"[automesh] delaunay output_type={output_type} "
        f"input={len(all_coords)}v/{len(edges_constraint)}e "
        f"output={len(out_verts)}v/{len(out_faces)}f"
    )
    return _commit_cdt_faces(bm, out_verts, out_faces)
