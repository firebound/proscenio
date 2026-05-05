"""Generate the effect placeholder atlas.

Run once to (re)create `atlas.png`. The image is 64×16 — a horizontal strip of
four 16×16 frames demonstrating a frame-by-frame animation cycle:

    [ frame 0 ] [ frame 1 ] [ frame 2 ] [ frame 3 ]
       red       yellow      green       blue

The shape inside each frame grows from a small dot to a larger square, then
shrinks back. This makes the frame transitions visible at a glance during
manual inspection — no animation tooling needed to spot a misordered import.

Requires Pillow:

    python examples/effect/generate_atlas.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ATLAS_SIZE = (64, 16)
FRAME_SIZE = 16
FRAME_COUNT = 4
DEBUG_BG = (255, 0, 255, 255)  # magenta — anything off-grid is "wrong"

# (frame index, fill color, inset from frame edge in pixels)
FRAMES: list[tuple[int, tuple[int, int, int, int], int]] = [
    (0, (220, 70, 70, 255), 6),
    (1, (220, 200, 70, 255), 4),
    (2, (90, 200, 90, 255), 2),
    (3, (70, 130, 220, 255), 4),
]


def main() -> None:
    img = Image.new("RGBA", ATLAS_SIZE, DEBUG_BG)
    draw = ImageDraw.Draw(img)

    for index, color, inset in FRAMES:
        x = index * FRAME_SIZE
        draw.rectangle((x, 0, x + FRAME_SIZE - 1, FRAME_SIZE - 1), fill=(0, 0, 0, 255))
        draw.rectangle(
            (x + inset, inset, x + FRAME_SIZE - 1 - inset, FRAME_SIZE - 1 - inset),
            fill=color,
        )

    out = Path(__file__).parent / "atlas.png"
    img.save(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
