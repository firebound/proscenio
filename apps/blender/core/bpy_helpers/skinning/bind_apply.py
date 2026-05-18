"""Apply bind weights to a bpy mesh + write the WeightSidecar stub.

Wipes every vertex group EXCEPT ``proscenio_base_sprite`` (D3 UV
anchor must survive), recreates one group per deform bone, then
populates per-vert weights from the chosen ``BindMode``. After
weights succeed, stamps ``obj["proscenio_weight_sidecar"]`` with
the version-1 stub the Wave 13.2-sidecar wave consumes.
"""

from __future__ import annotations

import bpy

from ...skinning.planar_proximity import BoneSegmentNamed2D
from ...skinning.sidecar_schema import (
    build_minimal_stub,
    compute_topology_hash,
    to_json,
)
from ...skinning.skinning_modes import BindMode, bind_weights_for_mode

_BASE_SPRITE_GROUP = "proscenio_base_sprite"
_SIDECAR_KEY = "proscenio_weight_sidecar"
_ENVELOPE_RADIUS_KEY = "proscenio_envelope_radius"
_ENVELOPE_DEFAULT_RADIUS = 1.0
_ORPHAN_EPS = 1e-6
_ADAPTIVE_MAX_FACTOR = 1.5


def _wipe_non_base_groups(obj: bpy.types.Object) -> None:
    """Remove every vertex group except the UV-anchor base sprite group."""
    to_remove = [g for g in obj.vertex_groups if g.name != _BASE_SPRITE_GROUP]
    for group in to_remove:
        obj.vertex_groups.remove(group)


def _bone_segments_xz(
    armature: bpy.types.Object,
) -> list[BoneSegmentNamed2D]:
    """Project deform bones to XZ world-space (matches sprite plane)."""
    matrix_world = armature.matrix_world
    segments: list[BoneSegmentNamed2D] = []
    for bone in armature.data.bones:
        if not bone.use_deform:
            continue
        head = matrix_world @ bone.head_local
        tail = matrix_world @ bone.tail_local
        segments.append(((head.x, head.z), (tail.x, tail.z), bone.name))
    return segments


def _adaptive_max_distance(armature: bpy.types.Object) -> float:
    """1.5 * max extent of the armature's world-space bbox."""
    matrix_world = armature.matrix_world
    if not armature.data.bones:
        return 1.0
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    for bone in armature.data.bones:
        for point in (matrix_world @ bone.head_local, matrix_world @ bone.tail_local):
            xs.append(point.x)
            ys.append(point.y)
            zs.append(point.z)
    extent = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    return _ADAPTIVE_MAX_FACTOR * extent if extent > 0.0 else 1.0


def _collect_envelope_radii(armature: bpy.types.Object) -> dict[str, float]:
    """Read per-bone ``proscenio_envelope_radius`` Custom Property.

    Missing keys default to ``_ENVELOPE_DEFAULT_RADIUS`` (1.0).
    Edit Weights modal (Wave 13.2-paint) becomes the UI surface
    for these radii; bind alone exposes them via the manual
    Custom Property editor.
    """
    radii: dict[str, float] = {}
    for bone in armature.data.bones:
        if not bone.use_deform:
            continue
        radii[bone.name] = float(bone.get(_ENVELOPE_RADIUS_KEY, _ENVELOPE_DEFAULT_RADIUS))
    return radii


def apply_bind(
    obj: bpy.types.Object,
    armature: bpy.types.Object,
    mode: BindMode,
    *,
    falloff_power: float = 2.0,
    max_distance: float = -1.0,
    envelope_radii: dict[str, float] | None = None,
) -> dict[str, int]:
    """Bind ``obj`` to ``armature`` weights. Returns counters dict.

    Counters: ``verts_bound`` (total verts), ``orphan_verts``
    (sum-of-weights < eps), ``groups_created`` (one per deform bone),
    ``bones_used`` (count of bones in armature deform set).
    """
    bone_segments = _bone_segments_xz(armature)
    effective_max = (
        max_distance
        if max_distance >= 0.0
        else _adaptive_max_distance(armature)
    )
    effective_radii = (
        envelope_radii
        if envelope_radii is not None
        else _collect_envelope_radii(armature)
    )

    mesh = obj.data
    vert_positions_xz = [(v.co.x, v.co.z) for v in mesh.vertices]

    weights = bind_weights_for_mode(
        mode,
        vert_positions_xz,
        bone_segments,
        falloff_power=falloff_power,
        max_distance=effective_max if mode == "PROXIMITY" else None,
        envelope_radii=effective_radii,
    )

    _wipe_non_base_groups(obj)
    for bone_name in weights:
        obj.vertex_groups.new(name=bone_name)
    for bone_name, per_vert_weights in weights.items():
        group = obj.vertex_groups[bone_name]
        for vert_idx, weight in enumerate(per_vert_weights):
            if weight > 0.0:
                group.add([vert_idx], weight, "REPLACE")

    orphan_verts = 0
    for vert_idx in range(len(mesh.vertices)):
        total = sum(weights[name][vert_idx] for name in weights)
        if total < _ORPHAN_EPS:
            orphan_verts += 1

    topology_hash = compute_topology_hash(
        len(mesh.vertices),
        [list(p.vertices) for p in mesh.polygons],
    )
    sidecar = build_minimal_stub(list(weights.keys()), topology_hash)
    obj[_SIDECAR_KEY] = to_json(sidecar)

    return {
        "verts_bound": len(mesh.vertices),
        "orphan_verts": orphan_verts,
        "groups_created": len(weights),
        "bones_used": len(bone_segments),
    }
