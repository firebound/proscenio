"""Pure reproject algorithm (SPEC 013.2 sidecar, T3).

Hand-rolled O(n) KNN + 2D barycentric interpolation over UV anchors.
Zero bpy / mathutils import so the module is testable in vanilla
Python. Typical sprite mesh has < 2000 verts; O(n) per query is fine.
"""

from __future__ import annotations

import math

from .sidecar_schema import ProvenanceKind, SidecarEntry

Point2D = tuple[float, float]

_DEGENERATE_AREA_EPS = 1e-9
"""2x signed area below this is treated as collinear (no enclosing triangle)."""

_BARYCENTRIC_TOLERANCE = 1e-3
"""Per-coord slack so points slightly outside the triangle still interpolate."""


def reproject_entries(
    old_entries: list[SidecarEntry],
    new_uv_anchors: list[Point2D],
    *,
    max_distance: float = 0.5,
) -> list[SidecarEntry | None]:
    """Per new anchor, return an interpolated SidecarEntry or None.

    Tries barycentric blend over 3 nearest donors first. Falls back to
    nearest-neighbor weight inheritance when (a) fewer than 3 donors lie
    within max_distance OR (b) the target sits outside the triangle the
    3 nearest donors form. Only returns None when NO donor exists within
    max_distance (truly out of range).

    The fallback exists because dropping straight from "3-donor barycentric"
    to "auto_seed empty weights" produces visible weight corruption after
    automesh regen (B2 from Wave 13.2-paint smoke). Inheriting the nearest
    donor's weights is strictly better than empty: Blender's Auto-Normalize
    smooths the resulting per-vert pattern, and the artist's painted
    regions stay anchored where the source mesh had them.

    Default max_distance bumped from 0.1 to 0.5 in B2 fix - 0.1 was too
    tight for typical sprite UV space (full sprite covers up to 1.0 in
    each axis; 0.1 = 10% would-be neighborhood missed half the verts
    when the new mesh's anchor density differed slightly from the old).

    Raises ValueError when ``max_distance`` is negative or non-finite -
    silent acceptance would distort neighbor filtering.
    """
    if not math.isfinite(max_distance) or max_distance < 0.0:
        raise ValueError(f"max_distance must be finite + non-negative (got {max_distance!r})")
    if not old_entries:
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
    if not neighbors:
        return None
    if len(neighbors) < 3:
        return _nearest_neighbor_entry(target, old_entries, neighbors)
    i, j, k = neighbors[0][0], neighbors[1][0], neighbors[2][0]
    a, b, c = (
        old_entries[i].uv_anchor,
        old_entries[j].uv_anchor,
        old_entries[k].uv_anchor,
    )
    bary = _barycentric_2d(target, a, b, c)
    if bary is None:
        return _nearest_neighbor_entry(target, old_entries, neighbors)
    wa, wb, wc = bary
    blended = _blend_weights(
        (old_entries[i].weights, wa),
        (old_entries[j].weights, wb),
        (old_entries[k].weights, wc),
    )
    provenance = _carry_user_paint_provenance((old_entries[i], old_entries[j], old_entries[k]))
    return SidecarEntry(uv_anchor=target, weights=blended, provenance=provenance)


def _nearest_neighbor_entry(
    target: Point2D,
    old_entries: list[SidecarEntry],
    neighbors: list[tuple[int, float]],
) -> SidecarEntry:
    """Fallback when barycentric blend not possible (fewer than 3 donors
    in range, OR target outside the donor triangle). Inherits the nearest
    donor's weights + carries its provenance verbatim.

    neighbors must be non-empty; caller already checked. Distances in the
    tuple come from _knn_3 (squared, ascending), so neighbors[0] is the
    closest.
    """
    nearest_idx = neighbors[0][0]
    donor = old_entries[nearest_idx]
    provenance: ProvenanceKind = "user_paint" if donor.provenance == "user_paint" else "reprojected"
    return SidecarEntry(
        uv_anchor=target,
        weights=dict(donor.weights),
        provenance=provenance,
    )


def _carry_user_paint_provenance(donors: tuple[SidecarEntry, ...]) -> ProvenanceKind:
    """Preserve user_paint marker when any donor was user-painted.

    Without this, automesh regen silently demotes painted verts to
    'reprojected' and the artist loses the visual signal that those
    weights came from manual work. Any-donor wins is the conservative
    choice (preserves intent) over majority-wins (could drop user paint
    when 2 of 3 donors were auto_seed).
    """
    for donor in donors:
        if donor.provenance == "user_paint":
            return "user_paint"
    return "reprojected"


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
