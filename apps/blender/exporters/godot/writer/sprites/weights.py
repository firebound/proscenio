"""Skinning weights: collect per-bone vertex weights into the wire format."""

from __future__ import annotations

import bpy
from proscenio_models import Weight

from .....core.bpy_helpers._shared._bpy_compat import (
    iter_vertex_groups,
    vertex_at,
)

_WEIGHT_EPS = 1e-9


def _resolve_known_groups(
    obj: bpy.types.Object,
    available_bones: set[str],
) -> dict[int, str]:
    """Return only the vertex groups whose names match real bones; warn for the rest."""
    vg_index_to_name = {int(vg.index): str(vg.name) for vg in iter_vertex_groups(obj)}
    known = {idx: name for idx, name in vg_index_to_name.items() if name in available_bones}
    skipped = sorted({n for n in vg_index_to_name.values() if n not in available_bones})
    for name in skipped:
        print(
            f"  WARN: sprite {obj.name!r} vertex group {name!r} has no "
            f"matching bone - dropping from weights"
        )
    return known


def _vertex_bone_weights(
    vertex: bpy.types.MeshVertex,
    known_groups: dict[int, str],
) -> dict[str, float]:
    """Sum per-bone weights for a single mesh vertex, ignoring unknown groups."""
    out: dict[str, float] = {}
    for vg in vertex.groups:
        bone = known_groups.get(int(vg.group))
        if bone is not None:
            out[bone] = out.get(bone, 0.0) + float(vg.weight)
    return out


def build_sprite_weights(
    obj: bpy.types.Object,
    mesh: bpy.types.Mesh,
    vertex_indices: list[int],
    *,
    fallback_bone: str,
    available_bones: set[str],
) -> list[Weight]:
    """Collect skinning weights from ``obj``'s vertex groups (the skinning-weights wire format)."""
    if not obj.vertex_groups or not vertex_indices:
        return []

    known_groups = _resolve_known_groups(obj, available_bones)
    if not known_groups:
        raise RuntimeError(
            f"Proscenio: sprite {obj.name!r} has vertex groups but none "
            f"resolve to bones in the armature - fix the group names or "
            f"remove them so the sprite can use rigid attach."
        )

    # Fallback bone for unweighted verts. The caller's fallback_bone can be a name
    # that does not resolve to a real bone (a non-bone attach name); fall back to a
    # deterministic real bone from known_groups (guaranteed non-empty above) so a
    # zero-weight vertex never ends up with an all-zero weight column = undeformed.
    effective_fallback = (
        fallback_bone
        if fallback_bone and fallback_bone in available_bones
        else min(known_groups.values())
    )

    n = len(vertex_indices)
    bone_to_values: dict[str, list[float]] = {name: [0.0] * n for name in known_groups.values()}
    bone_to_values.setdefault(effective_fallback, [0.0] * n)

    for slot, mesh_vi in enumerate(vertex_indices):
        weights_here = _vertex_bone_weights(vertex_at(mesh, mesh_vi), known_groups)
        total = sum(weights_here.values())
        if total > _WEIGHT_EPS:
            for bone, w in weights_here.items():
                bone_to_values[bone][slot] = w / total
        else:
            bone_to_values[effective_fallback][slot] = 1.0

    return [
        Weight(bone=bone, values=[round(v, 6) for v in values])
        for bone, values in bone_to_values.items()
        if any(abs(v) > _WEIGHT_EPS for v in values)
    ]
