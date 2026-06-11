"""Quad mesh + material stamper for the Photoshop importer.

Coordinate conversion: PSD top-left → Blender XZ centre at the
manifest's ``pixels_per_unit``::

    mesh_center.x = (px_x + px_w / 2 - W / 2) / pixels_per_unit
    mesh_center.z = (H / 2 - px_y - px_h / 2) / pixels_per_unit
    mesh_center.y = z_order * Z_EPSILON   (avoid Z-fight)
    mesh_size.x   = px_w / pixels_per_unit
    mesh_size.z   = px_h / pixels_per_unit

Re-import semantics: existing meshes are identified by the
``proscenio_import_origin == "psd:<layer_name>"`` custom property and
re-used in place. Object-level data (transform, parenting, custom
properties) is left alone. When the layer's placement (size + geometry
offset) is unchanged - the common art-retouch case - the mesh is left
fully intact, preserving any automesh densification and painted weights.
When the placement changed, the quad is rebuilt and the painted weights
(stored in the ``proscenio_weight_sidecar`` custom property, which survives
the rebuild) are reprojected onto the fresh quad by UV anchor; a follow-up
automesh regen redistributes them across a denser mesh. Meshes whose layer
no longer appears in the manifest are left for the user to clean up manually.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

import bpy

from ...core._shared.cp_keys import (
    PROSCENIO_BLEND_MODE,
    PROSCENIO_IMPORT_ORIGIN,
    PROSCENIO_IMPORT_PLACEMENT,
    PROSCENIO_PSD_KIND,
    PROSCENIO_WEIGHT_SIDECAR,
)
from ...core.bpy_helpers._shared._bpy_compat import (
    expect_mesh,
    expect_scene,
    first_uv_layer,
    iter_blend_objects,
    iter_collection_children,
    iter_shader_nodes,
    material_by_name,
    node_input_by_name,
    node_output_by_name,
    set_material_at,
    uv_loop_at,
)
from ...core.bpy_helpers.psd.psd_spritesheet import compose_spritesheet
from ...core.bpy_helpers.skinning import reproject_stored_sidecar, snapshot_live_vgroups
from ...core.psd import psd_manifest
from ...core.skinning.sidecar_schema import from_json, to_json

Z_EPSILON = 0.001
SPRITESHEET_DIR_NAME = "_spritesheets"

# EEVEE material.blend_method mapping for the photoshop tag system blend modes.
# Blender 4.2+ collapsed the alpha modes to {OPAQUE, CLIP, HASHED,
# BLEND} (the old "ADDITIVE" / "MULTIPLY" alpha modes were retired in
# favour of shader-node-based blending). Every non-opaque mode here
# routes through "BLEND"; the manifest-declared mode is stamped as a
# custom property so downstream writers (Godot) can emit the exact
# requested compositing operator.
_BLEND_METHOD_BY_MODE: dict[str, str] = {
    "normal": "BLEND",
    "multiply": "BLEND",
    "screen": "BLEND",
    "additive": "BLEND",
}


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
    hframes: int = 1,
    vframes: int = 1,
) -> bpy.types.Object:
    """Place + tag a stamped layer object (the shared mesh / sprite tail).

    Computes the layer placement, builds the quad mesh, sets its world
    position, attaches the ``image_path`` material, parents it under the
    PSD root + subfolder, then stamps the origin / kind / blend-mode /
    element-type tags. Callers pass the kind-specific bits: the resolved
    image (single PNG vs composed spritesheet), the ``kind`` +
    ``element_type`` tag values, and the sprite frame counts.
    """
    placement = _layer_placement(
        layer.position,
        layer.size,
        manifest.size,
        manifest.pixels_per_unit,
        layer.z_order,
        layer.origin,
        manifest.anchor,
    )
    obj = _ensure_mesh(layer.name, placement.size, placement.geometry_offset)
    _set_world_position(obj, placement.location)
    _attach_material(obj, image_path, blend_mode=layer.blend_mode)
    _parent_to_root(obj, armature_obj)
    _link_to_subfolder(obj, layer.subfolder)
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
        layer, manifest, armature_obj, image_path, kind=layer.kind, element_type="mesh"
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
        hframes=sheet.hframes,
        vframes=sheet.vframes,
    )
    return StampedSprite(mesh_obj=obj, spritesheet_path=sheet_path)


@dataclass(frozen=True)
class _Placement:
    """Output of `_layer_placement`: object world location plus the quad-vertex offset to bake."""

    location: tuple[float, float, float]
    size: tuple[float, float]
    # Geometry offset baked into the quad's local-space vertices so
    # the visible texture sits where the manifest says (`position +
    # size/2` in PSD pixels) even when the object's location was
    # shifted to an explicit `origin`. Zero when no origin is set.
    geometry_offset: tuple[float, float]


def _layer_placement(
    position_px: Sequence[int],
    size_px: Sequence[int],
    doc_size_px: Sequence[int],
    pixels_per_unit: float,
    z_order: int,
    origin_px: Sequence[int] | None,
    anchor_px: Sequence[int] | None,
) -> _Placement:
    """Translate PSD pixel coords + optional origin / anchor into Blender world placement.

    The Spine-style ``anchor`` (when set) becomes the world origin
    (0, 0, 0): every layer's PSD pixel position is re-zeroed against
    it. Without an anchor the importer falls back to canvas-centered
    placement.
    """
    px_x, px_y = position_px
    px_w, px_h = size_px
    doc_w, doc_h = doc_size_px
    if anchor_px is None:
        ref_x = doc_w / 2.0
        ref_y = doc_h / 2.0
    else:
        ref_x = float(anchor_px[0])
        ref_y = float(anchor_px[1])
    bbox_cx = (px_x + px_w / 2.0 - ref_x) / pixels_per_unit
    bbox_cz = (ref_y - px_y - px_h / 2.0) / pixels_per_unit
    cy = z_order * Z_EPSILON
    sx = px_w / pixels_per_unit
    sz = px_h / pixels_per_unit
    if origin_px is None:
        return _Placement(
            location=(bbox_cx, cy, bbox_cz),
            size=(sx, sz),
            geometry_offset=(0.0, 0.0),
        )
    origin_x, origin_y = origin_px
    ox = (origin_x - ref_x) / pixels_per_unit
    oz = (ref_y - origin_y) / pixels_per_unit
    return _Placement(
        location=(ox, cy, oz),
        size=(sx, sz),
        geometry_offset=(bbox_cx - ox, bbox_cz - oz),
    )


def _ensure_mesh(
    name: str,
    size: tuple[float, float],
    geometry_offset: tuple[float, float] = (0.0, 0.0),
) -> bpy.types.Object:
    """Reuse an existing mesh by ``proscenio_import_origin`` tag, else create.

    A re-import whose placement (size + geometry offset) is unchanged is an art
    retouch: the mesh is left fully intact, preserving any automesh
    densification and painted weights - only the caller's material refresh
    carries the new art. A changed placement rebuilds the quad and reprojects
    the painted weights (they live in the ``proscenio_weight_sidecar`` Custom
    Property, which survives the geometry wipe) onto the fresh quad by UV
    anchor. ``geometry_offset`` shifts the quad in local space so an object
    placed at a non-bbox-centre location still displays the texture at the
    bbox-centre world position.
    """
    obj = _find_existing(name)
    if obj is not None and _placement_unchanged(obj, size, geometry_offset):
        return obj
    rebuilt_existing = obj is not None
    if obj is not None:
        _snapshot_before_rebuild(obj)
    if obj is None:
        new_mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, new_mesh)
        expect_scene(bpy.context.scene).collection.objects.link(obj)
    _build_quad(obj, size, geometry_offset)
    obj[PROSCENIO_IMPORT_PLACEMENT] = [size[0], size[1], geometry_offset[0], geometry_offset[1]]
    if rebuilt_existing:
        reproject_stored_sidecar(obj)
    return obj


def _snapshot_before_rebuild(obj: bpy.types.Object) -> None:
    """Ensure a usable weight snapshot exists on obj before the geometry wipe.

    The stored sidecar survives the rebuild, so when it is present with entries
    nothing is needed. Otherwise - a native Auto Weights bind writes no sidecar,
    and a corrupt one is unusable - capture the live vertex-group weights now so
    the post-rebuild reproject restores them instead of dropping the mesh's only
    weights.
    """
    payload = obj.get(PROSCENIO_WEIGHT_SIDECAR)
    if payload is not None:
        try:
            if from_json(payload).entries:
                return
        except ValueError:
            # Corrupt stored sidecar - fall through to a live-weights snapshot.
            pass
    snapshot = snapshot_live_vgroups(obj)
    if snapshot is not None:
        obj[PROSCENIO_WEIGHT_SIDECAR] = to_json(snapshot)


def _build_quad(
    obj: bpy.types.Object,
    size: tuple[float, float],
    geometry_offset: tuple[float, float],
) -> None:
    """Clear the object's mesh and rebuild it as a single UV-mapped quad."""
    width, height = size
    ox, oz = geometry_offset
    mesh = expect_mesh(obj)
    mesh.clear_geometry()
    half_w = width / 2.0
    half_h = height / 2.0
    mesh.from_pydata(
        vertices=[
            (ox - half_w, 0.0, oz - half_h),
            (ox + half_w, 0.0, oz - half_h),
            (ox + half_w, 0.0, oz + half_h),
            (ox - half_w, 0.0, oz + half_h),
        ],
        edges=[],
        faces=[(0, 1, 2, 3)],
    )
    mesh.update()
    uv = first_uv_layer(mesh) or mesh.uv_layers.new(name="UVMap")
    uv_loop_at(uv, 0).uv = (0.0, 0.0)
    uv_loop_at(uv, 1).uv = (1.0, 0.0)
    uv_loop_at(uv, 2).uv = (1.0, 1.0)
    uv_loop_at(uv, 3).uv = (0.0, 1.0)


