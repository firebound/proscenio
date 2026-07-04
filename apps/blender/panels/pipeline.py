"""Pipeline panel - Import + Validate + Export accordion subpanels.

The first panel in the Proscenio tab and the grouper for the whole
PSD -> Blender -> Godot flow: Import (the Photoshop manifest importer),
Validate (the lazy validator + issue list), and Export (the .proscenio
writer + sticky path + pixels-per-unit + the export-target read-out).
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core._shared.armature_resolve import describe_export_target  # type: ignore[import-not-found]
from ..core.bpy_helpers.i18n import iface
from ._helpers import draw_subpanel_header


def _scene_props(context: bpy.types.Context) -> bpy.types.AnyType | None:
    """Return the scene Proscenio props, or None."""
    return getattr(context.scene, "proscenio", None)


class PROSCENIO_PT_pipeline(bpy.types.Panel):
    """Pipeline - the first panel; groups Import + Validate + Export."""

    bl_label = "Pipeline"
    bl_idname = "PROSCENIO_PT_pipeline"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 0
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "pipeline", "pipeline_overview")

    def draw(self, context: bpy.types.Context) -> None:
        if _scene_props(context) is None:
            self.layout.label(text=iface("proscenio scene props not registered"), icon="ERROR")


class PROSCENIO_PT_import(bpy.types.Panel):
    """Import subpanel - the Photoshop manifest importer."""

    bl_label = "Import"
    bl_idname = "PROSCENIO_PT_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_pipeline"
    bl_order = 0
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "import", "import_photoshop")

    def draw(self, _context: bpy.types.Context) -> None:
        self.layout.operator(
            "proscenio.import_photoshop",
            text="Import Photoshop Manifest",
            icon="IMPORT",
        )


class PROSCENIO_PT_export(bpy.types.Panel):
    """Export subpanel - the export-target read-out, sticky path, ppu, export."""

    bl_label = "Export"
    bl_idname = "PROSCENIO_PT_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_pipeline"
    bl_order = 2
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "export", "export")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene_props = _scene_props(context)
        if scene_props is None:
            return
        # The export-target read-out lives here (the panel that exports), not on
        # the Skeleton panel: "Exports: <name> (picked / first in scene)".
        described = describe_export_target(context.scene)
        if described is not None:
            name, picked = described
            source = "picked" if picked else "first in scene - no rig picked"
            layout.label(text=f"Exports: {name} ({source})", icon="ARMATURE_DATA")
        layout.prop(scene_props, "last_export_path")
        layout.prop(scene_props, "pixels_per_unit")
        layout.prop(scene_props, "bundle_textures")
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
