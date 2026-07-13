"""Generate the bone_attach PNG layer (step 1, Pillow only).

Run with::

    python packages/fixtures/bone_attach/draw_layers.py

Pure Python - no Blender required. Produces:

- ``examples/generated/bone_attach/pillow_layers/badge.png`` (32x32)

A deliberately asymmetric flag shape: a wrong rotation or a mirrored
render is visually obvious at a glance. The accompanying
``build_blend.py`` runs in headless Blender, loads the PNG from disk,
and assembles the ``.blend``.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from _draw import Canvas, circle, rect  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "bone_attach"
LAYERS_DIR = FIXTURE_DIR / "pillow_layers"
BADGE_PATH = LAYERS_DIR / "badge.png"

SIZE = 32

POLE = (0.25, 0.22, 0.20, 1.0)
FLAG = (0.85, 0.20, 0.15, 1.0)
KNOB = (0.95, 0.75, 0.10, 1.0)


def main() -> None:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    canvas = Canvas.empty(SIZE, SIZE)
    # Vertical pole, flag to the RIGHT at the TOP, knob at the bottom: no
    # symmetry axis survives, so any rotation/mirror error shows.
    rect(canvas, 14, 3, 4, 26, POLE)
    rect(canvas, 18, 3, 12, 10, FLAG)
    circle(canvas, 16, 28, 3, KNOB)
    canvas.save(BADGE_PATH)
    print(f"[draw_bone_attach] wrote {BADGE_PATH}")


if __name__ == "__main__":
    main()
