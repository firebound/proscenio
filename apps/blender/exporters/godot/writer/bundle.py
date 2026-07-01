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
from .scene_discovery import image_abspath, image_filename


@dataclass
class BundleResult:
    """Outcome of a bundle pass, keyed by referenced filename."""

    copied: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)  # source not on disk
    skipped: list[str] = field(default_factory=list)  # already beside the file
    collisions: list[str] = field(default_factory=list)  # 2+ sources, one name


def _register_image(
    image: bpy.types.Image,
    by_name: dict[str, bpy.types.Image],
    source_by_name: dict[str, Path | None],
    collisions: list[str],
) -> None:
    """Record one image under its bare filename, flagging a name collision.

    A collision is a DISTINCT source resolving to a filename already claimed by
    another source: only the first is bundled, so the later one is recorded (and
    warned) instead of vanishing silently.
    """
    filename = image_filename(image)
    if filename is None:
        return
    source = image_abspath(image)
    if filename not in by_name:
        by_name[filename] = image
        source_by_name[filename] = source
        return
    collided = source is not None and source != source_by_name[filename]
    if collided and filename not in collisions:
        collisions.append(filename)
        print(
            f"  WARN: texture filename {filename!r} is used by two different "
            f"sources - only one is bundled; rename one to keep both"
        )


def _collect_referenced_images(
    objects: list[bpy.types.Object],
) -> tuple[dict[str, bpy.types.Image], list[str]]:
    """Map bare filename -> the first Image seen, plus the names that collide.

    Godot resolves siblings by name, so two distinct sources sharing one bare
    filename can only bundle one; the collided names are surfaced (see
    :func:`_register_image`) rather than quietly dropped.
    """
    by_name: dict[str, bpy.types.Image] = {}
    source_by_name: dict[str, Path | None] = {}
    collisions: list[str] = []
    for obj in objects:
        if getattr(obj, "type", None) != "MESH":
            continue
        for image in iter_material_images(obj):
            _register_image(image, by_name, source_by_name, collisions)
    return by_name, collisions


def bundle_textures(objects: list[bpy.types.Object], dest_dir: Path) -> BundleResult:
    """Copy every referenced sprite/atlas texture into ``dest_dir``.

    Each referenced image is copied to ``dest_dir / <filename>`` - the bare
    name the .proscenio carries - so Godot's siblings-only resolution finds
    it. Sources already in ``dest_dir`` are left alone; a source missing on
    disk is reported, not copied. Two distinct sources sharing one bare filename
    are recorded as collisions (only the first is bundled).
    """
    by_name, collisions = _collect_referenced_images(objects)
    result = BundleResult(collisions=collisions)
    for filename, image in sorted(by_name.items()):
        source = image_abspath(image)
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
