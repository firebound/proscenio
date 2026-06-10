"""Nearest-point linear scan, dimension-agnostic.

The "walk the candidates, track the smallest squared distance to a query
point, optionally cap at a max distance" O(n) scan was hand-written in the
outer-contour splice, the stroke endpoint snap, and the cross-mesh weight
transfer. This module owns the scan; callers add their own derivation (the
index, the snapped point, the copied weights) on top.

Pure Python, no bpy. Works for any tuple arity (2D contour points, 3D mesh
verts) via ``zip`` over the coordinate pairs. KD-tree is not used: the
candidate sets in Proscenio (contours, sprite meshes) are well under 1k
points, where the linear scan's constant factor wins.
"""

from __future__ import annotations

from collections.abc import Sequence


def nearest_index(
    query: Sequence[float],
    points: Sequence[Sequence[float]],
    max_distance: float | None = None,
) -> int:
    """Index of the point closest to ``query`` by squared distance.

    Returns ``-1`` when ``points`` is empty or every point lies beyond
    ``max_distance`` (``None`` = no cap). Ties keep the lowest index (the
    comparison is strict ``<``). ``query`` and each point must share arity.
    """
    d2_cap = max_distance * max_distance if max_distance is not None else float("inf")
    best_idx = -1
    best_d2 = float("inf")
    for i, point in enumerate(points):
        d2 = sum((a - b) ** 2 for a, b in zip(query, point, strict=True))
        if d2 <= d2_cap and d2 < best_d2:
            best_d2 = d2
            best_idx = i
    return best_idx
