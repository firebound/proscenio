"""Scene-walker helpers: find armature, sprite meshes, atlas image, doc name."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import bpy

from ....core._shared.material_images import iter_material_node_images
from ....core._shared.props_access import resolve_export_armature
from ....core.bpy_helpers._shared._bpy_compat import iter_materials, iter_objects


def find_armature(scene: bpy.types.Scene) -> bpy.types.Object | None:
    """Return the armature Proscenio exports for the scene.

    Picker-first (``proscenio.active_armature``) when it points at a live
    ARMATURE in this scene, else the first ARMATURE in scene order. Shares
    ``resolve_export_armature`` with the export validator so the two agree on
    the rig in multi-armature scenes.
    """
    return resolve_export_armature(scene)


def find_sprite_meshes(scene: bpy.types.Scene) -> list[bpy.types.Object]:
    """Return every MESH in the scene, sorted by name for deterministic output."""
    sprites = [obj for obj in iter_objects(scene) if obj.type == "MESH"]
    sprites.sort(key=lambda o: o.name)
    return sprites


def find_atlas_image(out_path: Path) -> str | None:
    """Atlas filename: linked images first, sibling ``atlas.png`` fallback."""
    for image in _iter_linked_images():
        name = image_filename(image)
        if name is not None:
            return name
    sibling = out_path.parent / "atlas.png"
    return sibling.name if sibling.exists() else None


def _iter_linked_images() -> Iterator[bpy.types.Image]:
    for mat in iter_materials():
        yield from iter_material_node_images(mat)


def image_filename(image: bpy.types.Image) -> str | None:
    """On-disk filename for an Image datablock, or a synthesised ``<name>.png``
    when it has only a datablock name; ``None`` when it has neither.

    Append ``.png`` only when the name lacks it, so an image already named
    ``atlas.png`` does not become ``atlas.png.png``; the ``.png`` suffix check
    (not ``Path.suffix``) avoids mistaking Blender's numeric duplicate suffix
    (``Image.001``) for an extension - the writer only emits PNG. The single
    home for both the per-sprite ``texture`` filename and the atlas filename.
    """
    fp = str(getattr(image, "filepath", "") or "")
    if fp:
        return Path(bpy.path.abspath(fp)).name
    name = str(getattr(image, "name", ""))
    if not name:
        return None
    return name if name.lower().endswith(".png") else f"{name}.png"


def doc_name() -> str:
    blend = bpy.data.filepath
    return Path(blend).stem if blend else "proscenio_doc"
