"""Pure helpers for sidecar snapshot reconstruction.

Used by maybe_pre_regen_snapshot to rebuild a sidecar from current
vertex_groups state when no prior sidecar exists (mixed-flow case:
user bound via Ctrl+P Armature Auto Weights without our bind operator).
"""

from __future__ import annotations

from .sidecar_schema import SIDECAR_VERSION, SidecarEntry, WeightSidecar


def build_sidecar_from_vgroup_data(
    uvs: list[tuple[float, float]],
    weights_per_vert: list[dict[str, float]],
) -> WeightSidecar:
    """Pure constructor: build sidecar from parallel UV + weights lists.

    Provenance defaults to 'auto_seed' since vertex_group state alone
    carries no information about whether weights came from user paint
    or from a binding op. Conservative attribution per M2.

    Mismatched list lengths truncate to the shorter list - the bpy
    caller in skinning/__init__.py ensures equal lengths by iterating
    obj.data.vertices.
    """
    entries: list[SidecarEntry] = []
    for uv, weights in zip(uvs, weights_per_vert, strict=False):
        entries.append(SidecarEntry(uv_anchor=uv, weights=dict(weights), provenance="auto_seed"))
    return WeightSidecar(
        version=SIDECAR_VERSION,
        vertex_group_names=[],
        mesh_topology_hash="",
        entries=entries,
    )
