"""Pure-Python geometry helpers for SPEC 013 automesh.

bpy-free. Refines raw contour points from
``core/alpha_contour.py`` into the smooth, evenly-spaced contours
the bpy bridge feeds into ``bmesh.ops.triangle_fill`` to build the
annulus topology (SPEC 013 D2).

Two transforms ship here:

* **Laplacian smoothing** averages each vertex with its cyclic
  neighbours so the raw stair-step contour from a pixel grid
  becomes a curve that deforms predictably under bone rotation.
* **Arc-length resampling** redistributes points so the spacing
  is even along the perimeter - critical for the annulus topology
  because edge-loop density should not bunch up at convex corners
  or thin out along long straight runs.

Both transforms operate on pure Python tuples of floats so they
remain trivially testable without booting Blender. Coordinates
are 2D (X, Z) world units after the bpy bridge has converted
pixel int coords via the resolution + scale factor.
"""

from __future__ import annotations

import math
from itertools import pairwise

ContourPoint2D = tuple[float, float]
Contour2D = list[ContourPoint2D]


def to_float_contour(pixel_contour: list[tuple[int, int]]) -> Contour2D:
    """Lift an integer pixel contour into a 2D float contour.

    The bpy bridge applies the world-unit scale afterwards. Lifting
    early lets the smoothing + resample math stay in floats without
    needing to round between passes.
    """
    return [(float(x), float(y)) for (x, y) in pixel_contour]


def laplacian_smooth(contour: Contour2D, iterations: int) -> Contour2D:
    """Average each vertex with its two cyclic neighbours, N times.

    The contour is treated as a closed loop (first and last vertices
    are neighbours). Each pass moves every vertex to the midpoint of
    its neighbours - a classical Laplacian filter. After 3 passes a
    typical pixel-staircase contour reads as a smooth curve while
    still hugging the silhouette within sub-pixel error.

    Empty / single-vertex contours return unchanged. Two-vertex
    contours collapse to their midpoint after smoothing (the only
    sensible degenerate behaviour).
    """
    if iterations < 0:
        raise ValueError(f"iterations must be >= 0, got {iterations}")
    if iterations == 0 or len(contour) < 2:
        return list(contour)

    current = list(contour)
    count = len(current)
    for _ in range(iterations):
        smoothed: Contour2D = []
        for index in range(count):
            prev_x, prev_y = current[(index - 1) % count]
            curr_x, curr_y = current[index]
            next_x, next_y = current[(index + 1) % count]
            avg_x = (prev_x + curr_x + next_x) / 3.0
            avg_y = (prev_y + curr_y + next_y) / 3.0
            smoothed.append((avg_x, avg_y))
        current = smoothed
    return current


def perimeter_length(contour: Contour2D) -> float:
    """Sum the cyclic edge lengths of a closed contour."""
    if len(contour) < 2:
        return 0.0
    total = 0.0
    for index in range(len(contour)):
        x0, y0 = contour[index]
        x1, y1 = contour[(index + 1) % len(contour)]
        total += math.hypot(x1 - x0, y1 - y0)
    return total


def arc_length_resample(contour: Contour2D, target_count: int) -> Contour2D:
    """Redistribute contour points so spacing is uniform along the loop.

    Walks the contour cumulatively, placing ``target_count`` new
    points at even arc-length intervals. The output count is
    exactly ``target_count`` and every output point lies on an edge
    of the input contour (linear interpolation between adjacent
    input vertices). Used after smoothing so the final mesh has
    predictable edge-loop density.

    Raises ``ValueError`` for ``target_count < 3`` (a polygon needs
    at least three vertices to bound a region) and for contours
    with zero perimeter.
    """
    if target_count < 3:
        raise ValueError(f"target_count must be >= 3, got {target_count}")
    if len(contour) < 3:
        raise ValueError("contour must have at least 3 vertices to resample")

    # Dedupe consecutive identical points up front so the sampling
    # loop never has to handle zero-length edges. The earlier path
    # (skip-and-continue on zero length) could emit duplicate
    # samples and drift the arc-length distribution because the
    # current edge_index was never advanced past the degenerate edge
    # (regression caught in PR #51 review).
    deduped: Contour2D = [contour[0]]
    for prev, point in pairwise(contour):
        if point != prev:
            deduped.append(point)
    if len(deduped) < 3:
        raise ValueError("contour collapses to <3 unique points after dedupe - cannot resample")
    contour = deduped

    total = perimeter_length(contour)
    if total <= 0.0:
        raise ValueError("contour has zero perimeter - cannot resample")

    step = total / target_count
    output: Contour2D = []
    edge_index = 0
    edge_start = contour[0]
    edge_end = contour[1]
    edge_length = math.hypot(edge_end[0] - edge_start[0], edge_end[1] - edge_start[1])

    for sample in range(target_count):
        target_distance = sample * step
        accumulated = edge_index_start_distance(contour, edge_index)
        while accumulated + edge_length < target_distance and edge_index < len(contour) - 1:
            edge_index += 1
            edge_start = contour[edge_index]
            edge_end = contour[(edge_index + 1) % len(contour)]
            edge_length = math.hypot(edge_end[0] - edge_start[0], edge_end[1] - edge_start[1])
            accumulated = edge_index_start_distance(contour, edge_index)
        if edge_length <= 0.0:
            # Defensive only - dedupe above eliminates zero-length
            # edges. Reached only if a future caller passes
            # already-deduped contour with collinear degenerate
            # points slipping through. Snap to edge start.
            output.append(edge_start)
            continue
        distance_into_edge = target_distance - accumulated
        ratio = distance_into_edge / edge_length
        sample_x = edge_start[0] + (edge_end[0] - edge_start[0]) * ratio
        sample_y = edge_start[1] + (edge_end[1] - edge_start[1]) * ratio
        output.append((sample_x, sample_y))

    return output


