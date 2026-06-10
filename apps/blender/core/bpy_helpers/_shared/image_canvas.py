"""Shared bpy image-canvas writer: float32 RGBA canvas -> saved PNG image.

bpy-bound, but ``bpy`` is imported lazily inside the function so the
module stays importable from the non-bpy pytest contexts that pull in the
parent package.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

    import numpy as np


def save_rgba_canvas_as_png(name: str, canvas: np.ndarray, out_path: Path) -> Any:
    """Create a new RGBA ``bpy.types.Image`` from a ``(H, W, 4)`` float32
    canvas, write it to ``out_path`` as PNG, and return the image.

    Dimensions come from ``canvas.shape`` (height, width). The caller owns
    the returned image's lifetime: the packed atlas keeps it in
    ``bpy.data`` (it is the real output datablock), while the spritesheet
    composer removes it once saved (a throwaway temp). The caller must
    also clear any pre-existing same-name image first when the name has to
    be exact (``bpy.data.images.new`` auto-suffixes ``.001`` otherwise).

    On a write/save failure the half-created datablock is removed before
    the error propagates, so neither caller leaks an image into
    ``bpy.data``; the original exception is re-raised unchanged.
    """
    import bpy  # local import - module must remain importable from non-bpy contexts

    height, width = int(canvas.shape[0]), int(canvas.shape[1])
    image = bpy.data.images.new(name=name, width=width, height=height, alpha=True)
    try:
        image.pixels.foreach_set(canvas.flatten())
        image.filepath_raw = str(out_path)
        image.file_format = "PNG"
        image.save()
    except Exception:
        bpy.data.images.remove(image)
        raise
    return image
