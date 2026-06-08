"""Helpers panel - viewport authoring aids that are not part of the pipeline.

Currently hosts the Preview Camera (orthographic front camera) used to
frame sprites the way the Godot importer expects, moved out of the
Pipeline panel. The status badge + help button land with the
header-convention pass (a later phase).
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ._helpers import draw_subpanel_header


class PROSCENIO_PT_helpers(bpy.types.Panel):
    """Helpers - viewport authoring aids (Preview Camera)."""

    bl_label = "Helpers"
    bl_idname = "PROSCENIO_PT_helpers"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 11
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "helpers", "helpers")

    def draw(self, _context: bpy.types.Context) -> None:
        self.layout.operator(
            "proscenio.create_ortho_camera",
            text="Preview Camera",
            icon="OUTLINER_OB_CAMERA",
        )


_classes: tuple[type, ...] = (PROSCENIO_PT_helpers,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
