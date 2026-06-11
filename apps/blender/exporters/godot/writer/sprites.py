"""Element emission: mesh (polygon body) + sprite (frame metadata) + weights pipeline."""

from __future__ import annotations

import math
from typing import Literal, NotRequired, TypedDict

import bpy
from mathutils import Vector
from proscenio_models import MeshElement, SpriteElement, Weight

from ....core._shared import region as region_core
from ....core._shared.material_images import iter_material_images
from ....core._shared.pg_cp_fallback import read_field
from ....core.bpy_helpers._shared._bpy_compat import (
    expect_mesh,
    iter_poly_loop_indices,
    iter_poly_vertices,
    iter_polygons,
    iter_vertex_groups,
    object_color,
    vertex_at,
    vertex_group_at,
)
from .scene_discovery import image_filename
from .skeleton import BoneWorld, world_to_godot_xy

_WEIGHT_EPS = 1e-9

# Mirrors the PSD importer's per-layer depth stamp (planes.Z_EPSILON): the
# importer writes object Y = z_order * this, with z_order 0 = front. Kept as a
# local constant rather than imported so the exporter does not depend on the
# importer; the two are coupled by the format convention, not by code.
_DEPTH_EPSILON = 0.001
_OPAQUE_WHITE = [1.0, 1.0, 1.0, 1.0]


class _PolygonKwargs(TypedDict):
    """Constructor kwargs for ``MeshElement``.

    ``texture`` / ``weights`` are ``NotRequired`` so they are passed only when
    present; an explicit ``None`` would serialise as ``"field": null`` under
    exclude_unset and drift the goldens.
    """

    name: str
    bone: str
    texture_region: list[float]
    polygon: list[list[float]]
    uv: list[list[float]]
    polygons: NotRequired[list[list[int]]]
    texture: NotRequired[str]
    weights: NotRequired[list[Weight]]
    modulate: NotRequired[list[float]]
    z_index: NotRequired[int]


class _SpriteFrameKwargs(TypedDict):
    """Constructor kwargs for ``SpriteElement``; ``texture_region`` is omitted
    in auto mode and set only for manual regions."""

    type: Literal["sprite"]
    name: str
    bone: str
    hframes: int
    vframes: int
    frame: int
    centered: bool
    texture_region: NotRequired[list[float]]
    modulate: NotRequired[list[float]]
    z_index: NotRequired[int]
    flip_h: NotRequired[bool]
    flip_v: NotRequired[bool]
    offset: NotRequired[list[float]]


def _build_polygon_topology(
    faces: list[list[tuple[int, int]]],
) -> tuple[list[tuple[int, int]], list[list[int]]]:
    """Dedup ``(vertex_index, loop_index)`` pairs across faces into one list.

    Returns the ordered pairs in first-seen order plus per-face index arrays
    into that order - the shape Godot's ``Polygon2D.polygon`` (positions) +
    ``Polygon2D.polygons`` (per-face indices) expects. The retained loop index
    lets the caller stamp each shared vertex's UV from one of its corners;
    planar cutout UVs are consistent across a vertex's loops.
    """
    order: list[tuple[int, int]] = []
    seen: dict[int, int] = {}
    polygons: list[list[int]] = []
    for face in faces:
        emitted: list[int] = []
        for vi, li in face:
            if vi not in seen:
                seen[vi] = len(order)
                order.append((vi, li))
            emitted.append(seen[vi])
        polygons.append(emitted)
    return order, polygons


def _derive_modulate(obj: bpy.types.Object) -> list[float] | None:
    """RGBA tint from the native object color, or None when opaque white.

    Reads ``Object.color`` so appearance needs no new authoring surface; an
    object with no tint emits nothing and keeps the goldens stable.
    """
    color = [round(c, 6) for c in object_color(obj)]
    return None if color == _OPAQUE_WHITE else color


def _derive_z_index(obj: bpy.types.Object) -> int | None:
    """Draw order from the PSD-stamped depth (object Y), or None at the front.

    The PSD import stamps ``object.location.y = z_order * Z_EPSILON`` with
    z_order 0 = front; Godot draws a higher ``z_index`` on top, so negate to
    keep the authored stacking. A flat rig (Y = 0) emits nothing.
    """
    z = -round(obj.location.y / _DEPTH_EPSILON)
    return z or None


def _derive_flips(obj: bpy.types.Object) -> tuple[bool | None, bool | None]:
    """Flip flags from negative local scale signs (sprite only).

    A rigid sprite has no exported vertices to bake a mirror into, so the
    sign of the local scale becomes a Sprite2D flag. The quad is authored in
    local XY then stood up 90deg on X, so local X is horizontal and local Y
    vertical. A non-negative axis emits nothing.
    """
    flip_h = True if obj.scale.x < 0 else None
    flip_v = True if obj.scale.y < 0 else None
    return flip_h, flip_v


