"""Operator that wraps :func:`importers.photoshop.import_manifest`.

Surfaces a panel button + file picker for the photoshop importer PSD manifest
importer. Reports the number of stamped meshes (and any skipped
layers) via ``self.report`` so the user gets visible feedback in the
Blender info bar.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import bpy
from bpy.props import EnumProperty, StringProperty
from bpy_extras.io_utils import ImportHelper

from ..core._shared.report import (  # type: ignore[import-not-found]
    report_debug,
    report_error,
    report_info,
)
from ..core.psd import psd_manifest  # type: ignore[import-not-found]
from ..importers.photoshop import import_manifest  # type: ignore[import-not-found]


class PROSCENIO_OT_import_photoshop(bpy.types.Operator, ImportHelper):
    """Import a Photoshop layer manifest and stamp planes + stub armature."""

    bl_idname = "proscenio.import_photoshop"
    bl_label = "Proscenio: Import Photoshop Manifest"
    bl_description = (
        "Read a Photoshop manifest (the photoshop importer v1) and stamp one quad mesh "
        "per layer, plus a stub armature for posing"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})  # type: ignore[valid-type]

    placement: EnumProperty(  # type: ignore[valid-type]
        name="Placement",
        description="Where the imported figure sits relative to the world origin",
        items=[
            (
                "landed",
                "Landed (Feet on Z=0)",
                "Shift the figure so its lowest point sits on world Z=0. "
                "Matches the Godot / game-engine convention of pivoting "
                "characters at the feet.",
            ),
            (
                "centered",
                "Centered (Canvas at World Origin)",
                "Keep the figure centred around the manifest canvas centre "
                "(world origin). Useful when aligning multiple imports in a "
                "shared scene.",
            ),
        ],
        default="landed",
    )

    root_bone_name: StringProperty(  # type: ignore[valid-type]
        name="Root Bone Name",
        description=(
            "Name of the single bone created in the stub armature. Default "
            "is 'root'; rigs that prefer 'spine' or another identifier can "
            "override here."
        ),
        default="root",
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        path = Path(self.filepath)
        if not path.exists():
            report_error(self, f"Manifest not found: {path}")
            return {"CANCELLED"}
        try:
            result = import_manifest(
                path,
                placement=self.placement,
                root_bone_name=self.root_bone_name or "root",
            )
        except psd_manifest.ManifestError as exc:
            report_error(self, f"Manifest invalid: {exc}")
            return {"CANCELLED"}
        except Exception as exc:
            # Surface anything to the user - operator must not crash the UI.
            report_error(self, f"Import failed: {exc}")
            return {"CANCELLED"}
        msg = (
            f"stamped {len(result.meshes)} mesh(es)"
            f" (armature: {result.armature.name if result.armature else '<none>'})"
        )
        if result.skipped:
            msg += f"; skipped {len(result.skipped)}"
        if result.spritesheets:
            msg += f"; composed {len(result.spritesheets)} spritesheet(s)"
        report_info(self, msg)
        for obj in result.meshes:
            report_debug(self, f"stamped '{obj.name}' at z={obj.location.z:.4f}")
        for entry in result.skipped:
            report_debug(self, f"skipped layer {entry}")
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_import_photoshop,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
