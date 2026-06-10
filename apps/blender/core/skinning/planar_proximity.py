"""Planar proximity weight computation.

Pure-Python algorithm: for each vert, weight per bone =
1 / dist(vert, bone_segment) ** falloff_power, filtered by
max_distance, normalized so per-vert weights sum to 1.

Zero bpy import. Reuses ``distance_to_segment`` from
``core.automesh.density`` (already pure + tested).
"""

from __future__ import annotations

from .._shared.geometry_2d import Point2D
from ..automesh.density import distance_to_segment

BoneSegmentNamed2D = tuple[Point2D, Point2D, str]
"""((head_xz, tail_xz, bone_name)) - extends BoneSegment2D with the
group-name the bpy caller wants on the output dict."""

_DISTANCE_EPS = 1e-4
"""Floor for the distance before 1/d^p division.

Verts that land exactly on a bone segment would divide by zero;
clamping to 1e-4 produces a finite-but-dominant weight (1e8 at
power=2) that outranks any non-zero-distance bone by orders of
magnitude. Renormalization then pins the on-bone bone at ~1.0
and crushes the rest to ~0."""


def compute_proximity_weights(
    vert_xz: Point2D,
    bone_segments: list[BoneSegmentNamed2D],
    falloff_power: float = 2.0,
    max_distance: float | None = None,
) -> dict[str, float]:
    """Per-bone weight for one vert: 1/dist^power, filtered, normalized.

    Returns ``{}`` when no bone survives the ``max_distance`` filter -
    the bpy caller treats empty as orphan-vert signal.
    """
    raw: dict[str, float] = {}
    for head, tail, name in bone_segments:
        distance = distance_to_segment(vert_xz, (head, tail))
        if max_distance is not None and distance > max_distance:
            continue
        clamped = max(distance, _DISTANCE_EPS)
        raw[name] = 1.0 / (clamped**falloff_power)
    total = sum(raw.values())
    if total <= 0.0:
        return {}
    return {name: value / total for name, value in raw.items()}
