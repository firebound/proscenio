"""Interactive modal automesh authoring operator (SPEC 013.2).

5-stage modal that previews each pipeline stage with a GPU overlay
so the artist iterates on the mesh shape before any geometry commits.
Coexists with the one-shot automesh_from_sprite operator.
"""

from __future__ import annotations

import contextlib
import traceback
from typing import ClassVar

import bpy

from ..core.bpy_helpers.automesh.authoring_overlay import (  # type: ignore[import-not-found]
    OverlayHandles,
    refresh_overlay,
    register_overlay,
    unregister_overlay,
)
from ..core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
    apply_mesh,
    compute_all_steiners,
    compute_inner_loops_for_stage,
    compute_outer,
    read_user_outer_strokes,
    read_user_strokes,
    write_user_outer_strokes,
    write_user_strokes,
)
from ..core.bpy_helpers.automesh.authoring_session import (  # type: ignore[import-not-found]
    AuthoringSession,
)
from ..core.bpy_helpers.automesh.authoring_session import (
    capture as capture_session,
)
from ..core.bpy_helpers.automesh.authoring_session import (
    restore as restore_session,
)
from ..core.bpy_helpers.automesh.bridge import (  # type: ignore[import-not-found]
    collect_bone_segments,
)
from ..core.report import (  # type: ignore[import-not-found]
    report_error,
    report_info,
    report_warn,
)
from ..core.skinning.authoring_stages import (  # type: ignore[import-not-found]
    AuthoringStage,
    Point2D,
    StageOutput,
    StageParams,
    Stroke,
)

