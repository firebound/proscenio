"""Constrained Delaunay triangulation + hole-face prune (SPEC 013).

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
    for face in list(bm.faces):
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


def build_mesh_via_delaunay(
    bm: bmesh.types.BMesh,
    outer_world: list[tuple[float, float]],
    inner_world: list[tuple[float, float]],
    interior_points: list[tuple[float, float]],
    holes_world: list[list[tuple[float, float]]] | None = None,
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

    Returns the count of faces added.
    """
    outer_count = len(outer_world)
    inner_count = len(inner_world)
    if outer_count < 3:
        return 0
    holes = list(holes_world) if holes_world else []

    all_coords: list[tuple[float, float]] = (
        list(outer_world) + list(inner_world) + list(interior_points)
    )
    edges_constraint: list[tuple[int, int]] = []
    for i in range(outer_count):
        edges_constraint.append((i, (i + 1) % outer_count))
    if inner_count >= 3:
        inner_offset = outer_count
        for i in range(inner_count):
            edges_constraint.append((inner_offset + i, inner_offset + (i + 1) % inner_count))
    # Append every alpha hole as a closed constraint loop. CDT's
    # output_type=2 detects nested loops automatically; orientation
    # does not matter for hole detection.
    hole_offset = len(all_coords)
    for hole in holes:
        if len(hole) < 3:
            continue
        start = hole_offset
        all_coords.extend(hole)
        for i in range(len(hole)):
            edges_constraint.append((start + i, start + (i + 1) % len(hole)))
        hole_offset += len(hole)

    # Delaunay output_type enum (BLI_delaunay_2d.h):
    #   0 CDT_FULL: convex hull triangulation
    #   1 CDT_INSIDE: triangles enclosed by constraints
    #   2 CDT_INSIDE_WITH_HOLES: like 1 + auto-detect holes
    #   3 CDT_CONSTRAINTS: ONLY constraint edges (no fill - bug we hit)
    #   4 CDT_CONSTRAINTS_VALID_BMESH: like 3 + bmesh-valid
    #   5 CDT_CONSTRAINTS_VALID_BMESH_WITH_HOLES: like 4 + holes
    #
    # PR #51 smoke caught the bug: we were using 4 / 5 which omit
    # interior triangulation entirely, so the resulting mesh had
    # verts + boundary edges but NO faces. Use 1 / 2 to get the
    # full Delaunay fill of the constrained region.
    output_type = 2 if (inner_count >= 3 or holes) else 1
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
