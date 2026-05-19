"""WeightSidecar stub schema (SPEC 013.2 bind, Q3).

Bind writes a minimal stub: version + vertex_group_names +
topology_hash + entries=[]. Wave 13.2-sidecar populates entries
on user-driven paint events. Topology hash lets the sidecar wave
detect mesh edits that invalidate stored paint state.

Pure Python: stdlib only (json + hashlib + dataclasses).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field

SIDECAR_VERSION = 1


@dataclass(frozen=True)
class WeightSidecar:
    """Schema for ``obj["proscenio_weight_sidecar"]`` JSON payload."""

    version: int
    vertex_group_names: list[str]
    mesh_topology_hash: str
    entries: list[dict] = field(default_factory=list)  # type: ignore[type-arg]


def compute_topology_hash(vert_count: int, face_indices: list[list[int]]) -> str:
    """sha1 over vert count + flattened face index tuples.

    Hash is order-sensitive on both face order AND per-face vert
    order so winding flips invalidate cached weights (sidecar wave
    needs that signal). Returns hex digest.
    """
    payload_parts = [str(vert_count)]
    for face in face_indices:
        payload_parts.append(",".join(str(v) for v in face))
    payload = "|".join(payload_parts).encode("utf-8")
    return hashlib.sha1(payload).hexdigest()


def build_minimal_stub(vertex_group_names: list[str], topology_hash: str) -> WeightSidecar:
    """Build the version-1 empty-entries stub bind writes."""
    return WeightSidecar(
        version=SIDECAR_VERSION,
        vertex_group_names=list(vertex_group_names),
        mesh_topology_hash=topology_hash,
        entries=[],
    )


def to_json(sidecar: WeightSidecar) -> str:
    """Stable, indented JSON for sidecar payload."""
    return json.dumps(asdict(sidecar), indent=2, sort_keys=True)


def from_json(payload: str) -> WeightSidecar:
    """Parse + validate version + structure. Always raises ValueError on failure.

    Callers get one exception type to catch regardless of what went wrong
    (bad JSON / non-object root / missing required field / wrong version).
    """
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
    return WeightSidecar(
        version=version,
        vertex_group_names=list(data.get("vertex_group_names", [])),
        mesh_topology_hash=str(data["mesh_topology_hash"]),
        entries=list(data.get("entries", [])),
    )
