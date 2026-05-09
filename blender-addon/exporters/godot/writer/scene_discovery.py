"""Scene-walker helpers: find armature, sprite meshes, atlas image, doc name."""

from __future__ import annotations

from pathlib import Path

import bpy


def find_armature(scene: bpy.types.Scene) -> bpy.types.Object | None:
    """Return the first ARMATURE in the scene or ``None``."""
    for obj in scene.objects:
        if obj.type == "ARMATURE":
            return obj
    return None


def find_sprite_meshes(scene: bpy.types.Scene) -> list[bpy.types.Object]:
    """Return every MESH in the scene, sorted by name for deterministic output."""
    sprites: list[bpy.types.Object] = []
    for obj in scene.objects:
        if obj.type == "MESH":
            sprites.append(obj)
    sprites.sort(key=lambda o: o.name)
    return sprites


def find_atlas_image(out_path: Path) -> str | None:
    """Atlas filename: linked images first, sibling ``atlas.png`` fallback."""
    for mat in bpy.data.materials:
        if not mat.use_nodes or mat.node_tree is None:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image is not None:
                fp = node.image.filepath
                if fp:
                    return Path(bpy.path.abspath(fp)).name
                return f"{node.image.name}.png"
    sibling = out_path.parent / "atlas.png"
    if sibling.exists():
        return sibling.name
    return None


def doc_name() -> str:
    blend = bpy.data.filepath
    return Path(blend).stem if blend else "proscenio_doc"
