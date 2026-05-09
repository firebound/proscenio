"""sprite_frame preview slicer setup / remove (SPEC 004 D13)."""

from __future__ import annotations

from typing import ClassVar

import bpy

from ...core.report import report_info, report_warn  # type: ignore[import-not-found]


class PROSCENIO_OT_setup_sprite_frame_preview(bpy.types.Operator):
    """Insert the SpriteFrameSlicer node group into the active mesh's material (D13)."""

    bl_idname = "proscenio.setup_sprite_frame_preview"
    bl_label = "Proscenio: Setup Preview Material"
    bl_description = (
        "Slice the spritesheet in the viewport via shader nodes + drivers. "
        "Switch to Material Preview mode (Z-key) to see the active cell."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return False
        props = getattr(obj, "proscenio", None)
        if props is None or str(getattr(props, "sprite_type", "")) != "sprite_frame":
            return False
        mesh = obj.data
        materials = getattr(mesh, "materials", None) or []
        return any(m is not None for m in materials)

    def execute(self, context: bpy.types.Context) -> set[str]:
        from ...core.bpy_helpers import sprite_frame_shader  # type: ignore[import-not-found]

        obj = context.active_object
        material = next((m for m in obj.data.materials if m is not None), None)
        if material is None:
            report_warn(self, "no material on this mesh")
            return {"CANCELLED"}
        applied = sprite_frame_shader.apply_slicer_to_material(
            material,
            obj=obj,
            node_groups=bpy.data.node_groups,
        )
        if not applied:
            report_warn(self, "material has no Image Texture node -- cannot slice")
            return {"CANCELLED"}
        report_info(
            self,
            f"slicer applied to '{material.name}' "
            "(Z-key for Material Preview to see the active cell)",
        )
        return {"FINISHED"}


class PROSCENIO_OT_remove_sprite_frame_preview(bpy.types.Operator):
    """Strip the SpriteFrameSlicer from the active mesh's material (D13)."""

    bl_idname = "proscenio.remove_sprite_frame_preview"
    bl_label = "Proscenio: Remove Preview Material"
    bl_description = (
        "Remove the SpriteFrameSlicer node + drivers; re-link the ImageTexture "
        "directly so the material renders the full atlas again."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return False
        mesh = obj.data
        materials = getattr(mesh, "materials", None) or []
        return any(m is not None for m in materials)

    def execute(self, context: bpy.types.Context) -> set[str]:
        from ...core.bpy_helpers import sprite_frame_shader

        obj = context.active_object
        removed = 0
        for material in obj.data.materials:
            if material is None:
                continue
            if sprite_frame_shader.remove_slicer_from_material(material):
                removed += 1
        if removed == 0:
            report_info(self, "no slicer to remove")
            return {"CANCELLED"}
        report_info(self, f"removed slicer from {removed} material(s)")
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_setup_sprite_frame_preview,
    PROSCENIO_OT_remove_sprite_frame_preview,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
