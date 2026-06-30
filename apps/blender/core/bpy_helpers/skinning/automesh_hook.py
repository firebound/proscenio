"""Automesh pre/post regen hook.

Pre-hook: snapshot current weights into a WeightSidecar.
Post-hook: reproject prior entries onto new topology + apply.

Both hooks are no-op-safe (return None / pass-through) when (a) no
picker armature, (b) PG preserve_on_regen flag OFF, (c) sprite has
no populated sidecar yet (legacy migration state).
"""

from __future__ import annotations

from dataclasses import replace

import bpy

from ..._shared.cp_keys import PROSCENIO_WEIGHT_SIDECAR as _SIDECAR_KEY
from ..._shared.props_access import scene_skinning
from ..._shared.report import ReportTarget, report_warn
from ...skinning.sidecar_schema import (
    SIDECAR_VERSION,
    NamedSnapshot,
    SidecarEntry,
    WeightSidecar,
    compute_topology_hash,
    from_json,
    to_json,
    weight_bearing_bone_names,
)
from ...skinning.weight_reproject import reproject_entries
from .sidecar_io import apply_sidecar, per_vert_uv_anchors, snapshot_sidecar


def maybe_pre_regen_snapshot(
    obj: bpy.types.Object,
    armature: bpy.types.Object | None,
    op: ReportTarget | None = None,
) -> WeightSidecar | None:
    """Snapshot current weights before automesh wipes the mesh.

    Returns None when the auto-flow should NOT engage:
    - no picker armature set
    - PG flag preserve_on_regen = False
    - obj has no existing sidecar AND no vertex_groups (nothing to snapshot)

    Mixed-flow fallback: when no sidecar exists but vertex_groups are
    populated (e.g. user bound via Ctrl+P Armature Auto Weights without our
    bind operator), build the sidecar on-the-fly from current vgroup data so
    weights survive the next automesh regen.

    ``op`` (optional) receives a WARNING when a present-but-corrupt sidecar
    forces the vgroup fallback: that path can recover the live weights but not
    the painted-vs-auto provenance the corrupt CP carried, so the loss is
    surfaced rather than swallowed.
    """
    if armature is None or armature.type != "ARMATURE":
        return None
    skinning = _get_skinning_props()
    if skinning is None or not bool(getattr(skinning, "preserve_on_regen", True)):
        return None
    payload = obj.get(_SIDECAR_KEY)
    if payload is not None:
        return _snapshot_from_existing_sidecar(obj, armature, payload, op)
    return _snapshot_from_vgroups_fallback(obj, armature)


def _snapshot_from_existing_sidecar(
    obj: bpy.types.Object,
    armature: bpy.types.Object,
    payload: str,
    op: ReportTarget | None = None,
) -> WeightSidecar | None:
    """Existing sidecar present - snapshot from live vgroup state.

    Falls through to the vgroup fallback when (a) the JSON is corrupt or (b)
    the sidecar has zero entries. The fall-through is required: a corrupted or
    empty sidecar would otherwise silently wipe the user's vgroup-based weights
    on regen. The fallback rebuilds from live vgroups with a flat ``auto_seed``
    provenance, so any painted-vs-auto provenance the bad CP held is lost - warn
    ``op`` so that loss is visible, not silent.
    """
    try:
        existing = from_json(payload)
    except ValueError:
        _warn_provenance_loss(op, "sidecar is corrupt")
        return _snapshot_from_vgroups_fallback(obj, armature)
    if not existing.entries:
        _warn_provenance_loss(op, "sidecar has no entries")
        return _snapshot_from_vgroups_fallback(obj, armature)
    # Snapshot the live weights, then carry the prior sidecar's per-vert
    # provenance + its saved snapshots forward. snapshot_sidecar tags every
    # entry a flat auto_seed and keeps no snapshots, so without this carry a
    # regen would discard the painted-vs-auto provenance and every weight
    # snapshot - even on an identical-topology no-op regen.
    live = snapshot_sidecar(obj, armature, provenance="auto_seed")
    return _carry_provenance_and_snapshots(live, existing)


def _carry_provenance_and_snapshots(live: WeightSidecar, existing: WeightSidecar) -> WeightSidecar:
    """Overlay ``existing``'s per-vert provenance (matched by vertex index) and
    its named/rolling snapshots onto the live-weight ``live`` snapshot.

    The live snapshot carries the current weights (what must survive the wipe)
    but a flat auto_seed provenance and no snapshots; the prior sidecar carries
    the real provenance + the saved restore points. The post-regen reproject
    then resurrects ``user_paint`` from the carried provenance.
    """
    entries = [
        replace(entry, provenance=existing.entries[i].provenance)
        if i < len(existing.entries)
        else entry
        for i, entry in enumerate(live.entries)
    ]
    return replace(live, entries=entries, snapshots=list(existing.snapshots))


