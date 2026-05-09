"""Animation subpanel + actions UIList."""

from __future__ import annotations

from typing import ClassVar

import bpy

from ._helpers import draw_subpanel_header


class PROSCENIO_UL_actions(bpy.types.UIList):
    """List view for ``bpy.data.actions`` -- Animation subpanel uses this."""

    bl_idname = "PROSCENIO_UL_actions"

    def draw_item(
        self,
        _context: bpy.types.Context,
        layout: bpy.types.UILayout,
        _data: bpy.types.AnyType,
        item: bpy.types.AnyType,
        _icon: int,
        _active_data: bpy.types.AnyType,
        _active_propname: str,
    ) -> None:
        start, end = item.frame_range
        row = layout.row(align=True)
        row.label(text=item.name, icon="ACTION")
        row.label(text=f"[{start:.0f}-{end:.0f}]")


class PROSCENIO_PT_animation(bpy.types.Panel):
    """Read-only summary of the actions the writer would emit."""

    bl_label = "Animation"
    bl_idname = "PROSCENIO_PT_animation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "animation", "animation")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        actions = bpy.data.actions
        if not actions:
            layout.label(text="no actions to export", icon="INFO")
            return
        layout.template_list(
            "PROSCENIO_UL_actions",
            "",
            bpy.data,
            "actions",
            context.scene.proscenio,
            "active_action_index",
            rows=min(max(len(actions), 2), 6),
        )
        layout.label(text=f"{len(actions)} action(s) total", icon="INFO")


_classes: tuple[type, ...] = (
    PROSCENIO_UL_actions,
    PROSCENIO_PT_animation,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
