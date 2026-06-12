"""Generate the mixed_feature atlas PNG (the feature-stack fixture, Pillow only).

Run with::

    python packages/fixtures/mixed_feature/draw_layers.py

Pure Python - no Blender required. Produces one 128x128 ``atlas.png`` under
``examples/generated/blender_to_godot/mixed_feature/`` with four 64x64 quadrants,
one per element of the fixture so every feature shares a single packed atlas:

- top-left     -> ``mouth`` 4-frame strip   (sprite_frame, hframes=4)
- top-right    -> ``face_glow`` 2-frame strip (slot sprite attachment, hframes=2)
- bottom-left  -> ``body`` texture            (skinned polygon)
- bottom-right -> ``face_neutral`` texture    (slot mesh attachment)

The pixels are only there so the atlas is non-empty and visually
distinguishable; the golden carries geometry / UVs / weights, not pixels.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from _draw import Canvas, border, circle, rect  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "blender_to_godot" / "mixed_feature"
ATLAS_PATH = FIXTURE_DIR / "atlas.png"

ATLAS_W = 128
ATLAS_H = 128
QUAD = 64

# Per-frame tints for the two sprite strips, so consecutive cells differ.
_MOUTH_TINTS = (
    (0.85, 0.25, 0.30, 1.0),
    (0.85, 0.45, 0.30, 1.0),
    (0.85, 0.65, 0.30, 1.0),
    (0.85, 0.85, 0.30, 1.0),
)
_GLOW_TINTS = (
    (0.30, 0.45, 0.85, 1.0),
    (0.55, 0.75, 1.00, 1.0),
)


def main() -> None:
    canvas = Canvas.empty(ATLAS_W, ATLAS_H)

    # Top-left quadrant: mouth, 4 frames of 16x64 across x[0, 64).
    frame_w = QUAD // len(_MOUTH_TINTS)
    for i, tint in enumerate(_MOUTH_TINTS):
        rect(canvas, i * frame_w, 0, frame_w, QUAD, tint)

    # Top-right quadrant: face_glow, 2 frames of 32x64 across x[64, 128).
    glow_w = QUAD // len(_GLOW_TINTS)
    for i, tint in enumerate(_GLOW_TINTS):
        rect(canvas, QUAD + i * glow_w, 0, glow_w, QUAD, tint)

    # Bottom-left quadrant: body (skinned), a solid torso block.
    rect(canvas, 0, QUAD, QUAD, QUAD, (0.40, 0.70, 0.45, 1.0))
    border(canvas, (0.20, 0.40, 0.25, 1.0))

    # Bottom-right quadrant: face_neutral, a face disc.
    rect(canvas, QUAD, QUAD, QUAD, QUAD, (0.95, 0.80, 0.65, 1.0))
    circle(canvas, QUAD + QUAD / 2, QUAD + QUAD / 2, QUAD / 3, (0.80, 0.55, 0.40, 1.0))

    canvas.save(ATLAS_PATH)
    print(f"[draw_mixed_feature] wrote {ATLAS_PATH}")


if __name__ == "__main__":
    main()
