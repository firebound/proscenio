"""Generate the mixed_feature atlas PNG (the feature-stack fixture, Pillow only).

Run with::

    python packages/fixtures/mixed_feature/draw_layers.py

Pure Python - no Blender required. Produces one 128x128 ``atlas.png`` under
``examples/generated/blender_to_godot/mixed_feature/`` with four 64x64 quadrants,
one per element of the fixture so every feature shares a single packed atlas:

- top-left     -> ``mouth`` 4-frame strip (2x2 grid, a mouth opening; sprite)
- top-right    -> ``face_glow`` glowing head (slot sprite attachment)
- bottom-left  -> ``body`` torso (skinned polygon)
- bottom-right -> ``face_neutral`` neutral head (slot mesh attachment)

The two faces are the swappable slot attachments (a head with eyes); the mouth
is a separate animated sprite that sits on the face.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from _draw import Canvas, circle, rect  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = (
    REPO_ROOT / "examples" / "generated" / "blender_to_godot" / "mixed_feature"
)
ATLAS_PATH = FIXTURE_DIR / "atlas.png"

ATLAS_W = 128
ATLAS_H = 128
QUAD = 64

_SKIN = (0.95, 0.80, 0.65, 1.0)
_SKIN_GLOW = (1.0, 0.92, 0.55, 1.0)
_EYE = (0.25, 0.20, 0.18, 1.0)
_MOUTH = (0.55, 0.20, 0.20, 1.0)
_BODY = (0.40, 0.70, 0.45, 1.0)
_GLOW_RING = (1.0, 0.75, 0.30, 1.0)
_TRANSPARENT = (0.0, 0.0, 0.0, 0.0)


def _draw_head(canvas: Canvas, ox: int, oy: int, glow: bool) -> None:
    """A 64x64 head: skin square + two eyes; a glow ring + warmer skin when glow."""
    skin = _SKIN_GLOW if glow else _SKIN
    rect(canvas, ox, oy, QUAD, QUAD, skin)
    if glow:
        # A warm ring just inside the edge marks the glowing variant.
        for t in range(2):
            rect(canvas, ox + t, oy + t, QUAD - 2 * t, 1, _GLOW_RING)
            rect(canvas, ox + t, oy + QUAD - 1 - t, QUAD - 2 * t, 1, _GLOW_RING)
            rect(canvas, ox + t, oy + t, 1, QUAD - 2 * t, _GLOW_RING)
            rect(canvas, ox + QUAD - 1 - t, oy + t, 1, QUAD - 2 * t, _GLOW_RING)
    eye_y = oy + QUAD * 0.40
    circle(canvas, ox + QUAD * 0.34, eye_y, 5, _EYE)
    circle(canvas, ox + QUAD * 0.66, eye_y, 5, _EYE)


def _draw_mouth_frames(canvas: Canvas) -> None:
    """Mouth: 4 frames in a 2x2 grid of 16x16 cells in the top-left 32x32 of the
    atlas (smaller than the face). A round mouth opening wider 0 -> 3 (a small
    closed dot to a wide open 'o'). The rest of the quadrant stays transparent so
    the sprite overlays the face."""
    cell = 16
    radii = (1.5, 3.0, 4.5, 6.0)  # mouth radius per frame
    for i, radius in enumerate(radii):
        cx = (i % 2) * cell + cell / 2
        cy = (i // 2) * cell + cell / 2
        circle(canvas, cx, cy, radius, _MOUTH)


def main() -> None:
    canvas = Canvas.empty(ATLAS_W, ATLAS_H)

    _draw_mouth_frames(canvas)  # top-left
    _draw_head(canvas, QUAD, 0, glow=True)  # top-right: face_glow
    rect(canvas, 0, QUAD, QUAD, QUAD, _BODY)  # bottom-left: body torso
    _draw_head(canvas, QUAD, QUAD, glow=False)  # bottom-right: face_neutral

    canvas.save(ATLAS_PATH)
    print(f"[draw_mixed_feature] wrote {ATLAS_PATH}")


if __name__ == "__main__":
    main()
