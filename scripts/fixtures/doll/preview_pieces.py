"""Contact sheet of every doll sprite PNG (SPEC 007 fixture review).

Run with::

    python scripts/fixtures/preview_doll_pieces.py

Pure Pillow. Walks ``examples/authored/doll/layers/`` and tiles every PNG into
a single sheet with name labels — handy for eyeballing each piece in
isolation alongside the full-body composite preview.

Output: ``examples/authored/doll/doll_pieces_sheet.png``.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[3]
LAYERS_DIR = (
    REPO_ROOT / "examples" / "authored" / "doll" / "01_to_photoshop" / "render_layers"
)
OUT_PATH = LAYERS_DIR / "pieces_sheet.png"

SHEET_W = 1280
CELL_PAD_X = 12
CELL_PAD_Y = 28  # extra room below sprite for the label
CELL_W = 128
CELL_H = 140
COLS = SHEET_W // CELL_W
BACKGROUND = (32, 32, 38, 255)
CELL_BG = (52, 52, 60, 255)
LABEL = (220, 220, 224, 255)


def main() -> None:
    paths = sorted(LAYERS_DIR.glob("*.png"))
    if not paths:
        print(f"[preview_doll_pieces] no PNGs found in {LAYERS_DIR}")
        return
    rows = (len(paths) + COLS - 1) // COLS
    sheet_h = rows * CELL_H + CELL_PAD_Y
    sheet = Image.new("RGBA", (SHEET_W, sheet_h), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    font = _load_font(14)

    for idx, path in enumerate(paths):
        col = idx % COLS
        row = idx // COLS
        cell_x = col * CELL_W
        cell_y = row * CELL_H
        # Cell background (subtle so sprites pop)
        draw.rectangle(
            [(cell_x + 4, cell_y + 4), (cell_x + CELL_W - 4, cell_y + CELL_H - 8)],
            fill=CELL_BG,
        )
        sprite = Image.open(path).convert("RGBA")
        sw, sh = sprite.size
        max_w = CELL_W - CELL_PAD_X * 2
        max_h = CELL_H - CELL_PAD_Y - 8
        scale = min(max_w / max(sw, 1), max_h / max(sh, 1), 4.0)
        scale = max(scale, 1.0) if max(sw, sh) < 24 else min(scale, 2.5)
        scaled_w = max(1, int(sw * scale))
        scaled_h = max(1, int(sh * scale))
        if (scaled_w, scaled_h) != (sw, sh):
            sprite = sprite.resize((scaled_w, scaled_h), Image.NEAREST)
        paste_x = cell_x + (CELL_W - scaled_w) // 2
        paste_y = cell_y + 6 + (max_h - scaled_h) // 2
        sheet.alpha_composite(sprite, (paste_x, paste_y))
        label = path.stem
        text_w = draw.textlength(label, font=font)
        draw.text(
            (cell_x + (CELL_W - text_w) / 2, cell_y + CELL_H - 22),
            label,
            fill=LABEL,
            font=font,
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT_PATH, "PNG")
    print(f"[preview_doll_pieces] {len(paths)} sprite(s) -> {OUT_PATH}")


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


if __name__ == "__main__":
    main()
