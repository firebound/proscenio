"""Manual Draw ("Draw with vertices") - standalone manual mesh authoring.

Spec 070, Part B. A concept apart from the automeshes: the artist builds the
silhouette by clicking vertices (no alpha, no auto), sees a live SIMPLE
triangulation, and applies it. Reuses the shared closed-loop ``VertexPen`` +
``compute_triangulation_preview`` + ``apply_mesh`` (manual outer); it does NOT
touch the automesh stage machine. Mutually exclusive with the Automesh modal via
the authoring-modal guard.
"""

from __future__ import annotations

import contextlib
import traceback
from dataclasses import replace
from typing import ClassVar, cast

import bpy
from mathutils import Vector

from ...core._shared.armature_resolve import (  # type: ignore[import-not-found]
    active_armature,
)
from ...core._shared.material_images import (  # type: ignore[import-not-found]
    first_material_image,
)
from ...core._shared.report import (  # type: ignore[import-not-found]
    report_error,
    report_info,
    report_warn,
)
from ...core.automesh import point_in_polygon  # type: ignore[import-not-found]
from ...core.automesh.stroke_geometry import (  # type: ignore[import-not-found]
    subdivide_polyline_edges,
)
from ...core.bpy_helpers._shared.redraw import (  # type: ignore[import-not-found]
    tag_redraw_view3d_statusbar,
)
from ...core.bpy_helpers._shared.viewport_math import (  # type: ignore[import-not-found]
    event_in_canvas,
    find_window_region,
    region_event_to_xz,
    region_event_to_xz_offset,
)
from ...core.bpy_helpers.automesh.authoring_overlay import (  # type: ignore[import-not-found]
    OverlayHandles,
    empty_overlay_handles,
    register_manual_draw_overlay,
    unregister_overlay,
)
from ...core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
    apply_mesh,
    compute_mesh_preview_edges,
    read_manual_contour,
    read_user_strokes,
    write_manual_contour,
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
from ...core.bpy_helpers.automesh.vertex_pen import VertexPen  # type: ignore[import-not-found]
from ...core.skinning.authoring_stages import (  # type: ignore[import-not-found]
    StageOutput,
    StageParams,
    Stroke,
)
from .._status_bar import append_statusbar_draw, chord, remove_statusbar_draw
from ._authoring_modal_guard import is_running, mark_running, mark_stopped
from ._authoring_preconditions import poll_mesh_with_image, validate_authoring_invoke
from .automesh_authoring import _MOUSE_GATE_TYPES, _snapshot_params

_MODAL_NAME = "manual_draw"
# Background colors for the cursor tooltip (warning-only, like the automesh pen).
_TOOLTIP_BG_NORMAL = (0.0, 0.0, 0.0, 0.6)
_TOOLTIP_BG_WARN = (0.35, 0.05, 0.05, 0.85)  # red: an interior gesture would land outside


def _local_xz_to_world(
    obj: bpy.types.Object, local_pts: list[tuple[float, float]]
) -> list[tuple[float, float]]:
    """Project stored LOCAL XZ contour points to WORLD XZ for the pen (spec 070 C2)."""
    matrix = obj.matrix_world
    out: list[tuple[float, float]] = []
    for lx, lz in local_pts:
        world = matrix @ Vector((lx, 0.0, lz))
        out.append((world.x, world.z))
    return out


def _downsample(path: list[tuple[float, float]], max_points: int) -> list[tuple[float, float]]:
    """Thin a captured fold path to at most ``max_points`` evenly-spaced samples,
    always keeping the first + last (spec 070 C3) so the CDT gets a clean line."""
    if len(path) <= max_points:
        return list(path)
    step = (len(path) - 1) / (max_points - 1)
    out = [path[round(i * step)] for i in range(max_points)]
    out[-1] = path[-1]
    return out


def _world_xz_to_local(
    obj: bpy.types.Object, world_pts: list[tuple[float, float]]
) -> list[tuple[float, float]]:
    """Project the pen's WORLD XZ contour points to LOCAL XZ for storage (spec 070 C2)."""
    inv = obj.matrix_world.inverted()
    out: list[tuple[float, float]] = []
    for wx, wz in world_pts:
        local = inv @ Vector((wx, 0.0, wz))
        out.append((local.x, local.z))
    return out


