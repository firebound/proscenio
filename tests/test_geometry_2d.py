"""Pure-pytest tests for the XZ point-in-triangle predicate.

bpy-free geometry helper used by the automesh / quick-armature math.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core._shared.geometry_2d import point_in_triangle_xz  # noqa: E402

# Right triangle: (0,0), (4,0), (0,4); hypotenuse x + z = 4.
TRI = ((0.0, 0.0), (4.0, 0.0), (0.0, 4.0))


def test_point_inside_is_true() -> None:
    assert point_in_triangle_xz((1.0, 1.0), TRI) is True


def test_point_outside_is_false() -> None:
    assert point_in_triangle_xz((5.0, 5.0), TRI) is False


def test_point_just_past_hypotenuse_is_false() -> None:
    assert point_in_triangle_xz((2.1, 2.1), TRI) is False


def test_point_on_edge_is_inside() -> None:
    # Boundary is inclusive (the docstring contract).
    assert point_in_triangle_xz((2.0, 0.0), TRI) is True


def test_vertex_is_inside() -> None:
    assert point_in_triangle_xz((0.0, 0.0), TRI) is True


def test_winding_order_does_not_matter() -> None:
    clockwise = ((0.0, 0.0), (0.0, 4.0), (4.0, 0.0))
    assert point_in_triangle_xz((1.0, 1.0), clockwise) is True
