"""Quad mesh + material stamper for the Photoshop importer.

Coordinate conversion: PSD top-left -> Blender XZ centre at the
manifest's ``pixels_per_unit``::

    mesh_center.x = (px_x + px_w / 2 - W / 2) / pixels_per_unit
    mesh_center.z = (H / 2 - px_y - px_h / 2) / pixels_per_unit
    mesh_center.y = z_order * spacing   (the Y Location layer gap; avoid Z-fight)
    mesh_size.x   = px_w / pixels_per_unit
    mesh_size.z   = px_h / pixels_per_unit

The PSD layer order seeds ``y_draw_order`` (the Y Location / Draw Order
field); the per-layer ``spacing`` is the addon ``y_location_spacing``
preference.

Re-import semantics: existing meshes are identified by the
``proscenio_import_origin == "psd:<layer_name>"`` custom property and
re-used in place. See :mod:`mesh_build` for the reuse / rebuild + weight
reprojection detail. Meshes whose layer no longer appears in the manifest are
left for the user to clean up manually.

This module is the thin orchestrator (``stamp_mesh`` / ``stamp_sprite`` /
``_place_and_tag`` + placement/parenting glue); the quad reuse/rebuild lives in
:mod:`mesh_build`, the material graph in :mod:`material`, and the custom-property
taggers in :mod:`tags`. Those internals are re-exported here so callers and tests
that import ``planes._build_quad`` / ``planes._ensure_mesh`` / ``planes._attach_material``
/ ``planes._tag_draw_order`` are unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import bpy

from ...core.bpy_helpers._shared._bpy_compat import (
    expect_scene,
    iter_collection_children,
)
from ...core.bpy_helpers.psd.psd_spritesheet import compose_spritesheet
from ...core.psd import psd_manifest
from ...core.psd.placement import layer_placement, origin_for_kind
from ...core.slot.slot_emit import is_slot_empty
from .material import _attach_material, _set_material_blend_method
from .mesh_build import (
    _build_quad,
    _ensure_mesh,
    _find_existing,
    _placement_unchanged,
    _snapshot_before_rebuild,
)
from .tags import _tag_blend_mode, _tag_draw_order, _tag_element_type, _tag_kind, _tag_origin

__all__ = [
    "SPRITESHEET_DIR_NAME",
    "StampedSprite",
    "_attach_material",
    "_build_quad",
    "_ensure_mesh",
    "_find_existing",
    "_place_and_tag",
    "_placement_unchanged",
    "_set_material_blend_method",
    "_snapshot_before_rebuild",
    "_tag_blend_mode",
    "_tag_draw_order",
    "_tag_element_type",
    "_tag_kind",
    "_tag_origin",
    "stamp_mesh",
    "stamp_sprite",
]

SPRITESHEET_DIR_NAME = "_spritesheets"


@dataclass(frozen=True)
class StampedSprite:
    """Result of stamping one sprite layer."""

    mesh_obj: bpy.types.Object
    spritesheet_path: Path


def _place_and_tag(
    layer: psd_manifest.MeshLayer | psd_manifest.SpriteLayer,
    manifest: psd_manifest.LoadedManifest,
    armature_obj: bpy.types.Object,
    image_path: Path,
    *,
    kind: str,
    element_type: str,
    spacing: float,
    hframes: int = 1,
    vframes: int = 1,
) -> bpy.types.Object:
    """Place + tag a stamped layer object (the shared mesh / sprite tail).

    Computes the layer placement, builds the quad mesh, sets its world
    position, attaches the ``image_path`` material, parents it under the
    PSD root + subfolder, then stamps the origin / kind / blend-mode /
    element-type tags. Callers pass the kind-specific bits: the resolved
    image (single PNG vs composed spritesheet), the ``kind`` +
    ``element_type`` tag values, the ``spacing`` Y-gap preference (threaded in
    rather than read from context here), and the sprite frame counts.
    """
    placement = layer_placement(
        layer.position,
        layer.size,
        manifest.size,
        manifest.pixels_per_unit,
        layer.z_order,
        spacing,
        origin_for_kind(layer.origin, element_type, layer.name),
        manifest.anchor,
    )
    obj = _ensure_mesh(layer.name, placement.size, placement.geometry_offset)
    _attach_material(obj, image_path, blend_mode=layer.blend_mode)
    # A re-import refreshes the art in place, but the user owns where the mesh
    # lives. Once it has been re-parented into a slot Empty, the slot drives its
    # placement - re-rooting it back to the armature (and re-zeroing its world
    # position / outliner home) would silently break the attachment. Only the
    # manifest-driven placement is applied when the mesh is NOT slot-attached.
    # The draw order rides with the placement: a non-slot mesh resyncs to the
    # PSD layer order (its Y was just re-applied too); a slot-attached mesh is
    # left alone (the slot owns it).
    if not is_slot_empty(obj.parent):
        _set_world_position(obj, placement.location)
        _parent_to_root(obj, armature_obj)
        _link_to_subfolder(obj, layer.subfolder)
        _tag_draw_order(obj, layer.z_order)
    _tag_origin(obj, layer.name)
    _tag_kind(obj, kind)
    _tag_blend_mode(obj, layer.blend_mode)
    _tag_element_type(obj, element_type, hframes=hframes, vframes=vframes)
    return obj


def stamp_mesh(
    layer: psd_manifest.MeshLayer,
    manifest: psd_manifest.LoadedManifest,
    armature_obj: bpy.types.Object,
) -> bpy.types.Object | None:
    """Stamp a single-PNG mesh layer. Returns the mesh object."""
    image_path = psd_manifest.resolve_path(manifest, layer.path)
    if not image_path.exists():
        print(f"[psd_import] missing PNG for {layer.name}: {image_path}")
        return None
    return _place_and_tag(
        layer,
        manifest,
        armature_obj,
        image_path,
        kind=layer.kind,
        element_type="mesh",
        spacing=_y_location_spacing(),
    )


def stamp_sprite(
    layer: psd_manifest.SpriteLayer,
    manifest: psd_manifest.LoadedManifest,
    armature_obj: bpy.types.Object,
) -> StampedSprite | None:
    """Stamp a sprite layer: compose spritesheet, build single mesh."""
    frame_paths = [psd_manifest.resolve_path(manifest, frame.path) for frame in layer.frames]
    missing = [p for p in frame_paths if not p.exists()]
    if missing:
        names = ", ".join(str(p.name) for p in missing)
        print(f"[psd_import] missing frame PNG(s) for {layer.name}: {names}")
        return None
    sheet_dir = manifest.source_path.parent / SPRITESHEET_DIR_NAME
    sheet_path = sheet_dir / f"{layer.name}.png"
    sheet = compose_spritesheet(frame_paths, sheet_path)

    # Mesh is sized to the manifest-declared bbox of the largest frame.
    # The spritesheet image's tile_size matches that bbox in pixels (the
    # composer pads smaller frames in-place), so the displayed-frame quad
    # has the right world dimensions.
    obj = _place_and_tag(
        layer,
        manifest,
        armature_obj,
        sheet_path,
        kind="sprite",
        element_type="sprite",
        spacing=_y_location_spacing(),
        hframes=sheet.hframes,
        vframes=sheet.vframes,
    )
    return StampedSprite(mesh_obj=obj, spritesheet_path=sheet_path)


def _y_location_spacing() -> float:
    """Read the addon's Y-gap preference (local import avoids a register cycle)."""
    from ...addon_prefs import y_location_spacing

    return y_location_spacing(bpy.context)


