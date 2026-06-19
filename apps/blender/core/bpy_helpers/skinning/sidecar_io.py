"""Snapshot + reapply weight sidecar.

snapshot_sidecar reads obj's current vertex_groups + active UV layer
and builds a populated WeightSidecar. apply_sidecar writes the
entries back into vertex_groups, recreating groups as needed.

Missing UV layer = fall back to empty entries (matches build_minimal_stub).
The bind operator surfaces this as best-effort: bind still succeeds,
automesh-regen reproject simply skips later because entries==[].
"""

from __future__ import annotations

import time

import bpy

from ..._shared.cp_keys import PROSCENIO_WEIGHT_SIDECAR as _SIDECAR_KEY
from ...skinning.sidecar_schema import (
    SIDECAR_VERSION,
    NamedSnapshot,
    ProvenanceKind,
    SidecarEntry,
    WeightSidecar,
    add_auto_snapshot,
    compute_topology_hash,
    from_json,
    to_json,
)
from ._helpers import iter_deform_bones, wipe_non_base_groups


def snapshot_sidecar(
    obj: bpy.types.Object,
    armature: bpy.types.Object,
    *,
    provenance: ProvenanceKind = "auto_seed",
) -> WeightSidecar:
    """Build a WeightSidecar from obj's current vertex_groups + UV anchors.

    For each vert: read UV from active uv_layer's first loop containing
    it, read weight for each deform-bone vertex group. Tag all entries
    with the supplied provenance literal.

    UV layer missing = return empty-entries WeightSidecar (caller still
    gets the topology_hash + bone names for the stub).
    """
    mesh = obj.data
    deform_bone_names = [b.name for b in iter_deform_bones(armature)]
    topology_hash = compute_topology_hash(
        len(mesh.vertices),
        [list(p.vertices) for p in mesh.polygons],
    )
    uv_anchors = per_vert_uv_anchors(obj)
    if uv_anchors is None:
        return WeightSidecar(
            version=SIDECAR_VERSION,
            vertex_group_names=deform_bone_names,
            mesh_topology_hash=topology_hash,
            entries=[],
        )
    bone_group_indices = {
        obj.vertex_groups[name].index: name
        for name in deform_bone_names
        if name in obj.vertex_groups
    }
    entries: list[SidecarEntry] = []
    for vert_idx, vert in enumerate(mesh.vertices):
        weights: dict[str, float] = {}
        for group_elem in vert.groups:
            bone_name = bone_group_indices.get(group_elem.group)
            if bone_name is None:
                continue
            if group_elem.weight > 0.0:
                weights[bone_name] = float(group_elem.weight)
        entries.append(
            SidecarEntry(
                uv_anchor=uv_anchors[vert_idx],
                weights=weights,
                provenance=provenance,
            )
        )
    return WeightSidecar(
        version=SIDECAR_VERSION,
        vertex_group_names=deform_bone_names,
        mesh_topology_hash=topology_hash,
        entries=entries,
    )


def apply_sidecar(obj: bpy.types.Object, sidecar: WeightSidecar) -> dict[str, int]:
    """Write sidecar entries into obj's vertex groups.

    Wipes every vertex group EXCEPT proscenio_base_sprite (the UV
    anchor must survive), recreates one group per vertex_group_names
    entry, populates per-vert weights from entries[i].weights.

    Counters: {verts_applied, groups_created, missing_entry_verts}.
    missing_entry_verts is > 0 when sidecar.entries length differs from
    the mesh vert count - caller surfaces it as a WARN.
    """
    wipe_non_base_groups(obj)
    groups_created = 0
    for bone_name in sidecar.vertex_group_names:
        obj.vertex_groups.new(name=bone_name)
        groups_created += 1
    vert_count = len(obj.data.vertices)
    entry_count = len(sidecar.entries)
    verts_applied = min(vert_count, entry_count)
    for vert_idx in range(verts_applied):
        entry = sidecar.entries[vert_idx]
        for bone_name, weight in entry.weights.items():
            if bone_name not in obj.vertex_groups:
                continue
            if weight > 0.0:
                obj.vertex_groups[bone_name].add([vert_idx], weight, "REPLACE")
    return {
        "verts_applied": verts_applied,
        "groups_created": groups_created,
        "missing_entry_verts": max(0, vert_count - entry_count),
    }


def append_auto_snapshot(obj: bpy.types.Object, armature: bpy.types.Object) -> bool:
    """Capture the mesh's current weights as a rolling auto-snapshot.

    Reads the existing sidecar, snapshots the live vertex weights, appends them
    as an auto entry (the oldest auto rolls off past the cap), and writes the
    sidecar back. Returns ``False`` (no-op) when there is no sidecar yet, it is
    corrupt, the snapshot would be empty (no UV layer), or the live topology has
    drifted from the sidecar's hash (the snapshot could not be restored later,
    since restore guards on the hash). Best-effort: the Edit Weights modal calls
    this on a normal finish and must never let it raise.
    """
    payload = obj.get(_SIDECAR_KEY)
    if payload is None:
        return False
    try:
        sidecar = from_json(payload)
    except ValueError:
        return False
    current = snapshot_sidecar(obj, armature, provenance="user_paint")
    if not current.entries:
        return False
    if current.mesh_topology_hash != sidecar.mesh_topology_hash:
        return False
    # Sub-second suffix so two captures in the same second do not collide (restore
    # resolves a snapshot by name).
    now = time.time()
    name = f"auto {time.strftime('%H:%M:%S', time.localtime(now))}.{int(now * 1000) % 1000:03d}"
    obj[_SIDECAR_KEY] = to_json(add_auto_snapshot(sidecar, name, current.entries))
    return True


def read_snapshots(obj: bpy.types.Object) -> list[NamedSnapshot]:
    """Parse the named snapshots stored on the mesh, or ``[]`` when absent/corrupt."""
    payload = obj.get(_SIDECAR_KEY)
    if payload is None:
        return []
    try:
        return from_json(payload).snapshots
    except ValueError:
        return []


def per_vert_uv_anchors(obj: bpy.types.Object) -> list[tuple[float, float]] | None:
    """Active UV layer's value at each vert's first loop. None when no UV layer."""
    mesh = obj.data
    uv_layer = mesh.uv_layers.active if mesh.uv_layers else None
    if uv_layer is None:
        return None
    anchors: list[tuple[float, float]] = [(0.0, 0.0)] * len(mesh.vertices)
    seen: list[bool] = [False] * len(mesh.vertices)
    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            vert_idx = mesh.loops[loop_idx].vertex_index
            if seen[vert_idx]:
                continue
            uv = uv_layer.data[loop_idx].uv
            anchors[vert_idx] = (float(uv[0]), float(uv[1]))
            seen[vert_idx] = True
    return anchors
