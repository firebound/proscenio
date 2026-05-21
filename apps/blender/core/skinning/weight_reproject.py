"""Pure reproject algorithm (SPEC 013.2 sidecar, T3).

Hand-rolled O(n) KNN + 2D barycentric interpolation over UV anchors.
Zero bpy / mathutils import so the module is testable in vanilla
Python. Typical sprite mesh has < 2000 verts; O(n) per query is fine.
"""

from __future__ import annotations

from .sidecar_schema import SidecarEntry

Point2D = tuple[float, float]

_DEGENERATE_AREA_EPS = 1e-9
"""2x signed area below this is treated as collinear (no enclosing triangle)."""

_BARYCENTRIC_TOLERANCE = 1e-3
"""Per-coord slack so points slightly outside the triangle still interpolate."""


def reproject_entries(
    old_entries: list[SidecarEntry],
    new_uv_anchors: list[Point2D],
    *,
    max_distance: float = 0.1,
) -> list[SidecarEntry | None]:
    """Per new anchor, return an interpolated SidecarEntry or None.

    None signals 'no triangle of old anchors covers this target within
    max_distance'; the caller (automesh_hook) replaces None with an
    auto_seed entry (empty weights) so downstream apply_sidecar still
    visits every vert.
    """
    if len(old_entries) < 3:
        return [None] * len(new_uv_anchors)
    out: list[SidecarEntry | None] = []
    for target in new_uv_anchors:
        out.append(_reproject_one(old_entries, target, max_distance))
    return out


def _reproject_one(
    old_entries: list[SidecarEntry],
    target: Point2D,
    max_distance: float,
) -> SidecarEntry | None:
    neighbors = _knn_3(old_entries, target, max_distance)
    if len(neighbors) < 3:
        return None
    i, j, k = neighbors[0][0], neighbors[1][0], neighbors[2][0]
    a, b, c = (
        old_entries[i].uv_anchor,
        old_entries[j].uv_anchor,
        old_entries[k].uv_anchor,
    )
    bary = _barycentric_2d(target, a, b, c)
    if bary is None:
        return None
    wa, wb, wc = bary
    blended = _blend_weights(
        (old_entries[i].weights, wa),
        (old_entries[j].weights, wb),
        (old_entries[k].weights, wc),
    )
    return SidecarEntry(uv_anchor=target, weights=blended, provenance="reprojected")


def _knn_3(
    entries: list[SidecarEntry], target: Point2D, max_distance: float
) -> list[tuple[int, float]]:
    """O(n) scan: return up to 3 (index, distance) pairs sorted ascending."""
    ranked: list[tuple[int, float]] = []
    tx, ty = target
    max_sq = max_distance * max_distance
    for idx, entry in enumerate(entries):
        ax, ay = entry.uv_anchor
        dx, dy = ax - tx, ay - ty
        dist_sq = dx * dx + dy * dy
        if dist_sq > max_sq:
            continue
        ranked.append((idx, dist_sq))
    ranked.sort(key=lambda pair: pair[1])
    return ranked[:3]


def _barycentric_2d(
    p: Point2D, a: Point2D, b: Point2D, c: Point2D
) -> tuple[float, float, float] | None:
    """Barycentric coords of p in triangle abc. None if degenerate / outside."""
    v0 = (b[0] - a[0], b[1] - a[1])
    v1 = (c[0] - a[0], c[1] - a[1])
    v2 = (p[0] - a[0], p[1] - a[1])
    den = v0[0] * v1[1] - v1[0] * v0[1]
    if abs(den) < _DEGENERATE_AREA_EPS:
        return None
    inv_den = 1.0 / den
    v = (v2[0] * v1[1] - v1[0] * v2[1]) * inv_den
    w = (v0[0] * v2[1] - v2[0] * v0[1]) * inv_den
    u = 1.0 - v - w
    tol = _BARYCENTRIC_TOLERANCE
    if u < -tol or v < -tol or w < -tol or u > 1.0 + tol or v > 1.0 + tol or w > 1.0 + tol:
        return None
    return (u, v, w)


def _blend_weights(
    *components: tuple[dict[str, float], float],
) -> dict[str, float]:
    """Weighted sum across donor weight dicts. Missing bones treated as 0."""
    out: dict[str, float] = {}
    for weights, coeff in components:
        for bone, weight in weights.items():
            out[bone] = out.get(bone, 0.0) + weight * coeff
    return out
