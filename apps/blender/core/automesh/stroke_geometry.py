"""Pure polyline helpers for Stage 3 stroke pipeline.

Stage 3 captures raw mouse paths during EDIT_INTERIOR_POINTS; this module
processes them before they reach the CDT:

- chaikin_smooth: noise reduction (industry standard for input polylines)
- resample_polyline: enforce global interior_spacing along the path
- snap_endpoint: pull stroke endpoints to nearest contour vert when close

All functions are pure: no bpy / no mathutils import. Tested in
isolation by tests/automesh/test_stroke_geometry.py.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence

from .._shared.geometry_2d import Point2D
from .._shared.nearest import nearest_index


def subdivide_polyline(points: Sequence[Point2D], n: int) -> list[Point2D]:
    """Insert ``n`` evenly-spaced verts into every edge of an open polyline.

    ``n<=0`` or polylines shorter than 2 points return the input
    unchanged. Original verts are preserved; only interior points are
    added per edge, so a straight pen line stops collapsing to
    a single long CDT edge that wrecks the triangulation.
    """
    if n <= 0 or len(points) < 2:
        return list(points)
    out: list[Point2D] = [points[0]]
    for a, b in itertools.pairwise(points):
        out.extend(_subdivide_one_edge(a, b, n))
        out.append(b)
    return out


def _subdivide_one_edge(a: Point2D, b: Point2D, n: int) -> list[Point2D]:
    """``n`` evenly-spaced interior points along edge ``a -> b`` (exclusive)."""
    out: list[Point2D] = []
    for i in range(1, n + 1):
        t = i / (n + 1)
        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def subdivide_polyline_edges(
    points: Sequence[Point2D], edge_subdivs: Sequence[int]
) -> list[Point2D]:
    """Per-edge open subdivide: edge ``i`` (``points[i] -> points[i+1]``) gets
    ``edge_subdivs[i]`` interior verts (0 when missing), so each segment keeps
    the subdivision count it was drawn with (spec 070). Polylines shorter than
    2 points return the input unchanged."""
    if len(points) < 2:
        return list(points)
    out: list[Point2D] = [points[0]]
    for i, (a, b) in enumerate(itertools.pairwise(points)):
        n = edge_subdivs[i] if i < len(edge_subdivs) else 0
        out.extend(_subdivide_one_edge(a, b, max(0, n)))
        out.append(b)
    return out


def contour_ring_from_pen_edges(
    points: Sequence[Point2D], edge_subdivs: Sequence[int]
) -> list[Point2D] | None:
    """Closed-ring form of :func:`subdivide_polyline_edges` (spec 070 per-edge).

    Drops the close-on-first-vert duplicate, requires >= 3 distinct verts (else
    ``None``), and subdivides EVERY edge - including the wrap (last -> first) -
    by its own count from ``edge_subdivs``. A wrap edge with no recorded count
    (the loop was confirmed open, not closed onto the first vert) gets 0, so the
    implicit closing edge stays unsubdivided, matching the polygon convention.
    """
    ring = list(points)
    if len(ring) >= 2 and ring[0] == ring[-1]:
        ring = ring[:-1]
    if len(ring) < 3 or len(set(ring)) < 3:
        return None
    out: list[Point2D] = []
    n = len(ring)
    for i in range(n):
        a = ring[i]
        b = ring[(i + 1) % n]
        out.append(a)
        count = edge_subdivs[i] if i < len(edge_subdivs) else 0
        out.extend(_subdivide_one_edge(a, b, max(0, count)))
    return out


def contour_ring_from_pen(points: Sequence[Point2D], subdivisions: int) -> list[Point2D] | None:
    """Form an outer-contour ring from a closed pen polyline (spec 066).

    The close-on-first-vert click leaves the first vert duplicated at the end;
    drop it so the ring is not degenerate. A ring with fewer than 3 distinct
    verts is not a silhouette and returns ``None`` (the caller keeps the prior
    outer). Otherwise the ring is subdivided like any pen line; the closing edge
    stays implicit (``output.outer`` is a polygon per the point_in_polygon
    convention), so it is not re-subdivided.
    """
    ring = list(points)
    if len(ring) >= 2 and ring[0] == ring[-1]:
        ring = ring[:-1]
    # Need three DISTINCT verts: a ring of 3 entries that are only 2 unique
    # points (a back-and-forth click) is degenerate, not a silhouette.
    if len(ring) < 3 or len(set(ring)) < 3:
        return None
    return subdivide_polyline(ring, subdivisions)


def chaikin_smooth(points: Sequence[Point2D], iters: int) -> list[Point2D]:
    """Chaikin corner-cutting subdivision.

    Each iteration replaces every interior segment with two new points
    at 1/4 and 3/4 along the segment. Endpoints are preserved.

    iters=0 returns input unchanged.
    Polylines of length <= 1 return unchanged regardless of iters.
    """
    if iters <= 0 or len(points) <= 1:
        return list(points)
    pts = list(points)
    for _ in range(iters):
        if len(pts) <= 1:
            break
        new_pts: list[Point2D] = [pts[0]]
        for i in range(len(pts) - 1):
            ax, ay = pts[i]
            bx, by = pts[i + 1]
            new_pts.append((ax * 0.75 + bx * 0.25, ay * 0.75 + by * 0.25))
            new_pts.append((ax * 0.25 + bx * 0.75, ay * 0.25 + by * 0.75))
        new_pts.append(pts[-1])
        pts = new_pts
    return pts


def resample_polyline(points: Sequence[Point2D], spacing: float) -> list[Point2D]:
    """Uniform arc-length resample of an open polyline.

    Walks the input as a piecewise-linear curve and emits a point
    every `spacing` world units along the arc. Endpoints are
    preserved. Polylines shorter than spacing return endpoints only.

    Raises ValueError on spacing <= 0.
    """
    if spacing <= 0:
        raise ValueError(f"spacing must be > 0, got {spacing}")
    if len(points) <= 1:
        return list(points)
    pts = list(points)
    segments: list[tuple[Point2D, Point2D, float]] = []
    total_len = 0.0
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        seg_len = math.hypot(bx - ax, by - ay)
        if seg_len > 0:
            segments.append((pts[i], pts[i + 1], seg_len))
            total_len += seg_len
    if total_len <= spacing:
        return [pts[0], pts[-1]]
    out: list[Point2D] = [pts[0]]
    target = spacing
    consumed = 0.0
    for (ax, ay), (bx, by), seg_len in segments:
        while target <= consumed + seg_len:
            t = (target - consumed) / seg_len
            out.append((ax + (bx - ax) * t, ay + (by - ay) * t))
            target += spacing
        consumed += seg_len
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return out


def snap_endpoint(
    point: Point2D,
    candidates: Sequence[Point2D],
    max_dist: float,
) -> int | None:
    """Return index of nearest candidate within max_dist, else None.

    Linear scan O(N). For Stage 3 endpoint snap the candidate list
    is the outer contour (typically <256 verts) - KD-tree overhead
    not justified at this scale.

    Tie-break: lowest index wins.
    Raises ValueError on max_dist < 0.
    """
    if max_dist < 0:
        raise ValueError(f"max_dist must be >= 0, got {max_dist}")
    idx = nearest_index(point, candidates, max_dist)
    return idx if idx >= 0 else None


def apply_pen_axis_lock(world_pt: Point2D, last_pt: Point2D | None, axis: str) -> Point2D:
    """Snap a new pen vert to share the locked axis with the last vert.

    ``axis`` is "x" (horizontal - keep the last vert's world-Z) or "z"
    (vertical - keep its world-X). An empty axis or a missing last vert returns
    ``world_pt`` unchanged. Shared by the automesh open-stroke pen and the
    manual-draw ``VertexPen``, which held identical copies.
    """
    if not axis or last_pt is None:
        return world_pt
    last_x, last_z = last_pt
    if axis == "x":  # horizontal: keep the last vert's world-Z
        return (world_pt[0], last_z)
    return (last_x, world_pt[1])  # vertical: keep the last vert's world-X
