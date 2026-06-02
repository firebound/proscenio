"""WeightSidecar schema (the sidecar work wave).

Populated entries live here as ``SidecarEntry`` dataclasses keyed
by UV anchor + tagged with provenance. ``build_minimal_stub`` still
returns an empty-entries instance for pre-paint sprites; the bind
path swaps it for a populated snapshot in this wave.

Pure Python: stdlib only (json + hashlib + dataclasses + typing).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Literal, cast, get_args

SIDECAR_VERSION = 1

ProvenanceKind = Literal["auto_seed", "user_paint", "reprojected"]
_PROVENANCE_VALUES = frozenset(get_args(ProvenanceKind))


@dataclass(frozen=True)
class SidecarEntry:
    """One per-vert record: UV anchor + bone weights + how the weights got there."""

    uv_anchor: tuple[float, float]
    weights: dict[str, float]
    provenance: ProvenanceKind


@dataclass(frozen=True)
class WeightSidecar:
    """Schema for ``obj["proscenio_weight_sidecar"]`` JSON payload."""

    version: int
    vertex_group_names: list[str]
    mesh_topology_hash: str
    entries: list[SidecarEntry] = field(default_factory=list)


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
    return WeightSidecar(
        version=version,
        vertex_group_names=list(data.get("vertex_group_names", [])),
        mesh_topology_hash=str(data["mesh_topology_hash"]),
        entries=entries,
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
    return SidecarEntry(
        uv_anchor=(float(anchor_raw[0]), float(anchor_raw[1])),
        weights={str(k): float(v) for k, v in weights_raw.items()},
        provenance=cast(ProvenanceKind, provenance),
    )
