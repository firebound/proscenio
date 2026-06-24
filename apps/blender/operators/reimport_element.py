"""Operator: re-import a single Element from its source manifest entry.

Wraps :func:`importers.photoshop.reimport_element`. Surfaced as a button in
the Element panel. The source manifest path is remembered per object at first
import (``proscenio_import_manifest``); this operator reuses it silently and
only falls back to the file picker when that path is absent or the file is gone
(the spec 053 stale-folder re-pick).
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from ..core._shared.cp_keys import (  # type: ignore[import-not-found]
    PROSCENIO_IMPORT_MANIFEST,
)
from ..core._shared.report import (  # type: ignore[import-not-found]
    report_error,
    report_info,
    report_warn,
)
from ..core.psd import psd_manifest  # type: ignore[import-not-found]
from ..importers.photoshop import reimport_element  # type: ignore[import-not-found]


class PROSCENIO_OT_reimport_element(bpy.types.Operator, ImportHelper):
    """Re-import only the active Element from its source PSD manifest entry."""

    bl_idname = "proscenio.reimport_element"
    bl_label = "Proscenio: Re-import Element"
    bl_description = (
        "Refresh only the active Element from its source manifest entry, leaving "
        "every other Element untouched. Same-bounds keeps painted weights; a "
        "resized layer reprojects them"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})  # type: ignore[valid-type]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return obj is not None and obj.type == "MESH" and obj.get("proscenio_type") is not None

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        # One click when the Element remembers its source manifest and the file
        # still exists; otherwise fall back to the file browser to re-pick it.
        obj = context.active_object
        stored = obj.get(PROSCENIO_IMPORT_MANIFEST) if obj is not None else None
        if stored and Path(stored).exists():
            self.filepath = str(stored)
            return self.execute(context)
        return ImportHelper.invoke(self, context, event)

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            report_error(self, "no active Element to re-import")
            return {"CANCELLED"}
        path = Path(self.filepath)
        if not path.exists():
            report_error(self, f"Manifest not found: {path}")
            return {"CANCELLED"}
        try:
            result = reimport_element(obj, path)
        except psd_manifest.ManifestError as exc:
            report_error(self, f"Manifest invalid: {exc}")
            return {"CANCELLED"}
        except Exception as exc:
            # Surface anything to the user - operator must not crash the UI.
            report_error(self, f"Re-import failed: {exc}")
            return {"CANCELLED"}
        if result.status == "restamped":
            report_info(self, f"re-imported Element {result.layer_name!r}")
            return {"FINISHED"}
        # missing / skipped: a no-op that left the Element intact - report and
        # FINISH (not CANCELLED) so the warning surfaces and the undo step is clean.
        report_warn(self, result.warning or "Element left unchanged")
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_reimport_element,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
