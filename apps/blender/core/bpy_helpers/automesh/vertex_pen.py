"""Reusable closed-loop vertex pen for manual contour authoring.

Host-agnostic: owns the in-progress polyline plus the click / RMB-drag / snap /
axis-lock / subdivide / undo state and the live-preview overlay dict, but knows
nothing about automesh stages or where the finished ring is committed. Both the
standalone Manual Draw operator and the Automesh island tools (ADD / REMOVE)
drive it from their ``modal()`` and read ``.points`` / call ``.ring()`` on
finish - so the click-pen lives in exactly one place.

bpy-coupled (viewport projection) but imports nothing automesh-specific.

``handle`` returns a small action string for the events the pen owns (so the
host can re-preview / commit) or ``None`` for events it does not (ENTER / ESC /
TAB / nav), which the host then handles itself.
"""

from __future__ import annotations

from typing import Literal

import bpy

from ..._shared.geometry_2d import Point2D
from ..._shared.nearest import nearest_index
from ...automesh.stroke_geometry import contour_ring_from_pen_edges
from .._shared.viewport_math import region_event_to_xz, region_event_to_xz_offset

# Action returned by ``handle`` for a consumed event. ``closed`` means the artist
# clicked the first vert to close the loop (host should commit); the rest signal
# a change the host may want to re-preview on. ``noop`` = consumed, nothing to do.
PenAction = Literal["placed", "closed", "dragged", "undo", "subdiv", "axis", "noop"]

# Top-row + numpad digit event types -> subdivision count.
_DIGIT_KEYS = {
    "ZERO": 0, "ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4,
    "FIVE": 5, "SIX": 6, "SEVEN": 7, "EIGHT": 8, "NINE": 9,
    "NUMPAD_0": 0, "NUMPAD_1": 1, "NUMPAD_2": 2, "NUMPAD_3": 3, "NUMPAD_4": 4,
    "NUMPAD_5": 5, "NUMPAD_6": 6, "NUMPAD_7": 7, "NUMPAD_8": 8, "NUMPAD_9": 9,
}  # fmt: skip


def _point_segment_dist2(p: Point2D, a: Point2D, b: Point2D) -> float:
    """Squared distance from point ``p`` to segment ``a -> b`` (world XZ)."""
    ax, az = a
    bx, bz = b
    px, pz = p
    dx = bx - ax
    dz = bz - az
    len2 = dx * dx + dz * dz
    if len2 < 1e-18:  # degenerate (coincident endpoints): distance to the point
        return (px - ax) ** 2 + (pz - az) ** 2
    t = ((px - ax) * dx + (pz - az) * dz) / len2
    t = max(0.0, min(1.0, t))
    cx = ax + t * dx
    cz = az + t * dz
    return (px - cx) ** 2 + (pz - cz) ** 2


