"""Export subpanel - sticky path, ppu, validate, export, re-export."""

from __future__ import annotations

import bpy

from ._helpers import draw_subpanel_header


class PROSCENIO_PT_export(bpy.types.Panel):
    """Export panel - sticky path, ppu, validate, export, re-export."""

    bl_label = "Export"
    bl_idname = "PROSCENIO_PT_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "export", "export")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene_props = getattr(context.scene, "proscenio", None)
        if scene_props is None:
            layout.label(text="proscenio scene props not registered", icon="ERROR")
            return

        layout.prop(scene_props, "last_export_path")
        layout.prop(scene_props, "pixels_per_unit")
        layout.operator(
            "proscenio.create_ortho_camera", text="Preview Camera", icon="OUTLINER_OB_CAMERA"
        )
        layout.separator()
        col = layout.column(align=True)
        col.operator("proscenio.validate_export", text="Validate", icon="CHECKMARK")
        col.operator("proscenio.export_godot", text="Export (.proscenio)", icon="EXPORT")
        if scene_props.last_export_path:
            col.operator("proscenio.reexport_godot", text="Re-export", icon="FILE_REFRESH")
        layout.separator()
        layout.operator(
            "proscenio.import_photoshop",
            text="Import Photoshop Manifest",
            icon="IMPORT",
        )


_classes: tuple[type, ...] = (PROSCENIO_PT_export,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
