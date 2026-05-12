"""Generate atlas_pack PNG layers (SPEC 005.1.c packer test fixture).

Run with::

    python scripts/fixtures/atlas_pack/draw_layers.py

Pure Python -- no Blender required. Produces 9 distinct 32x32 PNGs
under ``examples/generated/atlas_pack/pillow_layers/`` (``sprite_1.png`` ..
``sprite_9.png``). Each PNG is a flat-colored square with a bold digit
centered in it so packed-atlas placement is visually verifiable.

The accompanying ``build_blend.py`` runs in headless Blender, loads
these PNGs from disk, and assembles a ``.blend`` with 9 quad meshes,
each on its own material referencing one PNG. That ``.blend`` is the
workbench for testing the Atlas panel: Pack / Apply / Unpack flows
exercise nine distinct sources so atlas layout / padding / POT
behavior is visible.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from _draw import Canvas, fill  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "atlas_pack"
LAYERS_DIR = FIXTURE_DIR / "pillow_layers"

FRAME_W = 32
FRAME_H = 32
SPRITE_COUNT = 9

# Distinct flat colors -- 9 entries, 1-indexed match the digit overlay.
COLORS: tuple[tuple[float, float, float, float], ...] = (
    (0.85, 0.20, 0.20, 1.0),  # 1 red
    (0.95, 0.55, 0.20, 1.0),  # 2 orange
    (0.95, 0.85, 0.20, 1.0),  # 3 yellow
    (0.35, 0.75, 0.30, 1.0),  # 4 green
    (0.30, 0.80, 0.85, 1.0),  # 5 cyan
    (0.25, 0.45, 0.85, 1.0),  # 6 blue
    (0.55, 0.30, 0.80, 1.0),  # 7 purple
    (0.90, 0.45, 0.75, 1.0),  # 8 pink
    (0.55, 0.55, 0.55, 1.0),  # 9 gray
)

DIGIT_COLOR = (20, 20, 24, 255)


def main() -> None:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    font = _load_font(20)
    for idx in range(SPRITE_COUNT):
        canvas = Canvas.empty(FRAME_W, FRAME_H)
        fill(canvas, COLORS[idx])
        _stamp_digit(canvas, str(idx + 1), font)
        canvas.save(LAYERS_DIR / f"sprite_{idx + 1}.png")
    print(f"[draw_atlas_pack] wrote {SPRITE_COUNT} sprites under {LAYERS_DIR}")


def _stamp_digit(canvas: Canvas, digit: str, font: ImageFont.ImageFont) -> None:
    """Centered black digit on top of the flat-colored cell."""
    draw = ImageDraw.Draw(canvas.image)
    bbox = draw.textbbox((0, 0), digit, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (canvas.width - tw) / 2 - bbox[0]
    y = (canvas.height - th) / 2 - bbox[1]
    draw.text((x, y), digit, fill=DIGIT_COLOR, font=font)


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "C:/Windows/Fonts/consolab.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    )
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


if __name__ == "__main__":
    main()