class VertexPen:
    """Closed-loop click pen: LMB places a vert (drag places at the drag end),
    clicking the first vert closes the loop, RMB drags a placed vert, DEL /
    Ctrl+Z drops the last, X/Z axis-lock the next placement, wheel / digit set
    the per-edge subdivision baked on finish.
    """

    DRAG_THRESHOLD_PX = 5
    PICK_RADIUS_PX = 12
    SUBDIV_MAX = 20

    def __init__(
        self, *, kind: str = "stroke", live_preview: dict[str, object] | None = None
    ) -> None:
        self.kind = kind
        self.points: list[Point2D] = []
        # subdivisions = the CURRENT count (next edge / rubber-band); edge_subdivs
        # = the count baked into each already-placed edge, so scroll only changes
        # the next segment, not the whole line (spec 070 per-edge).
        self.subdivisions: int = 0
        self.edge_subdivs: list[int] = []
        self.axis_lock: str = ""  # "", "x" (keep world-Z), "z" (keep world-X)
        # Spec 070 C4: once the loop closes the pen enters the EDIT phase - the
        # contour is a closed editable ring (insert verts on edges, per-edge
        # subdiv of placed edges, drag/remove verts), and a placement no longer
        # extends an open line. `_hover_edge` is the closed edge under the cursor.
        self.closed = False
        self._hover_edge: int | None = None
        self._active = False  # >= 1 vert placed in the current line
        self._stroke_active = False
        self._start_screen: tuple[int, int] | None = None
        self._drag_index: int | None = None
        # Mutated in place; the overlay's _draw_live_preview holds this by ref. A
        # host can pass its own dict (e.g. the automesh modal's shared
        # _live_preview) so the existing overlay shows the pen without a second
        # handler; otherwise the pen owns a fresh one (Manual Draw).
        self.live_preview: dict[str, object] = live_preview if live_preview is not None else {}
        self.live_preview.update(
            {
                "active": False,
                "kind": kind,
                "points": [],
                "cursor": None,
                "mode": "pen",
                "axis": "",
                "subdivisions": 0,  # current count, for the rubber-band ghost
                "edge_subdivs": [],  # per placed-edge count, for the placed ghosts
                "close_loop": True,  # closed-loop pen: draw the cursor -> first ghost
                "closed": False,  # EDIT phase: draw the wrap edge + drop the rubber-band
            }
        )

    # -- lifecycle ---------------------------------------------------------

    def arm(self) -> None:
        """Begin a fresh line (clears any in-progress verts, lights the preview)."""
        self.points.clear()
        self.edge_subdivs.clear()
        self.subdivisions = 0
        self.axis_lock = ""
        self.closed = False
        self._hover_edge = None
        self._active = False
        self._stroke_active = False
        self._start_screen = None
        self._drag_index = None
        self.live_preview["active"] = True
        self.live_preview["mode"] = "pen"
        self.live_preview["points"] = self.points
        self.live_preview["edge_subdivs"] = self.edge_subdivs
        self.live_preview["cursor"] = None
        self.live_preview["axis"] = ""
        self.live_preview["subdivisions"] = 0
        self.live_preview["close_loop"] = True
        self.live_preview["closed"] = False

    def reset(self) -> None:
        """Clear all state and hide the preview."""
        self.arm()
        self.live_preview["active"] = False
        self.live_preview["cursor"] = None

    def load(self, points: list[Point2D], edge_subdivs: list[int]) -> None:
        """Preload an existing contour for re-editing (spec 070 C2).

        Sets the placed verts (WORLD XZ) + their baked per-edge subdivisions and
        lights the preview, as if the artist had just drawn them - so a re-invoke
        on a manually-meshed element continues the drawing instead of starting
        blank. Caller converts the stored LOCAL points to world first.
        """
        self.arm()
        self.points.extend(points)
        self.edge_subdivs.extend(edge_subdivs)
        self._active = bool(points)
        # A reloaded contour is already complete - open it straight into the EDIT
        # phase (spec 070 C4) so the artist edits it rather than re-closing it.
        if len(self.points) >= 3:
            self.close()
        else:
            self.live_preview["points"] = list(self.points)
            self.live_preview["edge_subdivs"] = list(self.edge_subdivs)

    @property
    def dragging(self) -> bool:
        return self._drag_index is not None

    def ring(self) -> list[Point2D] | None:
        """The finished contour ring (closing-dup dropped, each edge subdivided
        by its own baked count), or None when fewer than 3 distinct verts."""
        return contour_ring_from_pen_edges(list(self.points), self.edge_subdivs)

    # -- event entry -------------------------------------------------------

    def handle(
        self, context: bpy.types.Context, event: bpy.types.Event, snap_candidates: list[Point2D]
    ) -> PenAction | None:
        """Dispatch one modal event. Returns a ``PenAction`` when the pen
        consumed it, or ``None`` when the event is not the pen's (the host
        handles ENTER / ESC / TAB / nav)."""
        if self.closed:
            return self._handle_closed(context, event)
        if event.type == "MOUSEMOVE":
            self._on_mousemove(context, event)
            return "noop"
        if event.type == "RIGHTMOUSE":
            if event.value == "PRESS":
                self._on_rmb_press(context, event)
                return "noop"
            if event.value == "RELEASE":
                return self._on_rmb_release()
            return None
        if event.type == "LEFTMOUSE":
            if event.value == "PRESS":
                self._on_lmb_press(event)
                return "noop"
            if event.value == "RELEASE" and self._stroke_active:
                return self._on_lmb_release(context, event, snap_candidates)
            return None
        return self._on_key(event)

    # -- EDIT phase (closed loop) ------------------------------------------

    def close(self) -> None:
        """Enter the EDIT phase: the open contour becomes a closed editable loop
        (spec 070 C4). Drops a trailing close-on-first-vert duplicate, pads the
        per-edge subdivision list to one-per-edge (incl the wrap), and switches
        the preview to draw the closed ring without the rubber-band."""
        if len(self.points) >= 2 and self.points[0] == self.points[-1]:
            self.points.pop()
            if self.edge_subdivs:
                self.edge_subdivs.pop()
        self.closed = True
        self._hover_edge = None
        self._stroke_active = False
        self._pad_edge_subdivs()
        self.live_preview["mode"] = "edit"
        self.live_preview["closed"] = True
        self._sync_preview_points()

    def _handle_closed(
        self, context: bpy.types.Context, event: bpy.types.Event
    ) -> PenAction | None:
        """EDIT-phase dispatch: RMB drags a vert, LMB on an edge inserts a vert,
        wheel / digit set the hovered edge's subdivision, DEL removes the vert
        under the cursor. ENTER / ESC stay the host's (returns None)."""
        if event.type == "MOUSEMOVE":
            self._on_mousemove(context, event)
            if self._drag_index is None:
                self._hover_edge = self.nearest_edge(context, event)
            return "noop"
        if event.type == "RIGHTMOUSE":
            if event.value == "PRESS":
                self._on_rmb_press(context, event)
                return "noop"
            if event.value == "RELEASE":
                return self._on_rmb_release()
            return None
        if event.type == "LEFTMOUSE":
            if event.value == "PRESS":
                self._stroke_active = True
                return "noop"
            if event.value == "RELEASE" and self._stroke_active:
                self._stroke_active = False
                return self._insert_on_hovered_edge(context, event)
            return None
        return self._on_key_closed(context, event)

    def _insert_on_hovered_edge(
        self, context: bpy.types.Context, event: bpy.types.Event
    ) -> PenAction:
        """LMB on a placed edge (away from any vert) inserts a vert at the click,
        splitting that edge; a click on a vert or away from the ring is a no-op."""
        world = region_event_to_xz(context, event)
        if world is None:
            return "noop"
        if self._nearest_vert(context, event) is not None:
            return "noop"  # a vert is the drag target, not an insert
        edge = self.nearest_edge(context, event)
        if edge is None:
            return "noop"
        self.insert_on_edge(edge, world)
        return "placed"

    def _on_key_closed(
        self, context: bpy.types.Context, event: bpy.types.Event
    ) -> PenAction | None:
        if event.type in {"WHEELUPMOUSE", "WHEELDOWNMOUSE"}:
            if self._hover_edge is None:
                return "noop"
            self.bump_edge_subdiv(self._hover_edge, 1 if event.type == "WHEELUPMOUSE" else -1)
            return "subdiv"
        if event.value != "PRESS":
            return None
        if (event.type == "Z" and event.ctrl) or event.type == "DEL":
            return self._remove_nearest_vert(context, event)
        if event.type in _DIGIT_KEYS and self._hover_edge is not None:
            self.set_edge_subdiv(self._hover_edge, _DIGIT_KEYS[event.type])
            return "subdiv"
        return None

    def _remove_nearest_vert(self, context: bpy.types.Context, event: bpy.types.Event) -> PenAction:
        """Drop the vert under the cursor (kept >= 3 so the ring stays valid)."""
        if len(self.points) <= 3:
            return "noop"
        idx = self._nearest_vert(context, event)
        if idx is None:
            return "noop"
        self.points.pop(idx)
        if idx < len(self.edge_subdivs):
            self.edge_subdivs.pop(idx)
        self._hover_edge = None
        self._sync_preview_points()
        return "undo"

    # -- EDIT-phase geometry (pure) ----------------------------------------

    def _pad_edge_subdivs(self) -> None:
        """Grow ``edge_subdivs`` to one-per-vertex (one per closed edge, incl the
        wrap edge ``last -> first``), so EDIT-phase index math is total."""
        while len(self.edge_subdivs) < len(self.points):
            self.edge_subdivs.append(0)

    def _sync_preview_points(self) -> None:
        self.live_preview["points"] = list(self.points)
        self.live_preview["edge_subdivs"] = list(self.edge_subdivs)

    def insert_on_edge(self, edge_index: int, point: Point2D) -> None:
        """Insert ``point`` splitting closed edge ``edge_index`` (vertex i ->
        (i+1) % n); both halves inherit the edge's subdivision count (spec 070
        C4). Out-of-range index is a no-op."""
        self._pad_edge_subdivs()
        n = len(self.points)
        if not 0 <= edge_index < n:
            return
        count = self.edge_subdivs[edge_index] if edge_index < len(self.edge_subdivs) else 0
        insert_at = (edge_index + 1) % n
        if insert_at == 0:  # wrap edge: the new vert lands at the end of the ring
            self.points.append(point)
            self.edge_subdivs.append(count)
        else:
            self.points.insert(insert_at, point)
            self.edge_subdivs.insert(insert_at, count)
        self._sync_preview_points()

    def set_edge_subdiv(self, edge_index: int, n: int) -> None:
        """Set closed edge ``edge_index``'s subdivision count (clamped)."""
        self._pad_edge_subdivs()
        if 0 <= edge_index < len(self.edge_subdivs):
            self.edge_subdivs[edge_index] = max(0, min(self.SUBDIV_MAX, n))
            self.live_preview["edge_subdivs"] = list(self.edge_subdivs)

    def bump_edge_subdiv(self, edge_index: int, delta: int) -> None:
        """Nudge closed edge ``edge_index``'s subdivision count by ``delta``."""
        self._pad_edge_subdivs()
        if 0 <= edge_index < len(self.edge_subdivs):
            self.set_edge_subdiv(edge_index, self.edge_subdivs[edge_index] + delta)

    def nearest_edge(self, context: bpy.types.Context, event: bpy.types.Event) -> int | None:
        """Closed-loop edge nearest the cursor within the pick radius; ``None``
        when the cursor is off every edge (or the ring is too small)."""
        if len(self.points) < 3:
            return None
        mouse = region_event_to_xz(context, event)
        if mouse is None:
            return None
        near = region_event_to_xz_offset(context, event, dx=self.PICK_RADIUS_PX)
        best_d2 = (
            (near[0] - mouse[0]) ** 2 + (near[1] - mouse[1]) ** 2
            if near is not None
            else float("inf")
        )
        best_i: int | None = None
        n = len(self.points)
        for i in range(n):
            d2 = _point_segment_dist2(mouse, self.points[i], self.points[(i + 1) % n])
            if d2 <= best_d2:
                best_d2 = d2
                best_i = i
        return best_i

    # -- mouse -------------------------------------------------------------

    def _on_mousemove(self, context: bpy.types.Context, event: bpy.types.Event) -> None:
        cursor = region_event_to_xz(context, event)
        if self._drag_index is not None:
            idx = self._drag_index
            if cursor is not None and 0 <= idx < len(self.points):
                self.points[idx] = cursor  # no axis lock mid-drag
                self.live_preview["points"] = list(self.points)
                self.live_preview["cursor"] = None
            return
        self.live_preview["cursor"] = (
            self._apply_axis_lock(cursor) if (cursor and self._active) else cursor
        )

    def _on_lmb_press(self, event: bpy.types.Event) -> None:
        self._start_screen = (event.mouse_region_x, event.mouse_region_y)
        self._stroke_active = True

    def _on_lmb_release(
        self, context: bpy.types.Context, event: bpy.types.Event, snap_candidates: list[Point2D]
    ) -> PenAction:
        self._stroke_active = False
        start = self._start_screen
        self._start_screen = None
        world = region_event_to_xz(context, event)
        if start is None or world is None:
            return "noop"
        pt, close = self._snap(context, event, world, snap_candidates)
        self._active = True
        self.points.append(pt)
        if len(self.points) >= 2:
            # The just-created edge (prev vert -> this one) bakes the current
            # subdivision count; later scrolls only change the next edge.
            self.edge_subdivs.append(self.subdivisions)
        self.live_preview["points"] = list(self.points)
        self.live_preview["edge_subdivs"] = list(self.edge_subdivs)
        self.live_preview["cursor"] = None
        return "closed" if close else "placed"

    def _on_rmb_press(self, context: bpy.types.Context, event: bpy.types.Event) -> None:
        """Grab the nearest placed vert within the pick radius (miss = no-op).
        RMB never finishes the pen here - the host's ENTER does."""
        self._drag_index = self._nearest_vert(context, event)

    def _on_rmb_release(self) -> PenAction:
        if self._drag_index is None:
            return "noop"
        self._drag_index = None
        return "dragged"

    # -- keys --------------------------------------------------------------

    def _on_key(self, event: bpy.types.Event) -> PenAction | None:
        if event.type in {"WHEELUPMOUSE", "WHEELDOWNMOUSE"}:
            delta = 1 if event.type == "WHEELUPMOUSE" else -1
            self._set_subdivisions(self.subdivisions + delta)
            return "subdiv"
        if event.value != "PRESS":
            return None
        if (event.type == "Z" and event.ctrl) or event.type == "DEL":
            return self._undo_last()
        if event.type in {"X", "Z"} and not event.ctrl:
            self._toggle_axis_lock("x" if event.type == "X" else "z")
            return "axis"
        if event.type in _DIGIT_KEYS:
            self._set_subdivisions(_DIGIT_KEYS[event.type])
            return "subdiv"
        return None

    def _undo_last(self) -> PenAction:
        if self.points:
            self.points.pop()
            if self.edge_subdivs:
                self.edge_subdivs.pop()  # drop the removed edge's baked count
            self._active = bool(self.points)
            self.live_preview["points"] = list(self.points)
            self.live_preview["edge_subdivs"] = list(self.edge_subdivs)
            self.live_preview["active"] = True  # tool stays armed even when empty
        return "undo"

    def _set_subdivisions(self, n: int) -> None:
        self.subdivisions = max(0, min(self.SUBDIV_MAX, n))
        self.live_preview["subdivisions"] = self.subdivisions

    def _toggle_axis_lock(self, axis: str) -> None:
        self.axis_lock = "" if self.axis_lock == axis else axis
        self.live_preview["axis"] = self.axis_lock

    # -- geometry ----------------------------------------------------------

    def _apply_axis_lock(self, world_pt: Point2D) -> Point2D:
        if not self.axis_lock or not self.points:
            return world_pt
        last_x, last_z = self.points[-1]
        if self.axis_lock == "x":  # horizontal: keep the last vert's world-Z
            return (world_pt[0], last_z)
        return (last_x, world_pt[1])  # vertical: keep the last vert's world-X

    def _snap(
        self,
        context: bpy.types.Context,
        event: bpy.types.Event,
        world_pt: Point2D,
        snap_candidates: list[Point2D],
    ) -> tuple[Point2D, bool]:
        """Resolve a click: close the loop on the first vert, union onto a
        snap candidate, else axis-lock the raw point. Returns (point, close)."""
        mouse = region_event_to_xz(context, event)
        near = region_event_to_xz_offset(context, event, dx=self.PICK_RADIUS_PX)
        if mouse is None or near is None:
            return self._apply_axis_lock(world_pt), False
        pick_d2 = (near[0] - mouse[0]) ** 2 + (near[1] - mouse[1]) ** 2
        if len(self.points) >= 2:
            fx, fz = self.points[0]
            if (fx - mouse[0]) ** 2 + (fz - mouse[1]) ** 2 <= pick_d2:
                return (fx, fz), True
        best: Point2D | None = None
        best_d2 = pick_d2
        for cx, cz in snap_candidates:
            d2 = (cx - mouse[0]) ** 2 + (cz - mouse[1]) ** 2
            if d2 <= best_d2:
                best_d2 = d2
                best = (cx, cz)
        if best is not None:
            return best, False
        return self._apply_axis_lock(world_pt), False

    def _nearest_vert(self, context: bpy.types.Context, event: bpy.types.Event) -> int | None:
        if not self.points:
            return None
        mouse = region_event_to_xz(context, event)
        if mouse is None:
            return None
        near = region_event_to_xz_offset(context, event, dx=self.PICK_RADIUS_PX)
        radius = (
            ((near[0] - mouse[0]) ** 2 + (near[1] - mouse[1]) ** 2) ** 0.5
            if near is not None
            else None
        )
        idx = nearest_index(mouse, self.points, radius)
        return idx if idx >= 0 else None
