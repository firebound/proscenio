"""Interactive modal automesh authoring operator (the weight-paint productivity follow-up).

5-stage modal that previews each pipeline stage with a GPU overlay
so the artist iterates on the mesh shape before any geometry commits.
Coexists with the one-shot automesh_from_sprite operator.
"""

from __future__ import annotations

import contextlib
import traceback
from typing import ClassVar, Literal, cast

import bpy

from ...core._shared.report import (  # type: ignore[import-not-found]
    report_error,
    report_info,
    report_warn,
)
from ...core.bpy_helpers.automesh.authoring_overlay import (  # type: ignore[import-not-found]
    OverlayHandles,
    refresh_overlay,
    register_overlay,
    unregister_overlay,
)
from ...core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
    apply_mesh,
    compute_all_steiners,
    compute_inner_loops_for_stage,
    compute_outer,
    compute_outer_preview,
    compute_triangulation_preview,
    read_user_outer_strokes,
    read_user_strokes,
    write_user_outer_strokes,
    write_user_strokes,
)
from ...core.bpy_helpers.automesh.authoring_session import (  # type: ignore[import-not-found]
    AuthoringSession,
)
from ...core.bpy_helpers.automesh.authoring_session import (
    capture as capture_session,
)
from ...core.bpy_helpers.automesh.authoring_session import (
    restore as restore_session,
)
from ...core.bpy_helpers.automesh.bridge import (  # type: ignore[import-not-found]
    collect_bone_segments,
)
from ...core.skinning.authoring_stages import (  # type: ignore[import-not-found]
    AuthoringStage,
    Point2D,
    StageOutput,
    StageParams,
    Stroke,
)

_TIMER_INTERVAL = 0.1
# Cursor tooltip background colors (passed to the overlay via _tooltip_color_ref).
_TOOLTIP_BG_NORMAL = (0.0, 0.0, 0.0, 0.6)
_TOOLTIP_BG_WARN = (0.35, 0.05, 0.05, 0.85)  # red: gesture would clip/drop the stroke
# Modifier key event types. The cursor tooltip reflects the held modifier, so
# it must refresh on these (not only on MOUSEMOVE) or a stationary cursor shows
# stale intent text while Shift/Ctrl/Alt is tapped.
_SHIFT_CTRL_KEYS = frozenset({"LEFT_SHIFT", "RIGHT_SHIFT", "LEFT_CTRL", "RIGHT_CTRL"})
#  toggle-pen: top-row + numpad digit event types -> subdivision count.
_DIGIT_KEYS = {
    "ZERO": 0,
    "ONE": 1,
    "TWO": 2,
    "THREE": 3,
    "FOUR": 4,
    "FIVE": 5,
    "SIX": 6,
    "SEVEN": 7,
    "EIGHT": 8,
    "NINE": 9,
    "NUMPAD_0": 0,
    "NUMPAD_1": 1,
    "NUMPAD_2": 2,
    "NUMPAD_3": 3,
    "NUMPAD_4": 4,
    "NUMPAD_5": 5,
    "NUMPAD_6": 6,
    "NUMPAD_7": 7,
    "NUMPAD_8": 8,
    "NUMPAD_9": 9,
}
_PEN_SUBDIV_MAX = 20  # wheel can exceed the single-digit set; cap to keep CDT sane
# Short stage titles; per-stage gesture chords render separately in the
# statusbar via _emit_authoring_chord_layout, so these stay terse. The
# "N/M" prefix is derived per active mode by _stage_label, so
# these are base names only.
_STAGE_BASE_NAMES = {
    AuthoringStage.OUTER: "Outer contour",
    AuthoringStage.EDIT_OUTLINE: "Edit silhouette",
    AuthoringStage.INNER_LOOPS: "Inner loops",
    AuthoringStage.EDIT_INTERIOR_POINTS: "Interior detail",
    AuthoringStage.PREVIEW_INTERIOR: "Vertex preview",
    AuthoringStage.APPLY: "Apply",
}
# : SIMPLE drops INNER_LOOPS and relabels PREVIEW_INTERIOR to the
# real triangulation preview; DENSE keeps the full 6-stage pipeline.
_SIMPLE_STAGE_ORDER = [
    AuthoringStage.OUTER,
    AuthoringStage.EDIT_OUTLINE,
    AuthoringStage.EDIT_INTERIOR_POINTS,
    AuthoringStage.PREVIEW_INTERIOR,
    AuthoringStage.APPLY,
]
_DENSE_STAGE_ORDER = [
    AuthoringStage.OUTER,
    AuthoringStage.EDIT_OUTLINE,
    AuthoringStage.INNER_LOOPS,
    AuthoringStage.EDIT_INTERIOR_POINTS,
    AuthoringStage.PREVIEW_INTERIOR,
    AuthoringStage.APPLY,
]


def _stages_for_mode(mode: str) -> list[AuthoringStage]:
    """Ordered stage list for the active interior mode."""
    return list(_SIMPLE_STAGE_ORDER if mode == "SIMPLE" else _DENSE_STAGE_ORDER)


def _stage_base_name(stage: AuthoringStage, mode: str) -> str:
    if stage == AuthoringStage.PREVIEW_INTERIOR and mode == "SIMPLE":
        return "Triangulation preview"
    return _STAGE_BASE_NAMES[stage]


def _stage_label(stage: AuthoringStage, mode: str) -> str:
    """'N/M Name' label; N/M reflects the active mode's stage count."""
    stages = _stages_for_mode(mode)
    idx = stages.index(stage)
    return f"{idx + 1}/{len(stages)} {_stage_base_name(stage, mode)}"


