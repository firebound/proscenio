"""Cut stroke geometry (the weight-paint-automesh spec ).

Generate 2 parallel offset polylines perpendicular to a stroke path.
Each pair forms a "lens" polygon used for post-CDT face-prune.

Pure module: stdlib only, no bpy / mathutils.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

Point2D = tuple[float, float]

_DEGENERATE_EPSILON = 1e-9


def perpendicular_offsets(
    polyline: Sequence[Point2D],
    half_width: float,
) -> tuple[list[Point2D], list[Point2D]]:
    """Return (left_loop, right_loop) parallel to polyline at +/- half_width.

    At each sample i, the tangent direction t is the average of the segments
    (i-1, i) and (i, i+1) (forward at start, backward at end). The perpendicular
    (rotated 90deg CCW) is (-ty, tx). Left offset = sample + perp * half_width;
    right = sample - perp * half_width.

    Raises ValueError if polyline has < 2 points or half_width <= 0.
    """
    if len(polyline) < 2:
        raise ValueError("polyline needs at least 2 points")
    if half_width <= 0:
        raise ValueError(f"half_width must be > 0, got {half_width}")
    n = len(polyline)
    left: list[Point2D] = []
    right: list[Point2D] = []
    for i in range(n):
        if i == 0:
            tx, ty = polyline[1][0] - polyline[0][0], polyline[1][1] - polyline[0][1]
        elif i == n - 1:
            tx = polyline[i][0] - polyline[i - 1][0]
            ty = polyline[i][1] - polyline[i - 1][1]
        else:
            ax = polyline[i][0] - polyline[i - 1][0]
            ay = polyline[i][1] - polyline[i - 1][1]
            bx = polyline[i + 1][0] - polyline[i][0]
            by = polyline[i + 1][1] - polyline[i][1]
            tx, ty = (ax + bx) * 0.5, (ay + by) * 0.5
        mag = math.hypot(tx, ty)
        if mag < _DEGENERATE_EPSILON:
            # Use previous perpendicular offset delta when tangent is degenerate
            # (consecutive duplicate samples). Falls back to (0, half_width) at
            # first sample (vertical offset when tangent is unknown).
            if left:
                prev_lx, prev_lz = left[-1]
                prev_sx, prev_sz = polyline[i - 1]
                left.append(
                    (polyline[i][0] + (prev_lx - prev_sx), polyline[i][1] + (prev_lz - prev_sz))
                )
                prev_rx, prev_rz = right[-1]
                right.append(
                    (polyline[i][0] + (prev_rx - prev_sx), polyline[i][1] + (prev_rz - prev_sz))
                )
            else:
                left.append((polyline[i][0], polyline[i][1] + half_width))
                right.append((polyline[i][0], polyline[i][1] - half_width))
            continue
        tx /= mag
        ty /= mag
        # CCW perpendicular: (-ty, tx)
        px, py = -ty, tx
        sx, sy = polyline[i]
        left.append((sx + px * half_width, sy + py * half_width))
        right.append((sx - px * half_width, sy - py * half_width))
    return left, right


def lens_polygon(
    left_loop: Sequence[Point2D],
    right_loop: Sequence[Point2D],
) -> list[Point2D]:
    """Close the lens by walking left forward + right reversed.

    Returns a single closed polygon suitable for point_in_polygon tests.
    """
    return list(left_loop) + list(reversed(right_loop))
