"""Atlas source image collection (SPEC 009 wave 9.10 split of atlas_io).

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

from ..uv_bounds import uv_bbox_to_pixels


@dataclass(frozen=True)
class SourceImage:
    """One source slice to be repacked.

    ``image`` is the source ``bpy.types.Image`` (often shared between
    sprites). ``width`` / ``height`` are the source image dimensions.
    ``slice_px`` ``(x, y, w, h)`` is the sub-rect of the source image
    that this sprite actually uses, derived from its mesh UV bounds.
    """

    obj_name: str
    image: Any  # bpy.types.Image -- Any here so the module imports without bpy
    width: int
    height: int
    slice_px: tuple[int, int, int, int]


def collect_source_images(objects: list[Any]) -> list[SourceImage]:
    """Walk ``objects`` and gather their first image-textured material.

    Each entry carries a ``slice_px`` rect derived from the mesh's UV
    bounds -- for 1-sprite-per-PNG sources this covers the whole image;
    for shared-atlas sources it picks out just the sprite's sub-region.

    Objects with no image-textured material or no UV layer are silently
    skipped -- the caller's validation pass should surface that as a
    warning.
    """
    out: list[SourceImage] = []
    for obj in objects:
        image = _find_first_image(obj)
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

    Defensive against partially-initialized meshes -- Blender 5.x can
    have a UV layer marker whose ``.data`` collection is empty (seen
    after the apply operator on certain shared-material objects), which
    previously crashed with ``IndexError`` on the second Pack Atlas run.
    """
    mesh = obj.data
    uv_layer = getattr(mesh, "uv_layers", None)
    if uv_layer is None:
        return []
    active = uv_layer.active
    if active is None or len(active.data) == 0:
        return []
    out: list[tuple[float, float]] = []
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            if li >= len(active.data):
                continue
            u, v = active.data[li].uv
            out.append((float(u), float(v)))
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
