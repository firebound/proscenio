"""Pure stroke hit-testing for the automesh authoring modal.

The screen->world pick radius is resolved by the operator (it needs bpy region
math); this module owns the bpy-free "which stroke is under this point" loop so
it is unit-testable without a viewport.
"""

from __future__ import annotations

from collections.abc import Sequence

from ..skinning.authoring_stages import Stroke


def stroke_index_within(
    strokes: Sequence[Stroke],
    point_xz: tuple[float, float],
    pick_radius_sq: float,
) -> int | None:
    """Index of the first stroke with a vertex within ``pick_radius_sq`` of ``point_xz``.

    ``pick_radius_sq`` is a squared world-unit distance (the caller converts the
    screen-space pixel radius at the cursor). Returns ``None`` when no stroke
    vertex falls inside the pick disc.
    """
    px, py = point_xz
    for idx, stroke in enumerate(strokes):
        for pt in stroke["points"]:
            if (pt[0] - px) ** 2 + (pt[1] - py) ** 2 <= pick_radius_sq:
                return idx
    return None
