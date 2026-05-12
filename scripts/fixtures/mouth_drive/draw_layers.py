"""Generate mouth_drive PNG layers + spritesheet (Pillow only).

Run with::

    py scripts/fixtures/mouth_drive/draw_layers.py

Pure Python -- no Blender required. Produces:

- ``examples/generated/mouth_drive/pillow_layers/mouth_0.png`` ... ``mouth_3.png`` (32x32 each)
- ``examples/generated/mouth_drive/pillow_layers/mouth_spritesheet.png`` (128x32, 4 frames horizontal)

Frames: 0=open, 1=mid-open, 2=closed line, 3=open-talking.
Stylized, just enough visual diff between cells to validate
``Drive from Bone`` -> ``proscenio.frame`` swapping.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from _draw import Canvas, capsule, circle, rect  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "mouth_drive"
LAYERS_DIR = FIXTURE_DIR / "pillow_layers"
SHEET_PATH = LAYERS_DIR / "mouth_spritesheet.png"

FRAME_W = 32
FRAME_H = 32
HFRAMES = 4
VFRAMES = 1
SHEET_W = FRAME_W * HFRAMES
SHEET_H = FRAME_H * VFRAMES

LIP = (0.85, 0.30, 0.30, 1.0)
INSIDE = (0.20, 0.05, 0.10, 1.0)
TONGUE = (0.95, 0.45, 0.45, 1.0)
TRANSPARENT = (0.0, 0.0, 0.0, 0.0)

# Frame index -> (mouth_open_height_ratio, has_tongue)
FRAMES: tuple[tuple[int, float, bool], ...] = (
    (0, 0.7, False),  # open
    (1, 0.4, True),   # mid-open with tongue
    (2, 0.05, False),  # closed (lip line)
    (3, 0.6, True),   # talking shape
)


def main() -> None:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    _generate_per_frame_pngs()
    _generate_spritesheet()
    print(f"[draw_mouth_drive] wrote {len(FRAMES)} frames under {LAYERS_DIR}")
    print(f"[draw_mouth_drive] wrote spritesheet {SHEET_PATH}")


def _draw_mouth_frame(canvas: Canvas, open_ratio: float, has_tongue: bool) -> None:
    """Stylized mouth: outer lip ellipse + dark inside + optional tongue dot."""
    cx = canvas.width / 2.0
    cy = canvas.height / 2.0
    lip_w = canvas.width - 6
    lip_h = max(2.0, canvas.height * open_ratio)

    # Outer lip ellipse (approximated by capsule + clip)
    capsule(canvas, LIP, padding=3)
    # Clip vertically to open_ratio
    if open_ratio < 1.0:
        clip = int(canvas.height / 2.0 - lip_h / 2.0)
        if clip > 0:
            rect(canvas, 0, 0, canvas.width, clip, TRANSPARENT)
            rect(canvas, 0, canvas.height - clip, canvas.width, clip, TRANSPARENT)

    # Inside dark fill (slightly smaller than lip)
    if lip_h > 4:
        inside_w = max(2, int(lip_w - 6))
        inside_h = max(2, int(lip_h - 4))
        ix = int(cx - inside_w / 2)
        iy = int(cy - inside_h / 2)
        rect(canvas, ix, iy, inside_w, inside_h, INSIDE)

    # Tongue dot (lower half center)
    if has_tongue and lip_h > 6:
        tongue_r = max(2.0, lip_h * 0.25)
        circle(canvas, cx, cy + lip_h * 0.15, tongue_r, TONGUE)


def _generate_per_frame_pngs() -> None:
    for idx, open_ratio, has_tongue in FRAMES:
        canvas = Canvas.empty(FRAME_W, FRAME_H)
        _draw_mouth_frame(canvas, open_ratio, has_tongue)
        canvas.save(LAYERS_DIR / f"mouth_{idx}.png")


def _generate_spritesheet() -> None:
    sheet = Canvas.empty(SHEET_W, SHEET_H)
    for idx, open_ratio, has_tongue in FRAMES:
        sub = Canvas.empty(FRAME_W, FRAME_H)
        _draw_mouth_frame(sub, open_ratio, has_tongue)
        sheet.image.paste(sub.image, (idx * FRAME_W, 0))
    sheet.save(SHEET_PATH)


if __name__ == "__main__":
    main()