class PROSCENIO_OT_draw_mesh_vertices(bpy.types.Operator):
    """Manual Draw: build the mesh silhouette by clicking vertices.

    LMB place a vertex (click the first vertex to close), RMB drag a vertex,
    DEL / Ctrl+Z drop the last, ENTER apply, ESC cancel. A live triangulation
    previews the SIMPLE mesh the contour will build.
    """

    bl_idname = "proscenio.draw_mesh_vertices"
    bl_label = "Proscenio: Draw Mesh with Vertices"
    bl_description = (
        "Manual Draw: build the mesh by clicking the silhouette vertices "
        "(LMB place / RMB drag / DEL last / ENTER apply / ESC cancel). Fully "
        "manual - separate from the automeshes; a live triangulation previews "
        "the SIMPLE mesh"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    _pen: VertexPen
    _handles: OverlayHandles
    _session: AuthoringSession | None
    _tri: list[tuple[tuple[float, float], tuple[float, float]]]
    # Spec 070 C3: Tab cycles the active tool OUTER -> POINT -> FOLD. POINT drops a
    # Steiner on click; FOLD lays a fold line either by free-draw drag or by
    # clicking its vertices (point-by-point edges, like a pen). All feed the
    # pipeline's user_strokes. _fold_chain is the in-progress click-built fold.
    _user_strokes: list[Stroke]
    _tool: str
    _fold_chain: list[tuple[float, float]]
    _fold_subdivs: list[int]  # per-edge subdivision baked into the click-chain
    _fold_current_subdiv: int  # scroll-set count for the next chain edge
    _stroke_capture: list[tuple[float, float]] | None
    _stroke_start_screen: tuple[int, int] | None
    # RMB-drag target: ("outer", i) a contour vert, or ("stroke", si, pi) an
    # interior stroke vert. None when not dragging.
    _drag_target: tuple[str, int] | tuple[str, int, int] | None
    # Spec 070 C3 polish: live preview of the in-progress interior stroke + the
    # Alt+click delete-hover highlight (revisit), so the interior tool reads like
    # the automesh Stage-4 editor.
    _interior_live: dict[str, object]
    _delete_hover: list[tuple[float, float]]
    _DRAG_THRESHOLD_PX: ClassVar[int] = 5
    _INTERIOR_MAX_PATH: ClassVar[int] = 24  # cap a fold path so the CDT stays sane
    _STROKE_PICK_RADIUS_PX: ClassVar[int] = 12  # Alt+click delete pick radius
    _TOOLS: ClassVar[tuple[str, ...]] = ("outer", "point", "fold")
    # Active tool mirrored at class level so the STATUSBAR draw shows it (mode is
    # surfaced there, not in a mouse tooltip - tooltips are warning-only here).
    _current_tool: ClassVar[str] = "outer"
    _statusbar_appended: bool = False
    # Set by the panel's "Exit" button (a re-invoke while live): the running modal
    # finishes on its next event (Quick Armature toggle pattern).
    _exit_requested: ClassVar[bool] = False

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return poll_mesh_with_image(context, _MODAL_NAME)

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        # Re-invoke while live = the panel's "Exit" button: ask the running modal
        # to finish on its next event instead of starting fresh.
        if is_running(_MODAL_NAME):
            type(self)._exit_requested = True
            tag_redraw_view3d_statusbar(context.window_manager)
            return {"CANCELLED"}
        obj = validate_authoring_invoke(self, context, _MODAL_NAME)
        if obj is None:
            return {"CANCELLED"}

        self._session = capture_session(context, obj)
        # Viewport canvas region (not the N-panel button's): lets the modal pass
        # mouse events over the UI through (so the Exit button + panel stay live).
        self._invoke_area: bpy.types.Area | None = context.area
        self._invoke_region: bpy.types.Region | None = (
            find_window_region(context.area) if context.area is not None else None
        )
        self._pen = VertexPen(kind="stroke")
        self._pen.arm()
        # Spec 070 C2: continue a prior drawing - reload its stored source contour
        # (LOCAL XZ -> world) so the artist edits it instead of starting blank.
        local_pts, edge_subdivs = read_manual_contour(obj)
        if local_pts:
            self._pen.load(_local_xz_to_world(obj, local_pts), edge_subdivs)
        # Spec 070 C3: reload committed interior strokes too (re-edit continues them).
        self._user_strokes = read_user_strokes(obj) if local_pts else []
        self._tool = "outer"
        type(self)._current_tool = "outer"
        self._fold_chain = []
        self._fold_subdivs = []
        self._fold_current_subdiv = 0
        self._stroke_capture = None
        self._stroke_start_screen = None
        self._drag_target = None
        self._interior_live = {"active": False, "kind": "stroke", "points": [], "mode": "free"}
        self._delete_hover = []
        self._tri = self._compute_triangulation(context)
        # Cursor tooltip live refs (mutated in place; read by the POST_PIXEL handler).
        self._tooltip_mouse_ref: list[tuple[int, int]] = [(-1, -1)]
        self._tooltip_text_ref: list[str] = [""]
        self._tooltip_color_ref: list[tuple[float, float, float, float]] = [_TOOLTIP_BG_NORMAL]

        # Seed a complete empty handle set BEFORE registering so the except path
        # can _finish() (which tears the overlay down) even if registration itself
        # raised - mirrors the automesh modal's invoke.
        self._handles = empty_overlay_handles()
        try:
            self._handles = self._register_overlay()
            self._append_statusbar()
            mark_running(_MODAL_NAME)
            self._tag_redraw(context)
        except Exception as exc:
            report_error(self, f"Manual Draw setup failed: {exc}")
            self._finish(context, cancel=True)
            return {"CANCELLED"}

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        try:
            early = self._consume_early(context, event)
            if early is not None:
                return early
            if self._tool == "outer":
                handled = self._dispatch_pen(context, event)
                return handled if handled is not None else {"PASS_THROUGH"}
            handled = self._dispatch_interior(context, event)
            return handled if handled is not None else {"PASS_THROUGH"}
        except Exception:
            traceback.print_exc()
            return self._finish(context, cancel=True)

    def _consume_early(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str] | None:
        """Pre-tool guards: the panel Exit handshake, the UI-canvas pass-through
        (keeps the N-panel editable + refreshes the draw cursor), ESC, ENTER, and
        the OUTER / POINT / FOLD Tab cycle. Returns a status when consumed, else
        None."""
        if type(self)._exit_requested:
            type(self)._exit_requested = False
            return self._finish(context, cancel=True)
        # Mouse over the UI (N-panel / the Exit button) -> let it through.
        if event.type in _MOUSE_GATE_TYPES and not event_in_canvas(
            event, self._invoke_region, self._invoke_area
        ):
            return {"PASS_THROUGH"}
        if event.type == "MOUSEMOVE":
            self._tooltip_mouse_ref[0] = (event.mouse_region_x, event.mouse_region_y)
            # Over the canvas (the gate passed UI moves through above): force the
            # draw cursor so the N-panel border's resize cursor does not stick on
            # re-entry - this modal has no timer to refresh it (Quick Armature parity).
            context.window.cursor_set("CROSSHAIR")
        if event.type == "ESC" and event.value == "PRESS":
            return self._handle_escape(context)
        if event.type in {"RET", "NUMPAD_ENTER"} and event.value == "PRESS":
            # A FOLD click-chain in progress finalizes first; otherwise ENTER applies.
            if self._tool == "fold" and len(self._fold_chain) >= 2:
                return self._commit_fold_chain(context)
            return self._apply(context)
        if (
            event.type == "TAB"
            and event.value == "PRESS"
            and not (event.ctrl or event.shift or event.alt)
        ):
            return self._cycle_tool(context)
        return None

    def _handle_escape(self, context: bpy.types.Context) -> set[str]:
        """ESC unwinds the deepest in-progress thing first: a FOLD click-chain, then
        an OPEN outer line, else it exits the modal."""
        if self._fold_chain:
            self._fold_chain = []
            self._fold_subdivs = []
            self._interior_live["active"] = False
            self._refresh_triangulation(context)
            return {"RUNNING_MODAL"}
        if self._pen.points and not self._pen.closed:
            self._pen.arm()
            self._refresh_triangulation(context)
            return {"RUNNING_MODAL"}
        return self._finish(context, cancel=True)

    def _cycle_tool(self, context: bpy.types.Context) -> set[str]:
        """Tab cycles OUTER -> POINT -> FOLD (spec 070 C3), clearing any in-progress
        interior capture / chain / hover. The active tool shows in the status bar
        (not a mouse tooltip - tooltips are warning-only here)."""
        idx = (self._TOOLS.index(self._tool) + 1) % len(self._TOOLS)
        self._tool = self._TOOLS[idx]
        type(self)._current_tool = self._tool
        self._fold_chain = []
        self._fold_subdivs = []
        self._stroke_capture = None
        self._drag_target = None
        self._interior_live["active"] = False
        self._delete_hover.clear()
        self._tooltip_text_ref[0] = ""
        self._tag_redraw(context)
        return {"RUNNING_MODAL"}

    def _dispatch_pen(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str] | None:
        """Feed the event to the pen; commit on close, re-preview on a change.
        Returns a status set when consumed, or None to fall through to nav."""
        action = self._pen.handle(context, event, snap_candidates=[])
        if action is None:
            return None
        if action == "closed":
            # Spec 070 C4: closing the loop enters the EDIT phase (insert verts on
            # edges, per-edge subdiv, drag/remove) instead of applying. ENTER applies.
            self._pen.close()
            self._refresh_triangulation(context)
            return {"RUNNING_MODAL"}
        if action in {"placed", "dragged", "undo", "subdiv"}:
            self._refresh_triangulation(context)
        else:
            self._tag_redraw(context)
        return {"RUNNING_MODAL"}

    def _dispatch_interior(
        self, context: bpy.types.Context, event: bpy.types.Event
    ) -> set[str] | None:
        """INTERIOR tools (spec 070 C3). POINT drops a Steiner on click; FOLD lays a
        fold line by free-draw drag OR by clicking its vertices (RMB-free edge chain;
        ENTER ends it; scroll/0-9 set the next edge's subdivisions). Placement is
        gated INSIDE the contour - a click on the border snaps to the OUTER contour
        regardless of tool, a click outside is denied with a warning. RMB drags any
        vert (interior or contour); Alt+click deletes the stroke under the cursor;
        DEL drops the last. Returns a status when consumed, else None."""
        if event.type == "MOUSEMOVE":
            self._interior_mousemove(context, event)
            return {"RUNNING_MODAL"}
        if event.type == "RIGHTMOUSE":
            return self._interior_rmb(context, event)
        if event.type == "LEFTMOUSE":
            return self._interior_lmb(context, event)
        if event.type in {"WHEELUPMOUSE", "WHEELDOWNMOUSE"} and self._tool == "fold":
            delta = 1 if event.type == "WHEELUPMOUSE" else -1
            self._fold_current_subdiv = max(0, min(20, self._fold_current_subdiv + delta))
            self._interior_live["subdivisions"] = self._fold_current_subdiv
            self._tag_redraw(context)
            return {"RUNNING_MODAL"}
        if event.value == "PRESS" and ((event.type == "Z" and event.ctrl) or event.type == "DEL"):
            return self._interior_undo(context)
        return None

    def _interior_undo(self, context: bpy.types.Context) -> set[str]:
        """Drop the last FOLD click-chain vertex if building one, else the last
        committed interior stroke."""
        if self._tool == "fold" and self._fold_chain:
            self._fold_chain.pop()
            if self._fold_subdivs:
                self._fold_subdivs.pop()
        elif self._user_strokes:
            self._user_strokes.pop()
        self._refresh_triangulation(context)
        return {"RUNNING_MODAL"}

    def _interior_mousemove(self, context: bpy.types.Context, event: bpy.types.Event) -> None:
        """Drag a grabbed vert, extend a held free-draw path, rubber-band the next
        FOLD chain segment, or track the Alt delete-hover - and keep the
        outside-the-contour warning tooltip current."""
        if self._drag_target is not None:
            self._move_dragged_vert(context, event)
            self._tag_redraw(context)
            return
        if self._stroke_capture is not None:  # LMB held: free-draw candidate path
            world = region_event_to_xz(context, event)
            if world is not None:
                self._stroke_capture.append(world)
                self._interior_live.update({"mode": "free", "points": list(self._stroke_capture)})
            self._tag_redraw(context)
            return
        if self._tool == "fold" and self._fold_chain:  # click-chain rubber-band
            self._interior_live.update(
                {
                    "active": True,
                    "kind": "stroke",
                    "mode": "pen",
                    "points": list(self._fold_chain),
                    "edge_subdivs": list(self._fold_subdivs),
                    "subdivisions": self._fold_current_subdiv,
                    "cursor": region_event_to_xz(context, event),
                    "close_loop": False,
                }
            )
            self._update_outside_warn(context, event)
            self._tag_redraw(context)
            return
        idx = self._nearest_stroke(context, event) if event.alt else None
        self._delete_hover[:] = list(self._user_strokes[idx]["points"]) if idx is not None else []
        self._update_outside_warn(context, event)
        self._tag_redraw(context)

    def _update_outside_warn(self, context: bpy.types.Context, event: bpy.types.Event) -> None:
        """Show a red cursor warning when an interior gesture would land outside the
        contour (the one allowed mouse-tooltip use here - a denial). Cleared when
        inside or over the border."""
        world = region_event_to_xz(context, event)
        kind = self._classify_target(context, event, world)[0] if world is not None else "outside"
        if kind == "outside":
            self._tooltip_text_ref[0] = "outside the contour - point/fold must be inside"
            self._tooltip_color_ref[0] = _TOOLTIP_BG_WARN
        else:
            self._tooltip_text_ref[0] = ""

    def _classify_target(
        self, context: bpy.types.Context, event: bpy.types.Event, world: tuple[float, float] | None
    ) -> tuple[str, int]:
        """Where an interior gesture lands: ('outer', edge) on the border (snap to
        the contour), ('inside', -1) within it, or ('outside', -1). Needs a closed
        contour; an open one is always 'outside'."""
        if world is None or not self._pen.closed or len(self._pen.points) < 3:
            return ("outside", -1)
        edge = self._pen.nearest_edge(context, event)
        if edge is not None:
            return ("outer", edge)
        if point_in_polygon(world, list(self._pen.points)):
            return ("inside", -1)
        return ("outside", -1)

    def _interior_rmb(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        """RMB grabs the nearest vert (contour or interior stroke) on press and
        drops it on release - move any vert without leaving the interior tool."""
        if event.value == "PRESS":
            self._drag_target = self._grab_nearest_vert(context, event)
            return {"RUNNING_MODAL"}
        if event.value == "RELEASE" and self._drag_target is not None:
            self._drag_target = None
            self._refresh_triangulation(context)
        return {"RUNNING_MODAL"}

    def _interior_lmb(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        """Alt+press deletes the hovered stroke; a plain press starts a free-draw
        capture; release commits it (POINT / FOLD-drag) or extends the FOLD chain."""
        if event.value == "PRESS":
            if event.alt:
                return self._interior_delete_under_cursor(context, event)
            self._stroke_start_screen = (event.mouse_region_x, event.mouse_region_y)
            world = region_event_to_xz(context, event)
            self._stroke_capture = [world] if world is not None else []
            self._interior_live.update(
                {
                    "active": True,
                    "kind": "stroke",
                    "mode": "free",
                    "points": list(self._stroke_capture),
                }
            )
            self._tag_redraw(context)
            return {"RUNNING_MODAL"}
        if event.value == "RELEASE":
            return self._interior_release(context, event)
        return {"RUNNING_MODAL"}

    def _interior_release(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        """Commit on LMB release, gated by where it lands: a border tap snaps to the
        OUTER contour (any tool); an outside tap is denied; an inside moved capture
        is a free-draw fold, an inside tap is a POINT or one more FOLD chain vert."""
        path = self._stroke_capture or []
        start = self._stroke_start_screen
        self._stroke_capture = None
        self._stroke_start_screen = None
        self._interior_live["active"] = False
        if not path:
            return {"RUNNING_MODAL"}
        world = path[-1]
        kind, edge = self._classify_target(context, event, world)
        if kind == "outer":  # border: add to the OUTER contour regardless of tool
            self._pen.insert_on_edge(edge, world)
            self._refresh_triangulation(context)
            return {"RUNNING_MODAL"}
        if kind == "outside":  # denied (the warn tooltip already says why)
            self._tag_redraw(context)
            return {"RUNNING_MODAL"}
        moved = (
            start is not None
            and ((event.mouse_region_x - start[0]) ** 2 + (event.mouse_region_y - start[1]) ** 2)
            > self._DRAG_THRESHOLD_PX**2
        )
        if moved and len(path) >= 2:  # free-draw drag (either tool): a fold line
            # The whole path must stay inside the contour, not just the release
            # point - a stroke that leaves and re-enters would feed out-of-contour
            # constraints into the CDT. Drop it with the warning if any vert is out.
            contour = list(self._pen.points)
            if any(not point_in_polygon(p, contour) for p in path):
                self._tooltip_text_ref[0] = "fold left the contour - keep it inside"
                self._tooltip_color_ref[0] = _TOOLTIP_BG_WARN
                self._tag_redraw(context)
                return {"RUNNING_MODAL"}
            self._user_strokes.append(
                {"kind": "stroke", "points": _downsample(path, self._INTERIOR_MAX_PATH)}
            )
            self._refresh_triangulation(context)
            return {"RUNNING_MODAL"}
        if self._tool == "point":  # a tap with the point tool: single Steiner
            self._user_strokes.append({"kind": "point", "points": [world]})
            self._refresh_triangulation(context)
            return {"RUNNING_MODAL"}
        # FOLD tap inside: extend the click-built edge chain, baking the scroll-set
        # subdivision count into the new edge.
        self._fold_chain.append(world)
        if len(self._fold_chain) >= 2:
            self._fold_subdivs.append(self._fold_current_subdiv)
        # Re-triangulate so the preview reflects the fold as it is built (the
        # in-progress chain rides into _output as a provisional stroke).
        self._refresh_triangulation(context)
        return {"RUNNING_MODAL"}

    def _commit_fold_chain(self, context: bpy.types.Context) -> set[str]:
        """Finalize the FOLD click-chain into a committed fold stroke (>= 2 verts),
        subdividing each edge by its baked count."""
        if len(self._fold_chain) >= 2:
            points = subdivide_polyline_edges(self._fold_chain, self._fold_subdivs)
            self._user_strokes.append({"kind": "stroke", "points": points})
        self._fold_chain = []
        self._fold_subdivs = []
        self._interior_live["active"] = False
        self._refresh_triangulation(context)
        return {"RUNNING_MODAL"}

    def _grab_nearest_vert(
        self, context: bpy.types.Context, event: bpy.types.Event
    ) -> tuple[str, int] | tuple[str, int, int] | None:
        """Nearest vert within the pick radius across the OUTER contour and every
        interior stroke; ('outer', i) / ('stroke', si, pi) / None."""
        world = region_event_to_xz(context, event)
        if world is None:
            return None
        near = region_event_to_xz_offset(context, event, dx=self._STROKE_PICK_RADIUS_PX)
        best_d2 = (
            (near[0] - world[0]) ** 2 + (near[1] - world[1]) ** 2
            if near is not None
            else float("inf")
        )
        target: tuple[str, int] | tuple[str, int, int] | None = None
        for i, (px, pz) in enumerate(self._pen.points):
            d2 = (px - world[0]) ** 2 + (pz - world[1]) ** 2
            if d2 <= best_d2:
                best_d2 = d2
                target = ("outer", i)
        for si, stroke in enumerate(self._user_strokes):
            for pi, (px, pz) in enumerate(stroke["points"]):
                d2 = (px - world[0]) ** 2 + (pz - world[1]) ** 2
                if d2 <= best_d2:
                    best_d2 = d2
                    target = ("stroke", si, pi)
        return target

    def _move_dragged_vert(self, context: bpy.types.Context, event: bpy.types.Event) -> None:
        """Reposition the RMB-grabbed vert to the cursor (contour or interior)."""
        world = region_event_to_xz(context, event)
        if world is None or self._drag_target is None:
            return
        target = self._drag_target
        if target[0] == "outer":
            i = target[1]
            if 0 <= i < len(self._pen.points):
                self._pen.points[i] = world
                self._pen.live_preview["points"] = list(self._pen.points)
            return
        _, si, pi = target
        # An interior vert must stay inside the contour; ignore a drag that would
        # push it out (the contour verts themselves, the "outer" branch, move free).
        if not point_in_polygon(world, list(self._pen.points)):
            return
        if 0 <= si < len(self._user_strokes):
            pts = self._user_strokes[si]["points"]
            if 0 <= pi < len(pts):
                pts[pi] = world

    def _interior_delete_under_cursor(
        self, context: bpy.types.Context, event: bpy.types.Event
    ) -> set[str]:
        """Remove the interior stroke under the cursor (Alt+click revisit)."""
        idx = self._nearest_stroke(context, event)
        if idx is not None:
            self._user_strokes.pop(idx)
            self._delete_hover.clear()
            self._refresh_triangulation(context)
        return {"RUNNING_MODAL"}

    def _nearest_stroke(self, context: bpy.types.Context, event: bpy.types.Event) -> int | None:
        """Index of the committed interior stroke nearest the cursor within the
        pick radius (any of its verts), or None when the cursor is off them all."""
        world = region_event_to_xz(context, event)
        if world is None:
            return None
        near = region_event_to_xz_offset(context, event, dx=self._STROKE_PICK_RADIUS_PX)
        best_d2 = (
            (near[0] - world[0]) ** 2 + (near[1] - world[1]) ** 2
            if near is not None
            else float("inf")
        )
        best: int | None = None
        for i, stroke in enumerate(self._user_strokes):
            for px, pz in stroke["points"]:
                d2 = (px - world[0]) ** 2 + (pz - world[1]) ** 2
                if d2 <= best_d2:
                    best_d2 = d2
                    best = i
        return best

    def _apply(self, context: bpy.types.Context) -> set[str]:
        ring = self._pen.ring()
        if ring is None:
            report_warn(self, "place at least 3 vertices first", always=True)
            return {"RUNNING_MODAL"}
        obj = context.active_object
        image = first_material_image(obj)
        if obj is None or image is None:
            return self._finish(context, cancel=True)
        output = self._output(ring)
        picker = active_armature(context)
        try:
            counters = apply_mesh(obj, image, output, self._params(context), picker)
        except ValueError as exc:
            report_error(self, f"CDT failed: {exc}")
            return {"RUNNING_MODAL"}
        # Spec 070 C2: persist the SOURCE contour (LOCAL XZ + per-edge subdiv) + the
        # interior strokes so a later re-invoke reloads + continues this drawing
        # (the triangulated mesh is too lossy to reverse).
        write_manual_contour(
            obj, _world_xz_to_local(obj, list(self._pen.points)), list(self._pen.edge_subdivs)
        )
        write_user_strokes(obj, self._user_strokes)
        report_info(
            self,
            f"Manual Draw applied: {counters.get('total_verts', 0)} verts, "
            f"{counters.get('total_faces', 0)} faces",
        )
        return self._finish(context, cancel=False)

    def _refresh_triangulation(self, context: bpy.types.Context) -> None:
        """Recompute the live SIMPLE triangulation from the in-progress contour
        (one CDT per call) and re-register the overlay so it draws."""
        self._tri = self._compute_triangulation(context)
        unregister_overlay(self._handles)
        self._handles = self._register_overlay()
        self._tag_redraw(context)

    def _compute_triangulation(
        self, context: bpy.types.Context
    ) -> list[tuple[tuple[float, float], tuple[float, float]]]:
        ring = self._pen.ring()
        if ring is None:
            return []
        obj = context.active_object
        image = first_material_image(obj)
        if obj is None or image is None:
            return []
        try:
            return compute_mesh_preview_edges(obj, image, self._output(ring), self._params(context))
        except Exception:
            return []

    def _output(self, ring: list[tuple[float, float]]) -> StageOutput:
        """The StageOutput shared by APPLY + the live preview: the manual outer
        contour plus the committed interior point/fold strokes, and the in-progress
        FOLD click-chain as a provisional stroke so the triangulation preview
        updates as the fold is built (spec 070 C3)."""
        strokes = list(self._user_strokes)
        if len(self._fold_chain) >= 2:
            chain = subdivide_polyline_edges(self._fold_chain, self._fold_subdivs)
            strokes.append({"kind": "stroke", "points": chain})
        return StageOutput(outer=ring, outer_is_manual=True, user_strokes=strokes)

    def _params(self, context: bpy.types.Context) -> StageParams:
        """Scene params with the interior mode taken from the Manual Mesh panel's
        own ``manual_interior_mode`` toggle (spec 070 C1) - independent of the
        automesh trace fields."""
        mode = context.scene.proscenio.skinning.manual_interior_mode
        return cast("StageParams", replace(_snapshot_params(context), interior_mode=mode))

    def _register_overlay(self) -> OverlayHandles:
        return register_manual_draw_overlay(
            triangulation=self._tri,
            live_preview_ref=self._pen.live_preview,
            tooltip_mouse_ref=self._tooltip_mouse_ref,
            tooltip_text_ref=self._tooltip_text_ref,
            tooltip_color_ref=self._tooltip_color_ref,
            user_strokes=self._user_strokes,
            interior_live_ref=self._interior_live,
            delete_hover_ref=self._delete_hover,
        )

    def cancel(self, context: bpy.types.Context) -> None:
        # Blender calls cancel() when the modal is killed externally (window close,
        # file load). Without this the modal guard stays stuck and both authoring
        # polls fail until reload. Mirror the user exit path.
        self._finish(context, cancel=True)

    def _finish(self, context: bpy.types.Context, *, cancel: bool) -> set[str]:
        # Clear the exclusivity guard FIRST: a teardown step raising below must
        # never leave the modal marked running - that would lock out both
        # authoring modes until an addon reload. The bpy teardown call is
        # suppressed so a stale handle never aborts the rest of the teardown
        # (mirrors edit_weights._finish).
        mark_stopped(_MODAL_NAME)
        try:
            if context.window is not None:  # None on the window-close cancel path
                context.window.cursor_set("DEFAULT")  # drop the CROSSHAIR over the canvas
            with contextlib.suppress(RuntimeError):
                unregister_overlay(self._handles)
            self._remove_statusbar()
            if self._session is not None and cancel:
                restore_session(context, self._session)
        finally:
            self._tag_redraw(context)
        return {"CANCELLED" if cancel else "FINISHED"}

    def _append_statusbar(self) -> None:
        append_statusbar_draw(type(self), _draw_statusbar_manual_draw)

    def _remove_statusbar(self) -> None:
        remove_statusbar_draw(type(self), _draw_statusbar_manual_draw)

    def _tag_redraw(self, context: bpy.types.Context) -> None:
        tag_redraw_view3d_statusbar(context.window_manager)


_TOOL_LABELS = {"outer": "Outer contour", "point": "Interior point", "fold": "Interior fold"}


def emit_manual_draw_chords(layout: bpy.types.UILayout, active_tool: str = "outer") -> None:
    """Manual Mesh gesture cheatsheet - shared by the STATUSBAR draw + the panel's
    collapsible mirror (Quick Armature pattern). The active tool is surfaced here
    (status bar / panel), NOT in a mouse tooltip. Chords are per-tool so only the
    gestures that apply to the current Tab tool show."""
    chord(layout, ("GREASEPENCIL", f"Manual Mesh - {_TOOL_LABELS.get(active_tool, '')}"))
    chord(layout, ("EVENT_TAB", "tool: outer / point / fold"))
    if active_tool == "outer":
        chord(layout, ("MOUSE_LMB", "place vert / click 1st = edit"))
        chord(layout, ("MOUSE_RMB", "drag vert"))
        chord(layout, ("EVENT_X", "/"), ("EVENT_Z", "axis lock"))
        chord(layout, ("MOUSE_MMB", "/ 0-9 = subdiv edge"))
        chord(layout, ("MOUSE_LMB", "on edge = insert vert (edit)"))
        chord(layout, ("EVENT_CTRL", "+"), ("EVENT_Z", "/ Del = remove vert"))
    elif active_tool == "point":
        chord(layout, ("MOUSE_LMB", "drop interior point (inside only)"))
        chord(layout, ("MOUSE_RMB", "drag any vert"))
        chord(layout, ("EVENT_ALT", "+"), ("MOUSE_LMB", "= delete stroke"))
    else:  # fold
        chord(layout, ("MOUSE_LMB", "drag = free fold / click = edge chain"))
        chord(layout, ("MOUSE_MMB", "/ 0-9 = subdiv next edge"))
        chord(layout, ("EVENT_RETURN", "finish chain"))
        chord(layout, ("MOUSE_RMB", "drag any vert"))
        chord(layout, ("EVENT_ALT", "+"), ("MOUSE_LMB", "= delete stroke"))
    chord(layout, ("EVENT_RETURN", "apply"))
    chord(layout, ("EVENT_ESC", "cancel"))


def _draw_statusbar_manual_draw(self: bpy.types.Header, _context: bpy.types.Context) -> None:
    emit_manual_draw_chords(self.layout, PROSCENIO_OT_draw_mesh_vertices._current_tool)
    self.layout.separator_spacer()


_classes: tuple[type, ...] = (PROSCENIO_OT_draw_mesh_vertices,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
