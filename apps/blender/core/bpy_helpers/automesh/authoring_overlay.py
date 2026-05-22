"""GPU draw handlers for the authoring modal (SPEC 013.2, T8 + T13).

POST_VIEW SpaceView3D handlers per stage. Reuses UNIFORM_COLOR shader
from modal_overlay. Polylines as LINE_STRIP batches; Steiner / user
dots as POINTS batches.
"""

from __future__ import annotations

import contextlib
from typing import TypedDict

import bpy
import gpu
from gpu_extras.batch import batch_for_shader

from ...skinning.authoring_stages import AuthoringStage, StageOutput

_UNIFORM_COLOR_SHADER = "UNIFORM_COLOR"
_OUTER_COLOR = (0.0, 0.8, 1.0, 0.9)
_OUTER_DIM = (0.0, 0.4, 0.5, 0.5)
_INNER_BASE = (0.2, 1.0, 0.4, 0.85)
_INNER_DIM = (0.1, 0.5, 0.2, 0.5)
_STEINER_COLOR = (1.0, 0.3, 0.3, 0.7)
_USER_DOT_COLOR = (1.0, 1.0, 0.2, 0.95)
_LINE_WIDTH = 2.0
_DOT_SIZE_USER = 8.0
_DOT_SIZE_STEINER = 4.0


class OverlayHandles(TypedDict):
    """Draw handler refs returned by register_overlay; None when stage
    does not draw that primitive."""

    outer: object | None
    inner: object | None
    steiners: object | None
    user_dots: object | None


def register_overlay(stage: AuthoringStage, output: StageOutput) -> OverlayHandles:
    """Add POST_VIEW draw handlers per stage's overlay set."""
    handles: OverlayHandles = {
        "outer": None,
        "inner": None,
        "steiners": None,
        "user_dots": None,
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
    if stage >= AuthoringStage.STEINER_PREVIEW and output.all_steiners:
        handles["steiners"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_points,
            (list(output.all_steiners), _STEINER_COLOR, _DOT_SIZE_STEINER),
            "WINDOW",
            "POST_VIEW",
        )
    return handles


def unregister_overlay(handles: OverlayHandles) -> None:
    """No-op-safe cleanup; tolerates partial registration."""
    for key in ("outer", "inner", "steiners", "user_dots"):
        handle = handles.get(key)
        if handle is None:
            continue
        with contextlib.suppress(ValueError, RuntimeError):
            bpy.types.SpaceView3D.draw_handler_remove(handle, "WINDOW")
        handles[key] = None


def refresh_overlay(
    handles: OverlayHandles, stage: AuthoringStage, output: StageOutput
) -> OverlayHandles:
    """Replace handlers when stage data changes (slider drag or stage advance)."""
    unregister_overlay(handles)
    return register_overlay(stage, output)


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
