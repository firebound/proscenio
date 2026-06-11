"""Pure unit tests for the atlas padding-ring edge-extend.

The packer reserves a ``pad``-pixel ring around every placement
(``atlas_packer`` padding semantics). Leaving that ring transparent makes
bilinear filtering bleed alpha=0 into the sprite edge - a halo seam. The
compose step repeats the placement's border pixels into the ring instead.
This exercises the pure NumPy helper without Blender.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.atlas.edge_extend import edge_extend_ring  # noqa: E402


def _ramp_block(h: int, w: int) -> np.ndarray:
    """A block whose red channel ramps by column so each edge is distinct."""
    block = np.zeros((h, w, 4), dtype=np.float32)
    for c in range(w):
        block[:, c] = [(c + 1) / w, 0.0, 0.0, 1.0]
    return block


def test_ring_repeats_the_border_not_transparent():
    canvas = np.zeros((20, 20, 4), dtype=np.float32)
    block = _ramp_block(4, 4)
    canvas[8:12, 8:12] = block

    edge_extend_ring(canvas, 8, 8, 4, 4, 2, 20, 20)

    left_border = block[:, 0]
    right_border = block[:, -1]
    # Left / right rings repeat the nearest content column.
    assert np.allclose(canvas[8:12, 6], left_border)
    assert np.allclose(canvas[8:12, 7], left_border)
    assert np.allclose(canvas[8:12, 12], right_border)
    assert np.allclose(canvas[8:12, 13], right_border)
    # Top / bottom rings repeat the nearest content row.
    assert np.allclose(canvas[6, 8:12], canvas[8, 8:12])
    assert np.allclose(canvas[13, 8:12], canvas[11, 8:12])
    # Corners take the corner pixel (no transparent diagonal gap).
    assert np.allclose(canvas[6:8, 6:8], left_border[0])
    # The ring is opaque where it was transparent before.
    assert canvas[6, 6, 3] == 1.0


def test_clamps_at_the_atlas_edge_without_wrapping():
    canvas = np.zeros((10, 10, 4), dtype=np.float32)
    block = _ramp_block(3, 3)
    canvas[0:3, 0:3] = block

    # Placement flush against the top-left corner: the left/top ring has no
    # room. Must not negative-index-wrap into the opposite edge.
    edge_extend_ring(canvas, 0, 0, 3, 3, 2, 10, 10)

    # Opposite (bottom-right) corner stays untouched.
    assert np.allclose(canvas[8:10, 8:10], 0.0)
    # The right ring still extends from the content's right column.
    assert np.allclose(canvas[0:3, 3], block[:, -1])
    assert np.allclose(canvas[0:3, 4], block[:, -1])


def test_zero_padding_is_a_noop():
    canvas = np.zeros((10, 10, 4), dtype=np.float32)
    canvas[4:7, 4:7] = _ramp_block(3, 3)
    before = canvas.copy()

    edge_extend_ring(canvas, 4, 4, 3, 3, 0, 10, 10)

    assert np.array_equal(canvas, before)
