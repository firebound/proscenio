"""Pure-Python interior-point generation for the automesh.

bpy-free. Produces the Steiner points that the bpy bridge inserts
into the annulus triangulation before calling
``bmesh.ops.triangle_fill``, so the resulting mesh has interior
density (not just the silhouette ring of edge loops).

Two density modes ship together:

* **Uniform** - regular grid spaced by ``spacing``, clipped to
  the annulus interior. Used when no armature is targeted.
* **Bone-aware** (default when picker has an armature) -
  uniform base grid plus extra subdivision near bone segments so
  the mesh has more triangles where deformation happens. Reuses
  the picker contract from the quick-armature work: bone positions come
  from the active armature, not from heuristics.

All geometry math is XZ plane in world units (the Y=0 picture
plane convention, parallel to the quick-armature axis lock contract).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from .._shared.geometry_2d import Point2D

BoneSegment2D = tuple[Point2D, Point2D]


def bounding_box(contour: list[Point2D]) -> tuple[float, float, float, float]:
    """Return ``(min_x, min_y, max_x, max_y)`` for a non-empty contour."""
    if not contour:
        raise ValueError("contour must be non-empty")
    xs = [point[0] for point in contour]
    ys = [point[1] for point in contour]
    return (min(xs), min(ys), max(xs), max(ys))


_BOUNDARY_EPSILON = 1e-9
_BOUNDARY_EPSILON_SQ = _BOUNDARY_EPSILON * _BOUNDARY_EPSILON


def _point_on_segment(
    px: float,
    py: float,
    ax: float,
    ay: float,
    bx: float,
    by: float,
) -> bool:
    """True when ``(px, py)`` lies within epsilon of segment AB."""
    abx, aby = bx - ax, by - ay
    apx, apy = px - ax, py - ay
    seg_length_sq = abx * abx + aby * aby
    if seg_length_sq <= 0.0:
        return abs(apx) < _BOUNDARY_EPSILON and abs(apy) < _BOUNDARY_EPSILON
    ratio = (apx * abx + apy * aby) / seg_length_sq
    if not -_BOUNDARY_EPSILON <= ratio <= 1.0 + _BOUNDARY_EPSILON:
        return False
    closest_x = ax + ratio * abx
    closest_y = ay + ratio * aby
    # Compare squared distance against squared epsilon - mixing
    # squared LHS with linear epsilon widened the on-edge band to
    # ~31um at the default 1e-9 epsilon, excluding valid interior
    # points within that distance of the boundary.
    return (px - closest_x) ** 2 + (py - closest_y) ** 2 < _BOUNDARY_EPSILON_SQ


def point_in_polygon(point: Point2D, polygon: Sequence[Point2D]) -> bool:
    """Even-odd-rule point-in-polygon test for closed simple contours.

    Returns ``True`` when the point lies strictly inside the closed
    polygon, ``False`` on the boundary or outside. The explicit
    boundary check up front is what enforces "on the edge = outside"
    per the contract - the raw ray-casting below is indeterminate
    for points sitting exactly on a polygon segment and would
    otherwise leak the rare-but-possible edge case (regression
    caught in PR #51 review).

    Performance is linear in the polygon vertex count - fine for
    the few-hundred-vertex contours Proscenio's automesh produces
    after resampling.
    """
    if len(polygon) < 3:
        return False
    px, py = point
    count = len(polygon)
    for index in range(count):
        x0, y0 = polygon[index]
        x1, y1 = polygon[(index + 1) % count]
        if _point_on_segment(px, py, x0, y0, x1, y1):
            return False
    inside = False
    for index in range(count):
        x0, y0 = polygon[index]
        x1, y1 = polygon[(index + 1) % count]
        # Ray-cast horizontally to the right. Edge crosses the ray
        # iff one endpoint is above and the other below the test y.
        if (y0 > py) != (y1 > py):
            slope = (x1 - x0) / (y1 - y0) if y1 != y0 else 0.0
            x_crossing = x0 + slope * (py - y0)
            if px < x_crossing:
                inside = not inside
    return inside


def distance_to_segment(point: Point2D, segment: BoneSegment2D) -> float:
    """Euclidean distance from ``point`` to the line segment.

    Returns 0 when the point lies exactly on the segment, the
    distance to the nearest endpoint when the projection falls
    outside [0, 1], else the perpendicular distance to the line.
    Standard 2D math, no numpy.
    """
    (ax, ay), (bx, by) = segment
    abx, aby = bx - ax, by - ay
    apx, apy = point[0] - ax, point[1] - ay
    segment_length_sq = abx * abx + aby * aby
    if segment_length_sq <= 0.0:
        return math.hypot(apx, apy)
    # Projection ratio of AP onto AB, clamped to the segment.
    ratio = max(0.0, min(1.0, (apx * abx + apy * aby) / segment_length_sq))
    closest_x = ax + ratio * abx
    closest_y = ay + ratio * aby
    return math.hypot(point[0] - closest_x, point[1] - closest_y)


def uniform_interior_grid(
    bbox: tuple[float, float, float, float],
    spacing: float,
) -> list[Point2D]:
    """Regular grid of candidate interior points inside ``bbox``.

    Returns points spaced by ``spacing`` units along both axes,
    centered within the bounding box. Caller filters by
    point-in-polygon to keep only points inside the annulus.
    """
    if spacing <= 0.0:
        raise ValueError(f"spacing must be > 0, got {spacing}")
    min_x, min_y, max_x, max_y = bbox
    width = max_x - min_x
    height = max_y - min_y
    if width <= 0.0 or height <= 0.0:
        return []
    cols = max(1, int(width / spacing))
    rows = max(1, int(height / spacing))
    # Center the grid in the bbox so edge cells are not biased.
    offset_x = (width - cols * spacing) / 2.0 + spacing / 2.0
    offset_y = (height - rows * spacing) / 2.0 + spacing / 2.0
    points: list[Point2D] = []
    for row in range(rows):
        for col in range(cols):
            x = min_x + offset_x + col * spacing
            y = min_y + offset_y + row * spacing
            points.append((x, y))
    return points


def filter_inside_annulus(
    candidates: list[Point2D],
    outer: list[Point2D],
    inner: list[Point2D],
) -> list[Point2D]:
    """Keep only candidates inside ``outer`` AND outside ``inner``.

    When ``inner`` is empty the candidates only need to lie inside
    the outer contour (flat triangulation fallback for thin
    silhouettes per :func:`core.alpha_contour.extract_inner_contour`).
    """
    if not outer:
        return []
    if not inner:
        return [candidate for candidate in candidates if point_in_polygon(candidate, outer)]
    return [
        candidate
        for candidate in candidates
        if point_in_polygon(candidate, outer) and not point_in_polygon(candidate, inner)
    ]


def bone_aware_subdivision(
    base_points: list[Point2D],
    bone_segments: list[BoneSegment2D],
    influence_radius: float,
    subdivision_factor: int,
) -> list[Point2D]:
    """Add finer points near bones, on top of a uniform base grid.

    For every base point within ``influence_radius`` of any bone
    segment, emit ``subdivision_factor`` additional points jittered
    around the base location at quarter-spacing offsets. Result:
    triangles cluster where the mesh will bend, the rest of the
    silhouette keeps the lower base density.

    ``subdivision_factor=1`` returns the base unchanged.
    ``subdivision_factor=2`` doubles density near bones (each
    influenced base point gets 1 extra). ``subdivision_factor=4``
    quadruples. Bigger values get diminishing returns + linear
    cost.
    """
    if influence_radius < 0.0:
        raise ValueError(f"influence_radius must be >= 0, got {influence_radius}")
    if subdivision_factor < 1:
        raise ValueError(f"subdivision_factor must be >= 1, got {subdivision_factor}")
    if subdivision_factor == 1 or not bone_segments:
        return list(base_points)

    output: list[Point2D] = list(base_points)
    # Quarter-spacing jitter offsets; empirically gives good triangulations
    # without introducing collinear point sets that confuse Delaunay.
    jitter_offsets = [
        (0.25, 0.25),
        (-0.25, 0.25),
        (0.25, -0.25),
        (-0.25, -0.25),
    ]
    extras_per_point = subdivision_factor - 1
    for point in base_points:
        nearest = min(distance_to_segment(point, segment) for segment in bone_segments)
        if nearest > influence_radius:
            continue
        for jitter_index in range(min(extras_per_point, len(jitter_offsets))):
            dx, dy = jitter_offsets[jitter_index]
            output.append(
                (point[0] + dx * influence_radius * 0.25, point[1] + dy * influence_radius * 0.25)
            )
    return output


def filter_points_too_close_to_boundary(
    points: list[Point2D],
    boundary_verts: list[Point2D],
    min_distance: float,
) -> list[Point2D]:
    """Drop Steiner points within ``min_distance`` of any boundary vert.

    Constrained Delaunay does not auto-merge near-coincident verts
    when they sit just above the snap epsilon (default 1e-6). Result:
    pairs of clustered verts at the boundary where a grid Steiner
    point happened to land within a fraction of a pixel of an outer
    contour vert (regression caught in PR #51 smoke - visible as
    "phantom" close verts near the silhouette edge).

    Pre-filter on the pure-Python side keeps the Steiner grid clean
    before it enters Delaunay; downstream sees only well-separated
    points and produces well-shaped triangles.

    O(N * M) where N = Steiner candidates, M = boundary verts. Both
    small in practice (~100 each); cost negligible.
    """
    if min_distance <= 0.0 or not boundary_verts:
        return list(points)
    threshold_sq = min_distance * min_distance
    kept: list[Point2D] = []
    for px, py in points:
        too_close = False
        for bx, by in boundary_verts:
            dx = px - bx
            dy = py - by
            if dx * dx + dy * dy < threshold_sq:
                too_close = True
                break
        if not too_close:
            kept.append((px, py))
    return kept


def _in_exclude_zone(
    point: Point2D,
    zones: list[tuple[float, float, float]],
) -> bool:
    """Return True if ``point`` falls within any exclusion circle.

    Each zone is ``(cx, cz, radius)``. Uses squared-distance comparison
    to avoid a sqrt per candidate.
    """
    px, pz = point
    return any((cx - px) ** 2 + (cz - pz) ** 2 <= r * r for cx, cz, r in zones)


def interior_points_for_annulus(
    outer: list[Point2D],
    inner: list[Point2D],
    spacing: float,
    bone_segments: list[BoneSegment2D] | None = None,
    bone_density_radius: float = 0.0,
    bone_density_factor: int = 1,
    *,
    exclude_zones: list[tuple[float, float, float]] | None = None,
) -> list[Point2D]:
    """Top-level pipeline: generate annulus interior Steiner points.

    Uses ``outer`` bounding box as the candidate region, samples a
    uniform grid at ``spacing``, clips to the annulus interior,
    then (when bones are provided + ``bone_density_factor > 1``)
    adds bone-aware subdivision points near each bone segment.

    Without bones, the output is just the uniform grid clipped to
    the annulus - the safe default ("OFF when no picker
    armature").

    ``exclude_zones`` is an optional list of ``(cx, cz, radius)`` tuples.
    Any candidate that falls within ``radius`` of ``(cx, cz)`` is dropped
    before the bone-aware pass. Pass zone centres from artist-placed stroke
    verts (with ``radius = spacing * 0.5``) to prevent auto-fill grid
    points from clustering at sub-spacing distance from stroke verts,
    which causes degenerate slivers and fan-like CDT output.

    Returns an empty list when the annulus has zero area (degenerate
    silhouette) - the caller should fall back to contour-only
    triangulation and report INFO.
    """
    if not outer:
        return []
    if spacing <= 0.0:
        raise ValueError(f"spacing must be > 0, got {spacing}")
    bbox = bounding_box(outer)
    candidates = uniform_interior_grid(bbox, spacing)
    base = filter_inside_annulus(candidates, outer, inner)
    if exclude_zones:
        base = [p for p in base if not _in_exclude_zone(p, exclude_zones)]
    if not bone_segments or bone_density_factor <= 1:
        return base
    if bone_density_radius <= 0.0:
        return base
    enriched = bone_aware_subdivision(base, bone_segments, bone_density_radius, bone_density_factor)
    # Re-clip enriched points: the jitter may push some outside the annulus.
    clipped = filter_inside_annulus(enriched, outer, inner)
    if exclude_zones:
        clipped = [p for p in clipped if not _in_exclude_zone(p, exclude_zones)]
    return clipped
