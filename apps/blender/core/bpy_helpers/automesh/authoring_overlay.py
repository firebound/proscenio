"""GPU draw handlers for the authoring modal (the weight-paint productivity follow-up, T8 + T13).

POST_VIEW SpaceView3D handlers per stage. Reuses UNIFORM_COLOR shader
from modal_overlay. Polylines as LINE_STRIP batches; Steiner / user
dots as POINTS batches.

POST_PIXEL handler (_draw_tooltip) renders intent text near the mouse
cursor in Stage 2 (EDIT_OUTLINE) and Stage 4 (EDIT_INTERIOR_POINTS).
"""

from __future__ import annotations

import contextlib
from typing import TypedDict, cast

import bpy
import gpu
from gpu_extras.batch import batch_for_shader

from ...automesh.stroke_geometry import subdivide_polyline
from ...skinning.authoring_stages import AuthoringStage, StageOutput, Stroke
from ..modal_overlay import draw_text_panel_2d

_UNIFORM_COLOR_SHADER = "UNIFORM_COLOR"
_OUTER_COLOR = (0.0, 0.8, 1.0, 0.9)
_OUTER_DIM = (0.0, 0.4, 0.5, 0.5)
# green - spliced silhouette APPLY will build
_OUTER_PREVIEW_COLOR = (0.2, 1.0, 0.5, 0.95)
_INNER_BASE = (0.2, 1.0, 0.4, 0.85)
_INNER_DIM = (0.1, 0.5, 0.2, 0.5)
_STEINER_COLOR = (1.0, 0.3, 0.3, 0.7)
_TRIANGULATION_COLOR = (0.2, 0.9, 0.9, 0.85)  # cyan - SIMPLE triangulation preview wireframe
_TRIANGULATION_LINE_WIDTH = 1.5
_USER_DOT_COLOR = (1.0, 1.0, 0.2, 0.95)
_STROKE_VERT_COLOR_FOLD = (0.3, 0.7, 1.0, 1.0)  # blue - fold-line stroke (Stage 4 default)
_STROKE_VERT_COLOR_CUT_RIP = (1.0, 0.3, 0.3, 1.0)  # red - cut (both Stage 2 + Stage 4, )
_LINE_WIDTH = 2.0
_DOT_SIZE_USER = 8.0
_DOT_SIZE_STEINER = 4.0
_DOT_SIZE_STROKE_VERT = 6.0
_LIVE_VERT_SIZE = 7.0  # in-progress pen/free-draw verts (slightly larger than committed)
_LIVE_RUBBER_ALPHA = 0.5  # dimmed rubber-band segment to cursor (pen mode)
_DELETE_HOVER_COLOR = (1.0, 1.0, 1.0, 0.95)  # bright highlight on the stroke Alt+click removes
_DELETE_HOVER_VERT_SIZE = 10.0
_DELETE_HOVER_LINE_WIDTH = 3.0

# Tooltip (POST_PIXEL) draw constants. Rendered via draw_text_panel_2d
# (colored + backgrounded) for parity with quick_armature's cursor hint.
_TOOLTIP_TEXT_SIZE = 11
_TOOLTIP_OFFSET = (15, 15)  # px right + up of the cursor
_TOOLTIP_TEXT_COLOR = (1.0, 1.0, 1.0, 1.0)
_TOOLTIP_BG_DEFAULT = (0.0, 0.0, 0.0, 0.6)


class OverlayHandles(TypedDict):
    """Draw handler refs returned by register_overlay; None when stage
    does not draw that primitive."""

    outer: object | None
    outer_preview: object | None  # Stage 2 spliced silhouette preview
    inner: object | None
    steiners: object | None
    triangulation: object | None  # SIMPLE-mode triangulation preview wireframe
    user_dots: object | None
    user_strokes: object | None  # Stage 4 interior strokes (fold/rip)
    user_outer_strokes: object | None  # Stage 2 outer strokes (chunk-remove)
    live_preview: object | None  # in-progress pen/free-draw (colored verts+edges)
    delete_hover: object | None  # highlight on the stroke under the cursor while Alt held
    tooltip: object | None  # POST_PIXEL intent text; Stage 2 + Stage 4 only


