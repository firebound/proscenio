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

import math
from collections.abc import Sequence

Point2D = tuple[float, float]


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
