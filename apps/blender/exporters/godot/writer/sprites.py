"""Sprite emission: polygon body + sprite_frame metadata + weights pipeline."""

from __future__ import annotations

import math
from collections.abc import Iterator
from pathlib import Path
from typing import Literal, NotRequired, TypedDict

import bpy
from mathutils import Vector
from proscenio_models import PolygonSprite, SpriteFrameSprite, Weight

from ....core import region as region_core
from ....core._bpy_compat import (
    expect_mesh,
    iter_poly_loop_indices,
    iter_poly_vertices,
    iter_vertex_groups,
    polygon_at,
    vertex_at,
    vertex_group_at,
)
from ....core.pg_cp_fallback import read_field
from .skeleton import BoneWorld, world_to_godot_xy

_WEIGHT_EPS = 1e-9


class _PolygonKwargs(TypedDict):
    """Constructor kwargs for ``PolygonSprite``.

    ``texture`` / ``weights`` are ``NotRequired`` so they are passed
    only when present; with ``model_dump_json(exclude_unset=True)`` an
    explicit ``None`` would serialise as ``"field": null`` and drift
    from the goldens (which omit the key, matching the legacy
    dict-based writer that only set it conditionally).
    """

    name: str
    bone: str
    texture_region: list[float]
    polygon: list[list[float]]
    uv: list[list[float]]
    texture: NotRequired[str]
    weights: NotRequired[list[Weight]]


class _SpriteFrameKwargs(TypedDict):
    """Constructor kwargs for ``SpriteFrameSprite``; ``texture_region`` is
    omitted in auto mode (the legacy writer only set it for manual regions)."""

    type: Literal["sprite_frame"]
    name: str
    bone: str
    hframes: int
    vframes: int
    frame: int
    centered: bool
    texture_region: NotRequired[list[float]]


def build_sprite(
    obj: bpy.types.Object,
    world_godot: dict[str, BoneWorld],
    ppu: float,
) -> PolygonSprite | SpriteFrameSprite:
    """Build a sprite entry. The sprite kind is read from
    ``Object.proscenio.sprite_type`` (PropertyGroup), falling back to the
    legacy ``proscenio_type`` Custom Property when the PropertyGroup is
    unavailable (default ``"polygon"``).
    """
    sprite_type: str = str(
        read_field(obj, pg_field="sprite_type", cp_key="proscenio_type", default="polygon")
    )
    if sprite_type == "sprite_frame":
        return build_sprite_frame(obj)
    if sprite_type != "polygon":
        raise RuntimeError(
            f"Proscenio: object {obj.name!r} has unknown proscenio_type "
            f"{sprite_type!r}; expected 'polygon' or 'sprite_frame'."
        )

    mesh = expect_mesh(obj)
    mesh_world = obj.matrix_world

    bone_name = resolve_sprite_bone(obj)
    bone_world = world_godot.get(bone_name)
    uv_layer = mesh.uv_layers.active

    polygon: list[list[float]] = []
    uvs: list[list[float]] = []
    vertex_indices: list[int] = []

    if mesh.polygons:
        first_poly = polygon_at(mesh, 0)
        verts = iter_poly_vertices(first_poly)
        loops = iter_poly_loop_indices(first_poly)
        for vi, li in zip(verts, loops, strict=False):
            v = vertex_at(mesh, vi)
            vertex_indices.append(vi)
            world_blender = mesh_world @ v.co
            world_godot_pos = world_to_godot_xy(world_blender, ppu)
            if bone_world is None:
                local = world_godot_pos
            else:
                dx = world_godot_pos.x - bone_world.x
                dy = world_godot_pos.y - bone_world.y
                cos_b = math.cos(-bone_world.rot)
                sin_b = math.sin(-bone_world.rot)
                local = Vector((dx * cos_b - dy * sin_b, dx * sin_b + dy * cos_b))
            polygon.append([round(local.x, 6), round(local.y, 6)])

            if uv_layer is not None:
                u = uv_layer.data[li].uv
                uvs.append([round(float(u.x), 6), round(1.0 - float(u.y), 6)])
            else:
                uvs.append([0.0, 0.0])

    region = region_core.resolve_region(obj, uvs)
    weights = build_sprite_weights(
        obj,
        mesh,
        vertex_indices,
        fallback_bone=bone_name,
        available_bones=set(world_godot.keys()),
    )

    poly_kwargs: _PolygonKwargs = {
        "name": obj.name,
        "bone": bone_name,
        "texture_region": region,
        "polygon": polygon,
        "uv": uvs,
    }
    texture = _per_sprite_texture(obj)
    if texture is not None:
        poly_kwargs["texture"] = texture
    if weights:
        poly_kwargs["weights"] = weights
    return PolygonSprite(**poly_kwargs)


def _iter_tex_images(obj: bpy.types.Object) -> Iterator[bpy.types.Image]:
    """Yield every linked Image referenced by the object's materials."""
    for mat in getattr(obj.data, "materials", None) or []:
        if mat is None or not getattr(mat, "use_nodes", False):
            continue
        tree = getattr(mat, "node_tree", None)
        if tree is None:
            continue
        for node in tree.nodes:
            if node.type != "TEX_IMAGE":
                continue
            image = getattr(node, "image", None)
            if image is not None:
                yield image