def _draw_tooltip(
    mouse_pos_ref: list[tuple[int, int]],
    text_ref: list[str],
    color_ref: list[tuple[float, float, float, float]],
) -> None:
    """POST_PIXEL draw handler: colored + backgrounded intent text near cursor.

    All args are single-element lists the operator mutates in-place so this
    handler always reads current state without re-registration. ``color_ref``
    carries the background color (operator sets a red warning bg when the
    cursor is in a position that would clip/drop the stroke). Nothing is drawn
    when the mouse is outside the region or text is empty.
    """
    if not text_ref or not text_ref[0] or not mouse_pos_ref:
        return
    mx, my = mouse_pos_ref[0]
    if mx < 0 or my < 0:
        return
    region = bpy.context.region
    if region is None:
        return
    bg = color_ref[0] if color_ref else _TOOLTIP_BG_DEFAULT
    draw_text_panel_2d(
        (text_ref[0],),
        region_width=region.width,
        region_height=region.height,
        text_size=_TOOLTIP_TEXT_SIZE,
        padding=5,
        bg_color=bg,
        text_color=_TOOLTIP_TEXT_COLOR,
        origin_override=(mx + _TOOLTIP_OFFSET[0], my + _TOOLTIP_OFFSET[1]),
    )


def _register_interactive_handlers(
    handles: OverlayHandles,
    user_strokes: list[Stroke] | None,
    tooltip_mouse_ref: list[tuple[int, int]] | None,
    tooltip_text_ref: list[str] | None,
    live_preview_ref: dict[str, object] | None = None,
    tooltip_color_ref: list[tuple[float, float, float, float]] | None = None,
    delete_hover_ref: list[tuple[float, float]] | None = None,
) -> None:
    """Register draw handlers for interactive stages (EDIT_OUTLINE, EDIT_INTERIOR_POINTS).

    Covers committed strokes, the colored in-progress pen / free-draw preview,
    the delete-hover highlight, and the POST_PIXEL intent tooltip. All handlers
    receive mutable container references so they always see the latest operator
    state without needing re-registration on MOUSEMOVE.

    Cut strokes render RED in both stages ( unified the color).
    """
    if user_strokes is not None:
        handles["user_strokes"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_user_strokes,
            (user_strokes,),
            "WINDOW",
            "POST_VIEW",
        )
    if live_preview_ref is not None:
        handles["live_preview"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_live_preview,
            (live_preview_ref,),
            "WINDOW",
            "POST_VIEW",
        )
    if delete_hover_ref is not None:
        handles["delete_hover"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_delete_hover,
            (delete_hover_ref,),
            "WINDOW",
            "POST_VIEW",
        )
    if tooltip_mouse_ref is not None and tooltip_text_ref is not None:
        handles["tooltip"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_tooltip,
            (tooltip_mouse_ref, tooltip_text_ref, tooltip_color_ref or [_TOOLTIP_BG_DEFAULT]),
            "WINDOW",
            "POST_PIXEL",
        )


def _register_contour_handlers(
    handles: OverlayHandles, stage: AuthoringStage, output: StageOutput
) -> None:
    """Outer + inner contour and user-dot handlers, dimmed past their stage."""
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
    if stage >= AuthoringStage.EDIT_INTERIOR_POINTS and output.user_steiners:
        handles["user_dots"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_points,
            (list(output.user_steiners), _USER_DOT_COLOR, _DOT_SIZE_USER),
            "WINDOW",
            "POST_VIEW",
        )


def _register_preview_handlers(
    handles: OverlayHandles,
    stage: AuthoringStage,
    output: StageOutput,
    user_strokes: list[Stroke] | None,
    user_outer_strokes: list[Stroke] | None,
) -> None:
    """Stage >= PREVIEW_INTERIOR: the Steiner cloud or SIMPLE-mode wireframe,
    plus both committed stroke lists kept visible (cut = red)."""
    if stage < AuthoringStage.PREVIEW_INTERIOR:
        return
    if output.all_steiners:
        handles["steiners"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_points,
            (list(output.all_steiners), _STEINER_COLOR, _DOT_SIZE_STEINER),
            "WINDOW",
            "POST_VIEW",
        )
    # SIMPLE mode draws the real triangulation wireframe instead of the dense
    # Steiner point cloud (the two are mutually exclusive by mode).
    if output.triangulation_preview:
        handles["triangulation"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_edges,
            (list(output.triangulation_preview), _TRIANGULATION_COLOR, _TRIANGULATION_LINE_WIDTH),
            "WINDOW",
            "POST_VIEW",
        )
    if user_strokes is not None:
        handles["user_strokes"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_user_strokes,
            (user_strokes,),
            "WINDOW",
            "POST_VIEW",
        )
    if user_outer_strokes is not None:
        handles["user_outer_strokes"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_user_strokes,
            (user_outer_strokes,),
            "WINDOW",
            "POST_VIEW",
        )


