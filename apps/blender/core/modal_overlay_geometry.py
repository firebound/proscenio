"""Pure-geometry helpers for modal-overlay drawing (SPEC 012.1).

bpy-free. Lives under ``core/`` (not ``core/bpy_helpers/``) so unit
tests can exercise the vertex math without booting Blender. The
bpy-bound ``core/bpy_helpers/modal_overlay.py`` consumes these.
"""

from __future__ import annotations

import math
from typing import Literal

PlaneAxis = Literal["X", "Y", "Z"]


def build_circle_vertices(
    center: tuple[float, float, float],
    radius: float,
    plane_axis: PlaneAxis,
    segments: int,
) -> list[tuple[float, float, float]]:
    """Return ``segments`` vertices of a circle around ``center``.

    The circle lies on the plane orthogonal to ``plane_axis`` and
    passing through ``center``. Vertices wind counterclockwise as seen
    from the positive ``plane_axis`` half-space.
    """
    if segments < 3:
        raise ValueError(f"segments must be >= 3, got {segments}")
    if radius <= 0.0:
        raise ValueError(f"radius must be > 0, got {radius}")
    cx, cy, cz = center
    out: list[tuple[float, float, float]] = []
    for index in range(segments):
        angle = 2.0 * math.pi * index / segments
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        if plane_axis == "Y":
            out.append((cx + radius * cos_a, cy, cz + radius * sin_a))
        elif plane_axis == "Z":
            out.append((cx + radius * cos_a, cy + radius * sin_a, cz))
        else:
            out.append((cx, cy + radius * cos_a, cz + radius * sin_a))
    return out


def build_rect_vertices(
    x_min: float,
    y_min: float,
    x_max: float,
    y_max: float,
) -> list[tuple[float, float]]:
    """Return six 2D vertices forming the two triangles of a rectangle.

    Output order matches ``TRIS`` primitive expectations:
    ``[bl, br, tr, bl, tr, tl]`` where ``bl`` is bottom-left etc.
    """
    if x_max <= x_min or y_max <= y_min:
        raise ValueError(f"degenerate rect: ({x_min},{y_min})..({x_max},{y_max})")
    bl = (x_min, y_min)
    br = (x_max, y_min)
    tr = (x_max, y_max)
    tl = (x_min, y_max)
    return [bl, br, tr, bl, tr, tl]
