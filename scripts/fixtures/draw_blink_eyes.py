"""Generate the blink_eyes PNG layers (SPEC 007 step 1, Pillow only).

Run with::

    python scripts/fixtures/draw_blink_eyes.py

Pure Python — no Blender required. Produces:

- ``examples/blink_eyes/layers/eye_0.png`` … ``eye_3.png`` (32×32 each)
- ``examples/blink_eyes/eye_spritesheet.png`` (128×32, 4 frames horizontal)

The accompanying ``build_blink_eyes.py`` runs in headless Blender,
loads these PNGs from disk, and assembles the ``.blend``.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _draw import Canvas, circle, rect  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "examples" / "blink_eyes"
LAYERS_DIR = FIXTURE_DIR / "layers"
SHEET_PATH = FIXTURE_DIR / "eye_spritesheet.png"

FRAME_W = 32
FRAME_H = 32
HFRAMES = 4
VFRAMES = 1
SHEET_W = FRAME_W * HFRAMES
SHEET_H = FRAME_H * VFRAMES

WHITE = (0.95, 0.95, 0.95, 1.0)
PUPIL = (0.10, 0.10, 0.10, 1.0)
TRANSPARENT = (0.0, 0.0, 0.0, 0.0)

# (frame_index, eye_open_height_ratio) — 1.0 fully open, 0.0 fully closed.
FRAMES: tuple[tuple[int, float], ...] = (
    (0, 1.0),
    (1, 0.6),
    (2, 0.2),
    (3, 0.0),
)


def main() -> None:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    _generate_per_frame_pngs()
    _generate_spritesheet()
    print(f"[draw_blink_eyes] wrote {len(FRAMES)} frames under {LAYERS_DIR}")
    print(f"[draw_blink_eyes] wrote spritesheet {SHEET_PATH}")


def _draw_eye_frame(canvas: Canvas, open_ratio: float) -> None:
    """White iris + dark pupil, vertically clipped by ``open_ratio``."""
    cx = canvas.width / 2.0
    cy = canvas.height / 2.0
    iris_r = canvas.width / 2.0 - 2
    pupil_r = iris_r * 0.4
    open_h = (canvas.height * open_ratio) / 2.0
    circle(canvas, cx, cy, iris_r, WHITE)
    circle(canvas, cx, cy, pupil_r, PUPIL)
    # Vertical clip: paint transparent rectangles above / below the open extent.
    if open_h < canvas.height / 2.0:
        clip = max(0, int(cy - open_h))
        rect(canvas, 0, 0, canvas.width, clip, TRANSPARENT)
        rect(canvas, 0, canvas.height - clip, canvas.width, clip, TRANSPARENT)


def _generate_per_frame_pngs() -> None:
    for idx, open_ratio in FRAMES:
        canvas = Canvas.empty(FRAME_W, FRAME_H)
        _draw_eye_frame(canvas, open_ratio)
        canvas.save(LAYERS_DIR / f"eye_{idx}.png")


def _generate_spritesheet() -> None:
    sheet = Canvas.empty(SHEET_W, SHEET_H)
    for idx, open_ratio in FRAMES:
        sub = Canvas.empty(FRAME_W, FRAME_H)
        _draw_eye_frame(sub, open_ratio)
        sheet.image.paste(sub.image, (idx * FRAME_W, 0))
    sheet.save(SHEET_PATH)


if __name__ == "__main__":
    main()