def register_overlay(
    stage: AuthoringStage,
    output: StageOutput,
    user_strokes: list[Stroke] | None = None,
    user_outer_strokes: list[Stroke] | None = None,
    tooltip_mouse_ref: list[tuple[int, int]] | None = None,
    tooltip_text_ref: list[str] | None = None,
    live_preview_ref: dict[str, object] | None = None,
    tooltip_color_ref: list[tuple[float, float, float, float]] | None = None,
    delete_hover_ref: list[tuple[float, float]] | None = None,
) -> OverlayHandles:
    """Add POST_VIEW draw handlers per stage's overlay set.

    For Stage 2 (EDIT_OUTLINE) pass user_outer_strokes + tooltip + live-preview
    refs. For Stage 4 (EDIT_INTERIOR_POINTS) pass user_strokes + user_outer_strokes
    (kept visible) + tooltip refs. Cut strokes render RED in both stages
    ( unified the color).

    Live mutable container parameters (all optional):
    - user_strokes: interior Steiner strokes (_user_strokes in operator)
    - user_outer_strokes: outer-contour strokes (_user_outer_strokes in operator)
    - tooltip_mouse_ref: single-element list with (mouse_region_x, mouse_region_y) in pixels
    - tooltip_text_ref: single-element list with current intent text string

    The draw callbacks hold references to these containers so they always
    see the current live state without needing re-registration on each
    MOUSEMOVE event.
    """
    handles: OverlayHandles = {
        "outer": None,
        "outer_preview": None,
        "inner": None,
        "steiners": None,
        "triangulation": None,
        "user_dots": None,
        "user_strokes": None,
        "user_outer_strokes": None,
        "live_preview": None,
        "delete_hover": None,
        "tooltip": None,
    }
    _register_contour_handlers(handles, stage, output)
    if stage == AuthoringStage.EDIT_OUTLINE:
        # Stage 2: outer strokes only (cut = red, ). The spliced-outer
        # preview holds the live output.outer_preview list by
        # reference so the operator can update it in-place after each edit.
        handles["outer_preview"] = bpy.types.SpaceView3D.draw_handler_add(
            _draw_polyline,
            (output.outer_preview, _OUTER_PREVIEW_COLOR, _LINE_WIDTH),
            "WINDOW",
            "POST_VIEW",
        )
        _register_interactive_handlers(
            handles,
            user_outer_strokes,
            tooltip_mouse_ref,
            tooltip_text_ref,
            live_preview_ref=live_preview_ref,
            tooltip_color_ref=tooltip_color_ref,
            delete_hover_ref=delete_hover_ref,
        )
    elif stage == AuthoringStage.EDIT_INTERIOR_POINTS:
        # Stage 4: interior strokes, plus outer strokes kept visible via a
        # separate handler stored in "user_outer_strokes". Cut = red in both
        # . The colored live preview supersedes the gray raw-stroke.
        _register_interactive_handlers(
            handles,
            user_strokes,
            tooltip_mouse_ref,
            tooltip_text_ref,
            live_preview_ref=live_preview_ref,
            tooltip_color_ref=tooltip_color_ref,
            delete_hover_ref=delete_hover_ref,
        )
        if user_outer_strokes is not None:
            handles["user_outer_strokes"] = bpy.types.SpaceView3D.draw_handler_add(
                _draw_user_strokes,
                (user_outer_strokes,),
                "WINDOW",
                "POST_VIEW",
            )
    _register_preview_handlers(handles, stage, output, user_strokes, user_outer_strokes)
    return handles


