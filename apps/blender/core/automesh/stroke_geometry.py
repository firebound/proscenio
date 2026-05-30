"""Pure polyline helpers for Stage 3 stroke pipeline (SPEC 013).

Stage 3 captures raw mouse paths during USER_STEINERS; this module
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

Point2D = tuple[float, float]


def subdivide_polyline(points: Sequence[Point2D], n: int) -> list[Point2D]:
    """Insert ``n`` evenly-spaced verts into every edge of an open polyline.

    ``n<=0`` or polylines shorter than 2 points return the input
    unchanged. Original verts are preserved; only interior points are
    added per edge, so a straight pen line (AS-AM16) stops collapsing to
    a single long CDT edge that wrecks the triangulation.
    """
    if n <= 0 or len(points) < 2:
        return list(points)
    out: list[Point2D] = [points[0]]
    for (ax, ay), (bx, by) in itertools.pairwise(points):
        for i in range(1, n + 1):
            t = i / (n + 1)
            out.append((ax + (bx - ax) * t, ay + (by - ay) * t))
        out.append((bx, by))
    return out


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
    if not candidates:
        return None
    qx, qy = point
    cap_d2 = max_dist * max_dist
    best_idx = -1
    best_d2 = float("inf")
    for i, (cx, cy) in enumerate(candidates):
        d2 = (cx - qx) * (cx - qx) + (cy - qy) * (cy - qy)
        if d2 > cap_d2:
            continue
        if d2 < best_d2:
            best_d2 = d2
            best_idx = i
    return best_idx if best_idx >= 0 else None
