"""Open-stroke click pen for the automesh authoring modal.

Sibling of :class:`vertex_pen.VertexPen`, but for an OPEN polyline (a fold / cut
/ knife stroke or a manual contour in progress) rather than a closed loop. Owns
the in-progress line - points, per-edge subdivisions, the current subdivision
count, and the axis lock - plus the small live-preview mirror, with a single
click-resolution helper. Pure Python (no bpy): the operator does the viewport
projection and passes world-space points + a pre-computed pick radius, so every
transition here is unit-testable without a viewport - which is the whole point
(the old inline state machine could only be exercised interactively).

The operator still owns event dispatch, free-draw capture, and where a finished
stroke is committed (stage-specific); this class owns the line itself.
"""

from __future__ import annotations

from ..._shared.geometry_2d import Point2D
from ...automesh.stroke_geometry import apply_pen_axis_lock, subdivide_polyline_edges

_SUBDIV_MAX = 20  # wheel can exceed the single-digit set; cap to keep the CDT sane


class OpenStrokePen:
    """The in-progress open polyline for a fold / cut / contour pen line."""

    SUBDIV_MAX = _SUBDIV_MAX

    def __init__(
        self, *, kind: str = "stroke", live_preview: dict[str, object] | None = None
    ) -> None:
        self.kind = kind
        self.points: list[Point2D] = []
        # subdivisions = the CURRENT count baked onto the next placed edge;
        # edge_subdivs = the count already baked into each placed edge (spec 070
        # per-edge: a wheel/digit change only affects the next segment).
        self.subdivisions: int = 0
        self.edge_subdivs: list[int] = []
        self.axis_lock: str = ""  # "", "x" (keep world-Z), "z" (keep world-X)
        # >= 1 vert placed: once active, a drag adds a vert instead of free-drawing.
        self.active: bool = False
        # Mutated in place; the overlay's _draw_live_preview holds this by ref, so
        # a host can pass its shared dict (the automesh modal's _live_preview).
        self.live_preview: dict[str, object] = live_preview if live_preview is not None else {}

    # -- lifecycle ---------------------------------------------------------

    def arm(self, kind: str) -> None:
        """Begin a fresh open line of ``kind`` and light the preview."""
        self.kind = kind
        self.points.clear()
        self.edge_subdivs.clear()
        self.subdivisions = 0
        self.axis_lock = ""
        self.active = False
        self.live_preview.update(
            {
                "active": True,
                "mode": "pen",
                "kind": kind,
                "points": self.points,
                "edge_subdivs": self.edge_subdivs,
                "cursor": None,
                "axis": "",
                "subdivisions": 0,
                "close_loop": False,  # open-stroke pen: no closing ghost
            }
        )

    def clear(self) -> None:
        """Drop the in-progress line and hide the preview."""
        self.points.clear()
        self.edge_subdivs.clear()
        self.subdivisions = 0
        self.axis_lock = ""
        self.active = False
        self.live_preview["active"] = False
        self.live_preview["cursor"] = None

    # -- placement ---------------------------------------------------------

    def apply_axis_lock(self, world_pt: Point2D) -> Point2D:
        """Snap ``world_pt`` to share the locked axis with the last placed vert."""
        last = self.points[-1] if self.points else None
        return apply_pen_axis_lock(world_pt, last, self.axis_lock)

    def resolve_click(
        self,
        raw_pt: Point2D,
        mouse: Point2D,
        pick_radius_sq: float,
        snap_candidates: list[Point2D],
    ) -> tuple[Point2D, bool]:
        """Resolve a click into ``(point, close_loop)``.

        - within the pick radius of this line's FIRST vert (>= 2 placed) ->
          (first vert, True) to close;
        - within the pick radius of a snap candidate -> (that exact vert, False)
          to union rather than stack a near-duplicate;
        - otherwise -> (axis-locked raw point, False).
        """
        if len(self.points) >= 2:
            fx, fz = self.points[0]
            if (fx - mouse[0]) ** 2 + (fz - mouse[1]) ** 2 <= pick_radius_sq:
                return (fx, fz), True
        best: Point2D | None = None
        best_d2 = pick_radius_sq
        for cx, cz in snap_candidates:
            d2 = (cx - mouse[0]) ** 2 + (cz - mouse[1]) ** 2
            if d2 <= best_d2:
                best_d2 = d2
                best = (cx, cz)
        if best is not None:
            return best, False
        return self.apply_axis_lock(raw_pt), False

    def place(self, point: Point2D) -> None:
        """Append a resolved vert; the new edge bakes the current subdivision count."""
        self.active = True
        self.points.append(point)
        if len(self.points) >= 2:
            self.edge_subdivs.append(self.subdivisions)
        self.live_preview["active"] = True
        self.live_preview["mode"] = "pen"
        self.live_preview["kind"] = self.kind
        self.live_preview["points"] = list(self.points)
        self.live_preview["edge_subdivs"] = list(self.edge_subdivs)
        self.live_preview["cursor"] = None

    def undo_last_vert(self) -> bool:
        """Drop the last placed vert (and its baked edge count). False when empty."""
        if not self.points:
            return False
        self.points.pop()
        if self.edge_subdivs:
            self.edge_subdivs.pop()
        self.active = bool(self.points)
        self.live_preview["points"] = list(self.points)
        self.live_preview["edge_subdivs"] = list(self.edge_subdivs)
        self.live_preview["active"] = bool(self.points)
        return True

    # -- subdivision + axis ------------------------------------------------

    def set_subdivisions(self, n: int) -> None:
        self.subdivisions = max(0, min(self.SUBDIV_MAX, n))
        self.live_preview["subdivisions"] = self.subdivisions

    def bump_subdivisions(self, delta: int) -> None:
        self.set_subdivisions(self.subdivisions + delta)

    def toggle_axis(self, axis: str) -> None:
        self.axis_lock = "" if self.axis_lock == axis else axis
        self.live_preview["axis"] = self.axis_lock

    # -- finish ------------------------------------------------------------

    def dense_polyline(self) -> list[Point2D]:
        """The placed line with each edge subdivided by its own baked count."""
        return subdivide_polyline_edges(list(self.points), list(self.edge_subdivs))