def _placement_unchanged(
    obj: bpy.types.Object,
    size: tuple[float, float],
    geometry_offset: tuple[float, float],
) -> bool:
    """True when obj's baked placement matches ``size`` + ``geometry_offset``.

    A missing or malformed stored placement reads as changed, so an object that
    predates the placement tag rebuilds once (and gains the tag).
    """
    stored = obj.get(PROSCENIO_IMPORT_PLACEMENT)
    if stored is None:
        return False
    want = (size[0], size[1], geometry_offset[0], geometry_offset[1])
    try:
        return all(abs(float(stored[i]) - want[i]) < 1e-6 for i in range(4))
    except (TypeError, IndexError, ValueError):
        return False


def _find_existing(name: str) -> bpy.types.Object | None:
    """Locate a mesh previously imported from the same PSD layer.

    Identifies via the ``proscenio_import_origin = "psd:<name>"`` custom
    property (mirrors the addon's PropertyGroup-or-fallback pattern).
    Falls back to name match so a freshly-authored mesh that already
    uses the layer's name is treated as the existing one.
    """
    target = f"psd:{name}"
    for obj in iter_blend_objects():
        if obj.type != "MESH":
            continue
        if obj.get(PROSCENIO_IMPORT_ORIGIN) == target:
            return obj
        if obj.name == name and obj.get(PROSCENIO_IMPORT_ORIGIN) is None:
            return obj
    return None


