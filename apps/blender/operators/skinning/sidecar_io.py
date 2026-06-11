"""Export/Import the per-object weight snapshot to/from a JSON file.

User-facing strings say "weight snapshot"; the on-disk Custom Property key
stays ``proscenio_weight_sidecar`` (internal). Import pushes the snapshot onto
the live vertex groups when the mesh topology still matches, mirroring the
restore_weight_snapshot guard - a mismatch is a stored-only outcome, not an
error.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, ClassVar

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

from ...core._shared.cp_keys import PROSCENIO_WEIGHT_SIDECAR  # type: ignore[import-not-found]
from ...core.bpy_helpers.skinning import apply_sidecar  # type: ignore[import-not-found]
from ...core.skinning.sidecar_schema import (  # type: ignore[import-not-found]
    compute_topology_hash,
    from_json,
)

if TYPE_CHECKING:
    from ...core.skinning.sidecar_schema import WeightSidecar


def _apply_if_topology_matches(obj: bpy.types.Object, sidecar: WeightSidecar) -> int | None:
    """Push the snapshot onto live vertex groups when topology matches.

    Returns the verts applied, or None when the snapshot has no entries or the
    live mesh topology differs (stored-only). Mirrors the topology guard in
    restore_weight_snapshot, but a mismatch here is an informational
    stored-only outcome rather than an error.
    """
    if not sidecar.entries:
        return None
    current_hash = compute_topology_hash(
        len(obj.data.vertices),
        [list(p.vertices) for p in obj.data.polygons],
    )
    if current_hash != sidecar.mesh_topology_hash:
        return None
    counters = apply_sidecar(obj, sidecar)
    return int(counters["verts_applied"])


class PROSCENIO_OT_export_sidecar(bpy.types.Operator, ExportHelper):
    bl_idname = "proscenio.export_sidecar"
    bl_label = "Export Weight Snapshot"
    bl_description = "Write the active mesh's weight snapshot to a JSON file"
    bl_options: ClassVar[set[str]] = {"REGISTER"}

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})  # type: ignore[valid-type]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return (
            obj is not None and obj.type == "MESH" and obj.get(PROSCENIO_WEIGHT_SIDECAR) is not None
        )

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        payload = obj[PROSCENIO_WEIGHT_SIDECAR]
        try:
            text = payload if isinstance(payload, str) else json.dumps(payload)
        except (TypeError, ValueError) as exc:
            self.report({"WARNING"}, f"Invalid sidecar payload for export: {exc}")
            return {"CANCELLED"}
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write(text)
        except OSError as exc:
            self.report({"WARNING"}, f"Failed to write sidecar: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Sidecar exported to {self.filepath}")
        return {"FINISHED"}


class PROSCENIO_OT_import_sidecar(bpy.types.Operator, ImportHelper):
    bl_idname = "proscenio.import_sidecar"
    bl_label = "Import Weight Snapshot"
    bl_description = (
        "Load a weight snapshot JSON onto the active mesh, applying it to the "
        "live weights when the mesh topology still matches"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})  # type: ignore[valid-type]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return obj is not None and obj.type == "MESH"

    def execute(self, context: bpy.types.Context) -> set[str]:
        try:
            with open(self.filepath, encoding="utf-8") as f:
                payload = f.read()
        except OSError as exc:
            # WARNING (not ERROR) so bpy.ops returns {"CANCELLED"} cleanly
            # instead of raising RuntimeError - lets headless tests assert.
            self.report({"WARNING"}, f"Failed to read weight snapshot: {exc}")
            return {"CANCELLED"}
        try:
            sidecar = from_json(payload)
        except ValueError as exc:
            self.report({"WARNING"}, f"Invalid weight snapshot: {exc}")
            return {"CANCELLED"}
        obj = context.active_object
        obj[PROSCENIO_WEIGHT_SIDECAR] = payload
        applied = _apply_if_topology_matches(obj, sidecar)
        if applied is None:
            self.report(
                {"INFO"},
                "Weight snapshot imported (stored only - topology differs; re-run "
                "Automesh from Alpha with Preserve weights on regen to reproject)",
            )
        else:
            self.report({"INFO"}, f"Weight snapshot imported and applied to {applied} verts")
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_export_sidecar,
    PROSCENIO_OT_import_sidecar,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
