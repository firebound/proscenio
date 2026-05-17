"""Per-pixel coverage measurement + hole-bleed bookkeeping.

CPU-hot path of the validator: for every source pixel, decide
covered / leaked / hole-bleed against the generated mesh's triangle
list + paint the per-pixel debug PNG. Helpers are extracted to keep
the inner loop flat (cognitive complexity under 15 per function
after the cleanup of step 8).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import bpy  # type: ignore[import-not-found]

from core.geometry_2d import point_in_triangle_xz

if TYPE_CHECKING:
    Triangle = tuple[tuple[float, float], tuple[float, float], tuple[float, float]]


_DEBUG_COLOUR_COVERED = (0, 200, 0, 255)
_DEBUG_COLOUR_LEAK = (255, 0, 0, 255)
_DEBUG_COLOUR_HOLE_BLEED = (0, 100, 255, 255)


@dataclass(frozen=True)
class CoverageContext:
    """Pre-computed per-image values that every pixel classification needs.

    Bundles the alpha buffer + triangle list + hole mask + world-coord
    scaling constants + the debug image buffer in a single read-only
    record so the inner loop helpers stay under the parameter limit.
    """

    w: int
    h: int
    pixels: list[float]
    triangles: list[
        tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
    ]
    hole_mask: list[list[bool]]
    world_scale: float
    half_w: float
    half_h: float
    half_cell: float
    debug_image: list[int] | None


def compute_hole_pixel_mask(pixels: list[float], w: int, h: int) -> list[list[bool]]:
    """True for transparent pixels fully enclosed by alpha foreground.

    Flood-fills transparent pixels reachable from the image border;
    the remainder are alpha holes. Mirrors the bridge-side
    ``alpha_contour.extract_holes`` logic but operates on the raw
    full-resolution pixel grid (no downscaling) so the validator
    measures against ground truth, not the operator's downsampled
    view.
    """
    transparent: list[list[bool]] = [
        [int(pixels[(y * w + x) * 4 + 3] * 255) <= 0 for x in range(w)]
        for y in range(h)
    ]
    visited: list[list[bool]] = [[False] * w for _ in range(h)]
    stack: list[tuple[int, int]] = []
    for x in range(w):
        if transparent[0][x]:
            stack.append((x, 0))
        if transparent[h - 1][x]:
            stack.append((x, h - 1))
    for y in range(h):
        if transparent[y][0]:
            stack.append((0, y))
        if transparent[y][w - 1]:
            stack.append((w - 1, y))
    while stack:
        x, y = stack.pop()
        if not (0 <= x < w and 0 <= y < h):
            continue
        if visited[y][x] or not transparent[y][x]:
            continue
        visited[y][x] = True
        stack.append((x + 1, y))
        stack.append((x - 1, y))
        stack.append((x, y + 1))
        stack.append((x, y - 1))
    return [
        [transparent[y][x] and not visited[y][x] for x in range(w)] for y in range(h)
    ]


def _paint_debug_pixel(
    debug_image: list[int] | None,
    pixel_index: int,
    rgba: tuple[int, int, int, int],
) -> None:
    """Write one RGBA pixel into the flat debug-image buffer."""
    if debug_image is None:
        return
    idx = pixel_index * 4
    debug_image[idx] = rgba[0]
    debug_image[idx + 1] = rgba[1]
    debug_image[idx + 2] = rgba[2]
    debug_image[idx + 3] = rgba[3]


def _pixel_world_coords(x: int, y: int, ctx: CoverageContext) -> tuple[float, float]:
    """Cell-center world coords for source pixel ``(x, y)``.

    Matches the mesh's ``pixel_contour_to_world`` cell-center placement
    + the bridge's Y-flip-on-read convention so the validator measures
    against the same geometry the operator built.
    """
    visual_y = ctx.h - 1 - y
    wx = x * ctx.world_scale - ctx.half_w + ctx.half_cell
    wz = ctx.half_h - visual_y * ctx.world_scale - ctx.half_cell
    return wx, wz


def _classify_pixel(
    x: int,
    y: int,
    ctx: CoverageContext,
    leaks_records: list[dict[str, object]],
    quadrants: dict[str, int],
) -> tuple[int, int]:
    """Classify pixel ``(x, y)`` against the mesh + paint the debug buffer.

    Returns ``(fg_increment, bleed_increment)``. Leak records +
    quadrant counts mutate in-place via the passed-in collections.
    """
    alpha = int(ctx.pixels[(y * ctx.w + x) * 4 + 3] * 255)
    pixel_index = y * ctx.w + x
    wx, wz = _pixel_world_coords(x, y, ctx)
    inside_any = any(point_in_triangle_xz((wx, wz), t) for t in ctx.triangles)
    if alpha <= 0:
        # Transparent pixel. Only count as "hole bleed" when it sits
        # inside the alpha silhouette (= part of a detected hole).
        # Exterior transparent covered by mesh is the expected
        # safety-margin band from the 1-cell dilate + MAX downsample.
        if inside_any and ctx.hole_mask[y][x]:
            _paint_debug_pixel(ctx.debug_image, pixel_index, _DEBUG_COLOUR_HOLE_BLEED)
            return 0, 1
        return 0, 0
    if inside_any:
        _paint_debug_pixel(ctx.debug_image, pixel_index, _DEBUG_COLOUR_COVERED)
        return 1, 0
    _paint_debug_pixel(ctx.debug_image, pixel_index, _DEBUG_COLOUR_LEAK)
    visual_y = ctx.h - 1 - y
    quadrant = ("T" if visual_y > ctx.h / 2 else "B") + ("L" if x < ctx.w / 2 else "R")
    quadrants[quadrant] += 1
    leaks_records.append(
        {
            "pixel_x": x,
            "pixel_y_storage": y,
            "pixel_y_visual_pil": visual_y,
            "alpha": alpha,
            "world_x": round(wx, 6),
            "world_z": round(wz, 6),
            "quadrant": quadrant,
        }
    )
    return 1, 0


def write_debug_png(path: Path, w: int, h: int, rgba_bytes: list[int]) -> None:
    """Write an RGBA image to ``path`` via Blender's image API.

    Pure-Blender (no PIL dep at validate time). Pixels are written
    in Blender's bottom-up convention; since our debug_image was
    populated using ``y`` iterated in storage order (also bottom-up),
    the visual output matches the source image orientation pixel-for-
    pixel.
    """
    name = f"_debug_{path.stem}"
    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name])
    img = bpy.data.images.new(name, width=w, height=h, alpha=True)
    img.pixels[:] = [c / 255.0 for c in rgba_bytes]
    img.filepath_raw = str(path)
    img.file_format = "PNG"
    img.save()


def measure_coverage(
    image: bpy.types.Image,
    triangles: list[
        tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
    ],
    debug_png_path: Path | None = None,
) -> tuple[float, int, list[dict[str, object]], dict[str, int], int]:
    """Exhaustive per-pixel coverage + hole-bleed measurement.

    Returns ``(coverage_pct, leak_count, leak_records, quadrants, bleed_count)``.
    See ``_classify_pixel`` for the three-way classification each
    pixel goes through.
    """
    pixels = list(image.pixels[:])
    w, h = image.size[0], image.size[1]
    world_scale = 1.0 / 100.0
    ctx = CoverageContext(
        w=w,
        h=h,
        pixels=pixels,
        triangles=triangles,
        hole_mask=compute_hole_pixel_mask(pixels, w, h),
        world_scale=world_scale,
        half_w=w * world_scale / 2.0,
        half_h=h * world_scale / 2.0,
        half_cell=world_scale / 2.0,
        debug_image=[0, 0, 0, 0] * (w * h) if debug_png_path is not None else None,
    )

    fg = 0
    bleed_count = 0
    leaks_records: list[dict[str, object]] = []
    quadrants = {"TL": 0, "TR": 0, "BL": 0, "BR": 0}
    for y in range(h):
        for x in range(w):
            fg_inc, bleed_inc = _classify_pixel(x, y, ctx, leaks_records, quadrants)
            fg += fg_inc
            bleed_count += bleed_inc

    if ctx.debug_image is not None and debug_png_path is not None:
        write_debug_png(debug_png_path, w, h, ctx.debug_image)

    coverage = 1.0 - (len(leaks_records) / fg) if fg else 1.0
    return (coverage, len(leaks_records), leaks_records, quadrants, bleed_count)
