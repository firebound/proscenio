"""GPU draw handlers for the authoring modal (SPEC 013.2, T8 + T13).

POST_VIEW SpaceView3D handlers per stage. Reuses UNIFORM_COLOR shader
from modal_overlay. Polylines as LINE_STRIP batches; Steiner / user
dots as POINTS batches.

POST_PIXEL handler (_draw_tooltip) renders intent text near the mouse
cursor in Stage 2 (USER_OUTER) and Stage 4 (USER_STEINERS).
"""

from __future__ import annotations

import contextlib
from typing import TypedDict

import blf
import bpy
import gpu
from gpu_extras.batch import batch_for_shader

from ...skinning.authoring_stages import AuthoringStage, StageOutput, Stroke

_UNIFORM_COLOR_SHADER = "UNIFORM_COLOR"
_OUTER_COLOR = (0.0, 0.8, 1.0, 0.9)
_OUTER_DIM = (0.0, 0.4, 0.5, 0.5)
_INNER_BASE = (0.2, 1.0, 0.4, 0.85)
_INNER_DIM = (0.1, 0.5, 0.2, 0.5)
_STEINER_COLOR = (1.0, 0.3, 0.3, 0.7)
_USER_DOT_COLOR = (1.0, 1.0, 0.2, 0.95)
_STROKE_VERT_COLOR = (0.3, 0.7, 1.0, 1.0)
_RAW_STROKE_COLOR = (0.6, 0.6, 0.6, 0.7)
_LINE_WIDTH = 2.0
_DOT_SIZE_USER = 8.0
_DOT_SIZE_STEINER = 4.0
_DOT_SIZE_STROKE_VERT = 6.0

# Tooltip (POST_PIXEL) draw constants
_TOOLTIP_FONT_ID = 0  # default blf font
_TOOLTIP_FONT_SIZE = 11
_TOOLTIP_OFFSET_X = 15  # px right of mouse
_TOOLTIP_OFFSET_Y = -15  # px below mouse (viewport Y is bottom-up)
_TOOLTIP_COLOR = (1.0, 1.0, 1.0, 1.0)
_TOOLTIP_SHADOW_COLOR = (0.0, 0.0, 0.0, 0.8)


class OverlayHandles(TypedDict):
    """Draw handler refs returned by register_overlay; None when stage
    does not draw that primitive."""

    outer: object | None
    inner: object | None
    steiners: object | None
    user_dots: object | None
    user_strokes: object | None
    raw_stroke: object | None
    tooltip: object | None  # POST_PIXEL intent text; Stage 2 + Stage 4 only


def _draw_tooltip(
    mouse_pos_ref: list[tuple[int, int]],
    text_ref: list[str],
) -> None:
    """POST_PIXEL draw handler: render intent text near mouse cursor.

    Both args are single-element lists so the operator can mutate them
    without re-registering this handler (same pattern as _stroke_raw_points /
    _stroke_active_ref). Nothing is drawn when mouse is outside the region
    (mouse_region_x < 0) or when text is empty.
    """
    if not text_ref or not text_ref[0]:
        return
    if not mouse_pos_ref:
        return
    mx, my = mouse_pos_ref[0]
    if mx < 0 or my < 0:
        return
    text = text_ref[0]
    blf.size(_TOOLTIP_FONT_ID, _TOOLTIP_FONT_SIZE)
    # Shadow pass (offset 1 px down-right for legibility on any bg)
    blf.color(_TOOLTIP_FONT_ID, *_TOOLTIP_SHADOW_COLOR)
    blf.position(_TOOLTIP_FONT_ID, mx + _TOOLTIP_OFFSET_X + 1, my + _TOOLTIP_OFFSET_Y - 1, 0)
    blf.draw(_TOOLTIP_FONT_ID, text)
    # White text on top
    blf.color(_TOOLTIP_FONT_ID, *_TOOLTIP_COLOR)
    blf.position(_TOOLTIP_FONT_ID, mx + _TOOLTIP_OFFSET_X, my + _TOOLTIP_OFFSET_Y, 0)
    blf.draw(_TOOLTIP_FONT_ID, text)


def _register_interactive_handlers(
    handles: OverlayHandles,
    user_strokes: list[Stroke] | None,
    stroke_active_ref: list[bool] | None,
    stroke_raw_points_ref: list[tuple[float, float]] | None,
    tooltip_mouse_ref: list[tuple[int, int]] | None,
    tooltip_text_ref: list[str] | None,
) -> None:
    """Register draw handlers for interactive stages (USER_OUTER, USER_STEINERS).

    Covers committed strokes, in-progress raw stroke preview, and the
    POST_PIXEL intent tooltip. All handlers receive mutable container
    references so they always see the latest operator state without
    needing re-registration on MOUSEMOVE.
    """
    if user_strokes is not None:
        handles["user_strokes"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_user_strokes,
            (user_strokes,),
            "WINDOW",
            "POST_VIEW",
        )
    if stroke_active_ref is not None and stroke_raw_points_ref is not None:
        handles["raw_stroke"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_raw_stroke,
            (stroke_active_ref, stroke_raw_points_ref),
            "WINDOW",
            "POST_VIEW",
        )
    if tooltip_mouse_ref is not None and tooltip_text_ref is not None:
        handles["tooltip"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_tooltip,
            (tooltip_mouse_ref, tooltip_text_ref),
            "WINDOW",
            "POST_PIXEL",
        )


