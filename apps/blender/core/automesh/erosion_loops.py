"""Inner-loop erosion for interactive automesh authoring (the weight-paint productivity follow-up).

Each loop = a successively-eroded version of the outer mask, traced
to a contour. Reuses contour.erode + contour.find_first_boundary +
contour.trace_contour. Zero bpy import.
"""

from __future__ import annotations

from .contour import (
    BinaryMask,
    Contour,
    erode,
    find_first_boundary,
    trace_contour,
)


def compute_inner_loops(
    base_mask: BinaryMask,
    *,
    count: int,
    spacing_px: int,
) -> list[Contour]:
    """N successively-eroded contours from base_mask.

    Each iteration erodes the prior mask by spacing_px, then traces
    the outer contour of the eroded result. Stops early when erosion
    collapses (no contour traceable) OR count reached. count == 0
    returns empty.

    Raises ValueError when spacing_px is negative - silent acceptance
    would invert erode semantics.
    """
    if spacing_px < 0:
        raise ValueError(f"spacing_px must be non-negative (got {spacing_px!r})")
    if count <= 0:
        return []
    loops: list[Contour] = []
    mask = base_mask
    for _ in range(count):
        mask = erode(mask, spacing_px)
        start = find_first_boundary(mask)
        if start is None:
            break
        contour = trace_contour(mask, start)
        if len(contour) < 3:
            break
        loops.append(contour)
    return loops
