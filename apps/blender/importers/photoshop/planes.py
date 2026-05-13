"""Quad mesh + material stamper for the Photoshop importer (SPEC 006).

Coordinate conversion (D6): PSD top-left → Blender XZ centre at the
manifest's ``pixels_per_unit``::

    mesh_center.x = (px_x + px_w / 2 - W / 2) / pixels_per_unit
    mesh_center.z = (H / 2 - px_y - px_h / 2) / pixels_per_unit
    mesh_center.y = z_order * Z_EPSILON   (avoid Z-fight)
    mesh_size.x   = px_w / pixels_per_unit
    mesh_size.z   = px_h / pixels_per_unit

Re-import semantics (D5): existing meshes are identified by
``proscenio.import_origin == "psd:<layer_name>"`` and re-used (mesh
data + material refreshed; transform / parenting / weights left
alone). Meshes whose layer no longer appears in the manifest are
left for the user to clean up manually.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import bpy

from ...core import psd_manifest  # type: ignore[import-not-found]
from ...core.bpy_helpers.psd_spritesheet import (  # type: ignore[import-not-found]
    compose_spritesheet,
)

Z_EPSILON = 0.001
SPRITESHEET_DIR_NAME = "_spritesheets"

# EEVEE material.blend_method mapping for SPEC 011 blend modes.
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
class StampedSpriteFrame:
    """Result of stamping one sprite_frame layer."""

    mesh_obj: bpy.types.Object
    spritesheet_path: Path


def stamp_polygon(
    layer: psd_manifest.PolygonLayer,
    manifest: psd_manifest.Manifest,
    armature_obj: bpy.types.Object,
) -> bpy.types.Object | None:
    """Stamp a single-PNG polygon layer. Returns the mesh object."""
    image_path = psd_manifest.resolve_path(manifest, layer.path)
    if not image_path.exists():
        print(f"[psd_import] missing PNG for {layer.name}: {image_path}")
        return None
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
    _tag_kind(obj, layer.kind)
    _tag_blend_mode(obj, layer.blend_mode)
    _tag_sprite_type(obj, "polygon")
    return obj


def stamp_sprite_frame(
    layer: psd_manifest.SpriteFrameLayer,
    manifest: psd_manifest.Manifest,
    armature_obj: bpy.types.Object,
) -> StampedSpriteFrame | None:
    """Stamp a sprite_frame layer: compose spritesheet, build single mesh."""
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
    # composer pads smaller frames in-place), so the displayed-frame
    # quad has the right world dimensions.
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
    _attach_material(obj, sheet_path, blend_mode=layer.blend_mode)
    _parent_to_root(obj, armature_obj)
    _link_to_subfolder(obj, layer.subfolder)
    _tag_origin(obj, layer.name)
    _tag_kind(obj, "sprite_frame")
    _tag_blend_mode(obj, layer.blend_mode)
    _tag_sprite_type(obj, "sprite_frame", hframes=sheet.hframes, vframes=sheet.vframes)
    return StampedSpriteFrame(mesh_obj=obj, spritesheet_path=sheet_path)


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
    position_px: tuple[int, int],
    size_px: tuple[int, int],
    doc_size_px: tuple[int, int],
    pixels_per_unit: float,
    z_order: int,
    origin_px: tuple[int, int] | None,
    anchor_px: tuple[int, int] | None,
) -> _Placement:
    """Translate PSD pixel coords + optional origin / anchor into Blender world placement.

    The Spine-style ``anchor`` (when set) becomes the world origin
    (0, 0, 0): every layer's PSD pixel position is re-zeroed against
    it. Without an anchor the importer falls back to canvas-centered
    placement (legacy behaviour for fixtures authored before SPEC 011).

    Known drift (Wave 11.7 investigation, tests/BUGS_FOUND.md): on the
    Blender -> JSX export -> Blender round-trip, the JSX exporter
    captures the alpha-aware bbox of each Workbench-rendered PNG which
    bleeds 1 px on every edge from anti-aliasing. The manifest's
    ``size`` ends up +2 px on both axes while ``position`` stays put,
    which shifts the computed bbox centre by +1 px (~0.17 % on a
    1731 px doc - cosmetic). The math here is correct given the inputs;
    fixing the drift means either trimming the AA bleed at render time
    or anchoring the exporter to the layer's authored bounds rather
    than the rendered pixels' bbox. Left intentional until the round-
    trip oracle re-runs against the SPEC 011 v2 doll fixture.
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
    """Reuse an existing mesh by ``proscenio.import_origin`` tag, else create.

    Mesh data + UVs are rewritten on every import so size changes
    propagate. ``geometry_offset`` shifts the quad in local space so
    that an object placed at a non-bbox-centre location (e.g. the
    SPEC 011 ``origin`` pivot) still displays the texture at the
    bbox-centre world position. Material gets refreshed by the caller.
    """
    obj = _find_existing(name)
    width, height = size
    ox, oz = geometry_offset
    if obj is None:
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
    mesh = obj.data
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
    uv = mesh.uv_layers[0] if mesh.uv_layers else mesh.uv_layers.new(name="UVMap")
    uv.data[0].uv = (0.0, 0.0)
    uv.data[1].uv = (1.0, 0.0)
    uv.data[2].uv = (1.0, 1.0)
    uv.data[3].uv = (0.0, 1.0)
    return obj


