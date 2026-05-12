"""Generate the simple_psd PNG layers (SPEC 006 Wave 6.5, Pillow only).

Run with::

    python scripts/fixtures/simple_psd/draw_layers.py

Pure Python -- no Blender required. Produces:

- ``examples/generated/simple_psd/pillow_layers/square.png`` (64x64 polygon layer)
- ``examples/generated/simple_psd/pillow_layers/arrow_0.png`` ... ``arrow_3.png``
  (32x32 each, sprite_frame rotation cycle)
- ``examples/generated/simple_psd/pillow_layers/arrow_spritesheet.png``
  (preview only -- the importer composes its own internal sheet)

The accompanying ``build_blend.py`` runs in headless Blender, calls the
addon's ``import_manifest()`` on the committed manifest, and saves
``simple_psd.blend``. The fixture is the smallest end-to-end exercise
of both layer kinds (polygon + sprite_frame) defined by SPEC 006 v1.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from _draw import Canvas, fill, rect, triangle  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "simple_psd"
LAYERS_DIR = FIXTURE_DIR / "pillow_layers"
SHEET_PATH = LAYERS_DIR / "arrow_spritesheet.png"

SQUARE_W = 64
SQUARE_H = 64
ARROW_W = 32
ARROW_H = 32
HFRAMES = 4

CYAN = (0.18, 0.65, 0.85, 1.0)
ARROW_COLOR = (0.95, 0.55, 0.20, 1.0)


def main() -> None:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    _draw_polygon_square()
    _draw_sprite_frame_arrows()
    _draw_spritesheet_preview()
    print(f"[draw_simple_psd] wrote square.png + 4 arrow frames under {LAYERS_DIR}")
    print(f"[draw_simple_psd] wrote spritesheet preview {SHEET_PATH}")


def _draw_polygon_square() -> None:
    canvas = Canvas.empty(SQUARE_W, SQUARE_H)
    fill(canvas, CYAN)
    canvas.save(LAYERS_DIR / "square.png")


def _draw_sprite_frame_arrows() -> None:
    """Four 90-degree rotations of an upward-pointing arrow.

    Frame 0 -> up, 1 -> right, 2 -> down, 3 -> left. Tests that the
    sprite_frame importer keeps frame ordering intact through the
    manifest -> bpy planes -> spritesheet compose path.
    """
    for idx in range(HFRAMES):
        canvas = Canvas.empty(ARROW_W, ARROW_H)
        _draw_arrow(canvas, idx)
        canvas.save(LAYERS_DIR / f"arrow_{idx}.png")


def _draw_arrow(canvas: Canvas, frame: int) -> None:
    """Stamp an arrowhead pointing in one of four cardinal directions.

    `frame` 0=up, 1=right, 2=down, 3=left.
    """
    cx = canvas.width / 2.0
    cy = canvas.height / 2.0
    half = canvas.width / 2.0 - 4
    if frame == 0:
        tip, base_a, base_b = (cx, cy - half), (cx - half, cy + half), (cx + half, cy + half)
    elif frame == 1:
        tip, base_a, base_b = (cx + half, cy), (cx - half, cy - half), (cx - half, cy + half)
    elif frame == 2:
        tip, base_a, base_b = (cx, cy + half), (cx - half, cy - half), (cx + half, cy - half)
    else:
        tip, base_a, base_b = (cx - half, cy), (cx + half, cy - half), (cx + half, cy + half)
    triangle(canvas, tip, base_a, base_b, ARROW_COLOR)


def _draw_spritesheet_preview() -> None:
    sheet = Canvas.empty(ARROW_W * HFRAMES, ARROW_H)
    rect(sheet, 0, 0, sheet.width, sheet.height, (0.05, 0.05, 0.05, 1.0))
    for idx in range(HFRAMES):
        sub = Canvas.empty(ARROW_W, ARROW_H)
        _draw_arrow(sub, idx)
        sheet.image.paste(sub.image, (idx * ARROW_W, 0))
    sheet.save(SHEET_PATH)


if __name__ == "__main__":
    main()
