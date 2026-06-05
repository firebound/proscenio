"""Automesh pre/post regen hook.

Pre-hook: snapshot current weights into a WeightSidecar.
Post-hook: reproject prior entries onto new topology + apply.

Both hooks are no-op-safe (return None / pass-through) when (a) no
picker armature, (b) PG preserve_on_regen flag OFF, (c) sprite has
no populated sidecar yet (legacy migration state).
"""

from __future__ import annotations

import bpy

from ..._shared.cp_keys import PROSCENIO_WEIGHT_SIDECAR as _SIDECAR_KEY
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


def maybe_pre_regen_snapshot(
    obj: bpy.types.Object, armature: bpy.types.Object | None
) -> WeightSidecar | None:
    """Snapshot current weights before automesh wipes the mesh.

    Returns None when the auto-flow should NOT engage:
    - no picker armature set
    - PG flag preserve_on_regen = False
    - obj has no existing sidecar AND no vertex_groups (nothing to snapshot)

    Mixed-flow fallback (M1): when no sidecar exists but vertex_groups are
    populated (e.g. user bound via Ctrl+P Armature Auto Weights without our
    bind operator), build the sidecar on-the-fly from current vgroup data so
    weights survive the next automesh regen.
    """
    if armature is None or armature.type != "ARMATURE":
        return None
    skinning = _get_skinning_props()
    if skinning is None or not bool(getattr(skinning, "preserve_on_regen", True)):
        return None
    payload = obj.get(_SIDECAR_KEY)
    if payload is not None:
        return _snapshot_from_existing_sidecar(obj, armature, payload)
    return _snapshot_from_vgroups_fallback(obj, armature)


def _snapshot_from_existing_sidecar(
    obj: bpy.types.Object,
    armature: bpy.types.Object,
    payload: str,
) -> WeightSidecar | None:
    """Happy path: existing sidecar present - snapshot from live vgroup state.

    Falls through to the vgroup fallback when (a) the JSON is corrupt or (b)
    the sidecar has zero entries. Without the fall-through, a corrupted or
    empty sidecar would silently wipe the user's vgroup-based weights on
    regen (the exact mixed-flow data-loss class M1 was meant to prevent).
    """
    try:
        existing = from_json(payload)
    except ValueError:
        return _snapshot_from_vgroups_fallback(obj, armature)
    if not existing.entries:
        return _snapshot_from_vgroups_fallback(obj, armature)
    return snapshot_sidecar(obj, armature, provenance="auto_seed")


def _snapshot_from_vgroups_fallback(
    obj: bpy.types.Object,
    armature: bpy.types.Object,
) -> WeightSidecar | None:
    """Mixed-flow fallback (M1): no sidecar but vertex_groups may carry weights.

    Covers Ctrl+P Armature Auto Weights bind (no sidecar written). Build
    sidecar on-the-fly so post-regen reproject can restore weights.
    """
    if not obj.vertex_groups or not _has_any_weight(obj):
        return None
    return snapshot_sidecar(obj, armature, provenance="auto_seed")


def _has_any_weight(obj: bpy.types.Object) -> bool:
    """Return True when at least one vert carries a non-trivial group weight."""
    for vert in obj.data.vertices:
        for group_elem in vert.groups:
            if group_elem.weight > 1e-6:
                return True
    return False


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
        # identical topology = entries reapply verbatim
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
        # target mesh has no UVs - skip reproject; mesh ends weightless
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
