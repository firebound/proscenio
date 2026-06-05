"""Per-stroke weight diff + provenance flip.

StrokeDiffTracker captures pre-stroke weights for the active vertex
group; after stroke, diffs against current state, flips touched
sidecar entries to provenance='user_paint', rewrites sidecar JSON.

One snapshot dict + one diff per stroke = bounded cost regardless
of brush motion path.
"""

from __future__ import annotations

import bpy

from ..._shared.cp_keys import PROSCENIO_WEIGHT_SIDECAR as _SIDECAR_KEY
from ...skinning.sidecar_schema import SidecarEntry, WeightSidecar, to_json
from ...skinning.weight_diff import diff_weights


class StrokeDiffTracker:
    """Per-stroke weight snapshot + provenance flip."""

    def __init__(self, obj: bpy.types.Object, sidecar: WeightSidecar) -> None:
        self._obj = obj
        self._sidecar = sidecar
        self._snapshot: dict[int, float] = {}
        self._active_group_name: str | None = None

    def snapshot_active_vg(self) -> None:
        """Capture weights for the currently-active vertex group."""
        group = self._obj.vertex_groups.active
        if group is None:
            self._snapshot = {}
            self._active_group_name = None
            return
        self._active_group_name = group.name
        self._snapshot = _read_group_weights(self._obj, group.index)

    def flip_touched_after_stroke(self) -> int:
        """Diff current vs snapshot, flip touched entries to user_paint.

        Returns touched count. No-op when snapshot is empty (e.g. mouse
        release without prior press) or active group missing.
        """
        if self._active_group_name is None:
            return 0
        group = self._obj.vertex_groups.get(self._active_group_name)
        if group is None:
            self._snapshot = {}
            self._active_group_name = None
            return 0
        current = _read_group_weights(self._obj, group.index)
        touched = diff_weights(self._snapshot, current)
        if not touched:
            self._snapshot = {}
            self._active_group_name = None
            return 0
        new_entries: list[SidecarEntry] = []
        for vert_idx, entry in enumerate(self._sidecar.entries):
            if vert_idx in touched:
                new_entries.append(
                    SidecarEntry(
                        uv_anchor=entry.uv_anchor,
                        weights=entry.weights,
                        provenance="user_paint",
                    )
                )
            else:
                new_entries.append(entry)
        self._sidecar = WeightSidecar(
            version=self._sidecar.version,
            vertex_group_names=self._sidecar.vertex_group_names,
            mesh_topology_hash=self._sidecar.mesh_topology_hash,
            entries=new_entries,
        )
        self._obj[_SIDECAR_KEY] = to_json(self._sidecar)
        self._snapshot = {}
        self._active_group_name = None
        return len(touched)

    @property
    def sidecar(self) -> WeightSidecar:
        """Latest sidecar state after any flips."""
        return self._sidecar


def _read_group_weights(obj: bpy.types.Object, group_index: int) -> dict[int, float]:
    """All verts whose weight in the group is > 0."""
    weights: dict[int, float] = {}
    for vert in obj.data.vertices:
        for elem in vert.groups:
            if elem.group == group_index and elem.weight > 0.0:
                weights[vert.index] = float(elem.weight)
                break
    return weights
