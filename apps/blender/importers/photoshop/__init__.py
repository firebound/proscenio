"""Photoshop manifest importer (the photoshop importer).

Orchestrator. Reads a PSD manifest (parser lives in
``core.psd_manifest``), iterates layers, dispatches each entry to the
appropriate stamper (mesh vs sprite), and parents every
stamped mesh to a stub ``root`` bone in a fresh armature.

Public entry point::

    from importers.photoshop import import_manifest
    result = import_manifest(Path("/path/to/manifest.json"))
    print(f"stamped {len(result.meshes)} mesh(es)")

The operator (``operators.import_photoshop``) wraps this for the panel
button + file picker.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import bpy

from ...core._shared.cp_keys import PROSCENIO_IMPORT_MANIFEST, PROSCENIO_IMPORT_ORIGIN
from ...core.psd import psd_manifest
from ...core.slot.slot_emit import is_slot_empty
from .armature import DEFAULT_ROOT_BONE_NAME, build_root_armature
from .planes import stamp_mesh, stamp_sprite


@dataclass
class ImportResult:
    """Summary of an import pass; surfaced to the operator for reporting."""

    armature: bpy.types.Object | None = None
    meshes: list[bpy.types.Object] = field(default_factory=list)
    spritesheets: list[Path] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class SingleReimportResult:
    """Outcome of re-importing one Element from its source manifest entry.

    ``status`` is ``"restamped"`` when the Element's layer resolved and its
    art was refreshed (weights preserved or reprojected per the spec 055
    contract), ``"skipped"`` when the layer resolved but its PNG was missing,
    and ``"missing"`` when no manifest layer maps to the Element (renamed or
    deleted in the PSD) - a no-op that leaves the Element fully intact.
    """

    status: Literal["restamped", "skipped", "missing"]
    obj: bpy.types.Object | None = None
    layer_name: str | None = None
    warning: str | None = None


def import_manifest(
    manifest_path: Path | str,
    *,
    placement: Literal["centered", "landed"] = "landed",
    root_bone_name: str = DEFAULT_ROOT_BONE_NAME,
) -> ImportResult:
    """Read ``manifest_path`` (PSD manifest) and stamp the scene.

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
    ppu_warning = _sync_scene_pixels_per_unit(manifest)
    _apply_flat_color_management()
    armature_obj = build_root_armature(
        name=_armature_name(manifest),
        root_bone_name=root_bone_name,
    )
    result = ImportResult(armature=armature_obj)
    if ppu_warning is not None:
        result.warnings.append(ppu_warning)
    for layer in manifest.layers:
        _stamp_layer(layer, manifest, armature_obj, result)
    _tag_manifest_source(result.meshes, manifest)
    if placement == "landed":
        _anchor_meshes_at_feet(result.meshes, manifest)
    return result


def _stamp_layer(
    layer: psd_manifest.MeshLayer | psd_manifest.SpriteLayer,
    manifest: psd_manifest.LoadedManifest,
    armature_obj: bpy.types.Object,
    result: ImportResult,
) -> None:
    """Stamp one manifest entry, appending its outcome to ``result``.

    The per-entry tail shared by the whole-manifest loop and the single-Element
    reimport (``reimport_element``): dispatches by ``kind`` to the mesh / sprite
    stamper and records the stamped object, any composed spritesheet, or a skip.
    """
    if layer.kind == "mesh":
        obj = stamp_mesh(layer, manifest, armature_obj)
        if obj is not None:
            result.meshes.append(obj)
        else:
            result.skipped.append(f"mesh:{layer.name}")
    elif layer.kind == "sprite":
        stamped = stamp_sprite(layer, manifest, armature_obj)
        if stamped is not None:
            result.meshes.append(stamped.mesh_obj)
            result.spritesheets.append(stamped.spritesheet_path)
        else:
            result.skipped.append(f"sprite:{layer.name}")


def _tag_manifest_source(
    meshes: list[bpy.types.Object],
    manifest: psd_manifest.LoadedManifest,
) -> None:
    """Stamp the absolute source manifest path on every imported object.

    Lets a per-Element reimport (the Element panel button) find its origin file
    without a picker. Per-object - two manifests imported into one scene each
    carry their own source.
    """
    source = str(manifest.source_path)
    for obj in meshes:
        obj[PROSCENIO_IMPORT_MANIFEST] = source


