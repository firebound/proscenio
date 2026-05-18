"""BindMode dispatcher (SPEC 013.2 bind, D5).

Translates a chosen ``BindMode`` to a per-bone-per-vert weight
matrix. PROXIMITY delegates to ``compute_proximity_weights`` per
vert + transposes. SINGLE_NEAREST picks the nearest bone per vert
(weight 1.0, tie-break = first in input order). ENVELOPE assigns
weight 1.0 inside the bone's radius, 0.0 outside. EMPTY emits
all-zero weights.

Pure Python: zero bpy import.
"""

from __future__ import annotations

from typing import Literal

from ..automesh.density import distance_to_segment
from .planar_proximity import BoneSegmentNamed2D, Point2D, compute_proximity_weights

BindMode = Literal["PROXIMITY", "ENVELOPE", "SINGLE_NEAREST", "EMPTY"]


def bind_weights_for_mode(
    mode: BindMode,
    vert_positions_xz: list[Point2D],
    bone_segments: list[BoneSegmentNamed2D],
    *,
    falloff_power: float = 2.0,
    max_distance: float | None = None,
    envelope_radii: dict[str, float] | None = None,
) -> dict[str, list[float]]:
    """Per-bone list of per-vert weights. Dispatches by mode."""
    if mode == "EMPTY":
        return _empty(vert_positions_xz, bone_segments)
    if mode == "SINGLE_NEAREST":
        return _single_nearest(vert_positions_xz, bone_segments)
    if mode == "ENVELOPE":
        return _envelope(vert_positions_xz, bone_segments, envelope_radii or {})
    if mode == "PROXIMITY":
        return _proximity(vert_positions_xz, bone_segments, falloff_power, max_distance)
    raise ValueError(f"unknown BindMode: {mode!r}")


def _empty(
    verts: list[Point2D], bones: list[BoneSegmentNamed2D]
) -> dict[str, list[float]]:
    return {name: [0.0] * len(verts) for _, _, name in bones}


def _single_nearest(
    verts: list[Point2D], bones: list[BoneSegmentNamed2D]
) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {name: [0.0] * len(verts) for _, _, name in bones}
    if not bones:
        return out
    for vert_idx, vert in enumerate(verts):
        best_name = bones[0][2]
        best_dist = distance_to_segment(vert, (bones[0][0], bones[0][1]))
        for head, tail, name in bones[1:]:
            distance = distance_to_segment(vert, (head, tail))
            if distance < best_dist:
                best_dist = distance
                best_name = name
        out[best_name][vert_idx] = 1.0
    return out


def _envelope(
    verts: list[Point2D],
    bones: list[BoneSegmentNamed2D],
    radii: dict[str, float],
) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {name: [0.0] * len(verts) for _, _, name in bones}
    for vert_idx, vert in enumerate(verts):
        for head, tail, name in bones:
            if name not in radii:
                continue
            radius = radii[name]
            if distance_to_segment(vert, (head, tail)) <= radius:
                out[name][vert_idx] = 1.0
    return out


def _proximity(
    verts: list[Point2D],
    bones: list[BoneSegmentNamed2D],
    falloff_power: float,
    max_distance: float | None,
) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {name: [0.0] * len(verts) for _, _, name in bones}
    for vert_idx, vert in enumerate(verts):
        per_bone = compute_proximity_weights(vert, bones, falloff_power, max_distance)
        for name, weight in per_bone.items():
            out[name][vert_idx] = weight
    return out
