"""Active Sprite subpanel (SPEC 005 + 5.1.c.1 + 5.1.d.1).

Thin dispatcher: picks the body subsection by sprite_type + active
mode, then defers to the per-mode draw module. Per-mode helpers live
in ``_draw_sprite_frame.py``, ``_draw_polygon.py``, and the shared
``_draw_region.py`` / ``_draw_driver_shortcut.py``.

Wave 9.10 of SPEC 009 split the 13 ``_draw_*`` helpers out of this
file so each draw concern owns its module.
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core import validation  # type: ignore[import-not-found]
from . import _draw_driver_shortcut, _draw_polygon, _draw_sprite_frame
from ._helpers import _OBJECT_FRIENDLY_MODES, draw_subpanel_header


def _draw_active_sprite_body(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    obj: bpy.types.Object,
    props: bpy.types.AnyType,
) -> None:
    """Pick the body subsection by sprite_type + active mode."""
    if props.sprite_type == "sprite_frame":
        _draw_sprite_frame.draw_body(layout, context, obj, props)
    elif context.mode == "PAINT_WEIGHT":
        _draw_polygon.draw_weight_paint(layout, context)
    else:
        _draw_polygon.draw_body(layout, obj, props)


class PROSCENIO_PT_active_sprite(bpy.types.Panel):
    """Per-sprite settings -- sprite type dropdown + sprite_frame metadata."""

    bl_label = "Active Sprite"
    bl_idname = "PROSCENIO_PT_active_sprite"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return False
        return context.mode in _OBJECT_FRIENDLY_MODES

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "active_sprite", "active_sprite")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        obj = context.active_object
        if obj is None:
            return

        props = getattr(obj, "proscenio", None)
        if props is None:
            layout.label(text="proscenio property group not registered", icon="ERROR")
            return

        layout.prop(props, "sprite_type")
        _draw_active_sprite_body(layout, context, obj, props)
        _draw_driver_shortcut.draw_box(layout, context, props)

        for issue in validation.validate_active_sprite(obj):
            row = layout.row()
            icon = "ERROR" if issue.severity == "error" else "INFO"
            row.alert = issue.severity == "error"
            row.label(text=issue.message, icon=icon)


_classes: tuple[type, ...] = (PROSCENIO_PT_active_sprite,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
