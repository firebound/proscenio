"""Pure tests for the shared closed-loop VertexPen state (axis lock, subdivide,
undo, ring). The mouse / projection paths are bpy-coupled and covered by the
in-Blender operator tests; here we exercise the host-agnostic logic."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock Blender modules before any imports (VertexPen imports bpy via viewport_math).
sys.modules["bpy"] = MagicMock()
sys.modules["bmesh"] = MagicMock()
sys.modules["mathutils"] = MagicMock()

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.bpy_helpers.automesh.vertex_pen import VertexPen  # noqa: E402


def test_ring_needs_three_distinct_verts():
    pen = VertexPen()
    assert pen.ring() is None  # empty
    pen.points = [(0.0, 0.0), (1.0, 0.0)]
    assert pen.ring() is None  # two verts: not a silhouette
    pen.points = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    ring = pen.ring()
    assert ring is not None
    assert len(ring) == 3


def test_ring_bakes_per_edge_subdivisions():
    pen = VertexPen()
    pen.points = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0)]
    pen.edge_subdivs = [1, 1]  # one per open edge; the wrap edge has no count
    base = VertexPen()
    base.points = list(pen.points)
    ring = pen.ring()
    # Two open edges subdivided by 1 each -> +2; the implicit wrap stays bare.
    assert len(ring) == len(base.ring()) + 2
    # Pin WHERE the inserted verts land, not just the total: the midpoints of the
    # two subdivided edges must appear, so subdividing a DIFFERENT edge by the
    # same total count does not slip through on the length alone.
    assert (1.0, 0.0) in ring  # midpoint of edge 0: (0,0) -> (2,0)
    assert (2.0, 1.0) in ring  # midpoint of edge 1: (2,0) -> (2,2)


def test_load_preloads_points_and_subdivs_for_reedit():
    """Spec 070 C2: load() rehydrates a stored contour so a re-invoke continues
    the drawing - points + per-edge subdivs set, the pen armed + active."""
    pen = VertexPen()
    pts = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0)]
    subs = [1, 1]
    pen.load(pts, subs)
    assert pen.points == pts
    # A reloaded 3+ vert contour opens straight into the EDIT phase (spec 070 C4):
    # closed, with the per-edge subdivs padded to one-per-edge (wrap = 0).
    assert pen.closed is True
    assert pen.edge_subdivs == [1, 1, 0]
    assert pen._active is True
    ring = pen.ring()
    assert (
        ring is not None and len(ring) == len(pts) + 2
    )  # both open edges subdivided once


def test_close_enters_edit_phase_and_pads_subdivs():
    """Spec 070 C4: close() opens the EDIT phase and pads the per-edge subdiv list
    to one-per-edge (incl the wrap)."""
    pen = VertexPen()
    pen.points = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]
    pen.edge_subdivs = [1, 0, 0]
    pen.close()
    assert pen.closed is True
    assert len(pen.edge_subdivs) == len(pen.points)


def test_close_drops_trailing_duplicate_first_vert():
    """A loop confirmed onto the first vert carries a duplicate; close() drops it
    so the EDIT ring has no degenerate edge."""
    pen = VertexPen()
    pen.points = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 0.0)]
    pen.edge_subdivs = [0, 0, 0]
    pen.close()
    assert pen.points == [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0)]


def test_close_refuses_a_degenerate_two_vert_loop():
    """A 2-vert loop is degenerate: close() must NOT enter the EDIT phase (it
    would leave a stray dup vert + edge_subdiv that corrupts the next CDT).
    The pen stays open so drawing can continue or re-arm cleanly."""
    pen = VertexPen()
    pen.points = [(0.0, 0.0), (1.0, 0.0)]
    pen.edge_subdivs = [0]
    pen.close()
    assert pen.closed is False
    # a close-on-first-vert click on two points (dup of the first) also refuses
    pen.points = [(0.0, 0.0), (1.0, 0.0), (0.0, 0.0)]
    pen.edge_subdivs = [0, 0]
    pen.close()
    assert pen.closed is False


def test_close_refuses_three_points_with_a_coincident_pair():
    """3 points but only 2 distinct (a snap-to-candidate placed a duplicate
    mid-loop) is still degenerate - ring() rejects it on len(set) < 3, so close()
    must too, or EDIT enters with a ring the next CDT chokes on."""
    pen = VertexPen()
    pen.points = [(0.0, 0.0), (1.0, 0.0), (1.0, 0.0)]  # last two coincide
    pen.edge_subdivs = [0, 0]
    pen.close()
    assert pen.closed is False
    assert pen.ring() is None  # the ring the guard mirrors


def test_insert_on_edge_splits_and_inherits_subdiv():
    """Spec 070 C4: inserting a vert on a placed edge grows the ring at that spot
    and both halves inherit the edge's subdivision count."""
    pen = VertexPen()
    pen.points = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)]
    pen.close()
    pen.set_edge_subdiv(0, 3)  # edge 0 = v0 -> v1
    before = len(pen.points)
    pen.insert_on_edge(0, (2.0, 0.0))
    assert len(pen.points) == before + 1
    assert pen.points[1] == (2.0, 0.0)  # inserted between v0 and v1
    assert pen.edge_subdivs[0] == 3
    assert pen.edge_subdivs[1] == 3


