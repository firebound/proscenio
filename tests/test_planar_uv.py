"""Unit tests for the deterministic planar UV projection.

Pure pytest, no Blender. The Reproject UV operator delegates the UV math
to ``planar_uv_from_positions``; these pin the orientation it must keep
(the bug was Smart UV Project rotating and mirroring an XZ quad).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.bpy_helpers._shared.mesh_uvs import planar_uv_from_positions  # noqa: E402

# The loop order the PSD importer and every fixture author: bottom-left,
# bottom-right, top-right, top-left, mapped to (0,0) (1,0) (1,1) (0,1).
_XZ_QUAD = [
    (-1.0, 0.0, -1.0),  # min X, min Z
    (1.0, 0.0, -1.0),  # max X, min Z
    (1.0, 0.0, 1.0),  # max X, max Z
    (-1.0, 0.0, 1.0),  # min X, max Z
]
_CANONICAL_UVS = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]


def test_xz_quad_matches_the_canonical_layout() -> None:
    """An XZ picture-plane quad projects to the same UVs the importer authors."""
    assert planar_uv_from_positions(_XZ_QUAD) == _CANONICAL_UVS


def test_offset_xz_quad_normalizes_to_full_range() -> None:
    """Position offset and non-unit size do not skew the normalized UVs."""
    offset = [(x + 10.0, y, z - 5.0) for x, y, z in _XZ_QUAD]
    scaled = [(x * 3.0, y, z * 7.0) for x, y, z in offset]
    assert planar_uv_from_positions(scaled) == _CANONICAL_UVS


def test_projection_is_idempotent() -> None:
    """Re-running on the same geometry yields identical UVs (no drift)."""
    first = planar_uv_from_positions(_XZ_QUAD)
    second = planar_uv_from_positions(_XZ_QUAD)
    assert first == second


def test_xy_plane_maps_x_and_y_to_uv() -> None:
    """A mesh flat in Z (normal Z) maps the X,Y in-plane axes to U,V in order."""
    xy_quad = [
        (0.0, 0.0, 4.0),
        (2.0, 0.0, 4.0),
        (2.0, 6.0, 4.0),
        (0.0, 6.0, 4.0),
    ]
    assert planar_uv_from_positions(xy_quad) == [
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, 1.0),
        (0.0, 1.0),
    ]


def test_degenerate_in_plane_axis_does_not_divide_by_zero() -> None:
    """A zero-extent in-plane axis (a vertical edge) maps to 0.0, not NaN."""
    edge = [(0.0, 0.0, 0.0), (0.0, 0.0, 2.0)]
    result = planar_uv_from_positions(edge)
    # Y and X both have zero extent here; Z carries the only span. Whichever
    # axis pairs with a zero-extent partner, that partner reads 0.0 cleanly.
    assert all(0.0 <= u <= 1.0 and 0.0 <= v <= 1.0 for u, v in result)
    assert len(result) == 2


def test_empty_positions_returns_empty() -> None:
    assert planar_uv_from_positions([]) == []
