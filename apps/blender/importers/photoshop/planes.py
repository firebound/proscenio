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
    center, size = _layer_world_rect(
        layer.position, layer.size, manifest.size, manifest.pixels_per_unit, layer.z_order
    )
    obj = _ensure_mesh(layer.name, size)
    _set_world_position(obj, center)
    _attach_material(obj, image_path)
    _parent_to_root(obj, armature_obj)
    _tag_origin(obj, layer.name)
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
    center, size = _layer_world_rect(
        layer.position, layer.size, manifest.size, manifest.pixels_per_unit, layer.z_order
    )
    obj = _ensure_mesh(layer.name, size)
    _set_world_position(obj, center)
    _attach_material(obj, sheet_path)
    _parent_to_root(obj, armature_obj)
    _tag_origin(obj, layer.name)
    _tag_sprite_type(obj, "sprite_frame", hframes=sheet.hframes, vframes=sheet.vframes)
    return StampedSpriteFrame(mesh_obj=obj, spritesheet_path=sheet_path)


def _layer_world_rect(
    position_px: tuple[int, int],
    size_px: tuple[int, int],
    doc_size_px: tuple[int, int],
    pixels_per_unit: float,
    z_order: int,
) -> tuple[tuple[float, float, float], tuple[float, float]]:
    """PSD layer rect → Blender mesh (world centre, world XZ size)."""
    px_x, px_y = position_px
    px_w, px_h = size_px
    doc_w, doc_h = doc_size_px
    cx = (px_x + px_w / 2.0 - doc_w / 2.0) / pixels_per_unit
    cz = (doc_h / 2.0 - px_y - px_h / 2.0) / pixels_per_unit
    cy = z_order * Z_EPSILON
    sx = px_w / pixels_per_unit
    sz = px_h / pixels_per_unit
    return (cx, cy, cz), (sx, sz)


def _ensure_mesh(name: str, size: tuple[float, float]) -> bpy.types.Object:
    """Reuse an existing mesh by ``proscenio.import_origin`` tag, else create.

    Mesh data + UVs are rewritten on every import so size changes
    propagate. Material gets refreshed by the caller.
    """
    obj = _find_existing(name)
    width, height = size
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
            (-half_w, 0.0, -half_h),
            (half_w, 0.0, -half_h),
            (half_w, 0.0, half_h),
            (-half_w, 0.0, half_h),
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


def _attach_material(obj: bpy.types.Object, image_path: Path) -> None:
    """Build (or refresh) a flat-shaded material with a TexImage node."""
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


def _tag_origin(obj: bpy.types.Object, layer_name: str) -> None:
    obj["proscenio_import_origin"] = f"psd:{layer_name}"


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