def reimport_element(
    obj: bpy.types.Object,
    manifest_path: Path | str,
) -> SingleReimportResult:
    """Re-import the single Element ``obj`` from one entry of ``manifest_path``.

    Maps ``obj`` back to exactly one manifest layer (by its stamped
    ``proscenio_import_origin``, falling back to the object name), then re-stamps
    only that entry - reusing the import's existing root armature and honouring
    the spec 055 contract per entry (same-bounds keeps the mesh + painted
    weights, changed-bounds reprojects). Every sibling Element is untouched, and
    the whole-figure feet-anchor is deliberately skipped so the one Element does
    not shift relative to its siblings.

    A layer that no longer resolves (renamed / deleted in the PSD) is a
    warn-and-no-op leaving the Element intact (``status="missing"``); a resolved
    layer whose PNG is gone degrades to ``status="skipped"``.

    Raises :class:`psd_manifest.ManifestError` on a malformed manifest.
    """
    manifest = psd_manifest.load(manifest_path)
    layer = _layer_for_object(obj, manifest)
    if layer is None:
        origin = _origin_layer_name(obj)
        return SingleReimportResult(
            status="missing",
            layer_name=origin,
            warning=(
                f"no manifest layer matches this Element"
                f"{f' (origin {origin!r})' if origin else ''}; "
                "it was renamed or removed in the PSD - leaving the Element as is"
            ),
        )
    armature_obj = build_root_armature(name=_armature_name(manifest))
    result = ImportResult(armature=armature_obj)
    _stamp_layer(layer, manifest, armature_obj, result)
    if result.meshes:
        _tag_manifest_source(result.meshes, manifest)
        return SingleReimportResult(status="restamped", obj=result.meshes[0], layer_name=layer.name)
    return SingleReimportResult(
        status="skipped",
        layer_name=layer.name,
        warning=f"source art for layer {layer.name!r} is missing; the Element was left as is",
    )


def _origin_layer_name(obj: bpy.types.Object) -> str | None:
    """Return the layer name stamped on ``obj`` (``psd:`` stripped), or None."""
    origin = obj.get(PROSCENIO_IMPORT_ORIGIN)
    if not origin:
        return None
    return str(origin).removeprefix("psd:")


def _layer_for_object(
    obj: bpy.types.Object,
    manifest: psd_manifest.LoadedManifest,
) -> psd_manifest.MeshLayer | psd_manifest.SpriteLayer | None:
    """Resolve ``obj`` back to its source manifest layer.

    Prefers the stamped ``proscenio_import_origin`` (robust to a Blender-side
    object rename), falling back to the object name for a freshly-authored mesh
    adopted under the layer's name. A PSD-side layer rename misses and returns
    ``None`` (the caller degrades to a warn-and-no-op).
    """
    layer_by_name = {layer.name: layer for layer in manifest.layers}
    origin = _origin_layer_name(obj)
    if origin is not None and origin in layer_by_name:
        return layer_by_name[origin]
    return layer_by_name.get(obj.name)


def _apply_flat_color_management() -> None:
    """Switch the scene view transform to Standard for flat 2D art.

    Proscenio cutout art is authored flat; Blender's 4.x default AgX (and the
    older Filmic) view transform applies a film tone map that desaturates and
    lightens saturated colors, so the viewport stops matching the source PNG.
    Standard shows the rendered color 1:1. Best-effort + guarded so a config
    without the Standard transform never blocks an import.
    """
    view_settings = getattr(bpy.context.scene, "view_settings", None)
    if view_settings is None:
        return
    with contextlib.suppress(TypeError, AttributeError):
        view_settings.view_transform = "Standard"


def _sync_scene_pixels_per_unit(manifest: psd_manifest.LoadedManifest) -> str | None:
    """Push the manifest's PPU onto the active scene's Proscenio props.

    The importer sizes every mesh by ``manifest.pixels_per_unit``; if the
    scene property kept its default while an import used 1000, a later
    export would emit a 10x-scale mismatch, so the sync is intentional. But
    overwriting a value the user deliberately set, silently, hides that the
    import moved it - return a warning when the two differ so the operator
    can surface the change. No-op (and no warning) when the scene props are
    not registered (e.g. the addon is not enabled in this context).
    """
    scene = bpy.context.scene
    props = getattr(scene, "proscenio", None)
    if props is None:
        return None
    current = props.pixels_per_unit
    incoming = manifest.pixels_per_unit
    props.pixels_per_unit = incoming
    if current != incoming:
        return (
            f"scene pixels-per-unit changed {current:g} -> {incoming:g} to match the "
            f"imported manifest; a re-export now uses the imported scale."
        )
    return None


def _anchor_meshes_at_feet(
    meshes: list[bpy.types.Object],
    manifest: psd_manifest.LoadedManifest,
) -> None:
    """Shift every stamped mesh upward so the lowest figure point sits on Z=0.

    Computes the figure's lowest world Z by combining each mesh's
    location with its manifest-declared size (half-height in world
    units). The shift is applied as a Z translation so all relative
    layouts and the per-layer ``z_order`` Y-offset stay intact.

    Slot-attached meshes are excluded: their ``location`` is relative to
    the slot Empty, not the armature, so the slot owns their placement and
    feeding them into the world-Z math (or shifting them) would move them
    off their attachment on every re-import.
    """
    meshes = [obj for obj in meshes if not is_slot_empty(obj.parent)]
    if not meshes:
        return
    layer_by_name = {layer.name: layer for layer in manifest.layers}
    lowest_z: float | None = None
    for obj in meshes:
        layer = layer_by_name.get(obj.name) or layer_by_name.get(
            (obj.get(PROSCENIO_IMPORT_ORIGIN) or "").removeprefix("psd:")
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


def _armature_name(manifest: psd_manifest.LoadedManifest) -> str:
    """Derive a root-armature name from the manifest's ``doc`` field."""
    stem = Path(manifest.doc).stem or "psd_import"
    return f"{stem}.rig"
