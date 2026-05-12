"""Atlas image assembly + manifest write (SPEC 009 wave 9.10 split of atlas_io).

Bpy-bound: the function lazily imports ``bpy`` + ``numpy`` so pytest
contexts that import the parent package without Blender don't break.

Idempotency contract. ``compose_atlas`` snapshots every source image's
pixel buffer into NumPy *before* it removes the existing
``bpy.data.images`` entry with the same name. That detaches the
function from the StructRNA reference, so the case where a packed
atlas is the *source* of the next pack (true on second-pack-after-apply)
no longer crashes mid-loop.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..atlas_packer import PackResult, Rect
from .atlas_collect import SourceImage


def compose_atlas(
    sources: list[SourceImage],
    packed: PackResult,
    out_path: Path,
    padding: int = 2,
) -> Any:
    """Build a single bpy.types.Image holding every packed source and save it.

    Pixels are RGBA float32. Padding pixels are left transparent
    (alpha=0) in this iteration - edge-extend padding to combat
    bilinear bleeding can be added later without changing the operator
    surface.

    Idempotency note. The function tolerates the case where
    ``src.image`` is the same image we are about to overwrite (true on
    second pack runs after the first apply linked every sprite to the
    shared packed atlas). Source pixel arrays are copied into NumPy
    upfront - **before** the existing atlas image is removed from
    ``bpy.data.images`` - so the mid-loop ``StructRNA of type Image
    has been removed`` error cannot happen.

    Returns the new ``bpy.types.Image``.
    """
    import bpy  # local import - module must remain importable from non-bpy contexts
    import numpy as np

    # Snapshot every source's pixels into NumPy *before* mutating bpy.data.images.
    # If `src.image` is the existing atlas-with-the-same-name we are about to
    # remove, the snapshot detaches us from the bpy reference - Blender can
    # then free the StructRNA without us crashing later in the loop.
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
            # Source image was already invalidated (e.g. an earlier pack run
            # in this session removed it). Skip - the caller's validation
            # path should surface this as a warning.
            continue
        placed_sources.append((src, rect, pixels))

    name = out_path.stem
    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name])
    atlas_img = bpy.data.images.new(
        name=name,
        width=packed.atlas_w,
        height=packed.atlas_h,
        alpha=True,
    )

    canvas: np.ndarray = np.zeros((packed.atlas_h, packed.atlas_w, 4), dtype=np.float32)

    # Coordinate systems. The packer is internally top-down (y=0 means top of
    # the atlas, the bin-packing convention); ``bpy.types.Image.pixels`` is
    # bottom-up (row 0 = bottom of the image). UV-derived ``slice_px`` is
    # bottom-up because Blender mesh UVs use bottom-left origin. We slice the
    # source in bottom-up space, then convert the slot's top-down y to a
    # bottom-up canvas row before pasting.
    for src, rect, src_pixels in placed_sources:
        sx, sy_bu, sw, sh = src.slice_px
        sliced = src_pixels[sy_bu : sy_bu + sh, sx : sx + sw]
        # Defensive clamp in case the slice rect is slightly larger than the
        # placement (rounding from the packer's padding bookkeeping).
        h = min(rect.h, sliced.shape[0])
        w = min(rect.w, sliced.shape[1])
        slot_y_bu = packed.atlas_h - rect.y - rect.h
        canvas[slot_y_bu : slot_y_bu + h, rect.x : rect.x + w] = sliced[:h, :w]

    atlas_img.pixels.foreach_set(canvas.flatten().tolist())

    atlas_img.filepath_raw = str(out_path)
    atlas_img.file_format = "PNG"
    atlas_img.save()
    return atlas_img


def write_manifest(
    packed: PackResult,
    padding: int,
    sources: list[SourceImage],
    manifest_path: Path,
) -> None:
    """Persist the pack result + source slice metadata as JSON.

    ``format_version`` 2 adds ``source_w/h`` and ``slice_x/y/w/h`` per
    placement so ``apply_packed_atlas`` can rewrite UVs (polygon) and
    ``texture_region`` (sprite_frame) correctly when the source was a
    shared atlas (slice_px != full image).
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
        "format_version": 2,
        "atlas_w": packed.atlas_w,
        "atlas_h": packed.atlas_h,
        "padding": padding,
        "placements": placements_payload,
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