def _compute_sprite_offset(obj: bpy.types.Object, ppu: float) -> list[float] | None:
    """Sprite2D pixel offset from the object origin to its quad centre.

    A rigid sprite renders centred on its node origin (the bone attach
    point); when the authored pivot sits away from the quad centre the
    texture must shift by that gap or it lands in the wrong place. Projects
    the local mesh-bounds centre and the origin through the same Godot screen
    mapping the mesh path uses, then returns their difference. None when
    origin and centre coincide (no authored pivot) or the object carries no
    geometry. Reads ``mesh.vertices`` rather than ``bound_box`` so the bounds
    are current without a depsgraph refresh.
    """
    mesh = getattr(obj, "data", None)
    vertices = getattr(mesh, "vertices", None)
    if not vertices:
        return None
    xs = [v.co.x for v in vertices]
    ys = [v.co.y for v in vertices]
    zs = [v.co.z for v in vertices]
    local_center = Vector(
        (
            (min(xs) + max(xs)) / 2.0,
            (min(ys) + max(ys)) / 2.0,
            (min(zs) + max(zs)) / 2.0,
        )
    )
    matrix_world = obj.matrix_world
    center_godot = world_to_godot_xy(matrix_world @ local_center, ppu)
    origin_godot = world_to_godot_xy(matrix_world.translation, ppu)
    offset = [
        round(center_godot.x - origin_godot.x, 6),
        round(center_godot.y - origin_godot.y, 6),
    ]
    return None if offset == [0.0, 0.0] else offset


def build_element(
    obj: bpy.types.Object,
    world_godot: dict[str, BoneWorld],
    ppu: float,
) -> MeshElement | SpriteElement:
    """Build an element entry. The kind is read from
    ``Object.proscenio.element_type`` (PropertyGroup), falling back to the
    legacy ``proscenio_type`` Custom Property when the PropertyGroup is
    unavailable (default ``"mesh"``).
    """
    element_type: str = str(
        read_field(obj, pg_field="element_type", cp_key="proscenio_type", default="mesh")
    )
    if element_type == "sprite":
        return build_sprite(obj, ppu)
    if element_type != "mesh":
        raise RuntimeError(
            f"Proscenio: object {obj.name!r} has unknown element_type "
            f"{element_type!r}; expected 'mesh' or 'sprite'."
        )

    mesh = expect_mesh(obj)
    mesh_world = obj.matrix_world

    bone_name = resolve_sprite_bone(obj)
    bone_world = world_godot.get(bone_name)
    uv_layer = mesh.uv_layers.active

    # Whole-mesh emission: every face's vertices, deduplicated, plus per-face
    # index arrays. Emitting only the first polygon silently truncated any
    # multi-island or triangulated (automesh) mesh to one face.
    faces = [
        list(zip(iter_poly_vertices(poly), iter_poly_loop_indices(poly), strict=False))
        for poly in iter_polygons(mesh)
    ]
    vertex_order, face_indices = _build_polygon_topology(faces)

    polygon: list[list[float]] = []
    uvs: list[list[float]] = []
    vertex_indices: list[int] = []

    for vi, li in vertex_order:
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
    # Only multi-face meshes carry the index arrays; a single-face mesh keeps
    # the field-less shape so the existing single-quad goldens stay byte-stable.
    if len(face_indices) > 1:
        poly_kwargs["polygons"] = face_indices
    texture = _per_sprite_texture(obj)
    if texture is not None:
        poly_kwargs["texture"] = texture
    if weights:
        poly_kwargs["weights"] = weights
    modulate = _derive_modulate(obj)
    if modulate is not None:
        poly_kwargs["modulate"] = modulate
    z_index = _derive_z_index(obj)
    if z_index is not None:
        poly_kwargs["z_index"] = z_index
    return MeshElement(**poly_kwargs)


def _per_sprite_texture(obj: bpy.types.Object) -> str | None:
    """Return the filename of the first Image Texture on this object's material.

    Multi-PNG fixtures (one PNG per body part - the doll convention) need
    per-sprite texture metadata so the Godot importer can resolve a unique
    image per Polygon2D / Sprite2D. Single-atlas fixtures already get their
    image via the top-level ``atlas`` field; ``texture`` here adds a
    finer-grained per-sprite override that the importer prefers.
    """
    for image in iter_material_images(obj):
        filename = image_filename(image)
        if filename is not None:
            return filename
    return None


def build_sprite(obj: bpy.types.Object, ppu: float) -> SpriteElement:
    """Emit a ``sprite`` element entry (Sprite2D)."""
    hframes = int(read_field(obj, pg_field="hframes", cp_key="proscenio_hframes", default=1))
    vframes = int(read_field(obj, pg_field="vframes", cp_key="proscenio_vframes", default=1))
    if hframes < 1 or vframes < 1:
        raise RuntimeError(
            f"Proscenio: sprite object {obj.name!r} needs hframes >= 1 "
            f"and vframes >= 1 (got hframes={hframes}, vframes={vframes})."
        )

    sf_kwargs: _SpriteFrameKwargs = {
        "type": "sprite",
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
    modulate = _derive_modulate(obj)
    if modulate is not None:
        sf_kwargs["modulate"] = modulate
    z_index = _derive_z_index(obj)
    if z_index is not None:
        sf_kwargs["z_index"] = z_index
    flip_h, flip_v = _derive_flips(obj)
    if flip_h is not None:
        sf_kwargs["flip_h"] = flip_h
    if flip_v is not None:
        sf_kwargs["flip_v"] = flip_v
    offset = _compute_sprite_offset(obj, ppu)
    if offset is not None:
        sf_kwargs["offset"] = offset
    return SpriteElement(**sf_kwargs)


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
