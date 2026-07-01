"""GPU viewport overlay for the Quick Armature modal.

The two entry points (``draw_preview_3d`` POST_VIEW, ``draw_cursor_warning_2d``
POST_PIXEL) are registered as ``SpaceView3D`` draw handlers by the
operator, which passes its own class so the draw reads live modal state
(drag head, cursor, press mode, axis lock, ...). This module owns the
preview geometry + the color / anchor / axis constants so the operator
file stays focused on the modal state machine. The actual GL drawing
goes through the shared ``modal_overlay`` primitives.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import bpy
from mathutils import Vector

from ...core.armature.quick_armature_math import (  # type: ignore[import-not-found]
    BONE_TOO_SHORT_TOLERANCE,
    AxisLock,
    axis_guideline_endpoints,
    preview_color_for,
)
from ...core.bpy_helpers._shared.modal_overlay import (  # type: ignore[import-not-found]
    draw_circle_3d,
    draw_dashed_line_3d,
    draw_line_3d,
    draw_text_panel_2d,
)

if TYPE_CHECKING:
    from .quick_armature import PROSCENIO_OT_quick_armature

_AXIS_LINE_COLOR_X = (1.0, 0.3, 0.3, 0.9)
_AXIS_LINE_COLOR_Z = (0.3, 0.55, 1.0, 0.9)
_AXIS_LINE_HALF_LENGTH = 1000.0
_ANCHOR_RADIUS = 0.05
_ANCHOR_SEGMENTS = 12
_PREVIEW_LINE_WIDTH = 2.0

_CHEATSHEET_WARNING_TEXT_COLOR = (1.0, 0.55, 0.55, 1.0)


def draw_preview_3d(cls: type[PROSCENIO_OT_quick_armature]) -> None:
    head = cls._drag_head
    cursor = cls._cursor_world
    # Axis lock guideline renders even before the drag starts so the
    # user sees the constraint before pressing.
    if head is not None and cls._axis_lock is not None:
        _draw_axis_guideline(head, cls._axis_lock)
    if head is None or cursor is None:
        return
    color = _preview_color_for(cls)
    # Disconnected mode: head stays at the press point, so a dashed
    # line from the parent's tail keeps the parent link visible.
    if cls._press_mode == "disconnected":
        parent_tail = _resolve_parent_tail_world(cls)
        if parent_tail is not None:
            draw_dashed_line_3d(parent_tail, head, color)
    draw_line_3d(head, cursor, color, line_width=_PREVIEW_LINE_WIDTH)
    draw_circle_3d(
        head,
        _ANCHOR_RADIUS,
        color,
        plane_axis="Y",
        segments=_ANCHOR_SEGMENTS,
        line_width=_PREVIEW_LINE_WIDTH,
    )
    # In connected mode the head snapped to the parent tail; surface the
    # original press point as a faint marker to show how far it moved.
    press_point = cls._drag_press_point
    if (
        press_point is not None
        and cls._press_mode == "connected"
        and (Vector(press_point) - Vector(head)).length > BONE_TOO_SHORT_TOLERANCE
    ):
        draw_circle_3d(
            press_point,
            _ANCHOR_RADIUS * 0.6,
            (color[0], color[1], color[2], 0.35),
            plane_axis="Y",
            segments=_ANCHOR_SEGMENTS,
            line_width=1.0,
        )


def _resolve_parent_tail_world(
    cls: type[PROSCENIO_OT_quick_armature],
) -> tuple[float, float, float] | None:
    """Return the world-space tail of the most recent session bone.

    Used by the disconnected-mode dashed preview so the user sees the
    parent relationship even though the new bone's head sits at the
    press point (no auto-snap).
    """
    if not cls._last_bone_name:
        return None
    armature = bpy.data.objects.get(cls._target_armature_name)
    if armature is None or armature.type != "ARMATURE":
        return None
    bone = armature.data.bones.get(cls._last_bone_name)
    if bone is None:
        return None
    tail_world = armature.matrix_world @ bone.tail_local
    return (float(tail_world.x), float(tail_world.y), float(tail_world.z))


def _preview_color_for(
    cls: type[PROSCENIO_OT_quick_armature],
) -> tuple[float, float, float, float]:
    return preview_color_for(cls._cursor_in_canvas, cls._press_mode)


def _draw_axis_guideline(
    head: tuple[float, float, float],
    axis: AxisLock,
) -> None:
    """Render an infinite-looking axis line through the drag head.

    X=red, Z=blue. Only X and Z lock (the authoring plane is Y=0).
    """
    endpoints = axis_guideline_endpoints(head, axis, _AXIS_LINE_HALF_LENGTH)
    if endpoints is None:
        return
    start, end = endpoints
    color = _AXIS_LINE_COLOR_X if axis == "X" else _AXIS_LINE_COLOR_Z
    draw_line_3d(start, end, color, line_width=_PREVIEW_LINE_WIDTH)


def draw_cursor_warning_2d(cls: type[PROSCENIO_OT_quick_armature]) -> None:
    """Render a tooltip near the cursor when it leaves the canvas."""
    if cls._cursor_in_canvas:
        return
    region = cls._invoke_region
    if region is None:
        return
    region_x = cls._cursor_screen_x - region.x
    region_y = cls._cursor_screen_y - region.y
    # Offset so the tooltip does not sit under the cursor.
    tooltip_x = region_x + 16
    tooltip_y = region_y + 16
    draw_text_panel_2d(
        ("outside canvas",),
        region_width=region.width,
        region_height=region.height,
        align="top-left",
        margin=0,
        text_size=11,
        padding=4,
        bg_color=(0.35, 0.05, 0.05, 0.85),
        text_color=_CHEATSHEET_WARNING_TEXT_COLOR,
        origin_override=(tooltip_x, tooltip_y),
    )