_TIMER_INTERVAL = 0.1
_STAGE_NAMES = {
    AuthoringStage.OUTER: "1/6 Outer contour",
    AuthoringStage.USER_OUTER: (
        "2/6 User outer edits (LMB drag in=cut / out=extend [T7] / Ctrl+drag=delete)"
    ),
    AuthoringStage.INNER_LOOPS: "3/6 Inner loops",
    AuthoringStage.USER_STEINERS: (
        "4/6 User Steiner points (LMB stroke / Shift+drag cut / Ctrl+drag delete)"
    ),
    AuthoringStage.STEINER_PREVIEW: "5/6 Steiner preview",
    AuthoringStage.APPLY: "6/6 Apply",
}


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

    # Stage 3 stroke capture state (Wave: stroke redesign)
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
    _current_stage_label: str = _STAGE_NAMES[AuthoringStage.OUTER]

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
        self._output = StageOutput()
        self._handles = {
            "outer": None,
            "inner": None,
            "steiners": None,
            "user_dots": None,
            "user_strokes": None,
            "raw_stroke": None,
            "tooltip": None,
        }
        self._timer = None
        self._stroke_active: bool = False
        # Single-element list so the draw callback holds a stable reference
        # to the container; we mutate [0] instead of reassigning the bool.
        self._stroke_active_ref: list[bool] = [False]
        self._stroke_start_screen: tuple[int, int] | None = None
        # Must be mutated in-place (clear/append) so the registered draw
        # callback always reads the current contents via the same reference.
        self._stroke_raw_points: list[tuple[float, float]] = []
        # Whether the in-flight stroke was started with Shift held (kind="cut").
        # Captured at LMB PRESS so subsequent Shift release before LMB UP does
        # not change intent mid-drag.
        self._stroke_is_cut: bool = False
        self._user_strokes: list[Stroke] = []

        # Tooltip live state - single-element lists mutated in-place so the
        # registered POST_PIXEL draw handler always reads current values
        # without needing re-registration on every MOUSEMOVE.
        self._tooltip_mouse_ref: list[tuple[int, int]] = [(-1, -1)]
        self._tooltip_text_ref: list[str] = [""]

        # Stage 2 (USER_OUTER) stroke capture state (parallel to Stage 4).
        self._outer_stroke_active: bool = False
        # Single-element list so the draw callback holds a stable reference.
        self._outer_stroke_active_ref: list[bool] = [False]
        self._outer_stroke_start_screen: tuple[int, int] | None = None
        # Must be mutated in-place (clear/append) so draw callbacks stay valid.
        self._outer_stroke_raw_points: list[tuple[float, float]] = []
        # Intent captured at PRESS time: "extend" (start outside outer),
        # "cut" (start inside outer). Resolved once at LMB PRESS.
        self._outer_stroke_intent: str = "extend"
        self._user_outer_strokes: list[Stroke] = []

        try:
            self._output.outer = compute_outer(obj, image, params)
            self._handles = register_overlay(self._stage, self._output)
            type(self)._current_stage_label = _STAGE_NAMES[self._stage]
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
            if event.type == "ESC":
                return self._finish(context, cancel=True)
            if event.type in {"RET", "NUMPAD_ENTER"} and event.value == "PRESS":
                return self._advance(context)
            if event.type == "BACK_SPACE" and event.value == "PRESS":
                return self._retreat(context)
            if self._stage == AuthoringStage.USER_OUTER:
                handled = self._handle_user_outer_event(context, event)
                if handled is not None:
                    return handled
            if self._stage == AuthoringStage.USER_STEINERS:
                handled = self._handle_user_steiners_event(context, event)
                if handled is not None:
                    return handled
            if event.type == "TIMER" and getattr(event, "timer", None) is self._timer:
                current = _snapshot_params(context)
                if current != self._last_params:
                    self._recompute_current_stage(context, current)
                    self._last_params = current
        except Exception:
            traceback.print_exc()
            return self._finish(context, cancel=True)
        return {"PASS_THROUGH"}

    def _handle_user_outer_event(
        self, context: bpy.types.Context, event: bpy.types.Event
    ) -> set[str] | None:
        """Dispatch Stage 2 (USER_OUTER) event. Returns None when not consumed."""
        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            return self._outer_stroke_press(context, event)
        if event.type == "MOUSEMOVE":
            self._tooltip_mouse_ref[0] = (event.mouse_region_x, event.mouse_region_y)
            self._tooltip_text_ref[0] = self._compute_stage2_tooltip_text(context, event)
            _tag_redraw_view3d(context)
            if self._outer_stroke_active:
                return self._outer_stroke_move(context, event)
            return {"RUNNING_MODAL"}
        if event.type == "LEFTMOUSE" and event.value == "RELEASE" and self._outer_stroke_active:
            return self._outer_stroke_release(context, event)
        if event.type == "Z" and event.ctrl and event.value == "PRESS":
            return self._outer_stroke_undo(context)
        return None

    def _outer_stroke_press(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        if event.ctrl:
            self._delete_outer_stroke_at_mouse(context, event)
            _tag_redraw_view3d(context)
            return {"RUNNING_MODAL"}
        self._outer_stroke_active = True
        self._outer_stroke_active_ref[0] = True
        self._outer_stroke_start_screen = (event.mouse_region_x, event.mouse_region_y)
        world_pt = _region_to_world_xz(context, event)
        self._outer_stroke_raw_points.clear()
        # Intent decided by first mouse position: inside outer = cut, outside = extend.
        if world_pt and self._point_inside_outer(world_pt):
            self._outer_stroke_intent = "cut"
        else:
            self._outer_stroke_intent = "extend"
        if world_pt:
            self._outer_stroke_raw_points.append(world_pt)
        return {"RUNNING_MODAL"}

    def _outer_stroke_move(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        world_pt = _region_to_world_xz(context, event)
        if world_pt:
            self._outer_stroke_raw_points.append(world_pt)
            _tag_redraw_view3d(context)
        return {"RUNNING_MODAL"}

    def _outer_stroke_release(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        self._outer_stroke_active = False
        self._outer_stroke_active_ref[0] = False
        start = self._outer_stroke_start_screen
        self._outer_stroke_start_screen = None
        if start is None or not self._outer_stroke_raw_points:
            self._outer_stroke_raw_points.clear()
            return {"RUNNING_MODAL"}
        dx = event.mouse_region_x - start[0]
        dy = event.mouse_region_y - start[1]
        drag_px = (dx * dx + dy * dy) ** 0.5
        if drag_px < self._DRAG_THRESHOLD_PX:
            # Click without drag in Stage 2 = no-op (no single-Steiner on outer).
            self._outer_stroke_raw_points.clear()
            return {"RUNNING_MODAL"}
        self._commit_outer_drag_stroke(context)
        self._outer_stroke_raw_points.clear()
        obj = context.active_object
        if obj is not None:
            write_user_outer_strokes(obj, self._user_outer_strokes)
        _tag_redraw_view3d(context)
        return {"RUNNING_MODAL"}

    def _commit_outer_drag_stroke(self, context: bpy.types.Context) -> None:
        from ..core.automesh.stroke_geometry import (  # type: ignore[import-not-found]
            chaikin_smooth,
            resample_polyline,
        )

        smoothed = chaikin_smooth(self._outer_stroke_raw_points, iters=self._STROKE_SMOOTH_ITERS)
        spacing = self._resolve_interior_spacing(context)
        resampled = resample_polyline(smoothed, spacing=spacing)
        if len(resampled) < 2:
            return
        if self._outer_stroke_intent == "cut":
            kind = "cut"
        else:
            # "extend" intent: detect whether any sample lies outside outer.
            # If so, stroke crosses the border - warn artist. T7 implements
            # the actual splice; T6 just persists with kind="stroke".
            if any(not self._point_inside_outer(p) for p in resampled):
                report_warn(
                    self,
                    "stroke clipped to silhouette (extend portion deferred to T7 splice)",
                )
            kind = "stroke"
        self._user_outer_strokes.append({"kind": kind, "points": resampled})

    def _outer_stroke_undo(self, context: bpy.types.Context) -> set[str]:
        if self._user_outer_strokes:
            self._user_outer_strokes.pop()
            obj = context.active_object
            if obj is not None:
                write_user_outer_strokes(obj, self._user_outer_strokes)
            _tag_redraw_view3d(context)
        return {"RUNNING_MODAL"}

    def _delete_outer_stroke_at_mouse(
        self, context: bpy.types.Context, event: bpy.types.Event
    ) -> None:
        """Hit-test: remove outer stroke if any vert is within pick radius of mouse."""
        mouse_world = _region_to_world_xz(context, event)
        if mouse_world is None:
            return
        near_world = _region_to_world_xz_offset(context, event, dx=self._STROKE_PICK_RADIUS_PX)
        if near_world is None:
            spacing = self._resolve_interior_spacing(context)
            pick_d2 = spacing * spacing
        else:
            pick_dist = (
                (near_world[0] - mouse_world[0]) ** 2 + (near_world[1] - mouse_world[1]) ** 2
            ) ** 0.5
            pick_d2 = pick_dist * pick_dist
        for idx, stroke in enumerate(self._user_outer_strokes):
            for pt in stroke["points"]:
                d2 = (pt[0] - mouse_world[0]) ** 2 + (pt[1] - mouse_world[1]) ** 2
                if d2 <= pick_d2:
                    self._user_outer_strokes.pop(idx)
                    obj = context.active_object
                    if obj is not None:
                        write_user_outer_strokes(obj, self._user_outer_strokes)
                    return

    def _point_inside_outer(self, point_world_xz: tuple[float, float]) -> bool:
        """Check if a WORLD XZ point lies inside the current outer contour.

        output.outer is WORLD XZ per compute_outer convention, so no coordinate
        conversion is needed before calling point_in_polygon.
        """
        from ..core.automesh import point_in_polygon  # type: ignore[import-not-found]

        if not self._output.outer:
            return False
        return point_in_polygon(point_world_xz, self._output.outer)

    def _handle_user_steiners_event(
        self, context: bpy.types.Context, event: bpy.types.Event
    ) -> set[str] | None:
        """Dispatch Stage 4 (USER_STEINERS) event. Returns None when event
        was not consumed (modal falls through to TIMER + PASS_THROUGH)."""
        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            return self._stroke_press(context, event)
        if event.type == "MOUSEMOVE":
            self._tooltip_mouse_ref[0] = (event.mouse_region_x, event.mouse_region_y)
            self._tooltip_text_ref[0] = self._compute_stage4_tooltip_text(event)
            _tag_redraw_view3d(context)
            if self._stroke_active:
                return self._stroke_move(context, event)
            return {"RUNNING_MODAL"}
        if event.type == "LEFTMOUSE" and event.value == "RELEASE" and self._stroke_active:
            return self._stroke_release(context, event)
        if event.type == "Z" and event.ctrl and event.value == "PRESS":
            return self._stroke_undo(context)
        return None

    def _stroke_press(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        if event.ctrl:
            self._delete_stroke_at_mouse(context, event)
            _tag_redraw_view3d(context)
            return {"RUNNING_MODAL"}
        self._stroke_active = True
        self._stroke_active_ref[0] = True
        self._stroke_is_cut = bool(event.shift)
        self._stroke_start_screen = (event.mouse_region_x, event.mouse_region_y)
        world_pt = _region_to_world_xz(context, event)
        self._stroke_raw_points.clear()
        if world_pt:
            self._stroke_raw_points.append(world_pt)
        return {"RUNNING_MODAL"}

    def _stroke_move(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        world_pt = _region_to_world_xz(context, event)
        if world_pt:
            self._stroke_raw_points.append(world_pt)
            _tag_redraw_view3d(context)
        return {"RUNNING_MODAL"}

    def _stroke_release(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        self._stroke_active = False
        self._stroke_active_ref[0] = False
        start = self._stroke_start_screen
        self._stroke_start_screen = None
        if start is None or not self._stroke_raw_points:
            self._stroke_raw_points.clear()
            self._stroke_is_cut = False
            return {"RUNNING_MODAL"}
        dx = event.mouse_region_x - start[0]
        dy = event.mouse_region_y - start[1]
        drag_px = (dx * dx + dy * dy) ** 0.5
        if drag_px < self._DRAG_THRESHOLD_PX:
            self._commit_click_steiner()
        else:
            self._commit_drag_stroke(context)
        self._stroke_raw_points.clear()
        self._stroke_is_cut = False
        obj = context.active_object
        if obj is not None:
            write_user_strokes(obj, self._user_strokes)
        _tag_redraw_view3d(context)
        return {"RUNNING_MODAL"}

    def _commit_click_steiner(self) -> None:
        first_pt = self._stroke_raw_points[0]
        self._user_strokes.append({"kind": "point", "points": [first_pt]})

    def _commit_drag_stroke(self, context: bpy.types.Context) -> None:
        from ..core.automesh.stroke_geometry import (  # type: ignore[import-not-found]
            chaikin_smooth,
            resample_polyline,
        )

        smoothed = chaikin_smooth(self._stroke_raw_points, iters=self._STROKE_SMOOTH_ITERS)
        spacing = self._resolve_interior_spacing(context)
        resampled = resample_polyline(smoothed, spacing=spacing)
        if len(resampled) >= 2:
            kind = "cut" if self._stroke_is_cut else "stroke"
            self._user_strokes.append({"kind": kind, "points": resampled})

    def _stroke_undo(self, context: bpy.types.Context) -> set[str]:
        if self._user_strokes:
            self._user_strokes.pop()
            obj = context.active_object
            if obj is not None:
                write_user_strokes(obj, self._user_strokes)
            _tag_redraw_view3d(context)
        return {"RUNNING_MODAL"}

    def _advance(self, context: bpy.types.Context) -> set[str]:
        if self._stage == AuthoringStage.APPLY:
            return {"PASS_THROUGH"}
        obj = context.active_object
        image = _resolve_image(obj) if obj is not None else None
        if obj is None or image is None:
            return self._finish(context, cancel=True)
        params = _snapshot_params(context)
        next_stage = AuthoringStage(self._stage + 1)
        if next_stage == AuthoringStage.USER_OUTER:
            self._user_outer_strokes = read_user_outer_strokes(obj)
            self._outer_stroke_active_ref[0] = False
            self._outer_stroke_raw_points.clear()
        elif next_stage == AuthoringStage.INNER_LOOPS:
            self._output.inner_loops = compute_inner_loops_for_stage(
                obj, image, self._output.outer, params
            )
        elif next_stage == AuthoringStage.USER_STEINERS:
            self._user_strokes = read_user_strokes(obj)
            # Sync the live list reference used by the draw handler;
            # must update in-place so the registered handler's reference stays valid.
            self._stroke_active_ref[0] = False
            self._stroke_raw_points.clear()
        elif next_stage == AuthoringStage.STEINER_PREVIEW:
            picker = _resolve_picker(context)
            bone_segments = collect_bone_segments(picker) if picker is not None else []
            self._output.all_steiners = compute_all_steiners(
                self._output.outer,
                self._output.inner_loops,
                self._output.user_steiners,
                bone_segments,
                params,
            )
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
        type(self)._current_stage_label = _STAGE_NAMES[self._stage]
        self._handles = refresh_overlay(
            self._handles, self._stage, self._output, **self._overlay_kwargs()
        )
        _tag_redraw_view3d(context)
        return {"PASS_THROUGH"}

    def _retreat(self, context: bpy.types.Context) -> set[str]:
        if self._stage == AuthoringStage.OUTER:
            return {"PASS_THROUGH"}
        self._stage = AuthoringStage(self._stage - 1)
        type(self)._current_stage_label = _STAGE_NAMES[self._stage]
        self._handles = refresh_overlay(
            self._handles, self._stage, self._output, **self._overlay_kwargs()
        )
        _tag_redraw_view3d(context)
        return {"PASS_THROUGH"}

    def _recompute_current_stage(self, context: bpy.types.Context, params: StageParams) -> None:
        obj = context.active_object
        image = _resolve_image(obj) if obj is not None else None
        if obj is None or image is None:
            return
        if self._stage == AuthoringStage.OUTER:
            self._output.outer = compute_outer(obj, image, params)
        elif self._stage == AuthoringStage.INNER_LOOPS:
            self._output.inner_loops = compute_inner_loops_for_stage(
                obj, image, self._output.outer, params
            )
        elif self._stage == AuthoringStage.STEINER_PREVIEW:
            picker = _resolve_picker(context)
            bone_segments = collect_bone_segments(picker) if picker is not None else []
            self._output.all_steiners = compute_all_steiners(
                self._output.outer,
                self._output.inner_loops,
                self._output.user_steiners,
                bone_segments,
                params,
            )
        self._handles = refresh_overlay(
            self._handles, self._stage, self._output, **self._overlay_kwargs()
        )
        _tag_redraw_view3d(context)

    def _overlay_kwargs(self) -> dict[str, object]:
        """Return keyword args for register/refresh_overlay for the current stage."""
        if self._stage == AuthoringStage.USER_OUTER:
            return self._stage2_overlay_kwargs()
        if self._stage == AuthoringStage.USER_STEINERS:
            return self._stage3_overlay_kwargs()
        return self._stage4plus_overlay_kwargs()

    def _stage2_overlay_kwargs(self) -> dict[str, object]:
        """Return keyword args for Stage 2 (USER_OUTER) live containers.

        Passes outer stroke list + raw-stroke refs so the draw callbacks
        render both committed strokes and the in-progress one during Stage 2.
        Stage 4+ also shows Stage 4 strokes but not Stage 2's raw preview.
        Tooltip refs are included so the POST_PIXEL handler tracks intent.
        """
        return {
            "user_strokes": self._user_outer_strokes,
            "stroke_active_ref": self._outer_stroke_active_ref,
            "stroke_raw_points_ref": self._outer_stroke_raw_points,
            "tooltip_mouse_ref": self._tooltip_mouse_ref,
            "tooltip_text_ref": self._tooltip_text_ref,
        }

    def _stage3_overlay_kwargs(self) -> dict[str, object]:
        """Return keyword args for register/refresh_overlay Stage 3 live containers.

        Always passes the same mutable list references so registered draw
        callbacks remain valid across param-change re-registrations.
        Tooltip refs are included so the POST_PIXEL handler tracks intent.
        """
        return {
            "user_strokes": self._user_strokes,
            "stroke_active_ref": self._stroke_active_ref,
            "stroke_raw_points_ref": self._stroke_raw_points,
            "tooltip_mouse_ref": self._tooltip_mouse_ref,
            "tooltip_text_ref": self._tooltip_text_ref,
        }

    def _stage4plus_overlay_kwargs(self) -> dict[str, object]:
        """Return keyword args for register/refresh_overlay Stage 4+ live containers.

        Concatenates outer + inner strokes so both sets are visible from
        Stage 4 (USER_STEINERS) onward. Does not include raw stroke or
        active flag (Stage 2 and Stage 3 only).
        """
        return {
            "user_strokes": self._user_outer_strokes + self._user_strokes,
        }

    def _compute_stage4_tooltip_text(self, event: bpy.types.Event) -> str:
        """Return intent text for Stage 4 (USER_STEINERS) based on modifier state."""
        if event.ctrl:
            return "Delete stroke (hover + click)"
        if event.shift:
            return "Cut stroke"
        return "Fold-line stroke"

    def _compute_stage2_tooltip_text(
        self, context: bpy.types.Context, event: bpy.types.Event
    ) -> str:
        """Return intent text for Stage 2 (USER_OUTER) based on modifier + mouse location."""
        if event.ctrl:
            return "Delete outer stroke (hover + click)"
        world_pt = _region_to_world_xz(context, event)
        if world_pt is None:
            return ""
        if self._point_inside_outer(world_pt):
            return "Cut silhouette"
        return "Extend outer"

    def _delete_stroke_at_mouse(self, context: bpy.types.Context, event: bpy.types.Event) -> None:
        """Hit-test: remove stroke if any vert is within _STROKE_PICK_RADIUS_PX of mouse."""
        mouse_world = _region_to_world_xz(context, event)
        if mouse_world is None:
            return
        near_world = _region_to_world_xz_offset(context, event, dx=self._STROKE_PICK_RADIUS_PX)
        if near_world is None:
            return
        pick_dist_world = (
            (near_world[0] - mouse_world[0]) ** 2 + (near_world[1] - mouse_world[1]) ** 2
        ) ** 0.5
        pick_d2 = pick_dist_world * pick_dist_world
        for idx, stroke in enumerate(self._user_strokes):
            for pt in stroke["points"]:
                d2 = (pt[0] - mouse_world[0]) ** 2 + (pt[1] - mouse_world[1]) ** 2
                if d2 <= pick_d2:
                    self._user_strokes.pop(idx)
                    obj = context.active_object
                    if obj is not None:
                        write_user_strokes(obj, self._user_strokes)
                    return

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
        cut_width=float(skinning.authoring_cut_width),
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


def _draw_statusbar_authoring(self: bpy.types.Header, _context: bpy.types.Context) -> None:
    layout = self.layout
    row = layout.row(align=True)
    row.label(text="", icon="MOD_REMESH")
    row.label(text=f"Automesh Authoring: {PROSCENIO_OT_automesh_authoring._current_stage_label}")
    row = layout.row(align=True)
    row.label(text="", icon="EVENT_RETURN")
    row.label(text="next")
    row = layout.row(align=True)
    row.label(text="", icon="EVENT_BACKSPACE")
    row.label(text="back")
    row = layout.row(align=True)
    row.label(text="", icon="EVENT_ESC")
    row.label(text="cancel")


def _tag_redraw_view3d(context: bpy.types.Context) -> None:
    """Trigger a viewport repaint so GPU overlay updates land without
    user interaction (zoom/pan). Iterates every VIEW_3D area in every
    window since the modal may have been invoked from one but the user
    may be looking at another."""
    wm = context.window_manager
    if wm is None:
        return
    for window in wm.windows:
        if window.screen is None:
            continue
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


_classes: tuple[type, ...] = (PROSCENIO_OT_automesh_authoring,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