def _set_world_position(obj: bpy.types.Object, center: tuple[float, float, float]) -> None:
    obj.location = center


def _attach_material(
    obj: bpy.types.Object,
    image_path: Path,
    blend_mode: str | None = None,
) -> None:
    """Build (or refresh) a flat-shaded material with a TexImage node.

    ``blend_mode`` (when set) maps the photoshop tag system blend mode onto the
    EEVEE material's ``blend_method`` so the artist sees a sensible
    viewport approximation. The exact mode is preserved as a custom
    property by ``_tag_blend_mode`` for downstream writers.
    """
    mesh = expect_mesh(obj)
    image = bpy.data.images.load(str(image_path), check_existing=True)
    image.name = image_path.stem
    mat_name = f"{obj.name}.mat"
    mat = material_by_name(mat_name) or bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nt = mat.node_tree
    if nt is None:
        raise RuntimeError(
            f"Proscenio: material {mat_name!r} has no node tree after use_nodes=True"
        )
    while nt.nodes:
        nt.nodes.remove(next(iter_shader_nodes(nt)))
    out = nt.nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new(type="ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new(type="ShaderNodeTexImage")
    if not isinstance(tex, bpy.types.ShaderNodeTexImage):
        raise RuntimeError("Proscenio: nodes.new returned the wrong type for ShaderNodeTexImage")
    tex.image = image
    nt.links.new(node_output_by_name(tex, "Color"), node_input_by_name(bsdf, "Base Color"))
    nt.links.new(node_output_by_name(tex, "Alpha"), node_input_by_name(bsdf, "Alpha"))
    nt.links.new(node_output_by_name(bsdf, "BSDF"), node_input_by_name(out, "Surface"))
    _set_material_blend_method(mat, blend_mode)
    if mesh.materials:
        set_material_at(mesh, 0, mat)
    else:
        mesh.materials.append(mat)


def _set_material_blend_method(mat: bpy.types.Material, blend_mode: str | None) -> None:
    """Map the manifest blend mode onto the EEVEE material's ``blend_method``.

    Defensive against Blender enum drift (e.g. ADDITIVE retired in 4.2):
    look the value up in the property's enum_items before assigning so a
    stale mapping does not abort the entire import.
    """
    if not hasattr(mat, "blend_method"):
        return
    method = _BLEND_METHOD_BY_MODE.get(blend_mode or "normal", "BLEND")
    prop = mat.bl_rna.properties.get("blend_method")
    enum_items = cast(Iterable[bpy.types.EnumPropertyItem], getattr(prop, "enum_items", ()))
    valid: set[str] = {item.identifier for item in enum_items} if prop is not None else set()
    mat.blend_method = cast(
        Literal["OPAQUE", "CLIP", "HASHED", "BLEND"],
        method if method in valid else "BLEND",
    )


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


def _tag_origin(obj: bpy.types.Object, layer_name: str) -> None:
    obj[PROSCENIO_IMPORT_ORIGIN] = f"psd:{layer_name}"


def _tag_kind(obj: bpy.types.Object, kind: str) -> None:
    """Stamp the manifest ``kind`` so downstream writers can branch on it."""
    obj[PROSCENIO_PSD_KIND] = kind


def _tag_blend_mode(obj: bpy.types.Object, blend_mode: str | None) -> None:
    """Preserve the manifest-declared blend mode for downstream writers."""
    if blend_mode is None:
        return
    obj[PROSCENIO_BLEND_MODE] = blend_mode


def _tag_element_type(
    obj: bpy.types.Object,
    element_type: str,
    hframes: int = 1,
    vframes: int = 1,
) -> None:
    """Tag the mesh's element type via PropertyGroup if present, custom-prop fallback."""
    if hasattr(obj, "proscenio"):
        obj.proscenio.element_type = element_type
        obj.proscenio.hframes = hframes
        obj.proscenio.vframes = vframes
        if element_type == "sprite":
            obj.proscenio.frame = 0
            obj.proscenio.centered = True
    obj["proscenio_type"] = element_type
    obj["proscenio_hframes"] = hframes
    obj["proscenio_vframes"] = vframes
    if element_type == "sprite":
        obj["proscenio_frame"] = 0
        obj["proscenio_centered"] = True
