"""Restore weight snapshot operator (the sidecar work, T10).

Reapplies the stored sidecar to the active mesh. Single
responsibility - reverts manual paint to the last saved bind /
auto-flow state. Does NOT trigger automesh regen; topology
mismatch is an error pointing the user to the auto-flow.
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core.bpy_helpers.skinning import apply_sidecar  # type: ignore[import-not-found]
from ..core.report import (  # type: ignore[import-not-found]
    report_error,
    report_info,
)
from ..core.skinning.sidecar_schema import (  # type: ignore[import-not-found]
    compute_topology_hash,
    from_json,
)

_SIDECAR_KEY = "proscenio_weight_sidecar"


class PROSCENIO_OT_restore_weight_snapshot(bpy.types.Operator):
    """Reapply the last saved weight sidecar to the active mesh."""

    bl_idname = "proscenio.restore_weight_snapshot"
    bl_label = "Reset to Last Saved Weights"
    bl_description = (
        "Reverts paint edits since the last Bind or Automesh regen, restoring "
        "the weight snapshot saved at that time. Does NOT trigger automesh "
        "regen - if topology has changed since the snapshot, the operator "
        "cancels with a hint to re-run automesh with preserve_on_regen ON"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return False
        return obj.get(_SIDECAR_KEY) is not None

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            report_error(self, "active object must be a mesh")
            return {"CANCELLED"}
        payload = obj.get(_SIDECAR_KEY)
        if payload is None:
            report_error(
                self,
                "no sidecar found on active mesh - run Bind to Picker Armature first",
            )
            return {"CANCELLED"}
        try:
            sidecar = from_json(payload)
        except ValueError as exc:
            report_error(
                self,
                f"existing sidecar is corrupt: {exc} - re-bind to reset",
            )
            return {"CANCELLED"}
        if not sidecar.entries:
            report_error(
                self,
                "sidecar has no entries (pre-wave bind) - re-bind to populate",
            )
            return {"CANCELLED"}
        current_hash = compute_topology_hash(
            len(obj.data.vertices),
            [list(p.vertices) for p in obj.data.polygons],
        )
        if current_hash != sidecar.mesh_topology_hash:
            report_error(
                self,
                "topology changed since last snapshot - run Automesh from Sprite "
                "with preserve_on_regen ON to re-establish the snapshot",
            )
            return {"CANCELLED"}
        counters = apply_sidecar(obj, sidecar)
        report_info(
            self,
            (f"restored {counters['verts_applied']} verts ({counters['groups_created']} groups)"),
        )
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_restore_weight_snapshot,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
