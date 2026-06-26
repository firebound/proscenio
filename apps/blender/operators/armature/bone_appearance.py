"""Bone appearance operator: color a whole bone collection at once.

``color_bone_collection`` batches ``bone.color`` over every bone in a collection,
since Blender has no native per-collection color. (A generated custom-shape
assignment used to live here too; it was dropped - a flat 2D widget cannot be
oriented reliably across a 2D rig's varying bone rolls, and the native
``display_type`` dropdown covers the bone-display need. See spec 069 decision 7.)
"""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import EnumProperty, FloatVectorProperty, StringProperty

from ...core._shared.report import report_warn  # type: ignore[import-not-found]
from ...core.bpy_helpers._shared.bone_collections import (  # type: ignore[import-not-found]
    iter_collection_bones,
)

#: Bone-color palette ids: DEFAULT (inherit), the 15 theme slots, and CUSTOM.
_PALETTE_ITEMS = (
    ("DEFAULT", "Default", "No themed color - inherit"),
    *[(f"THEME{i:02d}", f"Theme {i:02d}", f"Theme color {i:02d}") for i in range(1, 16)],
    ("CUSTOM", "Custom", "Use the custom color triplet below"),
)


class PROSCENIO_OT_color_bone_collection(bpy.types.Operator):
    """Apply a bone color to every bone in a collection in one click.

    Blender has no per-collection color, so this batches ``bone.color`` over the
    collection's data bones, leaving the pose-bone override at DEFAULT so the
    color stays consistent across pose. A theme palette by default, with a
    custom triplet when the palette is CUSTOM.
    """

    bl_idname = "proscenio.color_bone_collection"
    bl_label = "Proscenio: Color Bone Collection"
    bl_description = "Apply a bone color to every bone in this collection at once"
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        name="Armature",
        default="",
    )
    collection_name: StringProperty(  # type: ignore[valid-type]
        name="Bone collection",
        default="",
    )
    palette: EnumProperty(  # type: ignore[valid-type]
        name="Palette",
        items=_PALETTE_ITEMS,
        default="THEME01",
    )
    custom_normal: FloatVectorProperty(  # type: ignore[valid-type]
        name="Regular",
        subtype="COLOR",
        size=3,
        min=0.0,
        max=1.0,
        default=(0.8, 0.2, 0.2),
    )
    custom_select: FloatVectorProperty(  # type: ignore[valid-type]
        name="Selected",
        subtype="COLOR",
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 0.4, 0.4),
    )
    custom_active: FloatVectorProperty(  # type: ignore[valid-type]
        name="Active",
        subtype="COLOR",
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 0.6, 0.6),
    )

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "palette")
        if self.palette == "CUSTOM":
            layout.prop(self, "custom_normal")
            layout.prop(self, "custom_select")
            layout.prop(self, "custom_active")

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            report_warn(self, f"armature '{self.armature_name}' not found")
            return {"CANCELLED"}
        bones = iter_collection_bones(armature, self.collection_name)
        if not bones:
            report_warn(self, f"collection '{self.collection_name}' has no bones")
            return {"CANCELLED"}
        for bone in bones:
            bone.color.palette = self.palette
            if self.palette == "CUSTOM":
                bone.color.custom.normal = self.custom_normal
                bone.color.custom.select = self.custom_select
                bone.color.custom.active = self.custom_active
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_color_bone_collection,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
