"""Active Element subpanel.

Thin dispatcher: picks the body subsection by element_type + active
mode, then defers to the per-mode draw module. Per-mode helpers live
in ``_draw_sprite.py``, ``_draw_mesh.py``, and the shared
``_draw_region.py`` / ``_draw_driver_shortcut.py``.

The code-modularity work split the 13 ``_draw_*`` helpers out of this
file so each draw concern owns its module.
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core import validation  # type: ignore[import-not-found]
from . import _draw_driver_shortcut, _draw_mesh, _draw_sprite
from ._helpers import _OBJECT_FRIENDLY_MODES, draw_subpanel_header


def _draw_active_element_body(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    obj: bpy.types.Object,
    props: bpy.types.AnyType,
) -> None:
    """Pick the body subsection by element_type + active mode."""
    if props.element_type == "sprite":
        _draw_sprite.draw_body(layout, context, obj, props)
    elif context.mode == "PAINT_WEIGHT":
        _draw_mesh.draw_weight_paint(layout, context)
    else:
        _draw_mesh.draw_body(layout, obj, props)


class PROSCENIO_PT_active_element(bpy.types.Panel):
    """Per-element settings - element type dropdown + sprite metadata."""

    bl_label = "Active Element"
    bl_idname = "PROSCENIO_PT_active_element"
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
        draw_subpanel_header(self.layout, "active_element", "active_element")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        obj = context.active_object
        if obj is None:
            return

        props = getattr(obj, "proscenio", None)
        if props is None:
            layout.label(text="proscenio property group not registered", icon="ERROR")
            return

        layout.prop(props, "element_type")
        _draw_active_element_body(layout, context, obj, props)
        _draw_driver_shortcut.draw_box(layout, context, props)

        for issue in validation.validate_active_element(obj):
            row = layout.row()
            icon = "ERROR" if issue.severity == "error" else "INFO"
            row.alert = issue.severity == "error"
            row.label(text=issue.message, icon=icon)


_classes: tuple[type, ...] = (PROSCENIO_PT_active_element,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
