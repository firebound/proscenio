"""Atlas source image collection (split out of atlas_io).

Walks a mesh list, returns one ``SourceImage`` per object whose first
material has an image-textured node. Each carries a ``slice_px`` rect
derived from the mesh's UV bounds so the packer can extract just the
relevant sub-region of the source image (covers both 1-sprite-per-PNG
and shared-atlas workflows).

Bpy-bound (the inputs are ``bpy.types.Object`` and the field reads
chase ``mesh.uv_layers`` / ``material.node_tree``), but the type
annotations stay ``Any`` so pytest can exercise it with
``SimpleNamespace`` fakes if ever needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..._shared.material_images import iter_material_images
from ...uv_bounds import uv_bbox_to_pixels
from .._shared.mesh_uvs import collect_mesh_loop_uvs


@dataclass(frozen=True)
class SourceImage:
    """One source slice to be repacked.

    ``image`` is the source ``bpy.types.Image`` (often shared between
    sprites). ``width`` / ``height`` are the source image dimensions.
    ``slice_px`` ``(x, y, w, h)`` is the sub-rect of the source image
    that this sprite actually uses, derived from its mesh UV bounds.
    """

    obj_name: str
    image: Any  # bpy.types.Image - Any here so the module imports without bpy
    width: int
    height: int
    slice_px: tuple[int, int, int, int]


def collect_source_images(objects: list[Any]) -> list[SourceImage]:
    """Walk ``objects`` and gather their first image-textured material.

    Each entry carries a ``slice_px`` rect derived from the mesh's UV
    bounds - for 1-sprite-per-PNG sources this covers the whole image;
    for shared-atlas sources it picks out just the sprite's sub-region.

    Objects with no image-textured material or no UV layer are silently
    skipped - the caller's validation pass should surface that as a
    warning.
    """
    out: list[SourceImage] = []
    for obj in objects:
        image = next(iter_material_images(obj), None)
        if image is None:
            continue
        w, h = image.size
        if w <= 0 or h <= 0:
            continue
        uvs = _collect_mesh_uvs(obj)
        slice_px = uv_bbox_to_pixels(uvs, int(w), int(h))
        out.append(
            SourceImage(
                obj_name=obj.name,
                image=image,
                width=int(w),
                height=int(h),
                slice_px=slice_px,
            )
        )
    return out


def _collect_mesh_uvs(obj: Any) -> list[tuple[float, float]]:
    """Flatten the active UV layer's loop coords into ``[(u, v), ...]``.

    Thin object-level wrapper over the shared ``collect_mesh_loop_uvs``
    mesh walk (which carries the Blender-5.x empty/short ``.data`` guard).
    """
    return collect_mesh_loop_uvs(obj.data)
