"""Pipeline panel - Import + Export accordion subpanels.

Was the Export panel. The parent is a grouper; the work lives in two
subpanels: Import (the Photoshop manifest importer) and Export (the
.proscenio writer + sticky path + pixels-per-unit). Validate + Preview
Camera ride along in the Export subpanel until Phase 3 relocates them to
the Validation + Helpers panels. The status badge + help button on each
subpanel header land with the header-convention pass (a later phase); the
parent keeps the existing ``export`` badge until the feature-id rename in
that same phase.
"""

from __future__ import annotations

import bpy

from ._helpers import draw_subpanel_header


def _scene_props(context: bpy.types.Context) -> bpy.types.AnyType | None:
    """Return the scene Proscenio props, or None."""
    return getattr(context.scene, "proscenio", None)


class PROSCENIO_PT_pipeline(bpy.types.Panel):
    """Pipeline - groups the Import + Export subpanels."""

    bl_label = "Pipeline"
    bl_idname = "PROSCENIO_PT_pipeline"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 10

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "pipeline", "pipeline_overview")

    def draw(self, context: bpy.types.Context) -> None:
        if _scene_props(context) is None:
            self.layout.label(text="proscenio scene props not registered", icon="ERROR")


class PROSCENIO_PT_import(bpy.types.Panel):
    """Import subpanel - the Photoshop manifest importer."""

    bl_label = "Import"
    bl_idname = "PROSCENIO_PT_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_pipeline"
    bl_order = 0

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "import", "import_photoshop")

    def draw(self, _context: bpy.types.Context) -> None:
        self.layout.operator(
            "proscenio.import_photoshop",
            text="Import Photoshop Manifest",
            icon="IMPORT",
        )


class PROSCENIO_PT_export(bpy.types.Panel):
    """Export subpanel - sticky path, ppu, validate, export, re-export.

    Validate + Preview Camera live here until Phase 3 moves them to the
    Validation + Helpers panels.
    """

    bl_label = "Export"
    bl_idname = "PROSCENIO_PT_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_pipeline"
    bl_order = 1

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "export", "export")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene_props = _scene_props(context)
        if scene_props is None:
            return
        layout.prop(scene_props, "last_export_path")
        layout.prop(scene_props, "pixels_per_unit")
        layout.separator()
        col = layout.column(align=True)
        col.operator("proscenio.export_godot", text="Export (.proscenio)", icon="EXPORT")
        if scene_props.last_export_path:
            col.operator("proscenio.reexport_godot", text="Re-export", icon="FILE_REFRESH")


_classes: tuple[type, ...] = (
    PROSCENIO_PT_pipeline,
    PROSCENIO_PT_import,
    PROSCENIO_PT_export,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