def edge_index_start_distance(contour: Contour2D, edge_index: int) -> float:
    """Cumulative arc length up to the start of edge ``edge_index``.

    Helper for :func:`arc_length_resample`. Walks edges 0..edge_index
    summing their lengths so the resample loop can convert a global
    target distance into an offset within the current edge without
    re-traversing from the start.
    """
    if edge_index <= 0:
        return 0.0
    total = 0.0
    for index in range(min(edge_index, len(contour))):
        x0, y0 = contour[index]
        x1, y1 = contour[(index + 1) % len(contour)]
        total += math.hypot(x1 - x0, y1 - y0)
    return total


def relax_contour(
    pixel_contour: list[tuple[int, int]],
    smooth_iterations: int,
    target_vertex_count: int,
) -> Contour2D:
    """Top-level "raw pixel contour -> ready-to-mesh" pipeline.

    Lifts integers to floats, runs Laplacian smoothing for the
    given iterations, then arc-length resamples to the target
    vertex count. This is the function the bpy bridge calls per
    contour (once for outer, once for inner) before building
    the annulus edges.

    When the input is shorter than ``target_vertex_count`` we
    still upsample to the target via arc-length sampling so the
    annulus topology has predictable density - this matches COA
    Tools 2's behaviour at low-resolution sprites.
    """
    if smooth_iterations < 0:
        raise ValueError(f"smooth_iterations must be >= 0, got {smooth_iterations}")
    if target_vertex_count < 3:
        raise ValueError(f"target_vertex_count must be >= 3, got {target_vertex_count}")
    if len(pixel_contour) < 3:
        raise ValueError(f"pixel_contour must have at least 3 points, got {len(pixel_contour)}")
    floats = to_float_contour(pixel_contour)
    smoothed = laplacian_smooth(floats, smooth_iterations)
    return arc_length_resample(smoothed, target_vertex_count)


def find_best_inner_rotation(
    outer: Contour2D,
    inner: Contour2D,
) -> int:
    """Inner contour rotation offset minimizing radial bridge length.

    Returns ``k`` such that bridging ``outer[i]`` to
    ``inner[(i + k) % N]`` produces the shortest total bridge edges
    across the annulus. Used by the bpy bridge before building the
    annulus topology: bridges that cross the annulus diagonally
    create huge skinny triangles, while bridges aligned radially
    produce clean strip triangulation.

    Requires equal-length contours. Returns 0 for empty inner.
    Pure data, no numpy - O(N^2) but N is small (32-64 vertices)
    so the worst-case is ~4k operations.
    """
    if not inner:
        return 0
    n = len(outer)
    if n != len(inner) or n == 0:
        return 0
    best_offset = 0
    best_total = float("inf")
    for offset in range(n):
        total = 0.0
        for i in range(n):
            ox, oz = outer[i]
            ix, iz = inner[(i + offset) % n]
            total += (ox - ix) ** 2 + (oz - iz) ** 2
        if total < best_total:
            best_total = total
            best_offset = offset
    return best_offset


def build_annulus_edge_pairs(
    outer_count: int,
    inner_count: int,
    bridge_offset: int = 0,
) -> list[tuple[int, int]]:
    """Build the edge index pairs for the annulus topology.

    Returns a list of ``(start_index, end_index)`` pairs that the
    bpy bridge feeds into ``bmesh.ops.triangle_fill``. Layout:

    * Vertices 0..outer_count-1 = outer contour, cyclic edges.
    * Vertices outer_count..outer_count+inner_count-1 = inner
      contour, cyclic edges.
    * When ``outer_count == inner_count`` AND > 0, radial bridge
      edges connect outer[i] to inner[(i + bridge_offset) %
      outer_count]. ``bridge_offset`` is computed by
      :func:`find_best_inner_rotation` from the actual contour
      geometry so the bridges are aligned (radial) rather than
      crossing the annulus diagonally.

    Without bridges, ``triangle_fill`` runs constrained Delaunay
    on the two cyclic loops alone and produces spiky fan-shaped
    triangles when outer / inner densities are mismatched (or
    even when matched, the Delaunay solver lacks the constraint
    to align outer vs inner verts). With bridges + matching
    counts, the result is a clean strip of trapezoids that
    Delaunay triangulates as 2N regular triangles.

    Pure-data helper so the test can assert the index pattern
    without instantiating a bmesh.
    """
    if outer_count < 3:
        raise ValueError(f"outer_count must be >= 3, got {outer_count}")
    if inner_count < 0:
        raise ValueError(f"inner_count must be >= 0, got {inner_count}")
    if 0 < inner_count < 3:
        raise ValueError(f"inner_count must be 0 or >= 3, got {inner_count}")

    edges: list[tuple[int, int]] = []
    for index in range(outer_count):
        edges.append((index, (index + 1) % outer_count))
    if inner_count >= 3:
        offset = outer_count
        for index in range(inner_count):
            edges.append((offset + index, offset + (index + 1) % inner_count))
        # Radial bridges (annulus strip topology) when outer and
        # inner counts match. Without these, triangle_fill produces
        # spiky fan triangles between the two loops because the
        # constrained Delaunay has nothing to anchor the radial
        # alignment to. With them, the annulus triangulates as N
        # quads (= 2N triangles) with predictable proportions.
        if outer_count == inner_count:
            normalized_offset = bridge_offset % outer_count
            for index in range(outer_count):
                inner_index = (index + normalized_offset) % inner_count
                edges.append((index, offset + inner_index))
    return edges
