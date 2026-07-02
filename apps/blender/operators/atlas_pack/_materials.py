"""Material image query + swap helpers for atlas packing."""

from __future__ import annotations

import bpy

from ...core._shared.material_images import (  # type: ignore[import-not-found]
    iter_material_node_images,
)


def first_texture_image_name(mat: bpy.types.Material) -> str:
    """Return the name of the first image-textured node on ``mat`` (or '')."""
    image = next(iter_material_node_images(mat), None)
    return str(image.name) if image is not None else ""


def swap_image_in_materials(materials: bpy.types.AnyType, atlas_image: bpy.types.Image) -> None:
    """For every image-textured node across ``materials``, swap to ``atlas_image``."""
    for mat in materials:
        if mat is None or not mat.use_nodes or mat.node_tree is None:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE":
                node.image = atlas_image
