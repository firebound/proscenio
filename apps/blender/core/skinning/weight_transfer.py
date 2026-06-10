"""Pure KNN weight transfer between meshes.

For each target vertex, find nearest source vertex within max_distance
and copy its weight dict. Targets beyond max_distance get empty dict.

Uses linear scan O(S * T); acceptable for sprite meshes (< 1k verts each).
For large meshes a future PR can swap to KDTree (apps/blender bpy layer;
this module stays pure).
"""

from __future__ import annotations

from collections.abc import Sequence

from .._shared.nearest import nearest_index

Point3D = tuple[float, float, float]


def transfer_weights_by_nearest(
    source_positions: Sequence[Point3D],
    source_weights: Sequence[dict[str, float]],
    target_positions: Sequence[Point3D],
    max_distance: float,
) -> list[dict[str, float]]:
    if max_distance < 0:
        raise ValueError(f"max_distance must be >= 0, got {max_distance}")
    if len(source_positions) != len(source_weights):
        raise ValueError(
            "source_positions and source_weights must have the same length "
            f"(got {len(source_positions)} vs {len(source_weights)})"
        )
    if not source_positions:
        return [{} for _ in target_positions]
    out: list[dict[str, float]] = []
    for target in target_positions:
        best_idx = nearest_index(target, source_positions, max_distance)
        out.append(dict(source_weights[best_idx]) if best_idx >= 0 else {})
    return out
