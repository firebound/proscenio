"""Photoshop manifest importer (SPEC 006 Wave 6.3).

Orchestrator. Reads a PSD manifest v1 (parser lives in
``core.psd_manifest``), iterates layers, dispatches each entry to the
appropriate stamper (polygon vs sprite_frame), and parents every
stamped mesh to a stub ``root`` bone in a fresh armature.

Public entry point::

    from importers.photoshop import import_manifest
    result = import_manifest(Path("/path/to/manifest.json"))
    print(f"stamped {len(result.meshes)} mesh(es)")

The operator (``operators.import_photoshop``) wraps this for the panel
button + file picker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import bpy

from ...core import psd_manifest  # type: ignore[import-not-found]
from .armature import build_root_armature
from .planes import stamp_polygon, stamp_sprite_frame


@dataclass
class ImportResult:
    """Summary of an import pass; surfaced to the operator for reporting."""

    armature: bpy.types.Object | None = None
    meshes: list[bpy.types.Object] = field(default_factory=list)
    spritesheets: list[Path] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def import_manifest(manifest_path: Path | str) -> ImportResult:
    """Read ``manifest_path`` (PSD manifest v1) and stamp the scene.

    Returns an :class:`ImportResult`. Raises :class:`psd_manifest.ManifestError`
    on shape mismatch.
    """
    manifest = psd_manifest.load(manifest_path)
    armature_obj = build_root_armature(name=_armature_name(manifest))
    result = ImportResult(armature=armature_obj)
    for layer in manifest.layers:
        if layer.kind == "polygon":
            obj = stamp_polygon(layer, manifest, armature_obj)
            if obj is not None:
                result.meshes.append(obj)
            else:
                result.skipped.append(f"polygon:{layer.name}")
        elif layer.kind == "sprite_frame":
            stamped = stamp_sprite_frame(layer, manifest, armature_obj)
            if stamped is not None:
                result.meshes.append(stamped.mesh_obj)
                result.spritesheets.append(stamped.spritesheet_path)
            else:
                result.skipped.append(f"sprite_frame:{layer.name}")
    return result


def _armature_name(manifest: psd_manifest.Manifest) -> str:
    """Derive a root-armature name from the manifest's ``doc`` field."""
    stem = Path(manifest.doc).stem or "psd_import"
    return f"{stem}.rig"