def register_overlay(
    stage: AuthoringStage,
    output: StageOutput,
    user_strokes: list[Stroke] | None = None,
    stroke_active_ref: list[bool] | None = None,
    stroke_raw_points_ref: list[tuple[float, float]] | None = None,
    tooltip_mouse_ref: list[tuple[int, int]] | None = None,
    tooltip_text_ref: list[str] | None = None,
) -> OverlayHandles:
    """Add POST_VIEW draw handlers per stage's overlay set.

    For Stage 3 (USER_STEINERS) and Stage 4 (STEINER_PREVIEW), pass the live mutable containers:
    - user_strokes: the operator's _user_strokes list (by reference)
    - stroke_active_ref: single-element list wrapping _stroke_active bool (Stage 3 only)
    - stroke_raw_points_ref: the operator's _stroke_raw_points list (by reference, Stage 3 only)
    - tooltip_mouse_ref: single-element list with (mouse_region_x, mouse_region_y) in pixels
    - tooltip_text_ref: single-element list with current intent text string

    The draw callbacks hold references to these containers so they always
    see the current live state without needing re-registration on each
    MOUSEMOVE event.
    """
    handles: OverlayHandles = {
        "outer": None,
        "inner": None,
        "steiners": None,
        "user_dots": None,
        "user_strokes": None,
        "raw_stroke": None,
        "tooltip": None,
    }
    if stage >= AuthoringStage.OUTER and output.outer:
        color = _OUTER_COLOR if stage == AuthoringStage.OUTER else _OUTER_DIM
        handles["outer"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_polyline,
            (list(output.outer), color, _LINE_WIDTH),
            "WINDOW",
            "POST_VIEW",
        )
    if stage >= AuthoringStage.INNER_LOOPS and output.inner_loops:
        color = _INNER_BASE if stage == AuthoringStage.INNER_LOOPS else _INNER_DIM
        handles["inner"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_polylines,
            (list(output.inner_loops), color, _LINE_WIDTH),
            "WINDOW",
            "POST_VIEW",
        )
    if stage >= AuthoringStage.USER_STEINERS and output.user_steiners:
        handles["user_dots"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_points,
            (list(output.user_steiners), _USER_DOT_COLOR, _DOT_SIZE_USER),
            "WINDOW",
            "POST_VIEW",
        )
    if stage in (AuthoringStage.USER_OUTER, AuthoringStage.USER_STEINERS):
        _register_interactive_handlers(
            handles,
            user_strokes,
            stroke_active_ref,
            stroke_raw_points_ref,
            tooltip_mouse_ref,
            tooltip_text_ref,
        )
    if stage >= AuthoringStage.STEINER_PREVIEW and output.all_steiners:
        handles["steiners"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_points,
            (list(output.all_steiners), _STEINER_COLOR, _DOT_SIZE_STEINER),
            "WINDOW",
            "POST_VIEW",
        )
    if stage >= AuthoringStage.STEINER_PREVIEW and user_strokes is not None:
        handles["user_strokes"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_user_strokes,
            (user_strokes,),
            "WINDOW",
            "POST_VIEW",
        )
    return handles


def unregister_overlay(handles: OverlayHandles) -> None:
    """No-op-safe cleanup; tolerates partial registration."""
    for key in ("outer", "inner", "steiners", "user_dots", "user_strokes", "raw_stroke", "tooltip"):
        handle = handles.get(key)
        if handle is None:
            continue
        with contextlib.suppress(ValueError, RuntimeError):
            bpy.types.SpaceView3D.draw_handler_remove(handle, "WINDOW")
        handles[key] = None


def refresh_overlay(
    handles: OverlayHandles,
    stage: AuthoringStage,
    output: StageOutput,
    user_strokes: list[Stroke] | None = None,
    stroke_active_ref: list[bool] | None = None,
    stroke_raw_points_ref: list[tuple[float, float]] | None = None,
    tooltip_mouse_ref: list[tuple[int, int]] | None = None,
    tooltip_text_ref: list[str] | None = None,
) -> OverlayHandles:
    """Replace handlers when stage data changes (slider drag or stage advance)."""
    unregister_overlay(handles)
    return register_overlay(
        stage,
        output,
        user_strokes=user_strokes,
        stroke_active_ref=stroke_active_ref,
        stroke_raw_points_ref=stroke_raw_points_ref,
        tooltip_mouse_ref=tooltip_mouse_ref,
        tooltip_text_ref=tooltip_text_ref,
    )


