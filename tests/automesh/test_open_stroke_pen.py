"""Pure tests for the open-stroke click pen (OpenStrokePen).

The open-pen state machine used to live inline in the automesh authoring modal
and could only be exercised interactively. Extracted to a pure controller, its
place / snap-resolve / subdivide / axis-lock / undo transitions are unit-tested
here without a viewport; the operator's bpy event dispatch is covered in-Blender.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

# open_stroke_pen imports stroke_geometry, which imports bmesh at module top; the
# pen's functions are pure Python, so mocking the Blender modules for import is
# enough to exercise them without a viewport.
sys.modules["bpy"] = MagicMock()
sys.modules["bmesh"] = MagicMock()
sys.modules["mathutils"] = MagicMock()

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.bpy_helpers.automesh.open_stroke_pen import OpenStrokePen  # noqa: E402


def test_arm_lights_the_preview_and_clears_the_line():
    pen = OpenStrokePen()
    pen.points.append((9.0, 9.0))  # stale state from a prior line
    pen.arm("cut")
    assert pen.kind == "cut"
    assert pen.points == []
    assert pen.live_preview["active"] is True
    # An open pen never draws a closing ghost.
    assert pen.live_preview["close_loop"] is False


def test_place_bakes_the_current_subdivision_onto_each_new_edge():
    pen = OpenStrokePen()
    pen.arm("stroke")
    pen.place((0.0, 0.0))
    assert pen.edge_subdivs == []  # first vert has no edge behind it
    pen.set_subdivisions(3)
    pen.place((1.0, 0.0))  # edge 0 bakes 3
    pen.set_subdivisions(1)
    pen.place((2.0, 0.0))  # edge 1 bakes 1
    assert pen.edge_subdivs == [3, 1]
    assert pen.active is True


def test_resolve_click_closes_on_the_first_vert_within_radius():
    pen = OpenStrokePen()
    pen.arm("stroke")
    pen.place((0.0, 0.0))
    pen.place((1.0, 0.0))
    # Click near the first vert (mouse close to (0,0)); radius^2 = 0.04.
    pt, close = pen.resolve_click((0.1, 0.0), (0.05, 0.0), 0.04, [])
    assert close is True
    assert pt == (0.0, 0.0)


def test_resolve_click_unions_onto_a_snap_candidate():
    pen = OpenStrokePen()
    pen.arm("stroke")
    pen.place((0.0, 0.0))
    candidate = (5.0, 5.0)
    pt, close = pen.resolve_click((5.1, 5.0), (5.05, 5.0), 0.04, [candidate])
    assert close is False
    assert pt == candidate  # exact union, not the near-duplicate raw point


def test_resolve_click_axis_locks_when_nothing_is_near():
    pen = OpenStrokePen()
    pen.arm("stroke")
    pen.place((0.0, 0.0))
    pen.toggle_axis("x")  # keep world-Z of the last vert (z=0)
    pt, close = pen.resolve_click((3.0, 7.0), (3.0, 7.0), 0.01, [])
    assert close is False
    assert pt[0] == 3.0 and pt[1] == 0.0  # x kept, z snapped to the last vert's z


def test_set_subdivisions_clamps_to_the_cap():
    pen = OpenStrokePen()
    pen.arm("stroke")
    pen.set_subdivisions(-4)
    assert pen.subdivisions == 0
    pen.set_subdivisions(999)
    assert pen.subdivisions == OpenStrokePen.SUBDIV_MAX
    pen.bump_subdivisions(-1)
    assert pen.subdivisions == OpenStrokePen.SUBDIV_MAX - 1


def test_toggle_axis_is_a_toggle():
    pen = OpenStrokePen()
    pen.arm("stroke")
    pen.toggle_axis("z")
    assert pen.axis_lock == "z"
    pen.toggle_axis("z")  # same axis again clears it
    assert pen.axis_lock == ""
    pen.toggle_axis("x")
    assert pen.axis_lock == "x"


def test_undo_last_vert_drops_the_point_and_its_edge_count():
    pen = OpenStrokePen()
    pen.arm("stroke")
    pen.place((0.0, 0.0))
    pen.set_subdivisions(2)
    pen.place((1.0, 0.0))
    assert pen.edge_subdivs == [2]
    assert pen.undo_last_vert() is True
    assert pen.points == [(0.0, 0.0)]
    assert pen.edge_subdivs == []
    assert pen.active is True
    assert pen.undo_last_vert() is True
    assert pen.active is False
    assert pen.undo_last_vert() is False  # empty


def test_dense_polyline_subdivides_each_edge_by_its_own_count():
    pen = OpenStrokePen()
    pen.arm("stroke")
    pen.place((0.0, 0.0))
    pen.set_subdivisions(1)
    pen.place((2.0, 0.0))  # edge 0 subdivided once -> inserts (1,0)
    dense = pen.dense_polyline()
    assert (1.0, 0.0) in dense
    assert dense[0] == (0.0, 0.0)
    assert dense[-1] == (2.0, 0.0)


def test_clear_hides_the_preview_and_empties_the_line():
    pen = OpenStrokePen()
    pen.arm("stroke")
    pen.place((0.0, 0.0))
    pen.clear()
    assert pen.points == []
    assert pen.active is False
    assert pen.live_preview["active"] is False
