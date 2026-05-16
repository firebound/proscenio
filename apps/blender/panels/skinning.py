"""Skinning subpanel (SPEC 013 Wave 13.1).

Parallel to ``PROSCENIO_PT_skeleton`` per D13. Surfaces the
Automesh + Bind + Edit Weights operators alongside the
``scene.proscenio.skinning`` defaults so the user can tune the
density / threshold / margin in context.

Wave 13.1 first cut ships only the Automesh sub-box. Bind +
Edit Weights buttons appear here in later Wave 13.1 commits;
they live behind ``# TODO(SPEC 013 follow-up)`` comments so
the layout shape is stable.
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ._helpers import draw_subpanel_header


class PROSCENIO_PT_skinning(bpy.types.Panel):
    """Skinning subpanel - automesh, bind, weight paint helpers."""

    bl_label = "Skinning"
    bl_idname = "PROSCENIO_PT_skinning"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return obj is not None and obj.type == "MESH"

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "skinning", "skinning")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene_props = getattr(context.scene, "proscenio", None)
        skinning_props = getattr(scene_props, "skinning", None) if scene_props is not None else None

        picker = getattr(scene_props, "active_armature", None) if scene_props is not None else None
        picker_row = layout.row(align=True)
        picker_row.label(text="", icon="ARMATURE_DATA")
        if picker is not None:
            picker_row.label(text=f"Picker: {picker.name}")
        else:
            picker_row.label(text="Picker: (none - set in Skeleton panel)", icon="INFO")

        _draw_automesh_box(layout, skinning_props)


def _draw_automesh_box(
    layout: bpy.types.UILayout,
    skinning_props: bpy.types.PropertyGroup | None,
) -> None:
    """Sub-box surfacing the Automesh defaults + the run button."""
    box = layout.box()
    box.label(text="Automesh from sprite", icon="OUTLINER_OB_MESH")
    if skinning_props is not None:
        col = box.column(align=True)
        col.prop(skinning_props, "automesh_resolution")
        col.prop(skinning_props, "automesh_alpha_threshold")
        col.prop(skinning_props, "automesh_margin_pixels")
        col.prop(skinning_props, "automesh_contour_vertices")
        col.prop(skinning_props, "automesh_interior_spacing")
        col.separator()
        col.prop(skinning_props, "automesh_density_under_bones")
        sub = col.column(align=True)
        sub.active = bool(skinning_props.automesh_density_under_bones)
        sub.prop(skinning_props, "automesh_bone_radius")
        sub.prop(skinning_props, "automesh_bone_factor")
    box.operator(
        "proscenio.automesh_from_sprite",
        text="Automesh from Sprite",
        icon="MOD_REMESH",
    )


_classes: tuple[type, ...] = (PROSCENIO_PT_skinning,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
