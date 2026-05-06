"""Pure-Python shape rasterizer used by the SPEC 007 fixture builders.

Every fixture's PNGs come out of geometric primitives drawn into a flat
RGBA float list (one entry per pixel × 4 channels, bottom-up to match
``bpy.types.Image.pixels`` semantics).

No external dependencies (no Pillow, no numpy needed) — Blender bundles
everything via bpy and stdlib. Designed to be readable: 5 shape primitives
plus a save helper, ~150 LOC total.

Coordinate convention: ``(0, 0)`` is bottom-left of the canvas, matching
Blender's UV origin and ``Image.pixels`` row order.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

RGBA = tuple[float, float, float, float]


@dataclass
class Canvas:
    """RGBA float canvas. ``pixels`` flat row-major, bottom-up."""

    width: int
    height: int
    pixels: list[float]

    @classmethod
    def empty(cls, width: int, height: int) -> "Canvas":
        return cls(width=width, height=height, pixels=[0.0] * (width * height * 4))

    def set(self, x: int, y: int, color: RGBA) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 4
            self.pixels[i] = color[0]
            self.pixels[i + 1] = color[1]
            self.pixels[i + 2] = color[2]
            self.pixels[i + 3] = color[3]


def fill(canvas: Canvas, color: RGBA) -> None:
    """Paint every pixel with ``color``."""
    for y in range(canvas.height):
        for x in range(canvas.width):
            canvas.set(x, y, color)


def rect(canvas: Canvas, x: int, y: int, w: int, h: int, color: RGBA) -> None:
    """Filled axis-aligned rectangle. ``(x, y)`` is the bottom-left corner."""
    for ry in range(max(0, y), min(canvas.height, y + h)):
        for rx in range(max(0, x), min(canvas.width, x + w)):
            canvas.set(rx, ry, color)


def border(canvas: Canvas, color: RGBA, thickness: int = 1) -> None:
    """Draw a rectangular border around the entire canvas."""
    for t in range(thickness):
        rect(canvas, t, t, canvas.width - 2 * t, 1, color)
        rect(canvas, t, canvas.height - 1 - t, canvas.width - 2 * t, 1, color)
        rect(canvas, t, t, 1, canvas.height - 2 * t, color)
        rect(canvas, canvas.width - 1 - t, t, 1, canvas.height - 2 * t, color)


def circle(canvas: Canvas, cx: float, cy: float, radius: float, color: RGBA) -> None:
    """Filled circle centered at ``(cx, cy)`` with the given ``radius``."""
    r2 = radius * radius
    x_min = max(0, int(cx - radius - 1))
    x_max = min(canvas.width, int(cx + radius + 1))
    y_min = max(0, int(cy - radius - 1))
    y_max = min(canvas.height, int(cy + radius + 1))
    for y in range(y_min, y_max):
        for x in range(x_min, x_max):
            dx = x + 0.5 - cx
            dy = y + 0.5 - cy
            if dx * dx + dy * dy <= r2:
                canvas.set(x, y, color)


def triangle(
    canvas: Canvas,
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    color: RGBA,
) -> None:
    """Filled triangle via simple barycentric scanline. Three pixel-space points."""
    xs = [p0[0], p1[0], p2[0]]
    ys = [p0[1], p1[1], p2[1]]
    x_min = max(0, int(min(xs)))
    x_max = min(canvas.width, int(max(xs)) + 1)
    y_min = max(0, int(min(ys)))
    y_max = min(canvas.height, int(max(ys)) + 1)
    for y in range(y_min, y_max):
        for x in range(x_min, x_max):
            if _point_in_triangle(x + 0.5, y + 0.5, p0, p1, p2):
                canvas.set(x, y, color)


def trapezoid(
    canvas: Canvas,
    x: float,
    y: float,
    bottom_w: float,
    top_w: float,
    h: float,
    color: RGBA,
) -> None:
    """Filled isoceles trapezoid. ``(x, y)`` is the bottom-left of the bottom edge."""
    bottom_left = (x, y)
    bottom_right = (x + bottom_w, y)
    top_left = (x + (bottom_w - top_w) / 2.0, y + h)
    top_right = (x + (bottom_w + top_w) / 2.0, y + h)
    triangle(canvas, bottom_left, bottom_right, top_right, color)
    triangle(canvas, bottom_left, top_right, top_left, color)


def _point_in_triangle(
    px: float,
    py: float,
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
) -> bool:
    """Sign-based point-in-triangle test."""
    s1 = _sign(px, py, p0, p1)
    s2 = _sign(px, py, p1, p2)
    s3 = _sign(px, py, p2, p0)
    has_neg = s1 < 0 or s2 < 0 or s3 < 0
    has_pos = s1 > 0 or s2 > 0 or s3 > 0
    return not (has_neg and has_pos)


def _sign(
    px: float,
    py: float,
    p0: tuple[float, float],
    p1: tuple[float, float],
) -> float:
    return (px - p1[0]) * (p0[1] - p1[1]) - (p0[0] - p1[0]) * (py - p1[1])


def save_as_png(canvas: Canvas, name: str, out_path: Path) -> Any:
    """Persist ``canvas`` to a PNG via ``bpy.data.images``. Returns the Image."""
    import bpy

    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name])
    img = bpy.data.images.new(
        name=name, width=canvas.width, height=canvas.height, alpha=True
    )
    img.pixels.foreach_set(canvas.pixels)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.filepath_raw = str(out_path)
    img.file_format = "PNG"
    img.save()
    return img