def test_insert_on_wrap_edge_appends_to_ring_end():
    """The wrap edge (last -> first) inserts at the end of the ring."""
    pen = VertexPen()
    pen.points = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0)]
    pen.close()  # n=3, wrap edge index = 2 (v2 -> v0)
    pen.insert_on_edge(2, (2.0, 2.0))
    assert pen.points[-1] == (2.0, 2.0)


def test_set_edge_subdiv_targets_only_that_edge():
    """Spec 070 C4: the hovered-edge subdiv changes one edge, not the whole ring."""
    pen = VertexPen()
    pen.points = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)]
    pen.close()
    pen.set_edge_subdiv(2, 5)
    assert pen.edge_subdivs[2] == 5
    assert pen.edge_subdivs[0] == 0
    assert pen.edge_subdivs[1] == 0


def test_ring_per_edge_counts_are_independent():
    """Each edge keeps its own subdivision count (spec 070) - scroll changes
    only the edge being drawn, not the whole ring."""
    pen = VertexPen()
    pen.points = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)]
    pen.edge_subdivs = [3, 0, 0]  # only the first edge is subdivided
    base = VertexPen()
    base.points = list(pen.points)
    assert len(pen.ring()) == len(base.ring()) + 3  # only edge 0's three verts


def test_axis_lock_x_keeps_last_z_z_keeps_last_x():
    pen = VertexPen()
    pen.points = [(1.0, 5.0)]
    pen.axis_lock = "x"  # horizontal: keep the last vert's world-Z
    assert pen._apply_axis_lock((9.0, 9.0)) == (9.0, 5.0)
    pen.axis_lock = "z"  # vertical: keep the last vert's world-X
    assert pen._apply_axis_lock((9.0, 9.0)) == (1.0, 9.0)
    pen.axis_lock = ""
    assert pen._apply_axis_lock((9.0, 9.0)) == (9.0, 9.0)


def test_axis_lock_noop_without_a_prior_vert():
    pen = VertexPen()
    pen.axis_lock = "x"
    assert pen._apply_axis_lock((9.0, 9.0)) == (9.0, 9.0)


def test_set_subdivisions_clamps_to_range():
    pen = VertexPen()
    pen._set_subdivisions(-5)
    assert pen.subdivisions == 0
    pen._set_subdivisions(999)
    assert pen.subdivisions == VertexPen.SUBDIV_MAX
    pen._set_subdivisions(3)
    assert pen.subdivisions == 3
    assert pen.live_preview["subdivisions"] == 3


def test_toggle_axis_lock_is_a_toggle():
    pen = VertexPen()
    pen._toggle_axis_lock("x")
    assert pen.axis_lock == "x"
    pen._toggle_axis_lock("x")  # same axis again clears it
    assert pen.axis_lock == ""
    pen._toggle_axis_lock("x")
    pen._toggle_axis_lock("z")  # different axis switches
    assert pen.axis_lock == "z"


def test_undo_last_pops_and_keeps_tool_armed():
    pen = VertexPen()
    pen.arm()
    pen.points = [(0.0, 0.0), (1.0, 0.0)]
    pen._active = True
    pen._undo_last()
    assert pen.points == [(0.0, 0.0)]
    assert pen._active is True
    pen._undo_last()
    assert pen.points == []
    assert pen._active is False
    assert pen.live_preview["active"] is True  # armed even with an empty line


def test_arm_clears_and_lights_preview_reset_hides_it():
    pen = VertexPen()
    pen.points = [(0.0, 0.0)]
    pen.subdivisions = 4
    pen.axis_lock = "x"
    pen.arm()
    assert pen.points == []
    assert pen.subdivisions == 0
    assert pen.axis_lock == ""
    assert pen.live_preview["active"] is True
    pen.points = [(1.0, 1.0)]
    pen.reset()
    assert pen.live_preview["active"] is False


def test_kind_flows_to_live_preview():
    pen = VertexPen(kind="cut")
    assert pen.kind == "cut"
    assert pen.live_preview["kind"] == "cut"
