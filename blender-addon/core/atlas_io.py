"""Bpy-side IO for the atlas packer (SPEC 005.1.c.2).

Splits the bpy.types.Image plumbing out of the operator so the packer
algorithm itself stays pure (and testable). This module is **not**
imported by the pytest suite — it touches ``bpy.types.Image`` and
``numpy`` (Blender bundles numpy, but pip-only test environments do not).

Responsibilities:

- :func:`collect_source_images` — walk a list of mesh objects, return one
  ``SourceImage`` per object whose first material has an image-textured
  node. Sprites with no source image are skipped.
- :func:`compose_atlas` — given a :class:`PackResult` and the source
  image list, assemble a new ``bpy.types.Image`` and save it to disk.
- :func:`write_manifest` — JSON sidecar with the per-sprite rect,
  consumed by ``apply_packed_atlas``.
- :func:`read_manifest` — inverse, used by the apply operator.

Edge case (deferred to a later iteration): sprites whose source material
points to an already-shared atlas (with different ``texture_region`` per
sprite) require slicing — extracting the sub-image from the shared atlas
before repacking. The current iteration assumes ``1 sprite = 1 source PNG``
matching the Photoshop-first workflow (SPEC 006). Sliced-atlas support is
tracked in the SPEC 005 TODO under "Defer".
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .atlas_packer import PackResult, Rect


@dataclass(frozen=True)
class SourceImage:
    """One source PNG to be repacked. ``image`` is the ``bpy.types.Image``."""

    obj_name: str
    image: Any  # bpy.types.Image — Any here so the module imports without bpy
    width: int
    height: int


def collect_source_images(objects: list[Any]) -> list[SourceImage]:
    """Walk ``objects`` and gather their first image-textured material.

    Returns one :class:`SourceImage` per object that has a usable source.
    Objects with no image-textured material are silently skipped — the
    caller's validation pass should surface that as a warning.
    """
    out: list[SourceImage] = []
    for obj in objects:
        image = _find_first_image(obj)
        if image is None:
            continue
        w, h = image.size
        if w <= 0 or h <= 0:
            continue
        out.append(SourceImage(obj_name=obj.name, image=image, width=int(w), height=int(h)))
    return out


def _find_first_image(obj: Any) -> Any | None:
    """Return the first image bound to any material on ``obj``."""
    mesh = obj.data
    materials = getattr(mesh, "materials", None) or []
    for mat in materials:
        if mat is None or not mat.use_nodes or mat.node_tree is None:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image is not None:
                return node.image
    return None


def compose_atlas(
    sources: list[SourceImage],
    packed: PackResult,
    out_path: Path,
    padding: int = 2,
) -> Any:
    """Build a single bpy.types.Image holding every packed source and save it.

    Pixels are RGBA float32. Padding pixels are left transparent (alpha=0)
    in this iteration — edge-extend padding to combat bilinear bleeding can
    be added later without changing the operator surface.

    Returns the new ``bpy.types.Image``.
    """
    import bpy  # local import — module must remain importable from non-bpy contexts
    import numpy as np

    name = out_path.stem
    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name])
    atlas_img = bpy.data.images.new(
        name=name,
        width=packed.atlas_w,
        height=packed.atlas_h,
        alpha=True,
    )

    canvas = np.zeros((packed.atlas_h, packed.atlas_w, 4), dtype=np.float32)

    for src in sources:
        rect: Rect | None = packed.placements.get(src.obj_name)
        if rect is None:
            continue
        src_pixels = np.array(src.image.pixels[:], dtype=np.float32).reshape(
            src.height, src.width, 4
        )
        # Blender pixel buffers are bottom-up. Convert to top-down before pasting,
        # then flip the whole canvas at the end so atlas saves bottom-up too.
        src_top_down = src_pixels[::-1]
        canvas[rect.y : rect.y + rect.h, rect.x : rect.x + rect.w] = src_top_down

    # Flip back to Blender's bottom-up convention.
    canvas = canvas[::-1]
    atlas_img.pixels.foreach_set(canvas.flatten().tolist())

    atlas_img.filepath_raw = str(out_path)
    atlas_img.file_format = "PNG"
    atlas_img.save()
    return atlas_img


def write_manifest(packed: PackResult, padding: int, manifest_path: Path) -> None:
    """Persist the pack result as JSON next to the atlas PNG."""
    payload: dict[str, Any] = {
        "format_version": 1,
        "atlas_w": packed.atlas_w,
        "atlas_h": packed.atlas_h,
        "padding": padding,
        "placements": {
            name: {"x": r.x, "y": r.y, "w": r.w, "h": r.h} for name, r in packed.placements.items()
        },
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_manifest(manifest_path: Path) -> tuple[int, int, int, dict[str, Rect]]:
    """Inverse of :func:`write_manifest`. Returns ``(atlas_w, atlas_h, padding, placements)``."""
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    placements = {
        name: Rect(int(r["x"]), int(r["y"]), int(r["w"]), int(r["h"]))
        for name, r in payload["placements"].items()
    }
    return (
        int(payload["atlas_w"]),
        int(payload["atlas_h"]),
        int(payload.get("padding", 0)),
        placements,
    )
