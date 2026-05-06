"""Pillow-based shape rasterizer used by the SPEC 007 fixture PNG draws.

Pure Python — runs **without Blender** (just Python + Pillow). The
fixture builders are split into two stages:

1. ``draw_<fixture>.py`` (this layer) — generates PNGs via Pillow.
   Run with ``python scripts/fixtures/draw_<fixture>.py``.
2. ``build_<fixture>.py`` — assembles the ``.blend`` via bpy, loading
   the PNGs from disk. Run with ``blender --background --python ...``.

This split lets a developer iterate on visuals without booting Blender
and lets the PNG generation be exercised in plain pytest if needed.

Coordinate convention
---------------------
Matches Pillow native: ``y = 0`` is the **top** row of the canvas.
Saved PNGs preserve this orientation — opening the file in Photoshop
or a browser shows pixel ``(0, 0)`` at the top-left, which is also
how Blender's UV editor displays the image once loaded.

API surface
-----------
- :class:`Canvas` — wraps ``PIL.Image`` + ``ImageDraw``. Construct with
  ``Canvas(width, height)``; saved via ``canvas.save(path)``.
- Free functions ``fill``, ``rect``, ``border``, ``circle``,
  ``triangle``, ``trapezoid`` — operate on a Canvas.

Colors are RGBA float tuples ``(r, g, b, a)`` in ``[0, 1]``, matching
the rest of the codebase. Pillow internally wants ``(0..255, ..., 0..255)``;
the helpers convert.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

RGBA = tuple[float, float, float, float]


def _to_pil_color(color: RGBA) -> tuple[int, int, int, int]:
    """Convert a float RGBA in [0,1] to Pillow's 8-bit tuple."""
    return (
        max(0, min(255, int(color[0] * 255 + 0.5))),
        max(0, min(255, int(color[1] * 255 + 0.5))),
        max(0, min(255, int(color[2] * 255 + 0.5))),
        max(0, min(255, int(color[3] * 255 + 0.5))),
    )


@dataclass
class Canvas:
    """RGBA Pillow-backed canvas. ``y = 0`` is the **top** row."""

    width: int
    height: int
    image: Image.Image
    draw: ImageDraw.ImageDraw

    @classmethod
    def empty(cls, width: int, height: int) -> "Canvas":
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        return cls(width=width, height=height, image=image, draw=ImageDraw.Draw(image))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.image.save(str(path), "PNG")


def fill(canvas: Canvas, color: RGBA) -> None:
    """Paint every pixel with ``color``."""
    canvas.draw.rectangle(
        [(0, 0), (canvas.width - 1, canvas.height - 1)],
        fill=_to_pil_color(color),
    )


def rect(canvas: Canvas, x: int, y: int, w: int, h: int, color: RGBA) -> None:
    """Filled axis-aligned rectangle. ``(x, y)`` is the top-left corner."""
    canvas.draw.rectangle(
        [(x, y), (x + w - 1, y + h - 1)],
        fill=_to_pil_color(color),
    )


def border(canvas: Canvas, color: RGBA, thickness: int = 1) -> None:
    """Draw a rectangular border around the entire canvas."""
    canvas.draw.rectangle(
        [(0, 0), (canvas.width - 1, canvas.height - 1)],
        outline=_to_pil_color(color),
        width=thickness,
    )


def circle(canvas: Canvas, cx: float, cy: float, radius: float, color: RGBA) -> None:
    """Filled circle centered at ``(cx, cy)``."""
    canvas.draw.ellipse(
        [(cx - radius, cy - radius), (cx + radius, cy + radius)],
        fill=_to_pil_color(color),
    )


def triangle(
    canvas: Canvas,
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    color: RGBA,
) -> None:
    """Filled triangle from three pixel-space points."""
    canvas.draw.polygon([p0, p1, p2], fill=_to_pil_color(color))


def trapezoid(
    canvas: Canvas,
    x: float,
    y: float,
    top_w: float,
    bottom_w: float,
    h: float,
    color: RGBA,
) -> None:
    """Filled isoceles trapezoid. ``(x, y)`` is the top-left of the top edge.

    The trapezoid widens downward when ``bottom_w > top_w`` (typical
    pelvis silhouette: narrower at top, wider at hips).
    """
    top_left = (x + (bottom_w - top_w) / 2.0, y)
    top_right = (x + (bottom_w + top_w) / 2.0, y)
    bottom_left = (x, y + h)
    bottom_right = (x + bottom_w, y + h)
    canvas.draw.polygon(
        [top_left, top_right, bottom_right, bottom_left],
        fill=_to_pil_color(color),
    )
