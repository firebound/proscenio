"""Spritesheet composer for sprite_frame layers (SPEC 006 D10).

Uses ``bpy.types.Image`` + ``numpy`` -- both ship with Blender. Pillow
is intentionally avoided here because it is a dev-only fixture
dependency (SPEC 007 D2 lock) and is not bundled with the addon.

The importer feeds this with N frame PNG paths; the composer pads
each frame to the bounding box of the largest frame (transparent
fill), pastes them horizontally into one image, and writes the result
to disk.

Output layout
-------------
- Tile size = ``(max_w, max_h)`` across all input frames.
- Each frame is anchored top-left in its tile slot.
- Final image: ``hframes = N``, ``vframes = 1``,
  dim ``(N * max_w, max_h)``.
- Saved as PNG-RGBA via ``bpy.types.Image.save``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import bpy
import numpy as np


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
    for path in frame_paths:
        if not path.exists():
            raise FileNotFoundError(f"frame PNG not found: {path}")

    images: list[bpy.types.Image] = []
    try:
        for path in frame_paths:
            images.append(bpy.data.images.load(str(path), check_existing=False))
        max_w = max(img.size[0] for img in images)
        max_h = max(img.size[1] for img in images)
        hframes = len(images)
        # bpy.types.Image.pixels is flat RGBA float, bottom-up row order.
        # Build the canvas in the same convention then write back via
        # foreach_set for a single contiguous transfer.
        canvas = np.zeros((max_h, max_w * hframes, 4), dtype=np.float32)
        for idx, img in enumerate(images):
            w, h = img.size
            pixels = np.empty(w * h * 4, dtype=np.float32)
            img.pixels.foreach_get(pixels)
            tile = pixels.reshape(h, w, 4)
            # Top-left anchor in PSD convention. bpy is bottom-up, so
            # "top of tile" = upper rows of the canvas slice.
            row_offset = max_h - h
            col_offset = idx * max_w
            canvas[row_offset : row_offset + h, col_offset : col_offset + w] = tile

        output_path.parent.mkdir(parents=True, exist_ok=True)
        sheet_name = f"{output_path.stem}_compose_tmp"
        sheet_img = bpy.data.images.new(
            sheet_name,
            width=max_w * hframes,
            height=max_h,
            alpha=True,
        )
        try:
            sheet_img.pixels.foreach_set(canvas.flatten())
            sheet_img.filepath_raw = str(output_path)
            sheet_img.file_format = "PNG"
            sheet_img.save()
        finally:
            bpy.data.images.remove(sheet_img)
        return SpritesheetResult(
            path=output_path,
            tile_size=(max_w, max_h),
            hframes=hframes,
            vframes=1,
        )
    finally:
        for img in images:
            bpy.data.images.remove(img)
