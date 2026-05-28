"""Pure tests for CDT extra_edges threading (SPEC 013 S8) and AS-AM1 pre-filter."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock Blender modules before any imports
sys.modules["bpy"] = MagicMock()
sys.modules["bmesh"] = MagicMock()
sys.modules["mathutils"] = MagicMock()

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.bpy_helpers.automesh.cdt import _build_cdt_inputs  # noqa: E402
from core.bpy_helpers.automesh.authoring_pipeline import (  # noqa: E402
    _build_stroke_node_indices,
    _edges_from_node_indices,
    _vert_inside_silhouette,
)


def test_no_extra_edges_baseline_unchanged():
    outer = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    coords, edges = _build_cdt_inputs(outer, [], [], [])
    assert len(coords) == 4
    assert len(edges) == 4  # cyclic outer loop


def test_extra_edges_appended_to_constraint_list():
    outer = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    interior = [(0.5, 0.5)]  # one interior vert (idx 4 after outer)
    extra = [(0, 2)]  # diagonal across outer
    coords, edges = _build_cdt_inputs(outer, [], interior, [], extra_edges=extra)
    assert (0, 2) in edges
    assert len(coords) == 5  # 4 outer + 1 interior


def test_extra_edges_none_behaves_as_empty():
    outer = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    coords_a, edges_a = _build_cdt_inputs(outer, [], [], [], extra_edges=None)
    coords_b, edges_b = _build_cdt_inputs(outer, [], [], [])
    assert coords_a == coords_b
    assert edges_a == edges_b


# ---------------------------------------------------------------------------
# AS-AM1: pre-index-allocation silhouette filter
# ---------------------------------------------------------------------------

# Unit square outer polygon used by all three filter tests.
_OUTER = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]


def test_vert_inside_silhouette_outside_outer_returns_false():
    """Vert outside the outer polygon is rejected."""
    assert not _vert_inside_silhouette((2.0, 2.0), _OUTER, None, None)


def test_vert_inside_silhouette_inside_outer_returns_true():
    """Vert inside the outer polygon with no inner/holes is accepted."""
    assert _vert_inside_silhouette((0.5, 0.5), _OUTER, None, None)


def test_build_stroke_node_indices_drops_outside_vert_no_edge_across_gap():
    """Middle vert outside silhouette is dropped; no edge connects its neighbours.

    Stroke: A(inside) - B(outside) - C(inside) - D(inside)
    Expected: A and C,D each get indices; no edge from A to C (gap at B).
    Edge runs: [A] and [C-D].
    """
    outer_contour = _OUTER
    # Stroke verts in local space (no snap - far from contour edges)
    pts_local = [
        (0.2, 0.5),   # A - inside - index interior_base_index + 0
        (2.0, 2.0),   # B - OUTSIDE -> dropped
        (0.6, 0.5),   # C - inside - index interior_base_index + 1
        (0.8, 0.5),   # D - inside - index interior_base_index + 2
    ]
    extras_local: list = []
    node_indices, dropped = _build_stroke_node_indices(
        pts_local,
        outer_contour,
        outer_base_index=0,
        interior_base_index=10,
        extras_local=extras_local,
        snap_radius=0.01,  # tiny - no snap
        silhouette_outer=outer_contour,
        silhouette_inner=None,
        silhouette_holes=None,
    )
    assert dropped == 1, f"expected 1 dropped, got {dropped}"
    # A, C, D survive -> 3 extras appended
    assert len(extras_local) == 3
    # node_indices = [10, None, 11, 12] - None sentinel preserves the gap.
    # Indices for survivors A=10, C=11, D=12.
    assert node_indices == [10, None, 11, 12]
    edges = _edges_from_node_indices(node_indices)
    # Only the C-D pair is valid (consecutive AND both not-None).
    # A-C must NOT be emitted (None sentinel between them).
    assert edges == [(11, 12)]
    assert (10, 11) not in edges, "edge spanned the dropped vert gap"
    assert (10, 12) not in edges, "edge skipped over dropped vert"


def test_build_stroke_node_indices_all_dropped_returns_empty():
    """Entire stroke outside silhouette -> empty extras, empty indices, dropped == len(pts)."""
    outer_contour = _OUTER
    pts_local = [(5.0, 5.0), (6.0, 6.0), (7.0, 7.0)]
    extras_local: list = []
    node_indices, dropped = _build_stroke_node_indices(
        pts_local,
        outer_contour,
        outer_base_index=0,
        interior_base_index=10,
        extras_local=extras_local,
        snap_radius=0.01,
        silhouette_outer=outer_contour,
        silhouette_inner=None,
        silhouette_holes=None,
    )
    assert dropped == 3
    assert node_indices == []
    assert extras_local == []
