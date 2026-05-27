"""Pure tests for CDT extra_edges threading (SPEC 013 S8)."""
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
