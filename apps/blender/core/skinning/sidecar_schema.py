"""WeightSidecar schema.

Populated entries live here as ``SidecarEntry`` dataclasses keyed
by UV anchor + tagged with provenance. ``build_minimal_stub`` still
returns an empty-entries instance for pre-paint sprites; the bind
path swaps it for a populated snapshot in the sidecar work.

Pure Python: stdlib only (json + hashlib + dataclasses + typing).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, replace
from typing import Literal, cast, get_args

SIDECAR_VERSION = 1

#: How many rolling auto-snapshots a sidecar keeps (the oldest drop off).
AUTO_SNAPSHOT_CAP = 3

ProvenanceKind = Literal["auto_seed", "user_paint", "reprojected"]
_PROVENANCE_VALUES = frozenset(get_args(ProvenanceKind))

SnapshotKind = Literal["manual", "auto"]
_SNAPSHOT_KINDS = frozenset(get_args(SnapshotKind))


@dataclass(frozen=True)
class SidecarEntry:
    """One per-vert record: UV anchor + bone weights + how the weights got there."""

    uv_anchor: tuple[float, float]
    weights: dict[str, float]
    provenance: ProvenanceKind


@dataclass(frozen=True)
class NamedSnapshot:
    """A labelled restore point: a copy of the per-vert entries at save time.

    ``kind`` separates user-named manual save points (unbounded) from the
    rolling auto-snapshots captured per paint session (capped at
    :data:`AUTO_SNAPSHOT_CAP`).
    """

    name: str
    kind: SnapshotKind
    entries: list[SidecarEntry] = field(default_factory=list)


@dataclass(frozen=True)
class WeightSidecar:
    """Schema for ``obj["proscenio_weight_sidecar"]`` JSON payload."""

    version: int
    vertex_group_names: list[str]
    mesh_topology_hash: str
    entries: list[SidecarEntry] = field(default_factory=list)
    # Additive (pre-launch, no version bump): named restore points layered over
    # the baseline ``entries``. Old payloads parse with an empty list.
    snapshots: list[NamedSnapshot] = field(default_factory=list)


def add_named_snapshot(
    sidecar: WeightSidecar, name: str, entries: list[SidecarEntry]
) -> WeightSidecar:
    """Return ``sidecar`` with a manual snapshot ``name`` added (replacing a same-name one).

    Manual snapshots are unbounded; re-saving a name overwrites that save point
    rather than piling up duplicates.
    """
    kept = [s for s in sidecar.snapshots if not (s.kind == "manual" and s.name == name)]
    kept.append(NamedSnapshot(name=name, kind="manual", entries=list(entries)))
    return replace(sidecar, snapshots=kept)


def add_auto_snapshot(
    sidecar: WeightSidecar,
    name: str,
    entries: list[SidecarEntry],
    *,
    cap: int = AUTO_SNAPSHOT_CAP,
) -> WeightSidecar:
    """Return ``sidecar`` with an auto snapshot added, keeping only the last ``cap``.

    Manual snapshots are untouched; only the auto snapshots roll - the oldest
    drop off once more than ``cap`` exist.
    """
    snaps = [*sidecar.snapshots, NamedSnapshot(name=name, kind="auto", entries=list(entries))]
    auto_positions = [i for i, s in enumerate(snaps) if s.kind == "auto"]
    # Drop the oldest autos beyond `cap`; `cap == 0` drops them all (the
    # `[:-cap]` slice would wrongly keep everything when cap is 0).
    drop_count = max(0, len(auto_positions) - max(cap, 0))
    drop = set(auto_positions[:drop_count])
    return replace(sidecar, snapshots=[s for i, s in enumerate(snaps) if i not in drop])


def find_snapshot(sidecar: WeightSidecar, name: str) -> NamedSnapshot | None:
    """Return the snapshot named ``name`` (first match), or ``None``."""
    return next((s for s in sidecar.snapshots if s.name == name), None)


def weight_bearing_bone_names(entries: list[SidecarEntry]) -> list[str]:
    """Sorted union of every bone name carrying weight across ``entries``.

    The authoritative group set for restoring a snapshot: a :class:`NamedSnapshot`
    stores only its per-vert entries (no ``vertex_group_names`` of its own), so the
    groups to recreate are exactly the names its weights reference - not the live
    baseline's names, which a deform-bone rename / re-rig can have moved out from
    under it. Also used to detect a rig switch (prior weight bones not present in
    the new armature's deform bones).
    """
    return sorted({name for entry in entries for name in entry.weights})


def compute_topology_hash(vert_count: int, face_indices: list[list[int]]) -> str:
    """sha1 over vert count + flattened face index tuples.

    Pure content fingerprint to detect mesh topology changes between
    sidecar writes - not a security digest, so ``usedforsecurity=False``
    keeps the cheap sha1 while telling scanners collision resistance is
    irrelevant here.
    """
    payload_parts = [str(vert_count)]
    for face in face_indices:
        payload_parts.append(",".join(str(v) for v in face))
    payload = "|".join(payload_parts).encode("utf-8")
    return hashlib.sha1(payload, usedforsecurity=False).hexdigest()


def build_minimal_stub(vertex_group_names: list[str], topology_hash: str) -> WeightSidecar:
    """Build the empty-entries stub. Used as fallback when UV layer missing."""
    return WeightSidecar(
        version=SIDECAR_VERSION,
        vertex_group_names=list(vertex_group_names),
        mesh_topology_hash=topology_hash,
        entries=[],
    )


def to_json(sidecar: WeightSidecar) -> str:
    """Stable, indented JSON for sidecar payload. Tuples serialize as 2-lists."""
    return json.dumps(asdict(sidecar), indent=2, sort_keys=True)


def from_json(payload: str) -> WeightSidecar:
    """Parse + validate version + structure. Always raises ValueError on failure."""
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid sidecar JSON payload") from exc
    if not isinstance(data, dict):
        raise ValueError("sidecar payload must be a JSON object")
    try:
        version = int(data.get("version", -1))
    except (TypeError, ValueError) as exc:
        raise ValueError("sidecar version is invalid") from exc
    if version != SIDECAR_VERSION:
        raise ValueError(f"sidecar version {version} unsupported (expected {SIDECAR_VERSION})")
    if "mesh_topology_hash" not in data:
        raise ValueError("sidecar missing mesh_topology_hash")
    entries_raw = data.get("entries", [])
    if not isinstance(entries_raw, list):
        raise ValueError("sidecar entries must be a list")
    entries = [_entry_from_dict(item) for item in entries_raw]
    snapshots_raw = data.get("snapshots", [])
    if not isinstance(snapshots_raw, list):
        raise ValueError("sidecar snapshots must be a list")
    snapshots = [_snapshot_from_dict(item) for item in snapshots_raw]
    return WeightSidecar(
        version=version,
        vertex_group_names=list(data.get("vertex_group_names", [])),
        mesh_topology_hash=str(data["mesh_topology_hash"]),
        entries=entries,
        snapshots=snapshots,
    )


def count_entries_by_provenance(payload: str | None) -> dict[str, int] | None:
    """Count sidecar entries by provenance kind; None when there is no sidecar.

    A lenient summary for the weight panel's provenance pill: it parses the raw
    JSON (not the strict ``from_json``) so a version-mismatched or partial
    sidecar still surfaces its entry counts. A missing or unparseable payload
    returns None. Pure so the panel keeps the bpy Custom-Property read and this
    stays unit-testable without Blender.
    """
    if payload is None:
        return None
    try:
        data = json.loads(payload)
    except (ValueError, TypeError):
        return None
    # Explicit display order for the panel pill (user paint first).
    counts: dict[str, int] = {"user_paint": 0, "auto_seed": 0, "reprojected": 0}
    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        # A corrupt sidecar with a non-list "entries" (int, bool, ...) still
        # returns the zero counts rather than raising - the leniency contract.
        return counts
    for entry in entries:
        provenance = entry.get("provenance") if isinstance(entry, dict) else None
        if provenance in counts:
            counts[provenance] += 1
    return counts


def _snapshot_from_dict(item: object) -> NamedSnapshot:
    if not isinstance(item, dict):
        raise ValueError("sidecar snapshot must be a JSON object")
    kind = item.get("kind")
    if kind not in _SNAPSHOT_KINDS:
        raise ValueError(f"snapshot kind {kind!r} must be one of {sorted(_SNAPSHOT_KINDS)}")
    entries_raw = item.get("entries", [])
    if not isinstance(entries_raw, list):
        raise ValueError("snapshot entries must be a list")
    return NamedSnapshot(
        name=str(item.get("name", "")),
        kind=cast(SnapshotKind, kind),
        entries=[_entry_from_dict(entry) for entry in entries_raw],
    )


def _entry_from_dict(item: object) -> SidecarEntry:
    if not isinstance(item, dict):
        raise ValueError("sidecar entry must be a JSON object")
    anchor_raw = item.get("uv_anchor")
    if not isinstance(anchor_raw, list | tuple) or len(anchor_raw) != 2:
        raise ValueError("entry uv_anchor must be a length-2 array")
    weights_raw = item.get("weights", {})
    if not isinstance(weights_raw, dict):
        raise ValueError("entry weights must be a JSON object")
    provenance = item.get("provenance")
    if provenance not in _PROVENANCE_VALUES:
        raise ValueError(
            f"entry provenance {provenance!r} must be one of {sorted(_PROVENANCE_VALUES)}"
        )
    # float() raises TypeError on a non-number (None, dict, list); from_json's
    # contract is to always raise ValueError, so convert the failure mode.
    try:
        uv_anchor = (float(anchor_raw[0]), float(anchor_raw[1]))
        weights = {str(k): float(v) for k, v in weights_raw.items()}
    except (TypeError, ValueError) as exc:
        raise ValueError(f"sidecar entry has a non-numeric uv_anchor or weight: {exc}") from exc
    return SidecarEntry(
        uv_anchor=uv_anchor,
        weights=weights,
        provenance=cast(ProvenanceKind, provenance),
    )