def unregister_overlay(handles: OverlayHandles) -> None:
    """No-op-safe cleanup; tolerates partial registration."""
    for key in (
        "outer",
        "outer_preview",
        "inner",
        "steiners",
        "triangulation",
        "user_dots",
        "user_strokes",
        "user_outer_strokes",
        "live_preview",
        "delete_hover",
        "tooltip",
    ):
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
    user_outer_strokes: list[Stroke] | None = None,
    tooltip_mouse_ref: list[tuple[int, int]] | None = None,
    tooltip_text_ref: list[str] | None = None,
    live_preview_ref: dict[str, object] | None = None,
    tooltip_color_ref: list[tuple[float, float, float, float]] | None = None,
    delete_hover_ref: list[tuple[float, float]] | None = None,
) -> OverlayHandles:
    """Replace handlers when stage data changes (slider drag or stage advance)."""
    unregister_overlay(handles)
    return register_overlay(
        stage,
        output,
        user_strokes=user_strokes,
        user_outer_strokes=user_outer_strokes,
        tooltip_mouse_ref=tooltip_mouse_ref,
        tooltip_text_ref=tooltip_text_ref,
        live_preview_ref=live_preview_ref,
        tooltip_color_ref=tooltip_color_ref,
        delete_hover_ref=delete_hover_ref,
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


def _draw_edges(
    edges: list[tuple[tuple[float, float], tuple[float, float]]],
    color: tuple[float, float, float, float],
    line_width: float,
) -> None:
    """Draw independent edge segments from world-XZ endpoint pairs (
    SIMPLE triangulation preview)."""
    if not edges:
        return
    verts: list[tuple[float, float, float]] = []
    for a, b in edges:
        verts.append((a[0], 0.0, a[1]))
        verts.append((b[0], 0.0, b[1]))
    shader = gpu.shader.from_builtin(_UNIFORM_COLOR_SHADER)
    batch = batch_for_shader(shader, "LINES", {"pos": verts})
    gpu.state.blend_set("ALPHA")
    gpu.state.line_width_set(line_width)
    try:
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
    color: tuple[float, float, float, float],
) -> None:
    """Draw a sequence of line segments for a committed stroke edge set."""
    line_coords: list[tuple[float, float, float]] = []
    for i in range(len(coords) - 1):
        line_coords.append(coords[i])
        line_coords.append(coords[i + 1])
    batch = batch_for_shader(shader, "LINES", {"pos": line_coords})
    shader.uniform_float("color", color)
    gpu.state.line_width_set(2.0)
    batch.draw(shader)


def _resolve_stroke_color(kind: str) -> tuple[float, float, float, float]:
    """Return the overlay color for a stroke given its kind.

    kind="point"  -> YELLOW (single Steiner dot)
    kind="stroke" -> BLUE   (fold-line)
    kind="cut"    -> RED    (cut, both Stage 2 + Stage 4, )
    """
    if kind == "point":
        return _USER_DOT_COLOR
    if kind == "cut":
        return _STROKE_VERT_COLOR_CUT_RIP
    # kind="stroke" (fold-line) and any unknown kind fall through to blue.
    return _STROKE_VERT_COLOR_FOLD