def _draw_polyline(
    points: list[tuple[float, float]],
    color: tuple[float, float, float, float],
    line_width: float,
) -> None:
    if len(points) < 2:
        return
    verts = [(p[0], 0.0, p[1]) for p in points] + [(points[0][0], 0.0, points[0][1])]
    shader = gpu.shader.from_builtin(_UNIFORM_COLOR_SHADER)
    batch = batch_for_shader(shader, "LINE_STRIP", {"pos": verts})
    gpu.state.blend_set("ALPHA")
    gpu.state.line_width_set(line_width)
    try:
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)
    finally:
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set("NONE")


def _draw_polylines(
    polylines: list[list[tuple[float, float]]],
    color: tuple[float, float, float, float],
    line_width: float,
) -> None:
    shader = gpu.shader.from_builtin(_UNIFORM_COLOR_SHADER)
    gpu.state.blend_set("ALPHA")
    gpu.state.line_width_set(line_width)
    try:
        for line in polylines:
            if len(line) < 2:
                continue
            verts = [(p[0], 0.0, p[1]) for p in line] + [(line[0][0], 0.0, line[0][1])]
            batch = batch_for_shader(shader, "LINE_STRIP", {"pos": verts})
            shader.bind()
            shader.uniform_float("color", color)
            batch.draw(shader)
    finally:
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set("NONE")


def _draw_points(
    points: list[tuple[float, float]],
    color: tuple[float, float, float, float],
    size: float,
) -> None:
    if not points:
        return
    verts = [(p[0], 0.0, p[1]) for p in points]
    shader = gpu.shader.from_builtin(_UNIFORM_COLOR_SHADER)
    batch = batch_for_shader(shader, "POINTS", {"pos": verts})
    gpu.state.blend_set("ALPHA")
    gpu.state.point_size_set(size)
    try:
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)
    finally:
        gpu.state.point_size_set(1.0)
        gpu.state.blend_set("NONE")


def _draw_stroke_lines(
    shader: gpu.types.GPUShader,
    coords: list[tuple[float, float, float]],
) -> None:
    """Draw a sequence of line segments for a committed stroke edge set."""
    line_coords: list[tuple[float, float, float]] = []
    for i in range(len(coords) - 1):
        line_coords.append(coords[i])
        line_coords.append(coords[i + 1])
    batch = batch_for_shader(shader, "LINES", {"pos": line_coords})
    shader.uniform_float("color", _STROKE_VERT_COLOR)
    gpu.state.line_width_set(2.0)
    batch.draw(shader)


def _draw_user_strokes(strokes: list[Stroke]) -> None:
    """Draw committed user strokes.

    kind=stroke: blue verts (6 px) + blue line segments.
    kind=point: yellow dot (8 px, backward-compat with legacy Steiner flow).

    The strokes list is held by reference so this callback always reflects
    the latest committed state without re-registration.
    """
    if not strokes:
        return
    shader = gpu.shader.from_builtin(_UNIFORM_COLOR_SHADER)
    gpu.state.blend_set("ALPHA")
    try:
        shader.bind()
        for stroke in strokes:
            pts = stroke["points"]
            if not pts:
                continue
            coords = [(p[0], 0.0, p[1]) for p in pts]
            if stroke["kind"] == "point":
                batch = batch_for_shader(shader, "POINTS", {"pos": coords})
                shader.uniform_float("color", _USER_DOT_COLOR)
                gpu.state.point_size_set(_DOT_SIZE_USER)
                batch.draw(shader)
            else:
                # Verts first
                batch_v = batch_for_shader(shader, "POINTS", {"pos": coords})
                shader.uniform_float("color", _STROKE_VERT_COLOR)
                gpu.state.point_size_set(_DOT_SIZE_STROKE_VERT)
                batch_v.draw(shader)
                # Edge segments (skip if single point)
                if len(coords) >= 2:
                    _draw_stroke_lines(shader, coords)
    finally:
        gpu.state.point_size_set(1.0)
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set("NONE")


def _draw_raw_stroke(
    stroke_active_ref: list[bool],
    raw_points: list[tuple[float, float]],
) -> None:
    """Draw the in-progress raw stroke as a light gray thin line.

    stroke_active_ref[0] gates the draw so nothing is emitted between
    strokes. Both args are mutable containers held by reference so this
    callback always sees the live operator state.
    """
    if not stroke_active_ref[0] or len(raw_points) < 2:
        return
    line_coords: list[tuple[float, float, float]] = []
    for i in range(len(raw_points) - 1):
        a = raw_points[i]
        b = raw_points[i + 1]
        line_coords.append((a[0], 0.0, a[1]))
        line_coords.append((b[0], 0.0, b[1]))
    shader = gpu.shader.from_builtin(_UNIFORM_COLOR_SHADER)
    batch = batch_for_shader(shader, "LINES", {"pos": line_coords})
    gpu.state.blend_set("ALPHA")
    gpu.state.line_width_set(1.0)
    try:
        shader.bind()
        shader.uniform_float("color", _RAW_STROKE_COLOR)
        batch.draw(shader)
    finally:
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set("NONE")