def _image_filename(image: bpy.types.Image) -> str | None:
    """Return the on-disk filename for an Image datablock, or a synthesised
    ``<name>.png`` when only the datablock name is set."""
    fp = str(getattr(image, "filepath", "") or "")
    if fp:
        return Path(bpy.path.abspath(fp)).name
    name = str(getattr(image, "name", ""))
    if not name:
        return None
    return name if name.lower().endswith(".png") else f"{name}.png"


def _per_sprite_texture(obj: bpy.types.Object) -> str | None:
    """Return the filename of the first Image Texture on this object's material.

    Multi-PNG fixtures (one PNG per body part - the doll convention) need
    per-sprite texture metadata so the Godot importer can resolve a unique
    image per Polygon2D / Sprite2D. Single-atlas fixtures already get their
    image via the top-level ``atlas`` field; ``texture`` here adds a
    finer-grained per-sprite override that the importer prefers.
    """
    for image in _iter_tex_images(obj):
        filename = _image_filename(image)
        if filename is not None:
            return filename
    return None


def build_sprite_frame(obj: bpy.types.Object) -> SpriteFrameSprite:
    """Emit a ``sprite_frame`` sprite entry."""
    hframes = int(read_field(obj, pg_field="hframes", cp_key="proscenio_hframes", default=1))
    vframes = int(read_field(obj, pg_field="vframes", cp_key="proscenio_vframes", default=1))
    if hframes < 1 or vframes < 1:
        raise RuntimeError(
            f"Proscenio: sprite_frame object {obj.name!r} needs hframes >= 1 "
            f"and vframes >= 1 (got hframes={hframes}, vframes={vframes})."
        )

    sf_kwargs: _SpriteFrameKwargs = {
        "type": "sprite_frame",
        "name": obj.name,
        "bone": resolve_sprite_bone(obj),
        "hframes": hframes,
        "vframes": vframes,
        "frame": int(read_field(obj, pg_field="frame", cp_key="proscenio_frame", default=0)),
        "centered": bool(
            read_field(obj, pg_field="centered", cp_key="proscenio_centered", default=True)
        ),
    }
    manual_region = region_core.manual_region_or_none(obj)
    if manual_region is not None:
        sf_kwargs["texture_region"] = manual_region
    return SpriteFrameSprite(**sf_kwargs)


def resolve_sprite_bone(obj: bpy.types.Object) -> str:
    if obj.parent_type == "BONE" and obj.parent_bone:
        return str(obj.parent_bone)
    if obj.vertex_groups:
        return str(vertex_group_at(obj, 0).name)
    return ""


def _resolve_known_groups(
    obj: bpy.types.Object,
    available_bones: set[str],
) -> dict[int, str]:
    """Return only the vertex groups whose names match real bones; warn for the rest."""
    vg_index_to_name = {int(vg.index): str(vg.name) for vg in iter_vertex_groups(obj)}
    known = {idx: name for idx, name in vg_index_to_name.items() if name in available_bones}
    skipped = sorted({n for n in vg_index_to_name.values() if n not in available_bones})
    for name in skipped:
        print(
            f"  WARN: sprite {obj.name!r} vertex group {name!r} has no "
            f"matching bone - dropping from weights"
        )
    return known


def _vertex_bone_weights(
    vertex: bpy.types.MeshVertex,
    known_groups: dict[int, str],
) -> dict[str, float]:
    """Sum per-bone weights for a single mesh vertex, ignoring unknown groups."""
    out: dict[str, float] = {}
    for vg in vertex.groups:
        bone = known_groups.get(int(vg.group))
        if bone is not None:
            out[bone] = out.get(bone, 0.0) + float(vg.weight)
    return out


def build_sprite_weights(
    obj: bpy.types.Object,
    mesh: bpy.types.Mesh,
    vertex_indices: list[int],
    *,
    fallback_bone: str,
    available_bones: set[str],
) -> list[Weight]:
    """Collect skinning weights from ``obj``'s vertex groups (the skinning-weights wire format)."""
    if not obj.vertex_groups or not vertex_indices:
        return []

    known_groups = _resolve_known_groups(obj, available_bones)
    if not known_groups:
        raise RuntimeError(
            f"Proscenio: sprite {obj.name!r} has vertex groups but none "
            f"resolve to bones in the armature - fix the group names or "
            f"remove them so the sprite can use rigid attach."
        )

    n = len(vertex_indices)
    bone_to_values: dict[str, list[float]] = {name: [0.0] * n for name in known_groups.values()}
    if fallback_bone and fallback_bone in available_bones:
        bone_to_values.setdefault(fallback_bone, [0.0] * n)

    for slot, mesh_vi in enumerate(vertex_indices):
        weights_here = _vertex_bone_weights(vertex_at(mesh, mesh_vi), known_groups)
        total = sum(weights_here.values())
        if total > _WEIGHT_EPS:
            for bone, w in weights_here.items():
                bone_to_values[bone][slot] = w / total
        elif fallback_bone in bone_to_values:
            bone_to_values[fallback_bone][slot] = 1.0

    return [
        Weight(bone=bone, values=[round(v, 6) for v in values])
        for bone, values in bone_to_values.items()
        if any(abs(v) > _WEIGHT_EPS for v in values)
    ]
