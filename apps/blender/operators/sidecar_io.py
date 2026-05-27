"""Export/Import the per-object weight sidecar to/from a JSON file (O3)."""

from __future__ import annotations

import json
from typing import ClassVar

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper


class PROSCENIO_OT_export_sidecar(bpy.types.Operator, ExportHelper):
    bl_idname = "proscenio.export_sidecar"
    bl_label = "Export Weight Sidecar"
    bl_description = (
        "Dump the active mesh's proscenio_weight_sidecar Custom Property to a JSON file"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER"}

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})  # type: ignore[valid-type]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return (
            obj is not None
            and obj.type == "MESH"
            and obj.get("proscenio_weight_sidecar") is not None
        )

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        payload = obj["proscenio_weight_sidecar"]
        text = payload if isinstance(payload, str) else json.dumps(payload)
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
    bl_label = "Import Weight Sidecar"
    bl_description = (
        "Load a JSON file into the active mesh's proscenio_weight_sidecar Custom Property"
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
            self.report({"WARNING"}, f"Failed to read sidecar: {exc}")
            return {"CANCELLED"}
        # Validate structure via the authoritative schema parser.
        from ..core.skinning.sidecar_schema import (
            from_json as _from_json,  # type: ignore[import-not-found]
        )

        try:
            _from_json(payload)
        except ValueError as exc:
            self.report({"WARNING"}, f"Invalid sidecar: {exc}")
            return {"CANCELLED"}
        context.active_object["proscenio_weight_sidecar"] = payload
        self.report({"INFO"}, f"Sidecar imported from {self.filepath}")
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
