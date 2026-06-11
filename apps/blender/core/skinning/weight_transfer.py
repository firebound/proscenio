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


def summarize_transfer(per_target: Sequence[tuple[str, int, int]]) -> tuple[bool, str]:
    """Build the report for a weight transfer run.

    ``per_target`` is ``(target_name, verts_weighted, verts_total)`` per
    target. Returns ``(all_covered, message)``: ``all_covered`` is False when
    any target received zero coverage, so the caller reports WARNING (else
    INFO). The message always lists per-target coverage; on a miss it names the
    empty targets with the fix hint, since a target left fully beyond the
    radius otherwise reads as a successful no-op.
    """
    if not per_target:
        return True, "Weight transfer: no target meshes"
    parts = [f"{name}: {weighted}/{total} verts" for name, weighted, total in per_target]
    summary = "Weight transfer - " + "; ".join(parts)
    zero = [name for name, weighted, _ in per_target if weighted == 0]
    if zero:
        return False, (
            f"{summary}. No coverage for {', '.join(zero)} - "
            "raise Max Distance or move the meshes closer."
        )
    return True, summary
