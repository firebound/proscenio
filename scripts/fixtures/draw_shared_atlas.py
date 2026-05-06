"""Generate the shared_atlas atlas PNG (SPEC 007 step 2, Pillow only).

Run with::

    python scripts/fixtures/draw_shared_atlas.py

Pure Python — no Blender required. Produces a 256×256 atlas with three
colored shapes drawn into three quadrants. The fourth quadrant stays
transparent so any regression that re-packs the whole atlas (instead
of slicing) shows up as visible empty space.

Companion ``build_shared_atlas.py`` runs in headless Blender, builds 3
polygon meshes referencing this atlas with per-quadrant UV bounds.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _draw import Canvas, circle, fill, rect, triangle  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "examples" / "shared_atlas"
ATLAS_PATH = FIXTURE_DIR / "atlas.png"

ATLAS_W = 256
ATLAS_H = 256
QUAD = 128

BACKGROUND_TRANSPARENT = (0.0, 0.0, 0.0, 0.0)
RED = (0.85, 0.20, 0.20, 1.0)
GREEN = (0.20, 0.75, 0.30, 1.0)
BLUE = (0.20, 0.40, 0.85, 1.0)


def main() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    canvas = Canvas.empty(ATLAS_W, ATLAS_H)
    fill(canvas, BACKGROUND_TRANSPARENT)

    # Top-left quadrant: red circle.
    # Pillow coords are top-down: y=0 is top of canvas.
    circle(canvas, QUAD * 0.5, QUAD * 0.5, QUAD * 0.4, RED)

    # Top-right quadrant: green triangle pointing up.
    triangle(
        canvas,
        (QUAD + QUAD * 0.5, QUAD * 0.1),
        (QUAD + QUAD * 0.1, QUAD * 0.9),
        (QUAD + QUAD * 0.9, QUAD * 0.9),
        GREEN,
    )

    # Bottom-left quadrant: blue square.
    rect(
        canvas,
        int(QUAD * 0.2),
        QUAD + int(QUAD * 0.2),
        int(QUAD * 0.6),
        int(QUAD * 0.6),
        BLUE,
    )

    # Bottom-right intentionally left transparent.

    canvas.save(ATLAS_PATH)
    print(f"[draw_shared_atlas] wrote {ATLAS_PATH}")


if __name__ == "__main__":
    main()
