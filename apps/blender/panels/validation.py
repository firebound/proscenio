"""Validate subpanel - lives under the Pipeline panel (Import / Validate / Export)."""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core.bpy_helpers.i18n import iface
from ._helpers import draw_issue_row, draw_subpanel_header


class PROSCENIO_PT_validation(bpy.types.Panel):
    """Lazy validation results - populated by the Validate operator.

    A subpanel of Pipeline, sitting between Import and Export so the run
    order reads top to bottom.
    """

    bl_label = "Validate"
    bl_idname = "PROSCENIO_PT_validation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_pipeline"
    bl_order = 1
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "validation", "validation")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene_props = getattr(context.scene, "proscenio", None)
        if scene_props is None:
            layout.label(text=iface("proscenio scene props not registered"), icon="ERROR")
            return

        layout.operator("proscenio.validate_export", text="Validate", icon="CHECKMARK")
        layout.separator()

        if not scene_props.validation_ran:
            layout.label(text=iface("run Validate to see issues"), icon="INFO")
            return

        issues = list(scene_props.validation_results)
        if not issues:
            layout.label(text=iface("no issues - ready to export"), icon="CHECKMARK")
            return

        for issue in issues:
            draw_issue_row(layout, issue)


_classes: tuple[type, ...] = (PROSCENIO_PT_validation,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