def _draw_user_strokes(strokes: list[Stroke]) -> None:
    """Draw committed user strokes, coloring by kind.

    kind=point:  YELLOW dot (8 px) - single Steiner.
    kind=stroke: BLUE verts (6 px) + blue line segments - fold-line.
    kind=cut:    RED verts + red line segments - cut (both stages, ).

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
            kind = stroke["kind"]
            color = _resolve_stroke_color(kind)
            if kind == "point":
                batch = batch_for_shader(shader, "POINTS", {"pos": coords})
                shader.uniform_float("color", color)
                gpu.state.point_size_set(_DOT_SIZE_USER)
                batch.draw(shader)
            else:
                # Verts first
                batch_v = batch_for_shader(shader, "POINTS", {"pos": coords})
                shader.uniform_float("color", color)
                gpu.state.point_size_set(_DOT_SIZE_STROKE_VERT)
                batch_v.draw(shader)
                # Edge segments (skip if single point)
                if len(coords) >= 2:
                    _draw_stroke_lines(shader, coords, color)
    finally:
        gpu.state.point_size_set(1.0)
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set("NONE")


def _draw_live_preview(state: dict[str, object]) -> None:
    """Draw the in-progress pen / free-draw stroke in its intent color.

    Used by both Stage 2 (EDIT_OUTLINE) and Stage 4 (EDIT_INTERIOR_POINTS): the artist
    sees committed-quality feedback (verts + colored edges) while a stroke is
    being placed. In pen mode an extra dimmed rubber-band segment connects
    the last placed vert to the live cursor.

    `state` is a single mutable dict held by reference; the operator mutates
    its fields in-place (never reassigns the dict) so this callback always
    reads the current in-progress geometry without re-registration. Keys:
      active: bool   - gate; nothing drawn when False
      kind:   str    - "cut" -> red, else blue (fold)
      points: list   - placed verts (pen) or sampled path (free-draw), WORLD XZ
      cursor: tuple  - live mouse WORLD XZ for the pen rubber-band, or None
      mode:   str    - "pen" (rubber-band) or "free" (path only)
      subdivisions: int - ghost subdivision verts to preview on the rubber-band
      axis:   str    - active axis lock ("", "x", "z"); cursor is pre-snapped
    """
    if not state.get("active"):
        return
    pts = cast("list[tuple[float, float]]", state.get("points") or [])
    if not pts:
        return
    kind = state.get("kind", "stroke")
    color = _STROKE_VERT_COLOR_CUT_RIP if kind == "cut" else _STROKE_VERT_COLOR_FOLD
    coords = [(p[0], 0.0, p[1]) for p in pts]
    shader = gpu.shader.from_builtin(_UNIFORM_COLOR_SHADER)
    gpu.state.blend_set("ALPHA")
    try:
        shader.bind()
        batch_v = batch_for_shader(shader, "POINTS", {"pos": coords})
        shader.uniform_float("color", color)
        gpu.state.point_size_set(_LIVE_VERT_SIZE)
        batch_v.draw(shader)
        if len(coords) >= 2:
            _draw_stroke_lines(shader, coords, color)
        cursor = cast("tuple[float, float] | None", state.get("cursor"))
        if state.get("mode") == "pen" and cursor is not None:
            cursor_coord = (cursor[0], 0.0, cursor[1])
            dim = (color[0], color[1], color[2], _LIVE_RUBBER_ALPHA)
            rubber = batch_for_shader(shader, "LINES", {"pos": [coords[-1], cursor_coord]})
            shader.uniform_float("color", dim)
            gpu.state.line_width_set(1.5)
            rubber.draw(shader)
            # : ghost dots for the subdivisions that will be baked into
            # the segment (cursor is already axis-locked by the operator, so the
            # rubber-band doubles as the X/Z guide line).
            subdiv = int(cast("int", state.get("subdivisions") or 0))
            if subdiv > 0:
                ghosts = subdivide_polyline([pts[-1], cursor], subdiv)[1:-1]
                if ghosts:
                    ghost_coords = [(g[0], 0.0, g[1]) for g in ghosts]
                    gbatch = batch_for_shader(shader, "POINTS", {"pos": ghost_coords})
                    shader.uniform_float("color", dim)
                    gpu.state.point_size_set(_LIVE_VERT_SIZE * 0.6)
                    gbatch.draw(shader)
    finally:
        gpu.state.point_size_set(1.0)
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set("NONE")


def _draw_delete_hover(points_ref: list[tuple[float, float]]) -> None:
    """Highlight the stroke under the cursor that Alt+click would delete.

    ``points_ref`` is mutated in-place by the operator (the hovered stroke's
    points, empty when nothing is hovered) so this callback always reflects
    the current hover target without re-registration.
    """
    if not points_ref:
        return
    coords = [(p[0], 0.0, p[1]) for p in points_ref]
    shader = gpu.shader.from_builtin(_UNIFORM_COLOR_SHADER)
    gpu.state.blend_set("ALPHA")
    try:
        shader.bind()
        shader.uniform_float("color", _DELETE_HOVER_COLOR)
        batch_v = batch_for_shader(shader, "POINTS", {"pos": coords})
        gpu.state.point_size_set(_DELETE_HOVER_VERT_SIZE)
        batch_v.draw(shader)
        if len(coords) >= 2:
            gpu.state.line_width_set(_DELETE_HOVER_LINE_WIDTH)
            _draw_stroke_lines(shader, coords, _DELETE_HOVER_COLOR)
    finally:
        gpu.state.point_size_set(1.0)
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set("NONE")
