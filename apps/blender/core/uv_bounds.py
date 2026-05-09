"""UV bounds → source-image pixel bbox (SPEC 005.1.c.2.1).

Used by the atlas packer to figure out which sub-region of a source image
each sprite actually needs. When 1 sprite = 1 source PNG (Photoshop-first
workflow), UV bounds cover the whole image and the slice equals the
source — no behavior change vs the un-sliced packer. When the source is
a shared atlas (dummy fixture), UV bounds cover only the sprite's region
and the packer extracts just that slice.

Pure Python — extracted from the bpy-side operators so pytest exercises
the math without spinning up Blender.
"""

from __future__ import annotations


def uv_bbox_to_pixels(
    uvs: list[tuple[float, float]],
    image_w: int,
    image_h: int,
    *,
    expand: int = 1,
) -> tuple[int, int, int, int]:
    """Return ``(x, y, w, h)`` in source-image pixel space.

    UVs are Blender-style ``(u, v)`` in ``[0, 1]`` with bottom-left origin.
    The returned rect is in the same orientation (bottom-left). ``expand``
    pads the bbox by N pixels on every side to swallow rounding artifacts;
    clamped to image bounds.

    Empty input → full image as a safe fallback.
    """
    if not uvs or image_w <= 0 or image_h <= 0:
        return (0, 0, max(0, image_w), max(0, image_h))

    us = [u for u, _ in uvs]
    vs = [v for _, v in uvs]
    u_min, u_max = max(0.0, min(us)), min(1.0, max(us))
    v_min, v_max = max(0.0, min(vs)), min(1.0, max(vs))

    x_min = max(0, int(u_min * image_w) - expand)
    y_min = max(0, int(v_min * image_h) - expand)
    x_max = min(image_w, int(u_max * image_w + 0.999) + expand)
    y_max = min(image_h, int(v_max * image_h + 0.999) + expand)

    w = max(1, x_max - x_min)
    h = max(1, y_max - y_min)
    return (x_min, y_min, w, h)


def remap_uv_into_slot(
    u: float,
    v: float,
    slice_px: tuple[int, int, int, int],
    src_w: int,
    src_h: int,
    slot_px: tuple[int, int, int, int],
    atlas_w: int,
    atlas_h: int,
) -> tuple[float, float]:
    """Translate a single UV from source-image space to packed-atlas space.

    All inputs are expected in **bottom-up** convention (Blender native:
    UV ``(0, 0)`` at bottom-left, pixel rows numbered from the bottom).
    Callers using the packer's top-down slot output must convert
    ``slot_px.y`` to bottom-up first via ``atlas_h - slot.y - slot.h``.
    """
    sx, sy, _sw, _sh = slice_px
    rx, ry, _rw, _rh = slot_px
    src_px_x = u * src_w
    src_px_y = v * src_h
    new_px_x = rx + (src_px_x - sx)
    new_px_y = ry + (src_px_y - sy)
    return (new_px_x / atlas_w, new_px_y / atlas_h)
