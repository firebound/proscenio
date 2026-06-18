"""Help panel - opens the in-panel help popup; carries the debug smoke test.

Replaces the old F3 operator cheat-sheet (which the panel rendered as an
unusable wall of idnames) with a single Open help button onto the existing
``proscenio.help`` popup. The Diagnostics panel folded in here: its lone
smoke-test button now shows under this panel when ``debug_mode`` is on.
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..addon_prefs import debug_mode_enabled
from ._helpers import draw_subpanel_header


class PROSCENIO_PT_help(bpy.types.Panel):
    """Help - opens the pipeline help popup; hosts the debug smoke test."""

    bl_label = "Help"
    bl_idname = "PROSCENIO_PT_help"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 12
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "help", "pipeline_overview")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        op = layout.operator("proscenio.help", text="Open help", icon="HELP")
        op.topic = "pipeline_overview"
        if debug_mode_enabled(context):
            layout.separator()
            layout.operator("proscenio.smoke_test", text="Run Smoke Test", icon="PLAY")


_classes: tuple[type, ...] = (PROSCENIO_PT_help,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
