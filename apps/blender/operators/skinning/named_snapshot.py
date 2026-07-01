"""Named weight-snapshot operators: save the current weights, restore by name.

Manual save points layer over the baseline sidecar (the last Bind / Automesh
state) and the rolling auto-snapshots the Edit Weights modal captures. Save
records the live weights under a user name; restore reapplies a named snapshot's
weights (topology-guarded, same as Reset to Last Saved Weights).
"""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import StringProperty

from ...core._shared.cp_keys import (  # type: ignore[import-not-found]
    PROSCENIO_WEIGHT_SIDECAR as _SIDECAR_KEY,
)
from ...core._shared.props_access import active_armature  # type: ignore[import-not-found]
from ...core._shared.report import (  # type: ignore[import-not-found]
    report_error,
    report_info,
)
from ...core.bpy_helpers.skinning import (  # type: ignore[import-not-found]
    apply_sidecar,
    snapshot_sidecar,
    topology_hash_of,
)
from ...core.skinning.sidecar_schema import (  # type: ignore[import-not-found]
    WeightSidecar,
    add_named_snapshot,
    find_snapshot,
    from_json,
    to_json,
    weight_bearing_bone_names,
)


def _active_mesh_with_sidecar(context: bpy.types.Context) -> bpy.types.Object | None:
    obj = context.active_object
    if obj is None or obj.type != "MESH":
        return None
    return obj if obj.get(_SIDECAR_KEY) is not None else None


class PROSCENIO_OT_save_weight_snapshot(bpy.types.Operator):
    """Save the mesh's current weights as a named restore point."""

    bl_idname = "proscenio.save_weight_snapshot"
    bl_label = "Save Weight Snapshot"
    bl_description = (
        "Save the current vertex weights as a named restore point. Named "
        "snapshots are unbounded and survive .blend save/reload"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    snapshot_name: StringProperty(  # type: ignore[valid-type]
        name="Name",
        description="Label for this save point",
        default="snapshot",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_mesh_with_sidecar(context) is not None

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = _active_mesh_with_sidecar(context)
        if obj is None:
            report_error(self, "no sidecar on active mesh - run Bind to Target Armature first")
            return {"CANCELLED"}
        armature = active_armature(context)
        if armature is None:
            report_error(self, "no target armature - pick one in the Skeleton panel first")
            return {"CANCELLED"}
        name = self.snapshot_name.strip()
        if not name:
            report_error(self, "snapshot name cannot be empty")
            return {"CANCELLED"}
        try:
            sidecar = from_json(obj[_SIDECAR_KEY])
        except ValueError as exc:
            report_error(self, f"existing sidecar is corrupt: {exc} - re-bind to reset")
            return {"CANCELLED"}
        current = snapshot_sidecar(obj, armature, provenance="user_paint")
        if not current.entries:
            report_error(self, "no weights to snapshot (mesh has no UV layer)")
            return {"CANCELLED"}
        if current.mesh_topology_hash != sidecar.mesh_topology_hash:
            report_error(self, "topology changed since bind - re-bind before saving snapshots")
            return {"CANCELLED"}
        obj[_SIDECAR_KEY] = to_json(add_named_snapshot(sidecar, name, current.entries))
        report_info(self, f"saved snapshot '{name}'")
        return {"FINISHED"}


class PROSCENIO_OT_restore_named_snapshot(bpy.types.Operator):
    """Restore a named weight snapshot onto the active mesh."""

    bl_idname = "proscenio.restore_named_snapshot"
    bl_label = "Restore Weight Snapshot"
    bl_description = (
        "Reapply this named snapshot's weights to the active mesh. Cancels when "
        "the mesh topology changed since the snapshot was taken"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    snapshot_name: StringProperty(  # type: ignore[valid-type]
        name="Name",
        description="The snapshot to restore",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_mesh_with_sidecar(context) is not None

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = _active_mesh_with_sidecar(context)
        if obj is None:
            report_error(self, "no sidecar on active mesh - run Bind to Target Armature first")
            return {"CANCELLED"}
        try:
            sidecar = from_json(obj[_SIDECAR_KEY])
        except ValueError as exc:
            report_error(self, f"existing sidecar is corrupt: {exc} - re-bind to reset")
            return {"CANCELLED"}
        snapshot = find_snapshot(sidecar, self.snapshot_name)
        if snapshot is None:
            report_error(self, f"no snapshot named '{self.snapshot_name}'")
            return {"CANCELLED"}
        if not snapshot.entries:
            report_error(self, f"snapshot '{self.snapshot_name}' has no entries")
            return {"CANCELLED"}
        current_hash = topology_hash_of(obj)
        if current_hash != sidecar.mesh_topology_hash:
            report_error(
                self,
                "topology changed since this snapshot - run Automesh from Alpha "
                "with preserve_on_regen ON to re-establish it",
            )
            return {"CANCELLED"}
        # Recreate the groups the snapshot's own weights reference, NOT the live
        # baseline's vertex_group_names: a re-bind under a renamed deform bone
        # drifts the baseline names away from the snapshot's keys, and apply only
        # writes a weight when its bone group exists - so baseline names here
        # silently drop every snapshot weight (same topology, no error).
        restore_sidecar = WeightSidecar(
            version=sidecar.version,
            vertex_group_names=weight_bearing_bone_names(snapshot.entries),
            mesh_topology_hash=sidecar.mesh_topology_hash,
            entries=snapshot.entries,
        )
        counters = apply_sidecar(obj, restore_sidecar)
        report_info(
            self,
            f"restored '{self.snapshot_name}' ({counters['verts_applied']} verts)",
        )
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_save_weight_snapshot,
    PROSCENIO_OT_restore_named_snapshot,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