def _snapshot_from_vgroups_fallback(
    obj: bpy.types.Object,
    armature: bpy.types.Object,
) -> WeightSidecar | None:
    """Mixed-flow fallback: no sidecar but vertex_groups may carry weights.

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


def snapshot_live_vgroups(obj: bpy.types.Object) -> WeightSidecar | None:
    """Build a sidecar from obj's current vertex-group weights + UV anchors.

    Armature-free counterpart to ``snapshot_sidecar`` for the PSD re-import:
    when a mesh carries painted weights but no usable sidecar (a native Auto
    Weights bind writes none, or the stored one is corrupt), capture the live
    weights before a rebuild wipes them so the post-rebuild reproject has
    something to restore. Returns None when the mesh has no UV layer or no
    weighted vertex.
    """
    anchors = per_vert_uv_anchors(obj)
    if anchors is None:
        return None
    group_names = [vg.name for vg in obj.vertex_groups]
    if not group_names:
        return None
    entries: list[SidecarEntry] = []
    any_weight = False
    for vert in obj.data.vertices:
        weights: dict[str, float] = {}
        for group_elem in vert.groups:
            weight = group_elem.weight
            if weight > 1e-6:
                weights[obj.vertex_groups[group_elem.group].name] = weight
                any_weight = True
        entries.append(
            SidecarEntry(uv_anchor=anchors[vert.index], weights=weights, provenance="auto_seed")
        )
    if not any_weight:
        return None
    new_hash = compute_topology_hash(
        len(obj.data.vertices),
        [list(p.vertices) for p in obj.data.polygons],
    )
    return WeightSidecar(
        version=SIDECAR_VERSION,
        vertex_group_names=group_names,
        mesh_topology_hash=new_hash,
        entries=entries,
    )


def maybe_post_regen_reproject(
    obj: bpy.types.Object,
    armature: bpy.types.Object,
    prior_sidecar: WeightSidecar,
) -> dict[str, int]:
    """Reproject prior_sidecar entries onto obj's new topology + apply.

    Counters: {reprojected, auto_seed, total, topology_changed, rig_mismatch}.
    topology_changed = 1 when the new hash differs from prior, 0 when
    identical (entries reapplied as-is without going through reproject).
    rig_mismatch = 1 when the prior weights reference bones absent from the
    current armature's deform bones (a picker rig switch between bind and regen):
    the carried weights would orphan to dead groups, so the caller must warn
    rather than claim a clean preserve.
    """
    deform_bone_names = [b.name for b in armature.data.bones if b.use_deform]
    rig_mismatch = _rig_mismatch(prior_sidecar, deform_bone_names)
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
            "rig_mismatch": rig_mismatch,
        }
    new_anchors = per_vert_uv_anchors(obj)
    if new_anchors is None:
        # target mesh has no UVs - skip reproject; mesh ends weightless. The
        # prior snapshots are dropped here on purpose: without anchors they
        # cannot be reprojected onto the new topology, and carrying them raw
        # would leave a restore that scrambles old entries onto the new mesh.
        stub = snapshot_sidecar(obj, armature, provenance="auto_seed")
        obj[_SIDECAR_KEY] = to_json(stub)
        return {
            "reprojected": 0,
            "auto_seed": len(stub.entries),
            "total": len(stub.entries),
            "topology_changed": 1,
            "rig_mismatch": rig_mismatch,
        }
    counts = _reproject_and_apply(
        obj,
        prior_sidecar.entries,
        new_anchors,
        new_hash,
        deform_bone_names,
        prior_sidecar.snapshots,
    )
    counts["rig_mismatch"] = rig_mismatch
    return counts


def _reprojected_or_fallback(
    reprojected: SidecarEntry | None, anchor: tuple[float, float]
) -> SidecarEntry:
    """One reprojected entry, or an empty auto_seed entry when the anchor fell
    out of reproject range (so every new vert still gets a record)."""
    if reprojected is not None:
        return reprojected
    return SidecarEntry(uv_anchor=anchor, weights={}, provenance="auto_seed")


def _reproject_snapshots(
    snapshots: list[NamedSnapshot], new_anchors: list[tuple[float, float]]
) -> list[NamedSnapshot]:
    """Reproject each snapshot's entries onto the new anchors so the carried
    restore points stay valid for the NEW topology.

    A raw carry would leave old-topology entries on a sidecar stamped with the
    new hash; a later restore (which guards only on the top-level hash) would
    then apply those stale entries by index onto the new mesh, silently
    scrambling the weights.
    """
    out: list[NamedSnapshot] = []
    for snap in snapshots:
        raw = reproject_entries(snap.entries, new_anchors)
        entries = [_reprojected_or_fallback(raw[i], anchor) for i, anchor in enumerate(new_anchors)]
        out.append(replace(snap, entries=entries))
    return out


def _reproject_and_apply(
    obj: bpy.types.Object,
    prior_entries: list[SidecarEntry],
    new_anchors: list[tuple[float, float]],
    new_hash: str,
    vertex_group_names: list[str],
    snapshots: list[NamedSnapshot] | None = None,
) -> dict[str, int]:
    """Reproject prior entries onto new_anchors, apply, and persist the sidecar.

    Shared by the automesh regen hook (vertex_group_names = the armature's
    deform bones) and the PSD re-import (vertex_group_names = the surviving
    snapshot's own names, since no deform armature is in hand there).

    ``snapshots`` carries the prior sidecar's saved restore points forward,
    reprojected onto the new topology so a later restore stays safe.
    """
    raw_results = reproject_entries(prior_entries, new_anchors)
    final_entries: list[SidecarEntry] = []
    reprojected_count = 0
    auto_seed_count = 0
    for vert_idx, anchor in enumerate(new_anchors):
        if raw_results[vert_idx] is None:
            auto_seed_count += 1
        else:
            reprojected_count += 1
        final_entries.append(_reprojected_or_fallback(raw_results[vert_idx], anchor))
    new_sidecar = WeightSidecar(
        version=SIDECAR_VERSION,
        vertex_group_names=vertex_group_names,
        mesh_topology_hash=new_hash,
        entries=final_entries,
        snapshots=_reproject_snapshots(snapshots or [], new_anchors),
    )
    apply_sidecar(obj, new_sidecar)
    obj[_SIDECAR_KEY] = to_json(new_sidecar)
    return {
        "reprojected": reprojected_count,
        "auto_seed": auto_seed_count,
        "total": len(final_entries),
        "topology_changed": 1,
    }


def reproject_stored_sidecar(obj: bpy.types.Object) -> dict[str, int] | None:
    """Reproject the obj's stored weight snapshot onto its current topology.

    The PSD re-import rebuilds the quad on a bounds change, wiping vertex
    weights - but the painted weights live in the proscenio_weight_sidecar
    Custom Property, which is object-level and survives the geometry rebuild.
    Reproject those onto the fresh quad's UV anchors and reapply. Returns None
    when there is no usable snapshot or the mesh has no UV layer; no deform
    armature is needed (the snapshot carries its own vertex_group_names).
    """
    payload = obj.get(_SIDECAR_KEY)
    if payload is None:
        return None
    try:
        prior = from_json(payload)
    except ValueError:
        return None
    if not prior.entries:
        return None
    new_anchors = per_vert_uv_anchors(obj)
    if new_anchors is None:
        return None
    new_hash = compute_topology_hash(
        len(obj.data.vertices),
        [list(p.vertices) for p in obj.data.polygons],
    )
    return _reproject_and_apply(
        obj, prior.entries, new_anchors, new_hash, prior.vertex_group_names, prior.snapshots
    )


def _rig_mismatch(prior_sidecar: WeightSidecar, deform_bone_names: list[str]) -> int:
    """1 when prior weights reference a bone the current rig does not deform.

    A picker rig switch between bind and regen leaves the carried entries keyed
    by the OLD rig's bones; ``apply_sidecar`` only writes a weight when its group
    exists, so those weights silently orphan under the new rig. Flag it so the
    caller can warn instead of reporting a clean preserve. 0 when the prior
    carries no weights (nothing to orphan) or every weight bone still deforms.
    """
    prior_names = set(weight_bearing_bone_names(prior_sidecar.entries))
    if not prior_names:
        return 0
    return 0 if prior_names <= set(deform_bone_names) else 1


def _warn_provenance_loss(op: ReportTarget | None, reason: str) -> None:
    """Warn ``op`` (when present) that a corrupt/empty sidecar forced the vgroup
    fallback, which cannot recover the painted-vs-auto provenance."""
    if op is not None:
        report_warn(
            op,
            f"{reason} - rebuilt weights from vertex groups, but painted-vs-auto "
            "provenance could not be recovered",
            always=True,
        )


def _get_skinning_props() -> bpy.types.PropertyGroup | None:
    """Scene-scoped Proscenio skinning PG. None when scene / addon not registered."""
    return scene_skinning(bpy.context)