def _find_existing(name: str) -> bpy.types.Object | None:
    """Locate a mesh previously imported from the same PSD layer.

    Identifies via the ``proscenio_import_origin = "psd:<name>"`` custom
    property (mirrors the addon's PropertyGroup-or-fallback pattern).
    Falls back to name match so a freshly-authored mesh that already
    uses the layer's name is treated as the existing one.
    """
    target = f"psd:{name}"
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        if obj.get("proscenio_import_origin") == target:
            return obj
        if obj.name == name and "proscenio_import_origin" not in obj:
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

    ``blend_mode`` (when set) maps the SPEC 011 blend mode onto the
    EEVEE material's ``blend_method`` so the artist sees a sensible
    viewport approximation. The exact mode is preserved as a custom
    property by ``_tag_blend_mode`` for downstream writers.
    """
    mesh = obj.data
    image = bpy.data.images.load(str(image_path), check_existing=True)
    image.name = image_path.stem
    mat_name = f"{obj.name}.mat"
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nt = mat.node_tree
    while nt.nodes:
        nt.nodes.remove(nt.nodes[0])
    out = nt.nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new(type="ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new(type="ShaderNodeTexImage")
    tex.image = image
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    method = _BLEND_METHOD_BY_MODE.get(blend_mode or "normal", "BLEND")
    if hasattr(mat, "blend_method"):
        # Defensive against Blender enum drift (e.g. ADDITIVE retired in
        # 4.2): look the value up in the property's enum_items before
        # assigning so a stale mapping does not abort the entire import.
        prop = mat.bl_rna.properties.get("blend_method")
        valid = (
            {item.identifier for item in prop.enum_items} if prop is not None else set()
        )
        mat.blend_method = method if method in valid else "BLEND"
    if mesh.materials:
        mesh.materials[0] = mat
    else:
        mesh.materials.append(mat)


def _parent_to_root(obj: bpy.types.Object, armature_obj: bpy.types.Object) -> None:
    """Parent ``obj`` to the armature object (D3 stub armature).

    Uses ``parent_type='OBJECT'`` rather than ``parent_type='BONE'``
    because bone-parenting rotates the child so its local Y aligns
    with the bone's direction (Blender bone-Y == bone-axis).
    With a conventional vertical root bone (pointing +Z) that flip
    would rotate every mesh out of the XZ world plane, leaving the
    figure visible only in Top Ortho instead of Front Ortho.
    Object-parenting keeps the mesh's authored XZ orientation.
    Per-bone vertex weights for posing land in a future wave.
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
    scene = bpy.context.scene
    parent = scene.collection
    for part in subfolder.split("/"):
        clean = part.strip()
        if not clean:
            continue
        child = bpy.data.collections.get(clean) or bpy.data.collections.new(clean)
        if child.name not in {c.name for c in parent.children}:
            parent.children.link(child)
        parent = child
    for existing in obj.users_collection:
        existing.objects.unlink(obj)
    parent.objects.link(obj)


def _tag_origin(obj: bpy.types.Object, layer_name: str) -> None:
    obj["proscenio_import_origin"] = f"psd:{layer_name}"


def _tag_kind(obj: bpy.types.Object, kind: str) -> None:
    """Stamp the manifest ``kind`` so downstream writers can branch on it."""
    obj["proscenio_psd_kind"] = kind


def _tag_blend_mode(obj: bpy.types.Object, blend_mode: str | None) -> None:
    """Preserve the manifest-declared blend mode for downstream writers."""
    if blend_mode is None:
        return
    obj["proscenio_blend_mode"] = blend_mode


def _tag_sprite_type(
    obj: bpy.types.Object,
    sprite_type: str,
    hframes: int = 1,
    vframes: int = 1,
) -> None:
    """Tag the mesh's sprite type via PropertyGroup if present, custom-prop fallback."""
    if hasattr(obj, "proscenio"):
        obj.proscenio.sprite_type = sprite_type
        obj.proscenio.hframes = hframes
        obj.proscenio.vframes = vframes
        if sprite_type == "sprite_frame":
            obj.proscenio.frame = 0
            obj.proscenio.centered = True
    obj["proscenio_type"] = sprite_type
    obj["proscenio_hframes"] = hframes
    obj["proscenio_vframes"] = vframes
    if sprite_type == "sprite_frame":
        obj["proscenio_frame"] = 0
        obj["proscenio_centered"] = True
