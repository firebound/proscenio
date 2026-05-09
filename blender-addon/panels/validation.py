"""Validation subpanel."""

from __future__ import annotations

import bpy

from ._helpers import draw_subpanel_header


class PROSCENIO_PT_validation(bpy.types.Panel):
    """Lazy validation results -- populated by the Validate operator."""

    bl_label = "Validation"
    bl_idname = "PROSCENIO_PT_validation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "validation", "validation")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene_props = getattr(context.scene, "proscenio", None)
        if scene_props is None:
            layout.label(text="proscenio scene props not registered", icon="ERROR")
            return

        if not scene_props.validation_ran:
            layout.label(text="run Validate to see issues", icon="INFO")
            return

        issues = list(scene_props.validation_results)
        if not issues:
            layout.label(text="no issues -- ready to export", icon="CHECKMARK")
            return

        for issue in issues:
            row = layout.row(align=True)
            row.alert = issue.severity == "error"
            icon = "ERROR" if issue.severity == "error" else "INFO"
            if issue.obj_name:
                op = row.operator(
                    "proscenio.select_issue_object",
                    text=f"[{issue.obj_name}] {issue.message}",
                    icon=icon,
                    emboss=False,
                )
                op.obj_name = issue.obj_name
            else:
                row.label(text=issue.message, icon=icon)


_classes: tuple[type, ...] = (PROSCENIO_PT_validation,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
