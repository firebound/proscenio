"""Automesh pre/post regen hook (SPEC 013.2 sidecar, T11).

Pre-hook: snapshot current weights into a WeightSidecar.
Post-hook: reproject prior entries onto new topology + apply.

Both hooks are no-op-safe (return None / pass-through) when (a) no
picker armature, (b) PG preserve_on_regen flag OFF, (c) sprite has
no populated sidecar yet (pre-wave migration state).
"""

from __future__ import annotations

import bpy

from ...skinning.sidecar_schema import (
    SIDECAR_VERSION,
    SidecarEntry,
    WeightSidecar,
    compute_topology_hash,
    from_json,
    to_json,
)
from ...skinning.weight_reproject import reproject_entries
from .sidecar_io import apply_sidecar, per_vert_uv_anchors, snapshot_sidecar

_SIDECAR_KEY = "proscenio_weight_sidecar"


def maybe_pre_regen_snapshot(
    obj: bpy.types.Object, armature: bpy.types.Object | None
) -> WeightSidecar | None:
    """Snapshot current weights before automesh wipes the mesh.

    Returns None when the auto-flow should NOT engage:
    - no picker armature set
    - PG flag preserve_on_regen = False
    - obj has no existing sidecar OR existing sidecar has empty entries
      (= pre-wave-bound sprite that never went through populated bind)
    """
    if armature is None or armature.type != "ARMATURE":
        return None
    skinning = _get_skinning_props()
    if skinning is None or not bool(getattr(skinning, "preserve_on_regen", True)):
        return None
    payload = obj.get(_SIDECAR_KEY)
    if payload is None:
        return None
    try:
        existing = from_json(payload)
    except ValueError:
        return None
    if not existing.entries:
        return None
    return snapshot_sidecar(obj, armature, provenance="auto_seed")


def maybe_post_regen_reproject(
    obj: bpy.types.Object,
    armature: bpy.types.Object,
    prior_sidecar: WeightSidecar,
) -> dict[str, int]:
    """Reproject prior_sidecar entries onto obj's new topology + apply.

    Counters: {reprojected, auto_seed, total, topology_changed}.
    topology_changed = 1 when the new hash differs from prior, 0 when
    identical (entries reapplied as-is without going through reproject).
    """
    new_hash = compute_topology_hash(
        len(obj.data.vertices),
        [list(p.vertices) for p in obj.data.polygons],
    )
    if new_hash == prior_sidecar.mesh_topology_hash:
        # T4: identical topology = entries reapply verbatim
        applied = apply_sidecar(obj, prior_sidecar)
        obj[_SIDECAR_KEY] = to_json(prior_sidecar)
        return {
            "reprojected": 0,
            "auto_seed": 0,
            "total": applied["verts_applied"],
            "topology_changed": 0,
        }
    new_anchors = per_vert_uv_anchors(obj)
    if new_anchors is None:
        # T8: target mesh has no UVs - skip reproject; mesh ends weightless
        stub = snapshot_sidecar(obj, armature, provenance="auto_seed")
        obj[_SIDECAR_KEY] = to_json(stub)
        return {
            "reprojected": 0,
            "auto_seed": len(stub.entries),
            "total": len(stub.entries),
            "topology_changed": 1,
        }
    raw_results = reproject_entries(prior_sidecar.entries, new_anchors)
    deform_bone_names = [b.name for b in armature.data.bones if b.use_deform]
    final_entries: list[SidecarEntry] = []
    reprojected_count = 0
    auto_seed_count = 0
    for vert_idx, anchor in enumerate(new_anchors):
        candidate = raw_results[vert_idx]
        if candidate is None:
            final_entries.append(
                SidecarEntry(
                    uv_anchor=anchor,
                    weights={},
                    provenance="auto_seed",
                )
            )
            auto_seed_count += 1
        else:
            final_entries.append(candidate)
            reprojected_count += 1
    new_sidecar = WeightSidecar(
        version=SIDECAR_VERSION,
        vertex_group_names=deform_bone_names,
        mesh_topology_hash=new_hash,
        entries=final_entries,
    )
    apply_sidecar(obj, new_sidecar)
    obj[_SIDECAR_KEY] = to_json(new_sidecar)
    return {
        "reprojected": reprojected_count,
        "auto_seed": auto_seed_count,
        "total": len(final_entries),
        "topology_changed": 1,
    }


def _get_skinning_props() -> bpy.types.PropertyGroup | None:
    """Scene-scoped Proscenio skinning PG. None when scene / addon not registered."""
    scene = bpy.context.scene
    scene_props = getattr(scene, "proscenio", None) if scene else None
    return getattr(scene_props, "skinning", None) if scene_props else None
