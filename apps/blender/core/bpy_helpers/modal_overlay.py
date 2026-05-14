"""Modal overlay drawing helpers (SPEC 012.1).

bpy-bound. Imports ``gpu``, ``blf`` and the GPU shader plumbing at module
top. Lives in ``core/bpy_helpers/``.

Provides three reusable primitives for modal operators that need
in-viewport feedback:

- :func:`build_line_3d_batch` and :func:`build_circle_3d_batch` for
  ``POST_VIEW`` overlays drawn in world space (preview line + anchor).
- :func:`draw_text_panel_2d` for ``POST_PIXEL`` overlays drawn in pixel
  space (modifier cheatsheet, status header).

Pure-geometry helpers (vertex builders) live in
:mod:`core.modal_overlay_geometry` and are bpy-free so they can be unit
tested without booting Blender.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import blf
import gpu
from gpu_extras.batch import batch_for_shader

from ..modal_overlay_geometry import (  # type: ignore[import-not-found]
    build_circle_vertices,
    build_rect_vertices,
)

_UNIFORM_COLOR_SHADER = "UNIFORM_COLOR"

PanelAlign = Literal["top-left", "top-center", "bottom-center"]


def _shader() -> gpu.types.GPUShader:
    return gpu.shader.from_builtin(_UNIFORM_COLOR_SHADER)


def draw_line_3d(
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    color: tuple[float, float, float, float],
    line_width: float = 2.0,
) -> None:
    """Draw a single line segment in world space.

    Intended to be called from a ``POST_VIEW`` draw handler. The shader
    is the built-in ``UNIFORM_COLOR`` so the line is unaffected by scene
    lighting.
    """
    shader = _shader()
    batch = batch_for_shader(shader, "LINES", {"pos": [start, end]})
    gpu.state.blend_set("ALPHA")
    gpu.state.line_width_set(line_width)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set("NONE")


def draw_circle_3d(
    center: tuple[float, float, float],
    radius: float,
    color: tuple[float, float, float, float],
    plane_axis: str = "Y",
    segments: int = 12,
    line_width: float = 2.0,
) -> None:
    """Draw a circle in world space lying on the picture plane.

    ``plane_axis`` selects which axis is held at the center value:
    ``"Y"`` produces a circle in the XZ plane (Proscenio convention),
    ``"Z"`` in the XY plane, ``"X"`` in the YZ plane.
    """
    vertices = build_circle_vertices(center, radius, plane_axis, segments)
    shader = _shader()
    batch = batch_for_shader(shader, "LINE_LOOP", {"pos": vertices})
    gpu.state.blend_set("ALPHA")
    gpu.state.line_width_set(line_width)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set("NONE")


def draw_text_panel_2d(
    lines: Sequence[str],
    region_width: int,
    region_height: int,
    align: PanelAlign = "top-left",
    margin: int = 16,
    text_size: int = 12,
    padding: int = 8,
    line_spacing: int = 4,
    bg_color: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.55),
    text_color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    font_id: int = 0,
    origin_override: tuple[int, int] | None = None,
) -> None:
    """Draw a multi-line text panel with translucent background in pixel space.

    Intended to be called from a ``POST_PIXEL`` draw handler. ``align``
    selects which region corner the panel anchors to and ``margin`` is
    the pixel offset from that corner. The panel measures its content
    via ``blf.dimensions`` and centers itself horizontally when
    ``align`` ends in ``"center"``.

    When ``origin_override`` is provided, it pins the panel's bottom-left
    corner at the given region-local pixel coordinate, ignoring
    ``align`` and ``margin``. Use this for cursor-relative tooltips.
    """
    if not lines:
        return
    blf.size(font_id, text_size)
    line_metrics = [blf.dimensions(font_id, line) for line in lines]
    text_width = max(int(width) for width, _ in line_metrics)
    line_height = max(int(height) for _, height in line_metrics)
    block_height = len(lines) * line_height + (len(lines) - 1) * line_spacing
    panel_width = text_width + 2 * padding
    panel_height = block_height + 2 * padding

    if origin_override is not None:
        rect_x = origin_override[0]
        rect_y_top = origin_override[1] + panel_height
    elif align == "top-left":
        rect_x = margin
        rect_y_top = region_height - margin
    elif align == "top-center":
        rect_x = (region_width - panel_width) // 2
        rect_y_top = region_height - margin
    elif align == "bottom-center":
        rect_x = (region_width - panel_width) // 2
        rect_y_top = margin + panel_height
    else:
        raise ValueError(f"unknown align: {align!r}")

    rect_y_bottom = rect_y_top - panel_height
    rect_vertices = build_rect_vertices(
        rect_x,
        rect_y_bottom,
        rect_x + panel_width,
        rect_y_top,
    )
    shader = _shader()
    batch = batch_for_shader(shader, "TRIS", {"pos": rect_vertices})
    gpu.state.blend_set("ALPHA")
    shader.bind()
    shader.uniform_float("color", bg_color)
    batch.draw(shader)
    gpu.state.blend_set("NONE")

    blf.color(font_id, *text_color)
    text_y = rect_y_top - padding - line_height
    for line in lines:
        blf.position(font_id, rect_x + padding, text_y, 0.0)
        blf.draw(font_id, line)
        text_y -= line_height + line_spacing
