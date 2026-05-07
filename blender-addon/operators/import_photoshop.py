"""Operator that wraps :func:`importers.photoshop.import_manifest`.

Surfaces a panel button + file picker for the SPEC 006 PSD manifest
importer. Reports the number of stamped meshes (and any skipped
layers) via ``self.report`` so the user gets visible feedback in the
Blender info bar.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from ..core import psd_manifest  # type: ignore[import-not-found]
from ..importers.photoshop import import_manifest  # type: ignore[import-not-found]


class PROSCENIO_OT_import_photoshop(bpy.types.Operator, ImportHelper):
    """Import a Photoshop layer manifest and stamp planes + stub armature."""

    bl_idname = "proscenio.import_photoshop"
    bl_label = "Proscenio: Import Photoshop Manifest"
    bl_description = (
        "Read a Photoshop manifest (SPEC 006 v1) and stamp one quad mesh "
        "per layer, plus a stub root armature for posing"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})  # type: ignore[valid-type]

    def execute(self, context: bpy.types.Context) -> set[str]:
        path = Path(self.filepath)
        if not path.exists():
            self.report({"ERROR"}, f"Manifest not found: {path}")
            return {"CANCELLED"}
        try:
            result = import_manifest(path)
        except psd_manifest.ManifestError as exc:
            self.report({"ERROR"}, f"Manifest invalid: {exc}")
            return {"CANCELLED"}
        except Exception as exc:
            # Surface anything to the user — operator must not crash the UI.
            self.report({"ERROR"}, f"Import failed: {exc}")
            return {"CANCELLED"}
        msg = (
            f"Proscenio: stamped {len(result.meshes)} mesh(es)"
            f" (armature: {result.armature.name if result.armature else '<none>'})"
        )
        if result.skipped:
            msg += f"; skipped {len(result.skipped)}"
        if result.spritesheets:
            msg += f"; composed {len(result.spritesheets)} spritesheet(s)"
        self.report({"INFO"}, msg)
        return {"FINISHED"}
