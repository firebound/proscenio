"""Gather every texture a .proscenio references into the export folder.

The .proscenio references textures by bare filename and the Godot importer
resolves siblings only, but PSD-imported assets live in images/ and
_spritesheets/ subfolders. Copying each referenced image next to the
.proscenio closes the manual gather every PSD-sourced export needs. The
writer already knows the images (per-sprite texture + atlas) through the
same ``iter_material_images`` walk; this reuses it and copies the sources.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

import bpy

from ....core._shared.material_images import iter_material_images
from .scene_discovery import image_filename


@dataclass
class BundleResult:
    """Outcome of a bundle pass, keyed by referenced filename."""

    copied: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)  # source not on disk
    skipped: list[str] = field(default_factory=list)  # already beside the file


def bundle_textures(objects: list[bpy.types.Object], dest_dir: Path) -> BundleResult:
    """Copy every referenced sprite/atlas texture into ``dest_dir``.

    Each referenced image is copied to ``dest_dir / <filename>`` - the bare
    name the .proscenio carries - so Godot's siblings-only resolution finds
    it. Sources already in ``dest_dir`` are left alone; a source missing on
    disk is reported, not copied.
    """
    by_name: dict[str, bpy.types.Image] = {}
    for obj in objects:
        if getattr(obj, "type", None) != "MESH":
            continue
        for image in iter_material_images(obj):
            filename = image_filename(image)
            if filename is not None:
                by_name.setdefault(filename, image)

    result = BundleResult()
    for filename, image in sorted(by_name.items()):
        source = _resolve_image_source(image)
        dest = dest_dir / filename
        if source is None or not source.exists():
            result.missing.append(filename)
            continue
        if source.resolve() == dest.resolve():
            result.skipped.append(filename)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        result.copied.append(filename)
    return result


def _resolve_image_source(image: bpy.types.Image) -> Path | None:
    """Absolute on-disk path of an image, or None when it has no filepath."""
    fp = str(getattr(image, "filepath", "") or "")
    if not fp:
        return None
    return Path(bpy.path.abspath(fp))
