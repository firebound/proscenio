"""Sprite emission: polygon body + sprite_frame metadata + weights pipeline."""

from __future__ import annotations

import math
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import bpy
from mathutils import Vector

from ....core import region as region_core  # type: ignore[import-not-found]
from ....core.pg_cp_fallback import read_field  # type: ignore[import-not-found]
from ._schema import SpriteFrameDict, WeightDict
from .skeleton import world_to_godot_xy

_WEIGHT_EPS = 1e-9


def build_sprite(
    obj: bpy.types.Object,
    world_godot: dict[str, dict[str, float]],
    ppu: float,
) -> dict[str, Any]:
    """Build a sprite entry. The sprite kind is read from
    ``Object.proscenio.sprite_type`` (PropertyGroup), falling back to the
    legacy ``proscenio_type`` Custom Property when the PropertyGroup is
    unavailable (default ``"polygon"``).
    """
    sprite_type: str = str(
        read_field(obj, pg_field="sprite_type", cp_key="proscenio_type", default="polygon")
    )
    if sprite_type == "sprite_frame":
        return dict(build_sprite_frame(obj))
    if sprite_type != "polygon":
        raise RuntimeError(
            f"Proscenio: object {obj.name!r} has unknown proscenio_type "
            f"{sprite_type!r}; expected 'polygon' or 'sprite_frame'."
        )

    mesh: bpy.types.Mesh = obj.data
    mesh_world = obj.matrix_world

    bone_name = resolve_sprite_bone(obj)
    bone_world = world_godot.get(bone_name)
    uv_layer = mesh.uv_layers.active

    polygon: list[list[float]] = []
    uvs: list[list[float]] = []
    vertex_indices: list[int] = []

    if mesh.polygons:
        first_poly = mesh.polygons[0]
        for vi, li in zip(first_poly.vertices, first_poly.loop_indices, strict=False):
            v = mesh.vertices[vi]
            vertex_indices.append(vi)
            world_blender = mesh_world @ v.co
            world_godot_pos = world_to_godot_xy(world_blender, ppu)
            if bone_world is None:
                local = world_godot_pos
            else:
                dx = world_godot_pos.x - bone_world["x"]
                dy = world_godot_pos.y - bone_world["y"]
                cos_b = math.cos(-bone_world["rot"])
                sin_b = math.sin(-bone_world["rot"])
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

    sprite: dict[str, Any] = {
        "name": obj.name,
        "bone": bone_name,
        "texture_region": region,
        "polygon": polygon,
        "uv": uvs,
    }
    texture = _per_sprite_texture(obj)
    if texture is not None:
        sprite["texture"] = texture
    if weights:
        sprite["weights"] = weights
    return sprite


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

    Multi-PNG fixtures (one PNG per body part -- the doll convention) need
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


def build_sprite_frame(obj: bpy.types.Object) -> SpriteFrameDict:
    """Emit a ``sprite_frame`` sprite entry."""
    hframes = int(read_field(obj, pg_field="hframes", cp_key="proscenio_hframes", default=1))
    vframes = int(read_field(obj, pg_field="vframes", cp_key="proscenio_vframes", default=1))
    if hframes < 1 or vframes < 1:
        raise RuntimeError(
            f"Proscenio: sprite_frame object {obj.name!r} needs hframes >= 1 "
            f"and vframes >= 1 (got hframes={hframes}, vframes={vframes})."
        )

    out: SpriteFrameDict = {
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
    manual = region_core.manual_region_or_none(obj)
    if manual is not None:
        out["texture_region"] = manual
    return out


def resolve_sprite_bone(obj: bpy.types.Object) -> str:
    if obj.parent_type == "BONE" and obj.parent_bone:
        return str(obj.parent_bone)
    if obj.vertex_groups:
        return str(obj.vertex_groups[0].name)
    return ""


def _resolve_known_groups(
    obj: bpy.types.Object,
    available_bones: set[str],
) -> dict[int, str]:
    """Return only the vertex groups whose names match real bones; warn for the rest."""
    vg_index_to_name = {int(vg.index): str(vg.name) for vg in obj.vertex_groups}
    known = {idx: name for idx, name in vg_index_to_name.items() if name in available_bones}
    skipped = sorted({n for n in vg_index_to_name.values() if n not in available_bones})
    for name in skipped:
        print(
            f"  WARN: sprite {obj.name!r} vertex group {name!r} has no "
            f"matching bone -- dropping from weights"
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
) -> list[WeightDict]:
    """Collect skinning weights from ``obj``'s vertex groups (SPEC 003)."""
    if not obj.vertex_groups or not vertex_indices:
        return []

    known_groups = _resolve_known_groups(obj, available_bones)
    if not known_groups:
        raise RuntimeError(
            f"Proscenio: sprite {obj.name!r} has vertex groups but none "
            f"resolve to bones in the armature -- fix the group names or "
            f"remove them so the sprite can use rigid attach."
        )

    n = len(vertex_indices)
    bone_to_values: dict[str, list[float]] = {name: [0.0] * n for name in known_groups.values()}
    if fallback_bone and fallback_bone in available_bones:
        bone_to_values.setdefault(fallback_bone, [0.0] * n)

    for slot, mesh_vi in enumerate(vertex_indices):
        weights_here = _vertex_bone_weights(mesh.vertices[mesh_vi], known_groups)
        total = sum(weights_here.values())
        if total > _WEIGHT_EPS:
            for bone, w in weights_here.items():
                bone_to_values[bone][slot] = w / total
        elif fallback_bone in bone_to_values:
            bone_to_values[fallback_bone][slot] = 1.0

    return [
        {"bone": bone, "values": [round(v, 6) for v in values]}
        for bone, values in bone_to_values.items()
        if any(abs(v) > _WEIGHT_EPS for v in values)
    ]