def _set_world_position(obj: bpy.types.Object, center: tuple[float, float, float]) -> None:
    obj.location = center


def _parent_to_root(obj: bpy.types.Object, armature_obj: bpy.types.Object) -> None:
    """Parent ``obj`` to the armature object (stub armature).

    Must use ``parent_type='OBJECT'``, not ``'BONE'``: bone-parenting
    aligns the child's local Y to the bone axis (Blender bone-Y ==
    bone-axis), which on a vertical root bone rotates every mesh out of
    the XZ world plane. Object-parenting keeps the authored XZ orientation.
    """
    obj.parent = armature_obj
    obj.parent_type = "OBJECT"


def _link_to_subfolder(obj: bpy.types.Object, subfolder: str | None) -> None:
    """Move ``obj`` into a nested Collection hierarchy mirroring ``subfolder``.

    A ``subfolder`` like ``"body/torso"`` creates (or reuses) collections
    ``body`` -> ``torso`` under the active scene's root collection, and
    relinks ``obj`` into the deepest one. ``None`` leaves it in the
    scene's root collection.
    """
    if not subfolder:
        return
    parent = expect_scene(bpy.context.scene).collection
    for part in subfolder.split("/"):
        clean = part.strip()
        if not clean:
            continue
        # Scope the lookup to the current parent's children, not the global
        # collection table. Two hierarchies sharing a leaf name (e.g.
        # `body/torso` and `props/torso`) must not collapse onto the same
        # Collection - a global lookup would re-link the existing one under
        # a different parent and flatten the import tree.
        child = next(
            (c for c in iter_collection_children(parent) if c.name == clean),
            None,
        )
        if child is None:
            child = bpy.data.collections.new(clean)
            parent.children.link(child)
        parent = child
    for existing in obj.users_collection:
        existing.objects.unlink(obj)
    parent.objects.link(obj)
