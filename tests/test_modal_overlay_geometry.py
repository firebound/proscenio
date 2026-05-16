"""Unit tests for SPEC 012.1 modal-overlay geometry helpers.

bpy-free. Exercises the vertex builders consumed by
``core/bpy_helpers/modal_overlay.py``.

Run from the repo root:

    pytest tests/test_modal_overlay_geometry.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.modal_overlay_geometry import (  # noqa: E402  - sys.path setup above
    build_circle_vertices,
    build_rect_vertices,
)


def test_circle_segments_count_matches_request() -> None:
    verts = build_circle_vertices((0.0, 0.0, 0.0), 1.0, "Y", 24)
    assert len(verts) == 24


def test_circle_xz_plane_holds_y_constant() -> None:
    verts = build_circle_vertices((1.0, 2.0, 3.0), 0.5, "Y", 16)
    for x, y, z in verts:
        assert y == pytest.approx(2.0)
        # Distance to center on XZ plane equals radius.
        dx = x - 1.0
        dz = z - 3.0
        assert math.hypot(dx, dz) == pytest.approx(0.5, abs=1e-6)


def test_circle_xy_plane_holds_z_constant() -> None:
    verts = build_circle_vertices((0.0, 0.0, 5.0), 2.0, "Z", 8)
    for _x, _y, z in verts:
        assert z == pytest.approx(5.0)


def test_circle_yz_plane_holds_x_constant() -> None:
    verts = build_circle_vertices((7.0, 0.0, 0.0), 1.5, "X", 12)
    for x, _y, _z in verts:
        assert x == pytest.approx(7.0)


def test_circle_first_vertex_lies_on_positive_axis() -> None:
    # Y plane: at angle 0 the offset is (radius, 0, 0).
    verts = build_circle_vertices((0.0, 0.0, 0.0), 1.0, "Y", 4)
    assert verts[0] == pytest.approx((1.0, 0.0, 0.0), abs=1e-9)


def test_circle_rejects_too_few_segments() -> None:
    with pytest.raises(ValueError):
        build_circle_vertices((0.0, 0.0, 0.0), 1.0, "Y", 2)


def test_circle_rejects_non_positive_radius() -> None:
    with pytest.raises(ValueError):
        build_circle_vertices((0.0, 0.0, 0.0), 0.0, "Y", 12)
    with pytest.raises(ValueError):
        build_circle_vertices((0.0, 0.0, 0.0), -1.0, "Y", 12)


def test_rect_returns_six_vertices_two_triangles() -> None:
    verts = build_rect_vertices(0.0, 0.0, 10.0, 5.0)
    assert len(verts) == 6
    # Two triangles share the bl/tr diagonal.
    assert verts[0] == verts[3]
    assert verts[2] == verts[4]


def test_rect_corners_are_correct() -> None:
    verts = build_rect_vertices(2.0, 3.0, 8.0, 7.0)
    assert (2.0, 3.0) in verts
    assert (8.0, 3.0) in verts
    assert (8.0, 7.0) in verts
    assert (2.0, 7.0) in verts


def test_rect_rejects_degenerate_size() -> None:
    with pytest.raises(ValueError):
        build_rect_vertices(0.0, 0.0, 0.0, 5.0)
    with pytest.raises(ValueError):
        build_rect_vertices(0.0, 0.0, 5.0, 0.0)
    with pytest.raises(ValueError):
        build_rect_vertices(5.0, 5.0, 0.0, 10.0)
