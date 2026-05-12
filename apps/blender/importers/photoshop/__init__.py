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
from typing import Literal

import bpy

from ...core import psd_manifest  # type: ignore[import-not-found]
from .armature import DEFAULT_ROOT_BONE_NAME, build_root_armature
from .planes import stamp_polygon, stamp_sprite_frame


@dataclass
class ImportResult:
    """Summary of an import pass; surfaced to the operator for reporting."""

    armature: bpy.types.Object | None = None
    meshes: list[bpy.types.Object] = field(default_factory=list)
    spritesheets: list[Path] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def import_manifest(
    manifest_path: Path | str,
    *,
    placement: Literal["centered", "landed"] = "landed",
    root_bone_name: str = DEFAULT_ROOT_BONE_NAME,
) -> ImportResult:
    """Read ``manifest_path`` (PSD manifest v1) and stamp the scene.

    ``placement`` chooses where the figure sits relative to the world:

    - ``"landed"`` (default): every stamped mesh is shifted so the
      lowest point of the figure lands on world Z=0 - matches the
      Godot / game-engine convention of placing a character's pivot
      at the feet.
    - ``"centered"``: figure stays centred around the manifest canvas
      centre (world origin), useful when the user already has a
      coordinate plan or wants to align multiple imports in a shared
      scene.

    ``root_bone_name`` controls the single armature bone created at
    import time. Default is ``"root"``; rigs that follow a different
    convention (e.g. ``"spine"``) can override.

    Returns an :class:`ImportResult`. Raises
    :class:`psd_manifest.ManifestError` on shape mismatch.
    """
    manifest = psd_manifest.load(manifest_path)
    armature_obj = build_root_armature(
        name=_armature_name(manifest),
        root_bone_name=root_bone_name,
    )
    result = ImportResult(armature=armature_obj)
    for layer in manifest.layers:
        if layer.kind == "polygon" or layer.kind == "mesh":
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
    if placement == "landed":
        _anchor_meshes_at_feet(result.meshes, manifest)
    return result


def _anchor_meshes_at_feet(
    meshes: list[bpy.types.Object],
    manifest: psd_manifest.Manifest,
) -> None:
    """Shift every stamped mesh upward so the lowest figure point sits on Z=0.

    Computes the figure's lowest world Z by combining each mesh's
    location with its manifest-declared size (half-height in world
    units). The shift is applied as a Z translation so all relative
    layouts and the per-layer ``z_order`` Y-offset stay intact.
    """
    if not meshes:
        return
    layer_by_name = {layer.name: layer for layer in manifest.layers}
    lowest_z: float | None = None
    for obj in meshes:
        layer = layer_by_name.get(obj.name) or layer_by_name.get(
            (obj.get("proscenio_import_origin") or "").removeprefix("psd:")
        )
        if layer is None:
            continue
        half_h = layer.size[1] / (2.0 * manifest.pixels_per_unit)
        bottom = obj.location.z - half_h
        if lowest_z is None or bottom < lowest_z:
            lowest_z = bottom
    if lowest_z is None or abs(lowest_z) < 1e-6:
        return
    for obj in meshes:
        obj.location.z -= lowest_z


def _armature_name(manifest: psd_manifest.Manifest) -> str:
    """Derive a root-armature name from the manifest's ``doc`` field."""
    stem = Path(manifest.doc).stem or "psd_import"
    return f"{stem}.rig"
