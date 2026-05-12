"""Help subpanel - shortcut cheat-sheet for F3 search."""

from __future__ import annotations

from typing import ClassVar

import bpy

_OPERATOR_REFERENCE: tuple[tuple[str, str], ...] = (
    ("proscenio.validate_export", "Validate"),
    ("proscenio.export_godot", "Export Proscenio (.proscenio)"),
    ("proscenio.reexport_godot", "Re-export"),
    ("proscenio.import_photoshop", "Import Photoshop Manifest"),
    ("proscenio.create_ortho_camera", "Preview Camera"),
    ("proscenio.bake_current_pose", "Bake Current Pose"),
    ("proscenio.toggle_ik_chain", "Toggle IK"),
    ("proscenio.quick_armature", "Quick Armature"),
    ("proscenio.reproject_sprite_uv", "Reproject UV"),
    ("proscenio.snap_region_to_uv", "Snap region to UV bounds"),
    ("proscenio.pack_atlas", "Pack Atlas"),
    ("proscenio.apply_packed_atlas", "Apply Packed Atlas"),
    ("proscenio.unpack_atlas", "Unpack Atlas"),
    ("proscenio.select_issue_object", "Select Issue Object"),
    ("proscenio.select_outliner_object", "Select Outliner Object"),
    ("proscenio.toggle_outliner_favorite", "Toggle Outliner Favorite"),
    ("proscenio.smoke_test", "Smoke test (Hello Proscenio)"),
)


class PROSCENIO_PT_help(bpy.types.Panel):
    """Shortcut cheat-sheet - every Proscenio operator with its idname."""

    bl_label = "Help"
    bl_idname = "PROSCENIO_PT_help"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(text="Operators (use F3 to search):", icon="QUESTION")
        for idname, label in _OPERATOR_REFERENCE:
            row = layout.row(align=True)
            row.label(text=label)
            row.label(text=idname)


_classes: tuple[type, ...] = (PROSCENIO_PT_help,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