class PROSCENIO_OT_automesh_authoring(bpy.types.Operator):
    """Multi-stage modal preview of the automesh pipeline."""

    bl_idname = "proscenio.automesh_authoring"
    bl_label = "Proscenio: Automesh Authoring"
    bl_description = (
        "Multi-stage modal preview of the automesh pipeline. Each stage "
        "(outer contour / user outer edits / inner loops / user Steiner "
        "points / Steiner preview / apply) surfaces a GPU overlay + "
        "slider-driven re-run so the artist iterates on the mesh shape "
        "before any geometry commits. ENTER advances; BACKSPACE goes back; "
        "ESC cancels"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    # Stage 3 stroke capture state (gesture rewrite)
    _DRAG_THRESHOLD_PX: ClassVar[int] = 5
    _STROKE_SMOOTH_ITERS: ClassVar[int] = 2
    _STROKE_PICK_RADIUS_PX: ClassVar[int] = 12

    _stage: AuthoringStage
    _output: StageOutput
    _handles: OverlayHandles
    _session: AuthoringSession | None
    _last_params: StageParams | None
    _timer: bpy.types.Timer | None
    _statusbar_appended: bool = False
    _current_stage_label: str = _stage_label(AuthoringStage.OUTER, "SIMPLE")
    # Read by the module-level statusbar draw callback to pick per-stage chords.
    _current_stage: AuthoringStage = AuthoringStage.OUTER
    # Active interior mode, mirrored for the statusbar chord layout.
    _current_interior_mode: str = "SIMPLE"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return False
        return _resolve_image(obj) is not None

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            report_error(self, "active object must be a mesh")
            return {"CANCELLED"}
        image = _resolve_image(obj)
        if image is None:
            report_error(
                self,
                "active mesh has no image texture - add a material with a TEX_IMAGE node first",
            )
            return {"CANCELLED"}

        self._session = capture_session(context, obj)
        params = _snapshot_params(context)
        self._last_params = params
        self._stage = AuthoringStage.OUTER
        # : stage list depends on interior mode; navigation walks this
        # ordered list by index instead of raw enum arithmetic.
        self._interior_mode: str = params.interior_mode
        self._active_stages: list[AuthoringStage] = _stages_for_mode(self._interior_mode)
        self._output = StageOutput()
        self._handles = {
            "outer": None,
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
        self._timer = None
        # Click-vs-drag tracking + free-draw sample buffer (shared by both pen
        # stages). _stroke_raw_points is mutated in-place so any handler holding
        # it by reference stays valid.
        self._stroke_active: bool = False
        self._stroke_start_screen: tuple[int, int] | None = None
        self._stroke_raw_points: list[tuple[float, float]] = []
        self._user_strokes: list[Stroke] = []

        # Toggle-pen state. A clean Shift/Ctrl tap (press + release
        # with no intervening press) toggles draw mode - no holding - so the
        # keyboard is free for X/Z axis lock + digit subdivisions. Ctrl+<key>
        # combos clear the pending tap, so Ctrl+Z stays undo. The pen polyline
        # accumulates click-by-click and bakes its subdivision count on finish.
        # Shared by Stage 2 (outer) + Stage 4 (interior); commit target +
        # tooltip label differ by stage. _pen_points is mutated in-place so the
        # live-preview draw handler keeps a stable reference.
        self._draw_active: bool = False
        self._mod_tap_kind: str = ""  # pending tap: "", "stroke" (Shift), "cut" (Ctrl)
        self._pen_active: bool = False
        self._pen_kind: str = "stroke"  # committed Stroke kind: "stroke" or "cut"
        self._pen_points: list[tuple[float, float]] = []
        self._pen_subdivisions: int = 0
        self._axis_lock: str = ""  # "", "x" (horizontal/world-X), "z" (vertical/world-Z)
        # Modifier held at LMB PRESS (Alt-delete path only).
        self._press_modifier: str = ""

        # Live in-progress preview (Stage 4). Single mutable dict held by the
        # _draw_live_preview handler; fields mutated in-place so the colored
        # pen / free-draw feedback renders without re-registration. See
        # authoring_overlay._draw_live_preview for the key contract.
        self._live_preview: dict[str, object] = {
            "active": False,
            "kind": "stroke",
            "points": [],
            "cursor": None,
            "mode": "pen",
            "axis": "",  #  active axis lock ("", "x", "z") for the guide line
            "subdivisions": 0,  #  ghost subdivision verts to preview
        }

        # Tooltip live state - single-element lists mutated in-place so the
        # registered POST_PIXEL draw handler always reads current values
        # without needing re-registration on every MOUSEMOVE.
        self._tooltip_mouse_ref: list[tuple[int, int]] = [(-1, -1)]
        self._tooltip_text_ref: list[str] = [""]
        # Tooltip background color; flips to warn red when a Stage 4 fold/cut
        # gesture is aimed outside the silhouette (would clip/drop on APPLY).
        self._tooltip_color_ref: list[tuple[float, float, float, float]] = [_TOOLTIP_BG_NORMAL]
        # Points of the stroke under the cursor while Alt is held (delete
        # preview). Mutated in-place so the highlight draw handler stays valid.
        self._delete_hover_points: list[tuple[float, float]] = []

        # Stage 2 (EDIT_OUTLINE) committed outer strokes. The in-progress pen +
        # free-draw share the Stage 4 buffers (_stroke_*, _pen_*) via the
        # toggle-pen machine; only the commit target differs by stage.
        self._user_outer_strokes: list[Stroke] = []

        try:
            self._output.outer = compute_outer(obj, image, params)
            self._handles = register_overlay(self._stage, self._output)
            type(self)._current_stage_label = _stage_label(self._stage, self._interior_mode)
            type(self)._current_stage = self._stage
            type(self)._current_interior_mode = self._interior_mode
            self._timer = context.window_manager.event_timer_add(
                _TIMER_INTERVAL, window=context.window
            )
            self._append_statusbar()
            _tag_redraw_view3d(context)
        except Exception as exc:
            report_error(self, f"Authoring setup failed: {exc} - restoring state")
            self._finish(context, cancel=True)
            return {"CANCELLED"}

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        try:
            # : stage handlers get first crack so a pen line in progress
            # can intercept Enter/RMB (finish) + Esc (discard line) BEFORE modal
            # nav. In NEUTRAL they return None for those keys, so nav runs.
            if self._stage == AuthoringStage.EDIT_OUTLINE:
                handled = self._handle_user_outer_event(context, event)
                if handled is not None:
                    return handled
            if self._stage == AuthoringStage.EDIT_INTERIOR_POINTS:
                handled = self._handle_user_steiners_event(context, event)
                if handled is not None:
                    return handled
            if event.type == "ESC" and event.value == "PRESS":
                return self._finish(context, cancel=True)
            if event.type in {"RET", "NUMPAD_ENTER"} and event.value == "PRESS":
                return self._advance(context)
            if event.type == "BACK_SPACE" and event.value == "PRESS":
                return self._retreat(context)
            if event.type == "TIMER" and getattr(event, "timer", None) is self._timer:
                self._handle_timer_tick(context)
        except Exception:
            traceback.print_exc()
            return self._finish(context, cancel=True)
        return {"PASS_THROUGH"}

    def _handle_timer_tick(self, context: bpy.types.Context) -> None:
        """Re-snapshot the param panel; recompute the stage when it changed."""
        current = _snapshot_params(context)
        if current == self._last_params:
            return
        if current.interior_mode != self._interior_mode:
            self._apply_interior_mode_change(context, current.interior_mode)
        self._recompute_current_stage(context, current)
        self._last_params = current

    def _handle_user_outer_event(
        self, context: bpy.types.Context, event: bpy.types.Event
    ) -> set[str] | None:
        """Stage 2 (EDIT_OUTLINE) -> shared toggle-pen dispatch (outer). Shift =
        extend, Ctrl = cut, Alt+click = delete (/)."""
        return self._handle_pen_event(context, event, "outer")

    def _outer_stroke_undo(self, context: bpy.types.Context) -> set[str]:
        if self._user_outer_strokes:
            self._user_outer_strokes.pop()
            obj = context.active_object
            if obj is not None:
                write_user_outer_strokes(obj, self._user_outer_strokes)
            if self._outer_preview_relevant():
                self._refresh_outer_preview(context)
            _tag_redraw_view3d(context)
        return {"RUNNING_MODAL"}

    def _delete_outer_stroke_at_mouse(
        self, context: bpy.types.Context, event: bpy.types.Event
    ) -> None:
        """Hit-test: remove outer stroke if any vert is within pick radius of mouse."""
        mouse_world = _region_to_world_xz(context, event)
        if mouse_world is None:
            return
        pick_d2 = self._pick_radius_sq(context, event, mouse_world)
        for idx, stroke in enumerate(self._user_outer_strokes):
            for pt in stroke["points"]:
                d2 = (pt[0] - mouse_world[0]) ** 2 + (pt[1] - mouse_world[1]) ** 2
                if d2 <= pick_d2:
                    self._remove_outer_stroke(context, idx)
                    return

    def _pick_radius_sq(
        self,
        context: bpy.types.Context,
        event: bpy.types.Event,
        mouse_world: tuple[float, float],
    ) -> float:
        """Squared world-space pick radius for a screen-space pixel offset.

        Falls back to the interior spacing when the offset point cannot be
        projected (e.g. cursor off the picture plane)."""
        near_world = _region_to_world_xz_offset(context, event, dx=self._STROKE_PICK_RADIUS_PX)
        if near_world is None:
            spacing = self._resolve_interior_spacing(context)
            return spacing * spacing
        pick_dist = (
            (near_world[0] - mouse_world[0]) ** 2 + (near_world[1] - mouse_world[1]) ** 2
        ) ** 0.5
        return pick_dist * pick_dist

    def _remove_outer_stroke(self, context: bpy.types.Context, idx: int) -> None:
        """Pop the outer stroke at ``idx``, clear its stale delete-hover
        highlight, persist, and refresh the preview."""
        self._user_outer_strokes.pop(idx)
        # The hovered stroke just went away; drop its highlight now instead of
        # leaving it on screen until the next MOUSEMOVE recomputes the hover.
        self._delete_hover_points.clear()
        obj = context.active_object
        if obj is not None:
            write_user_outer_strokes(obj, self._user_outer_strokes)
        if self._outer_preview_relevant():
            self._refresh_outer_preview(context)

    def _point_inside_outer(self, point_world_xz: tuple[float, float]) -> bool:
        """Check if a WORLD XZ point lies inside the current outer contour.

        output.outer is WORLD XZ per compute_outer convention, so no coordinate
        conversion is needed before calling point_in_polygon.
        """
        from ...core.automesh import point_in_polygon  # type: ignore[import-not-found]

        if not self._output.outer:
            return False
        return bool(point_in_polygon(point_world_xz, self._output.outer))

    def _cursor_outside_outer(self, context: bpy.types.Context, event: bpy.types.Event) -> bool:
        """True when the cursor projects to a point outside the outer contour.

        Used to warn that a Stage 4 fold/cut gesture would be clipped. A
        failed projection counts as not-outside (no false warning)."""
        world_pt = _region_to_world_xz(context, event)
        if world_pt is None:
            return False
        return not self._point_inside_outer(world_pt)

    def _handle_user_steiners_event(
        self, context: bpy.types.Context, event: bpy.types.Event
    ) -> set[str] | None:
        """Stage 4 (EDIT_INTERIOR_POINTS) -> shared toggle-pen dispatch (interior)."""
        return self._handle_pen_event(context, event, "interior")

    # ----- Shared toggle-pen machine (Stage 2 outer + Stage 4 interior) -----

    def _handle_pen_event(
        self, context: bpy.types.Context, event: bpy.types.Event, stage: str
    ) -> set[str] | None:
        """Shared toggle-pen dispatch. A clean Shift/Ctrl tap toggles
        draw mode; in DRAW: LMB click adds a pen vert, drag free-draws, X/Z lock
        the next segment, wheel/digit set the subdivision count, RMB/Enter
        finish, Esc cancels. Returns None when the event is not consumed so the
        modal nav (advance/cancel/retreat) runs."""
        if event.type == "MOUSEMOVE":
            return self._pen_mousemove(context, event, stage)
        # Modifier-tap tracking: a tap is press+release with no intervening
        # press, so Ctrl+<key> (e.g. Ctrl+Z undo) does NOT enter cut-draw.
        if event.value == "PRESS":
            if event.type in _SHIFT_CTRL_KEYS:
                self._mod_tap_kind = (
                    "cut" if event.type in {"LEFT_CTRL", "RIGHT_CTRL"} else "stroke"
                )
            else:
                self._mod_tap_kind = ""
        if event.value == "RELEASE" and event.type in _SHIFT_CTRL_KEYS:
            tap = self._mod_tap_kind
            self._mod_tap_kind = ""
            if tap:
                return self._on_modifier_tap(context, tap)
        if self._draw_active:
            return self._draw_event(context, event, stage)
        return self._neutral_event(context, event, stage)

    def _on_modifier_tap(self, context: bpy.types.Context, tap: str) -> set[str]:
        """Enter draw mode (NEUTRAL) or exit if the in-progress line is empty."""
        if self._draw_active:
            if not self._pen_points:
                self._exit_draw(context)
            return {"RUNNING_MODAL"}
        self._enter_draw(context, tap)
        return {"RUNNING_MODAL"}

    def _enter_draw(self, context: bpy.types.Context, kind: str) -> None:
        self._draw_active = True
        self._pen_kind = kind
        self._pen_active = False
        self._pen_points.clear()
        self._pen_subdivisions = 0
        self._axis_lock = ""
        self._live_preview["active"] = True
        self._live_preview["mode"] = "pen"
        self._live_preview["kind"] = kind
        self._live_preview["points"] = self._pen_points
        self._live_preview["cursor"] = None
        self._live_preview["axis"] = ""
        self._live_preview["subdivisions"] = 0
        self._refresh_pen_tooltip()
        _tag_redraw_view3d(context)

    def _exit_draw(self, context: bpy.types.Context) -> None:
        self._draw_active = False
        self._pen_active = False
        self._stroke_active = False
        self._pen_points.clear()
        self._pen_subdivisions = 0
        self._axis_lock = ""
        self._live_preview["active"] = False
        self._live_preview["cursor"] = None
        self._refresh_pen_tooltip()
        _tag_redraw_view3d(context)

    def _reset_draw_state(self) -> None:
        """Clear all toggle-pen state on stage entry/exit so a stale draw mode,
        pen line, or live preview never carries across stages."""
        self._draw_active = False
        self._mod_tap_kind = ""
        self._pen_active = False
        self._stroke_active = False
        self._pen_points.clear()
        self._pen_subdivisions = 0
        self._axis_lock = ""
        self._stroke_raw_points.clear()
        self._live_preview["active"] = False
        self._live_preview["cursor"] = None
        self._delete_hover_points.clear()

    def _neutral_event(
        self, context: bpy.types.Context, event: bpy.types.Event, stage: str
    ) -> set[str] | None:
        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            if event.alt:
                self._delete_at_mouse(context, event, stage)
                _tag_redraw_view3d(context)
                return {"RUNNING_MODAL"}
            # Track click-vs-drag; commit decided on release.
            self._stroke_start_screen = (event.mouse_region_x, event.mouse_region_y)
            world_pt = _region_to_world_xz(context, event)
            self._stroke_raw_points.clear()
            if world_pt:
                self._stroke_raw_points.append(world_pt)
            self._stroke_active = True
            return {"RUNNING_MODAL"}
        if event.type == "LEFTMOUSE" and event.value == "RELEASE" and self._stroke_active:
            self._stroke_active = False
            start = self._stroke_start_screen
            self._stroke_start_screen = None
            raw = list(self._stroke_raw_points)
            self._stroke_raw_points.clear()
            if start is not None and raw and self._is_click(event, start) and stage == "interior":
                # Interior: a plain click drops a standalone Steiner point.
                # Outer: a plain click is a no-op (edits need a modifier).
                self._user_strokes.append({"kind": "point", "points": [raw[0]]})
                self._persist_and_redraw(context)
            return {"RUNNING_MODAL"}
        if event.type == "Z" and event.ctrl and event.value == "PRESS":
            return self._pen_undo(context, stage)
        return None

    def _draw_event(
        self, context: bpy.types.Context, event: bpy.types.Event, stage: str
    ) -> set[str] | None:
        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            return self._draw_lmb_press(context, event)
        if event.type == "LEFTMOUSE" and event.value == "RELEASE" and self._stroke_active:
            return self._draw_lmb_release(context, event, stage)
        return self._draw_key_event(context, event, stage)

    def _draw_lmb_press(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        self._stroke_start_screen = (event.mouse_region_x, event.mouse_region_y)
        world_pt = _region_to_world_xz(context, event)
        self._stroke_raw_points.clear()
        if world_pt:
            self._stroke_raw_points.append(world_pt)
        self._stroke_active = True
        # Free-draw is only available before the pen polyline starts; once a vert
        # is placed the line is a click-pen and a drag just adds a vert (clicks
        # and drags never mix within one line). Light the colored free-draw path
        # only while the pen is still empty.
        if not self._pen_active:
            self._live_preview["active"] = True
            self._live_preview["mode"] = "free"
            self._live_preview["kind"] = self._pen_kind
            self._live_preview["points"] = self._stroke_raw_points
            self._live_preview["cursor"] = None
        return {"RUNNING_MODAL"}

    def _draw_key_event(
        self, context: bpy.types.Context, event: bpy.types.Event, stage: str
    ) -> set[str] | None:
        if event.type in {"WHEELUPMOUSE", "WHEELDOWNMOUSE"}:
            delta = 1 if event.type == "WHEELUPMOUSE" else -1
            self._set_subdivisions(context, self._pen_subdivisions + delta)
            return {"RUNNING_MODAL"}
        if event.value != "PRESS":
            return None
        # Ctrl+Z undoes (pen vert if a line is in progress, else last committed
        # stroke) - checked before the bare X/Z axis-lock so it is never
        # swallowed as a vertical-lock toggle.
        if event.type == "Z" and event.ctrl:
            return self._pen_undo_in_draw(context, stage)
        if event.type in {"X", "Z"} and not event.ctrl:
            self._toggle_axis_lock(context, "x" if event.type == "X" else "z")
            return {"RUNNING_MODAL"}
        if event.type in _DIGIT_KEYS:
            self._set_subdivisions(context, _DIGIT_KEYS[event.type])
            return {"RUNNING_MODAL"}
        if event.type in {"RET", "NUMPAD_ENTER", "RIGHTMOUSE"}:
            return self._pen_finish(context, stage)
        if event.type == "ESC":
            self._pen_cancel(context)
            return {"RUNNING_MODAL"}
        return None

    def _draw_lmb_release(
        self, context: bpy.types.Context, event: bpy.types.Event, stage: str
    ) -> set[str]:
        self._stroke_active = False
        start = self._stroke_start_screen
        self._stroke_start_screen = None
        raw = list(self._stroke_raw_points)
        self._stroke_raw_points.clear()
        if start is None or not raw:
            return {"RUNNING_MODAL"}
        # Pen polyline in progress -> every LMB adds a vert (drag included), so
        # clicks and drags never mix within one line. Free-draw is only the
        # opening gesture (pen still empty).
        if self._pen_active:
            return self._pen_click(context, event, raw[-1], stage)
        if self._is_click(event, start):
            return self._pen_click(context, event, raw[0], stage)
        # Drag from an empty pen = free-draw stroke (commit immediately, stay in DRAW).
        self._commit_drag_stroke(context, raw, self._pen_kind, stage)
        # Restore the pen-polyline live view (free-draw drag was transient).
        self._live_preview["mode"] = "pen"
        self._live_preview["points"] = list(self._pen_points)
        self._live_preview["cursor"] = None
        self._append_persist(context, stage)
        return {"RUNNING_MODAL"}

    def _is_click(self, event: bpy.types.Event, start: tuple[int, int]) -> bool:
        dx = event.mouse_region_x - start[0]
        dy = event.mouse_region_y - start[1]
        return bool((dx * dx + dy * dy) ** 0.5 < self._DRAG_THRESHOLD_PX)

    def _pen_click(
        self,
        context: bpy.types.Context,
        event: bpy.types.Event,
        world_pt: tuple[float, float],
        stage: str,
    ) -> set[str]:
        """Append a pen vert: snap to a nearby existing vert / close the loop,
        else axis-lock the raw point."""
        pt, close = self._snap_pen_click(context, event, world_pt, stage)
        self._pen_active = True
        self._pen_points.append(pt)
        self._live_preview["active"] = True
        self._live_preview["mode"] = "pen"
        self._live_preview["kind"] = self._pen_kind
        self._live_preview["points"] = list(self._pen_points)
        self._live_preview["cursor"] = None
        if close:
            # Clicked the first vert again -> close the loop + commit.
            return self._pen_finish(context, stage)
        _tag_redraw_view3d(context)
        return {"RUNNING_MODAL"}

    def _snap_pen_click(
        self,
        context: bpy.types.Context,
        event: bpy.types.Event,
        world_pt: tuple[float, float],
        stage: str,
    ) -> tuple[tuple[float, float], bool]:
        """Resolve a pen click against nearby verts. Returns (point, close_loop):

        - click within the pick radius of the current line's FIRST vert ->
          (first vert, True) to close the loop;
        - click on an existing vert (committed strokes of this stage + outer
          contour) -> (that exact vert, False) to union rather than stack a
          near-duplicate;
        - otherwise -> (axis-locked world point, False).
        """
        mouse = _region_to_world_xz(context, event)
        near = _region_to_world_xz_offset(context, event, dx=self._STROKE_PICK_RADIUS_PX)
        if mouse is None or near is None:
            return self._apply_axis_lock(world_pt), False
        pick_d2 = (near[0] - mouse[0]) ** 2 + (near[1] - mouse[1]) ** 2
        if len(self._pen_points) >= 2:
            fx, fz = self._pen_points[0]
            if (fx - mouse[0]) ** 2 + (fz - mouse[1]) ** 2 <= pick_d2:
                return (fx, fz), True
        best: tuple[float, float] | None = None
        best_d2 = pick_d2
        for cx, cz in self._pen_snap_candidates(stage):
            d2 = (cx - mouse[0]) ** 2 + (cz - mouse[1]) ** 2
            if d2 <= best_d2:
                best_d2 = d2
                best = (cx, cz)
        if best is not None:
            return best, False
        return self._apply_axis_lock(world_pt), False

    def _pen_snap_candidates(self, stage: str) -> list[tuple[float, float]]:
        """World-XZ verts a pen click may union with: committed strokes of the
        active stage + the outer contour (so a fold/cut can anchor to the
        silhouette or an earlier stroke)."""
        strokes = self._user_strokes if stage == "interior" else self._user_outer_strokes
        candidates: list[tuple[float, float]] = list(self._output.outer)
        for stroke in strokes:
            candidates.extend(stroke["points"])
        return candidates

    def _apply_axis_lock(self, world_pt: tuple[float, float]) -> tuple[float, float]:
        """Snap the new vert to share the locked axis with the last pen vert."""
        if not self._axis_lock or not self._pen_points:
            return world_pt
        last_x, last_z = self._pen_points[-1]
        if self._axis_lock == "x":  # horizontal: keep world-Z of the last vert
            return (world_pt[0], last_z)
        return (last_x, world_pt[1])  # vertical: keep world-X of the last vert

    def _toggle_axis_lock(self, context: bpy.types.Context, axis: str) -> None:
        self._axis_lock = "" if self._axis_lock == axis else axis
        self._live_preview["axis"] = self._axis_lock
        self._refresh_pen_tooltip()
        _tag_redraw_view3d(context)

    def _set_subdivisions(self, context: bpy.types.Context, n: int) -> None:
        self._pen_subdivisions = max(0, min(_PEN_SUBDIV_MAX, n))
        self._live_preview["subdivisions"] = self._pen_subdivisions
        self._refresh_pen_tooltip()
        _tag_redraw_view3d(context)

    def _current_pen_stage(self) -> str:
        return "interior" if self._stage == AuthoringStage.EDIT_INTERIOR_POINTS else "outer"

    def _refresh_pen_tooltip(self) -> None:
        """Update the tooltip text for the current pen state without a mouse
        move. Tap-toggle, wheel/digit subdivisions, and X/Z axis lock are
        keyboard/wheel events that fire no MOUSEMOVE, so the tooltip would
        otherwise go stale until the cursor moves.

        Background color is NOT touched here so a warn-red bg set by the last
        MOUSEMOVE (cursor outside the silhouette) survives a key event; the
        next MOUSEMOVE recomputes it.
        """
        stage = self._current_pen_stage()
        if self._draw_active:
            self._tooltip_text_ref[0] = self._pen_tooltip_text(stage)
        else:
            self._tooltip_text_ref[0] = self._neutral_tooltip_text(stage)

    def _pen_finish(self, context: bpy.types.Context, stage: str) -> set[str]:
        """Bake subdivisions into the pen polyline + commit it; return NEUTRAL."""
        pts = list(self._pen_points)
        kind = self._pen_kind
        subdiv = self._pen_subdivisions
        self._exit_draw(context)
        if len(pts) == 1:
            if stage == "interior":
                self._user_strokes.append({"kind": "point", "points": [pts[0]]})
                self._persist_and_redraw(context)
            return {"RUNNING_MODAL"}
        if len(pts) >= 2:
            from ...core.automesh.stroke_geometry import (  # type: ignore[import-not-found]
                subdivide_polyline,
            )

            dense = subdivide_polyline(pts, subdiv)
            self._commit_pen_stroke(context, kind, dense, stage)
        return {"RUNNING_MODAL"}

    def _pen_cancel(self, context: bpy.types.Context) -> None:
        self._exit_draw(context)

    def _commit_pen_stroke(
        self,
        context: bpy.types.Context,
        kind: str,
        pts: list[tuple[float, float]],
        stage: str,
    ) -> None:
        """Commit a finished pen polyline. If an endpoint coincides with an
        endpoint of an existing same-kind stroke (snap guarantees exact coords),
        merge into that stroke so connected traces stay ONE deletable entity
        rather than two strokes stacked on a shared vert."""
        target = self._user_strokes if stage == "interior" else self._user_outer_strokes
        if not self._merge_into_existing(target, kind, pts):
            target.append({"kind": kind, "points": pts})
        self._append_persist(context, stage)

    @staticmethod
    def _merge_into_existing(
        target: list[Stroke], kind: str, pts: list[tuple[float, float]]
    ) -> bool:
        """Concatenate ``pts`` into the first same-kind stroke that shares an
        endpoint (dropping the duplicated shared vert). Returns True on merge."""

        def same(p: tuple[float, float], q: tuple[float, float]) -> bool:
            return abs(p[0] - q[0]) < 1e-6 and abs(p[1] - q[1]) < 1e-6

        a0, a1 = pts[0], pts[-1]
        for stroke in target:
            if stroke["kind"] != kind or len(stroke["points"]) < 2:
                continue
            sp = list(stroke["points"])
            b0, b1 = sp[0], sp[-1]
            if same(a0, b1):
                stroke["points"] = sp + pts[1:]
            elif same(a1, b0):
                stroke["points"] = pts + sp[1:]
            elif same(a0, b0):
                stroke["points"] = list(reversed(sp)) + pts[1:]
            elif same(a1, b1):
                stroke["points"] = sp + list(reversed(pts))[1:]
            else:
                continue
            return True
        return False

    def _append_persist(self, context: bpy.types.Context, stage: str) -> None:
        obj = context.active_object
        if obj is not None:
            if stage == "interior":
                write_user_strokes(obj, self._user_strokes)
            else:
                write_user_outer_strokes(obj, self._user_outer_strokes)
        if stage == "outer" and self._outer_preview_relevant():
            self._refresh_outer_preview(context)
        _tag_redraw_view3d(context)

    def _outer_preview_relevant(self) -> bool:
        """True when the spliced preview can change. Cut strokes carve corridor
        holes (not the contour) and never feed compute_outer_preview, so a
        cut-only commit/undo/delete skips the splice + resample when no extend
        stroke is currently in the list AND the preview is already empty."""
        if self._output.outer_preview:
            return True
        return any(s["kind"] == "stroke" for s in self._user_outer_strokes)

    def _refresh_outer_preview(self, context: bpy.types.Context) -> None:
        """Recompute the Stage 2 spliced-outer preview in place so the
        artist sees the silhouette APPLY will build after extend edits.

        ``compute_outer_preview`` reads ``output.user_outer_strokes``; that
        field is only synced into ``self._output`` at APPLY / stage 5 entry,
        so during Stage 2 editing we have to mirror the live operator list
        first or the preview is computed against an empty list and never
        renders.
        """
        self._output.user_outer_strokes = self._user_outer_strokes
        preview = compute_outer_preview(self._output, _snapshot_params(context))
        self._output.outer_preview[:] = preview
        _tag_redraw_view3d(context)

    def _delete_at_mouse(
        self, context: bpy.types.Context, event: bpy.types.Event, stage: str
    ) -> None:
        if stage == "interior":
            self._delete_stroke_at_mouse(context, event)
        else:
            self._delete_outer_stroke_at_mouse(context, event)

    def _pen_undo(self, context: bpy.types.Context, stage: str) -> set[str]:
        if stage == "interior":
            return self._stroke_undo(context)
        return self._outer_stroke_undo(context)

    def _pen_undo_in_draw(self, context: bpy.types.Context, stage: str) -> set[str]:
        """Ctrl+Z while drawing: drop the last placed pen vert if a line is in
        progress; with no pen verts placed this is a no-op rather than a
        silent undo of the last committed stroke (the artist has no visual
        cue that fallback would have happened)."""
        if not self._pen_points:
            return {"RUNNING_MODAL"}
        self._pen_points.pop()
        self._pen_active = bool(self._pen_points)
        self._live_preview["points"] = list(self._pen_points)
        self._live_preview["active"] = bool(self._pen_points)
        _tag_redraw_view3d(context)
        return {"RUNNING_MODAL"}

    def _pen_mousemove(
        self, context: bpy.types.Context, event: bpy.types.Event, stage: str
    ) -> set[str]:
        self._tooltip_mouse_ref[0] = (event.mouse_region_x, event.mouse_region_y)
        if self._draw_active:
            warn = stage == "interior" and self._cursor_outside_outer(context, event)
            text = self._pen_tooltip_text(stage)
            if warn:
                text += " - outside silhouette!"
            self._tooltip_text_ref[0] = text
            self._tooltip_color_ref[0] = _TOOLTIP_BG_WARN if warn else _TOOLTIP_BG_NORMAL
            self._delete_hover_points.clear()
            cursor = _region_to_world_xz(context, event)
            self._live_preview["cursor"] = (
                self._apply_axis_lock(cursor) if (cursor and self._pen_active) else cursor
            )
            if self._stroke_active and cursor:
                self._stroke_raw_points.append(cursor)
            _tag_redraw_view3d(context)
            return {"RUNNING_MODAL"}
        # NEUTRAL feedback.
        self._tooltip_text_ref[0] = self._neutral_tooltip_text(stage)
        self._tooltip_color_ref[0] = _TOOLTIP_BG_NORMAL
        hover = self._user_strokes if stage == "interior" else self._user_outer_strokes
        if event.alt:
            self._update_delete_hover(context, event, hover)
        else:
            self._delete_hover_points.clear()
        _tag_redraw_view3d(context)
        return {"RUNNING_MODAL"}

    def _pen_tooltip_text(self, stage: str) -> str:
        if self._pen_kind == "cut":
            verb = "Cut"
        elif stage == "outer":
            verb = "Extend"
        else:
            verb = "Fold"
        axis = f" | {self._axis_lock.upper()}-lock" if self._axis_lock else ""
        return (
            f"{verb} pen | subdiv {self._pen_subdivisions}{axis} - "
            "click=vert, drag=draw, X/Z=lock, wheel/0-9=subdiv, RMB/Enter=finish, Esc=cancel"
        )

    def _neutral_tooltip_text(self, stage: str) -> str:
        if stage == "outer":
            return "tap Shift=Extend / Ctrl=Cut | Alt+click=delete"
        return "click=point | tap Shift=Fold / Ctrl=Cut | Alt+click=delete"

    def _commit_drag_stroke(
        self, context: bpy.types.Context, raw: list[tuple[float, float]], kind: str, stage: str
    ) -> None:
        """Smooth, resample, and append a free-draw stroke (chaikin + arc-length
        resample by interior_spacing). Subdivisions do not apply here - free-draw
        is already dense ( subdivisions are pen-segment-only)."""
        from ...core.automesh.stroke_geometry import (
            chaikin_smooth,
            resample_polyline,
        )

        smoothed = chaikin_smooth(raw, iters=self._STROKE_SMOOTH_ITERS)
        spacing = self._resolve_interior_spacing(context)
        resampled = resample_polyline(smoothed, spacing=spacing)
        if len(resampled) >= 2:
            target = self._user_strokes if stage == "interior" else self._user_outer_strokes
            target.append({"kind": kind, "points": resampled})

    def _persist_and_redraw(self, context: bpy.types.Context) -> None:
        """Persist user strokes to the active object and request a redraw."""
        obj = context.active_object
        if obj is not None:
            write_user_strokes(obj, self._user_strokes)
        _tag_redraw_view3d(context)

    def _stroke_undo(self, context: bpy.types.Context) -> set[str]:
        if self._user_strokes:
            self._user_strokes.pop()
            obj = context.active_object
            if obj is not None:
                write_user_strokes(obj, self._user_strokes)
            _tag_redraw_view3d(context)
        return {"RUNNING_MODAL"}

    def _advance(self, context: bpy.types.Context) -> set[str]:
        idx = self._active_stages.index(self._stage)
        if idx >= len(self._active_stages) - 1:  # already on APPLY (last stage)
            return {"PASS_THROUGH"}
        obj = context.active_object
        image = _resolve_image(obj) if obj is not None else None
        if obj is None or image is None:
            return self._finish(context, cancel=True)
        params = _snapshot_params(context)
        next_stage = self._active_stages[idx + 1]
        if next_stage == AuthoringStage.EDIT_OUTLINE:
            self._user_outer_strokes = read_user_outer_strokes(obj)
            self._reset_draw_state()
            self._refresh_outer_preview(context)
        elif next_stage == AuthoringStage.INNER_LOOPS:
            self._output.inner_loops = compute_inner_loops_for_stage(obj, image, params)
        elif next_stage == AuthoringStage.EDIT_INTERIOR_POINTS:
            self._user_strokes = read_user_strokes(obj)
            self._reset_draw_state()
        elif next_stage == AuthoringStage.PREVIEW_INTERIOR:
            try:
                self._refresh_steiner_preview(context, obj, image, params)
            except ValueError as exc:
                # A degenerate CDT (self-intersecting fold/cut, empty silhouette)
                # used to bubble up to modal()'s except Exception and cancel the
                # whole session. Report + stay on the previous stage instead.
                report_error(self, f"Preview failed: {exc}")
                return {"PASS_THROUGH"}
        elif next_stage == AuthoringStage.APPLY:
            picker = _resolve_picker(context)
            self._output.user_outer_strokes = self._user_outer_strokes
            self._output.user_strokes = self._user_strokes
            try:
                counters = apply_mesh(obj, image, self._output, params, picker)
            except ValueError as exc:
                report_error(
                    self,
                    f"CDT failed: {exc} - reduce loop count or increase spacing",
                )
                return {"PASS_THROUGH"}
            if counters.get("stroke_verts_dropped", 0) > 0:
                dropped = counters["stroke_verts_dropped"]
                report_warn(
                    self,
                    f"Stroke: {dropped} vert(s) dropped (outside silhouette)",
                )
            report_info(
                self,
                f"Authoring applied: {counters.get('total_verts', 0)} verts, "
                f"{counters.get('total_faces', 0)} faces",
            )
            return self._finish(context, cancel=False)
        self._stage = next_stage
        type(self)._current_stage_label = _stage_label(self._stage, self._interior_mode)
        type(self)._current_stage = self._stage
        self._report_stage_entry(next_stage)
        self._handles = refresh_overlay(
            self._handles, self._stage, self._output, **self._overlay_kwargs()
        )
        _tag_redraw_view3d(context)
        return {"PASS_THROUGH"}

    def _report_stage_entry(self, stage: AuthoringStage) -> None:
        """Surface a one-line result for the stage just entered so the artist
        gets feedback on ENTER without having to move the mouse (APPLY reports
        its own verts/faces summary + finishes, so it is handled separately)."""
        if stage == AuthoringStage.EDIT_OUTLINE:
            msg = f"{len(self._output.outer)} outer verts"
        elif stage == AuthoringStage.INNER_LOOPS:
            msg = f"{len(self._output.inner_loops)} inner loop(s)"
        elif stage == AuthoringStage.EDIT_INTERIOR_POINTS:
            msg = f"{len(self._user_strokes)} interior stroke(s)"
        elif stage == AuthoringStage.PREVIEW_INTERIOR:
            if self._interior_mode == "SIMPLE":
                msg = f"{len(self._output.triangulation_preview)} triangulation edge(s)"
            else:
                msg = f"{len(self._output.all_steiners)} interior vert(s)"
        else:
            return
        report_info(self, f"{_stage_label(stage, self._interior_mode)}: {msg}")

    def _retreat(self, context: bpy.types.Context) -> set[str]:
        idx = self._active_stages.index(self._stage)
        if idx == 0:
            return {"PASS_THROUGH"}
        self._stage = self._active_stages[idx - 1]
        if self._stage in {AuthoringStage.EDIT_INTERIOR_POINTS, AuthoringStage.EDIT_OUTLINE}:
            # Drop any abandoned in-progress pen so a stale live preview is
            # not drawn when the artist steps back into a pen stage.
            self._reset_draw_state()
        type(self)._current_stage_label = _stage_label(self._stage, self._interior_mode)
        type(self)._current_stage = self._stage
        self._report_stage_entry(self._stage)
        self._handles = refresh_overlay(
            self._handles, self._stage, self._output, **self._overlay_kwargs()
        )
        _tag_redraw_view3d(context)
        return {"PASS_THROUGH"}

    def _apply_interior_mode_change(self, context: bpy.types.Context, mode: str) -> None:
        """Rebuild the active stage list when the interior mode flips mid-modal
        . If the current stage was dropped (INNER_LOOPS on flip to
         SIMPLE), snap back to EDIT_OUTLINE and clear any in-progress pen state
         + reload that stage's strokes so a stale Stage 4 live preview cannot
         leak into Stage 2."""
        self._interior_mode = mode
        self._active_stages = _stages_for_mode(mode)
        snapped = self._stage not in self._active_stages
        if snapped:
            self._stage = AuthoringStage.EDIT_OUTLINE
            self._reset_draw_state()
            obj = context.active_object
            if obj is not None:
                self._user_outer_strokes = read_user_outer_strokes(obj)
            self._refresh_outer_preview(context)
        type(self)._current_stage_label = _stage_label(self._stage, self._interior_mode)
        type(self)._current_stage = self._stage
        type(self)._current_interior_mode = self._interior_mode

    def _refresh_steiner_preview(
        self,
        context: bpy.types.Context,
        obj: bpy.types.Object,
        image: bpy.types.Image,
        params: StageParams,
    ) -> None:
        """Stage 5 preview compute. SIMPLE shows the real CDT
        triangulation wireframe; DENSE shows the dense Steiner point cloud.
        The two outputs are mutually exclusive so the overlay draws one."""
        if self._interior_mode == "SIMPLE":
            self._output.user_outer_strokes = self._user_outer_strokes
            self._output.user_strokes = self._user_strokes
            self._output.all_steiners = []
            self._output.triangulation_preview = compute_triangulation_preview(
                obj, image, self._output, params
            )
        else:
            picker = _resolve_picker(context)
            bone_segments = collect_bone_segments(picker) if picker is not None else []
            self._output.triangulation_preview = []
            self._output.all_steiners = compute_all_steiners(
                self._output.outer,
                self._output.inner_loops,
                self._output.user_steiners,
                bone_segments,
                params,
            )

    def _recompute_current_stage(self, context: bpy.types.Context, params: StageParams) -> None:
        obj = context.active_object
        image = _resolve_image(obj) if obj is not None else None
        if obj is None or image is None:
            return
        if self._stage == AuthoringStage.OUTER:
            self._output.outer = compute_outer(obj, image, params)
        elif self._stage == AuthoringStage.EDIT_OUTLINE:
            # : a slider drag while editing the silhouette must also
            # refresh the base outer + the spliced preview, otherwise both
            # lag the live params and extends are authored against an
            # outdated boundary.
            self._output.outer = compute_outer(obj, image, params)
            self._refresh_outer_preview(context)
        elif self._stage == AuthoringStage.INNER_LOOPS:
            self._output.inner_loops = compute_inner_loops_for_stage(obj, image, params)
        elif self._stage == AuthoringStage.PREVIEW_INTERIOR:
            try:
                self._refresh_steiner_preview(context, obj, image, params)
            except ValueError as exc:
                report_error(self, f"Preview failed: {exc}")
                return
        self._handles = refresh_overlay(
            self._handles, self._stage, self._output, **self._overlay_kwargs()
        )
        _tag_redraw_view3d(context)

    def _overlay_kwargs(self) -> dict[str, object]:
        """Return keyword args for register/refresh_overlay for the current stage."""
        if self._stage == AuthoringStage.EDIT_OUTLINE:
            return self._stage2_overlay_kwargs()
        if self._stage == AuthoringStage.EDIT_INTERIOR_POINTS:
            return self._stage3_overlay_kwargs()
        return self._stage4plus_overlay_kwargs()

    def _stage2_overlay_kwargs(self) -> dict[str, object]:
        """Return keyword args for Stage 2 (EDIT_OUTLINE) live containers.

        Passes the outer stroke list via user_outer_strokes (cut = red,
        ) plus the shared live-preview dict so the  toggle pen
        renders its in-progress polyline / free-draw / axis guide the same way
        Stage 4 does. Tooltip refs carry the DRAW/NEUTRAL intent text.
        """
        return {
            "user_outer_strokes": self._user_outer_strokes,
            "live_preview_ref": self._live_preview,
            "tooltip_mouse_ref": self._tooltip_mouse_ref,
            "tooltip_text_ref": self._tooltip_text_ref,
            "tooltip_color_ref": self._tooltip_color_ref,
            "delete_hover_ref": self._delete_hover_points,
        }

    def _stage3_overlay_kwargs(self) -> dict[str, object]:
        """Return keyword args for register/refresh_overlay Stage 4 live containers.

        Passes the live-preview dict instead of the gray raw-stroke refs:
        _draw_live_preview renders the colored in-progress pen / free-draw
        feedback (verts + edges + cursor rubber-band) for both gestures.
        Tooltip refs are included so the POST_PIXEL handler tracks intent.
        """
        return {
            "user_strokes": self._user_strokes,
            "live_preview_ref": self._live_preview,
            "tooltip_mouse_ref": self._tooltip_mouse_ref,
            "tooltip_text_ref": self._tooltip_text_ref,
            "tooltip_color_ref": self._tooltip_color_ref,
            "delete_hover_ref": self._delete_hover_points,
        }

    def _stage4plus_overlay_kwargs(self) -> dict[str, object]:
        """Return keyword args for register/refresh_overlay Stage 4+ live containers.

        Passes outer and interior stroke lists separately so register_overlay
        can register two distinct draw handlers - one per context - giving each
        the correct cut color: outer = orange (chunk-remove), interior = red (rip).
        Does not include raw stroke or active flag (Stage 2 and Stage 3 only).
        """
        return {
            "user_strokes": self._user_strokes,
            "user_outer_strokes": self._user_outer_strokes,
        }

    def _stroke_index_under_cursor(
        self, context: bpy.types.Context, event: bpy.types.Event, strokes: list[Stroke]
    ) -> int | None:
        """Index of the first stroke with a vert within the pick radius, or None.

        The pick radius is a screen-space pixel distance (_STROKE_PICK_RADIUS_PX)
        converted to world units at the cursor so picking feels consistent at
        any zoom level."""
        mouse_world = _region_to_world_xz(context, event)
        if mouse_world is None:
            return None
        near_world = _region_to_world_xz_offset(context, event, dx=self._STROKE_PICK_RADIUS_PX)
        if near_world is None:
            return None
        pick_d2 = (near_world[0] - mouse_world[0]) ** 2 + (near_world[1] - mouse_world[1]) ** 2
        for idx, stroke in enumerate(strokes):
            for pt in stroke["points"]:
                d2 = (pt[0] - mouse_world[0]) ** 2 + (pt[1] - mouse_world[1]) ** 2
                if d2 <= pick_d2:
                    return idx
        return None

    def _update_delete_hover(
        self, context: bpy.types.Context, event: bpy.types.Event, strokes: list[Stroke]
    ) -> None:
        """Set the delete highlight to the stroke under the cursor, or clear it."""
        self._delete_hover_points.clear()
        idx = self._stroke_index_under_cursor(context, event, strokes)
        if idx is not None:
            self._delete_hover_points.extend(strokes[idx]["points"])

    def _delete_stroke_at_mouse(self, context: bpy.types.Context, event: bpy.types.Event) -> None:
        """Hit-test: remove stroke if any vert is within _STROKE_PICK_RADIUS_PX of mouse."""
        idx = self._stroke_index_under_cursor(context, event, self._user_strokes)
        if idx is None:
            return
        self._user_strokes.pop(idx)
        self._delete_hover_points.clear()
        obj = context.active_object
        if obj is not None:
            write_user_strokes(obj, self._user_strokes)

    def _resolve_interior_spacing(self, context: bpy.types.Context) -> float:
        """Return the interior_spacing param from scene props (same source as _snapshot_params)."""
        skinning = context.scene.proscenio.skinning
        return float(skinning.automesh_interior_spacing)

    def _finish(self, context: bpy.types.Context, *, cancel: bool) -> set[str]:
        try:
            unregister_overlay(self._handles)
            if self._timer is not None:
                context.window_manager.event_timer_remove(self._timer)
                self._timer = None
            self._remove_statusbar()
            if self._session is not None:
                restore_session(context, self._session)
        finally:
            report_info(self, "Authoring modal restored")
        return {"CANCELLED" if cancel else "FINISHED"}

    def _append_statusbar(self) -> None:
        if not type(self)._statusbar_appended:
            bpy.types.STATUSBAR_HT_header.prepend(_draw_statusbar_authoring)
            type(self)._statusbar_appended = True

    def _remove_statusbar(self) -> None:
        if type(self)._statusbar_appended:
            with contextlib.suppress(ValueError, RuntimeError):
                bpy.types.STATUSBAR_HT_header.remove(_draw_statusbar_authoring)
            type(self)._statusbar_appended = False


def _snapshot_params(context: bpy.types.Context) -> StageParams:
    skinning = context.scene.proscenio.skinning
    return StageParams(
        resolution=float(skinning.automesh_resolution),
        alpha_threshold=int(skinning.automesh_alpha_threshold),
        margin_pixels=int(skinning.automesh_margin_pixels),
        contour_vertices=int(skinning.automesh_contour_vertices),
        inner_loop_count=int(skinning.authoring_inner_loop_count),
        inner_loop_spacing=float(skinning.authoring_inner_loop_spacing),
        interior_spacing=float(skinning.automesh_interior_spacing),
        bone_radius=float(skinning.automesh_bone_radius),
        bone_factor=int(skinning.automesh_bone_factor),
        cut_margin=float(skinning.authoring_cut_margin),
        interior_mode=cast(Literal["SIMPLE", "DENSE"], skinning.automesh_interior_mode),
    )


def _resolve_image(obj: bpy.types.Object | None) -> bpy.types.Image | None:
    """Reuse the same lookup automesh_from_sprite uses."""
    if obj is None or obj.data is None:
        return None
    active_material = getattr(obj, "active_material", None)
    image = _find_tex_image(active_material)
    if image is not None:
        return image
    for material in obj.data.materials:
        if material is active_material:
            continue
        image = _find_tex_image(material)
        if image is not None:
            return image
    return None


def _find_tex_image(material: bpy.types.Material | None) -> bpy.types.Image | None:
    if material is None or not material.use_nodes or material.node_tree is None:
        return None
    for node in material.node_tree.nodes:
        if node.type == "TEX_IMAGE" and node.image is not None:
            return node.image
    return None


def _resolve_picker(context: bpy.types.Context) -> bpy.types.Object | None:
    scene_props = getattr(context.scene, "proscenio", None)
    if scene_props is None:
        return None
    picker = getattr(scene_props, "active_armature", None)
    if picker is None or picker.type != "ARMATURE":
        return None
    return picker


def _region_to_world_xz(context: bpy.types.Context, event: bpy.types.Event) -> Point2D | None:
    """Project region pixel coords to Y=0 XZ plane (Proscenio convention)."""
    from bpy_extras import view3d_utils  # local: bpy_extras not always available at module load

    region = context.region
    rv3d = context.region_data
    if region is None or rv3d is None:
        return None
    coord = (event.mouse_region_x, event.mouse_region_y)
    origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    if abs(direction.y) < 1e-9:
        return None
    t = -origin.y / direction.y
    hit = origin + direction * t
    return (hit.x, hit.z)


def _region_to_world_xz_offset(
    context: bpy.types.Context, event: bpy.types.Event, dx: int = 0, dy: int = 0
) -> Point2D | None:
    """Project an offset pixel position to Y=0 XZ plane.

    Used to convert a screen-space pixel radius into a world-space distance
    for pick hit-testing without assuming a fixed world-space threshold.
    """
    from bpy_extras import view3d_utils  # local: bpy_extras not always available at module load

    region = context.region
    rv3d = context.region_data
    if region is None or rv3d is None:
        return None
    coord = (event.mouse_region_x + dx, event.mouse_region_y + dy)
    origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    if abs(direction.y) < 1e-9:
        return None
    t = -origin.y / direction.y
    if t < 0:
        return None
    hit = origin + direction * t
    return (hit.x, hit.z)


def _chord(layout: bpy.types.UILayout, *parts: tuple[str, str]) -> None:
    """Emit one aligned chord row. Each part is (icon, text); an empty
    icon prints text only, an empty text prints the icon only. Mirrors
    quick_armature._emit_chord_layout so the hint matches Blender's own
    modal status bars (knife / loop cut)."""
    row = layout.row(align=True)
    for icon, text in parts:
        row.label(text=text, icon=icon or "NONE")


def _emit_authoring_chord_layout(
    layout: bpy.types.UILayout, stage: AuthoringStage, mode: str
) -> None:
    """Render per-stage gesture chords with native EVENT_*/MOUSE_* icons."""
    _chord(layout, ("MOD_REMESH", f"Automesh: {_stage_label(stage, mode)}"))
    if stage in {AuthoringStage.EDIT_OUTLINE, AuthoringStage.EDIT_INTERIOR_POINTS}:
        #  toggle pen: tap a modifier to enter draw mode (no holding).
        verb = "extend" if stage == AuthoringStage.EDIT_OUTLINE else "fold"
        if stage == AuthoringStage.EDIT_INTERIOR_POINTS:
            _chord(layout, ("MOUSE_LMB", "point"))
        _chord(layout, ("EVENT_SHIFT", "tap"), ("", f"{verb}-pen"))
        _chord(layout, ("EVENT_CTRL", "tap"), ("", "cut-pen"))
        _chord(layout, ("MOUSE_LMB", "vert / drag=draw"))
        _chord(layout, ("EVENT_X", "/"), ("EVENT_Z", "axis lock"))
        _chord(layout, ("MOUSE_MMB", "/ 0-9 = subdiv"))
        _chord(layout, ("MOUSE_RMB", "/"), ("EVENT_RETURN", "finish"))
        _chord(layout, ("EVENT_ALT", "+"), ("MOUSE_LMB", "delete"))
        _chord(layout, ("EVENT_CTRL", "+"), ("EVENT_Z", "undo"))
    _chord(layout, ("EVENT_RETURN", "next"))
    _chord(layout, ("EVENT_BACKSPACE", "back"))
    _chord(layout, ("EVENT_ESC", "cancel"))


def _draw_statusbar_authoring(self: bpy.types.Header, _context: bpy.types.Context) -> None:
    _emit_authoring_chord_layout(
        self.layout,
        PROSCENIO_OT_automesh_authoring._current_stage,
        PROSCENIO_OT_automesh_authoring._current_interior_mode,
    )
    self.layout.separator_spacer()


def _tag_redraw_view3d(context: bpy.types.Context) -> None:
    """Trigger a viewport + statusbar repaint so GPU overlay updates AND the
    stage chord layout land without user interaction (zoom/pan/mouse move).
    Iterates every VIEW_3D + STATUSBAR area in every window since the modal
    may have been invoked from one but the user may be looking at another.
    The statusbar reads class-level stage state, so a stage advance/retreat
    must repaint it explicitly (it otherwise only refreshes on mouse move)."""
    wm = context.window_manager
    if wm is None:
        return
    for window in wm.windows:
        if window.screen is None:
            continue
        for area in window.screen.areas:
            if area.type in {"VIEW_3D", "STATUSBAR"}:
                area.tag_redraw()


_classes: tuple[type, ...] = (PROSCENIO_OT_automesh_authoring,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
