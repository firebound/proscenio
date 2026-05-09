"""Diagnostics subpanel -- smoke test + future addon-health buttons."""

from __future__ import annotations

from typing import ClassVar

import bpy


class PROSCENIO_PT_diagnostics(bpy.types.Panel):
    """Smoke test + future addon-health buttons."""

    bl_label = "Diagnostics"
    bl_idname = "PROSCENIO_PT_diagnostics"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.operator("proscenio.smoke_test", text="Run Smoke Test", icon="PLAY")


_classes: tuple[type, ...] = (PROSCENIO_PT_diagnostics,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
