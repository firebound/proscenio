"""BindMode dispatcher.

Translates a chosen ``BindMode`` to a per-bone-per-vert weight
matrix, or None for BONE_HEAT sentinel. PROXIMITY delegates to
``compute_proximity_weights`` per vert + transposes. SINGLE_NEAREST
picks the nearest bone per vert (weight 1.0, tie-break = first in
input order). ENVELOPE assigns weight 1.0 inside the bone's radius,
0.0 outside. EMPTY emits all-zero weights. BONE_HEAT signals the bpy
caller to delegate to Blender's parent_set ARMATURE_AUTO instead.

Pure Python: zero bpy import.
"""

from __future__ import annotations

from typing import Literal

from .._shared.geometry_2d import Point2D
from ..automesh.density import distance_to_segment
from .planar_proximity import BoneSegmentNamed2D, compute_proximity_weights

BindMode = Literal["BONE_HEAT", "PROXIMITY", "ENVELOPE", "SINGLE_NEAREST", "EMPTY"]


def bind_weights_for_mode(
    mode: BindMode,
    vert_positions_xz: list[Point2D],
    bone_segments: list[BoneSegmentNamed2D],
    *,
    falloff_power: float = 2.0,
    max_distance: float | None = None,
    envelope_radii: dict[str, float] | None = None,
) -> dict[str, list[float]] | None:
    """Per-bone list of per-vert weights, or None for BONE_HEAT sentinel.

    BONE_HEAT signals the bpy caller to delegate to Blender's
    parent_set ARMATURE_AUTO; pure module returns None and the caller
    runs the bpy.ops branch instead of computing weights here.
    """
    if mode == "BONE_HEAT":
        return None
    if mode == "EMPTY":
        return _zero_weight_matrix(vert_positions_xz, bone_segments)
    if mode == "SINGLE_NEAREST":
        return _single_nearest(vert_positions_xz, bone_segments)
    if mode == "ENVELOPE":
        return _envelope(vert_positions_xz, bone_segments, envelope_radii or {})
    if mode == "PROXIMITY":
        return _proximity(vert_positions_xz, bone_segments, falloff_power, max_distance)
    raise ValueError(f"unknown BindMode: {mode!r}")


def _zero_weight_matrix(
    verts: list[Point2D], bones: list[BoneSegmentNamed2D]
) -> dict[str, list[float]]:
    """Per-bone list of ``len(verts)`` zeros: the base every bind mode fills in,
    and the whole output of the EMPTY mode."""
    return {name: [0.0] * len(verts) for _, _, name in bones}


def _single_nearest(
    verts: list[Point2D], bones: list[BoneSegmentNamed2D]
) -> dict[str, list[float]]:
    out = _zero_weight_matrix(verts, bones)
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
    """Per-vert weight 1/N across the N bones whose envelope covers it.

    Per-vert normalization is required so a vert
    inside K overlapping envelopes contributes weight 1.0 total (1/K to
    each bone), not K. Without this, Blender's Auto-Normalize silently
    rebalances at deform time and the user sees unpredictable weight
    redistribution.
    """
    out = _zero_weight_matrix(verts, bones)
    for vert_idx, vert in enumerate(verts):
        hits: list[str] = []
        for head, tail, name in bones:
            if name not in radii:
                continue
            if distance_to_segment(vert, (head, tail)) <= radii[name]:
                hits.append(name)
        if not hits:
            continue
        share = 1.0 / len(hits)
        for name in hits:
            out[name][vert_idx] = share
    return out


def _proximity(
    verts: list[Point2D],
    bones: list[BoneSegmentNamed2D],
    falloff_power: float,
    max_distance: float | None,
) -> dict[str, list[float]]:
    out = _zero_weight_matrix(verts, bones)
    for vert_idx, vert in enumerate(verts):
        per_bone = compute_proximity_weights(vert, bones, falloff_power, max_distance)
        for name, weight in per_bone.items():
            out[name][vert_idx] = weight
    return out
