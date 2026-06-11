"""Atlas image assembly + manifest write.

Bpy-bound: the function lazily imports ``bpy`` + ``numpy`` so pytest
contexts that import the parent package without Blender don't break.

Idempotency contract. ``compose_atlas`` snapshots every source image's
pixel buffer into NumPy *before* it removes the existing
``bpy.data.images`` entry with the same name. That detaches the
function from the StructRNA reference, so a packed atlas that is the
*source* of the next pack no longer crashes mid-loop.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...atlas.atlas_packer import PackResult, Rect
from ...atlas.edge_extend import edge_extend_ring
from .._shared.image_canvas import save_rgba_canvas_as_png
from .atlas_collect import SourceImage


def compose_atlas(
    sources: list[SourceImage],
    packed: PackResult,
    out_path: Path,
    padding: int = 2,
) -> Any:
    """Build a single bpy.types.Image holding every packed source and save it.

    Pixels are RGBA float32. Each placement's reserved ``padding`` ring is
    filled by edge-extending its border pixels (alpha bleed), so bilinear
    filtering does not seam transparency into the sprite under it.

    Tolerates the case where ``src.image`` is the same image being
    overwritten: source pixel arrays are copied into NumPy **before** the
    existing atlas image is removed from ``bpy.data.images``, so the
    mid-loop ``StructRNA of type Image has been removed`` error cannot happen.

    Returns the new ``bpy.types.Image``.
    """
    import bpy  # local import - module must remain importable from non-bpy contexts
    import numpy as np

    # Snapshot every source's pixels into NumPy *before* mutating bpy.data.images,
    # so removing a same-named existing atlas cannot invalidate a source mid-loop.
    placed_sources: list[tuple[SourceImage, Rect, np.ndarray]] = []
    for src in sources:
        rect: Rect | None = packed.placements.get(src.obj_name)
        if rect is None:
            continue
        try:
            pixels = np.array(src.image.pixels[:], dtype=np.float32).reshape(
                src.height, src.width, 4
            )
        except (ReferenceError, AttributeError):
            # Source image already invalidated; skip - the caller's
            # validation path surfaces this as a warning.
            continue
        placed_sources.append((src, rect, pixels))

    name = out_path.stem
    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name])

    canvas: np.ndarray = np.zeros((packed.atlas_h, packed.atlas_w, 4), dtype=np.float32)

    # Coordinate systems: packer slots are top-down (y=0 = top); both
    # ``bpy.types.Image.pixels`` and the UV-derived ``slice_px`` are bottom-up
    # (row 0 = bottom). Slice in bottom-up space, then convert each slot's
    # top-down y to a bottom-up canvas row before pasting.
    for src, rect, src_pixels in placed_sources:
        sx, sy_bu, sw, sh = src.slice_px
        sliced = src_pixels[sy_bu : sy_bu + sh, sx : sx + sw]
        # Defensive clamp in case the slice rect is slightly larger than the
        # placement (rounding from the packer's padding bookkeeping).
        h = min(rect.h, sliced.shape[0])
        w = min(rect.w, sliced.shape[1])
        slot_y_bu = packed.atlas_h - rect.y - rect.h
        canvas[slot_y_bu : slot_y_bu + h, rect.x : rect.x + w] = sliced[:h, :w]
        edge_extend_ring(canvas, slot_y_bu, rect.x, h, w, padding, packed.atlas_w, packed.atlas_h)

    return save_rgba_canvas_as_png(name, canvas, out_path)


def write_manifest(
    packed: PackResult,
    padding: int,
    sources: list[SourceImage],
    manifest_path: Path,
) -> None:
    """Persist the pack result + source slice metadata as JSON.

    ``format_version`` 1 carries ``source_w/h`` and ``slice_x/y/w/h`` per
    placement (when the source image is known) so ``apply_packed_atlas``
    can rewrite UVs (mesh) and ``texture_region`` (sprite) correctly when
    the source was a shared atlas (slice_px != full image).
    """
    by_name = {src.obj_name: src for src in sources}
    placements_payload: dict[str, Any] = {}
    for name, r in packed.placements.items():
        src = by_name.get(name)
        entry: dict[str, Any] = {"x": r.x, "y": r.y, "w": r.w, "h": r.h}
        if src is not None:
            sx, sy, sw, sh = src.slice_px
            entry.update(
                {
                    "source_w": src.width,
                    "source_h": src.height,
                    "slice_x": sx,
                    "slice_y": sy,
                    "slice_w": sw,
                    "slice_h": sh,
                }
            )
        placements_payload[name] = entry
    payload: dict[str, Any] = {
        "format_version": 1,
        "atlas_w": packed.atlas_w,
        "atlas_h": packed.atlas_h,
        "padding": padding,
        "placements": placements_payload,
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
