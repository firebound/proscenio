"""Spritesheet composer for sprite_frame layers (SPEC 006 D10).

Pure Pillow — bpy-free, testable in plain pytest. The importer feeds
this with N frame PNG paths; the composer pads each frame to the
bounding box of the largest frame (transparent fill), pastes them
horizontally into one image, and writes the result to disk.

Output layout
-------------
- Tile size = ``(max_w, max_h)`` across all input frames.
- Each frame is anchored top-left in its tile slot — the smaller frames
  sit flush with the tile's top-left, leaving transparent padding to
  the right and bottom.
- Final image: ``hframes = N``, ``vframes = 1``, dim ``(N * max_w, max_h)``.
- Saved as PNG-RGBA, alpha preserved, no compression tweak.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class SpritesheetResult:
    """Outcome of a spritesheet compose pass."""

    path: Path
    tile_size: tuple[int, int]
    hframes: int
    vframes: int


def compose_spritesheet(
    frame_paths: list[Path],
    output_path: Path,
) -> SpritesheetResult:
    """Pad + concatenate ``frame_paths`` horizontally into one PNG.

    Pads every frame to the bounding box of the largest input frame
    (transparent fill), then pastes left-to-right into a single canvas.

    Raises :class:`ValueError` for empty input.
    Raises :class:`FileNotFoundError` when any frame PNG is missing.
    """
    if not frame_paths:
        raise ValueError("compose_spritesheet requires at least one frame")
    frames: list[Image.Image] = []
    for path in frame_paths:
        if not path.exists():
            raise FileNotFoundError(f"frame PNG not found: {path}")
        frames.append(Image.open(path).convert("RGBA"))
    max_w = max(frame.width for frame in frames)
    max_h = max(frame.height for frame in frames)
    hframes = len(frames)
    sheet = Image.new("RGBA", (max_w * hframes, max_h), (0, 0, 0, 0))
    for idx, frame in enumerate(frames):
        sheet.paste(frame, (idx * max_w, 0), frame)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, "PNG")
    for frame in frames:
        frame.close()
    return SpritesheetResult(
        path=output_path,
        tile_size=(max_w, max_h),
        hframes=hframes,
        vframes=1,
    )
