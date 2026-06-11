"""Edge-extend a packed placement's border into its padding ring.

Pure NumPy, no bpy: the compose step (``bpy_helpers.atlas.atlas_compose``)
calls this per placement, and ``tests/test_atlas_edge_extend`` exercises it
without Blender.

The packer (``core.atlas.atlas_packer``) reserves a ``pad``-pixel ring
around every placement. Leaving that ring transparent makes bilinear
filtering average alpha=0 neighbours into the sprite edge - a dark halo
seam. Repeating the nearest border pixel into the ring (alpha bleed /
edge-extend) is the standard fix and is default-on in every mainstream
packer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt


def edge_extend_ring(
    canvas: npt.NDArray[np.float32],
    y0: int,
    x0: int,
    h: int,
    w: int,
    pad: int,
    atlas_w: int,
    atlas_h: int,
) -> None:
    """Repeat the ``(y0, x0, h, w)`` placement's border into its padding ring.

    Mutates ``canvas`` (an ``(H, W, 4)`` RGBA array) in place. The reserved
    ring is ``pad`` pixels on every side; the spans are clamped to the atlas
    so a placement flush against an edge does not negative-index-wrap.
    """
    if pad <= 0 or h <= 0 or w <= 0:
        return
    x_lo = max(0, x0 - pad)
    x_hi = min(atlas_w, x0 + w + pad)
    y_lo = max(0, y0 - pad)
    y_hi = min(atlas_h, y0 + h + pad)
    # Left / right columns across the content rows.
    canvas[y0 : y0 + h, x_lo:x0] = canvas[y0 : y0 + h, x0 : x0 + 1]
    canvas[y0 : y0 + h, x0 + w : x_hi] = canvas[y0 : y0 + h, x0 + w - 1 : x0 + w]
    # Top / bottom rows across the now-widened span, which fills the corners
    # too (the widened rows already carry the left/right extension).
    canvas[y_lo:y0, x_lo:x_hi] = canvas[y0 : y0 + 1, x_lo:x_hi]
    canvas[y0 + h : y_hi, x_lo:x_hi] = canvas[y0 + h - 1 : y0 + h, x_lo:x_hi]
