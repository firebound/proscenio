"""Mesh (Polygon2D body) element emission: topology bake + region + weights."""

from __future__ import annotations

from typing import NotRequired, TypedDict

import bpy
from mathutils import Vector
from proscenio_models import MeshElement, SpriteElement, Weight

from .....core._shared import region as region_core
from .....core._shared.material_images import iter_material_images
from .....core._shared.pg_cp_fallback import read_field
from .....core.bpy_helpers._shared._bpy_compat import (
    expect_mesh,
    iter_poly_loop_indices,
    iter_poly_vertices,
    iter_polygons,
    vertex_at,
)
from ..scene_discovery import image_filename
from ..skeleton import BoneWorld, rotate_vec2, world_to_godot_xy
from ._common import _derive_modulate, _derive_z_index, resolve_sprite_bone
from .sprite_element import build_sprite
from .weights import build_sprite_weights


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
    element_type: str = str(read_field(obj, cp_key="proscenio_type", default="mesh"))
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
    # Bake polygon vertices in bone-local space ONLY for a rigid bone-parented
    # mesh (a Polygon2D child of that Bone2D in Godot). A skinned mesh is a
    # sibling of the Skeleton2D and Godot's skinning deforms it from skeleton
    # space - baking it bone-local would pre-rotate it by the bone rest (e.g. a
    # +Z spine bone rotates the torso 90deg). A bone-parented mesh that ALSO
    # carries vertex groups exports weights and so imports as a skinned sibling
    # too, so it must bake absolute as well. Object-parented meshes likewise bake
    # in absolute screen space.
    has_vertex_groups = bool(obj.vertex_groups)
    is_rigid_bone_parented = (
        obj.parent_type == "BONE" and bool(obj.parent_bone) and not has_vertex_groups
    )
    bone_world = world_godot.get(bone_name) if is_rigid_bone_parented else None
    uv_layer = mesh.uv_layers.active

    # Whole-mesh emission: every face's vertices, deduplicated, plus per-face
    # index arrays. Emitting only the first polygon silently truncated any
    # multi-island or triangulated (automesh) mesh to one face.
    # strict=True: a polygon's vertex count and loop count are always equal in
    # valid Blender mesh data, so a mismatch is corruption - fail loud rather
    # than zip-truncating to the shorter and emitting wrong topology.
    faces = [
        list(zip(iter_poly_vertices(poly), iter_poly_loop_indices(poly), strict=True))
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
            local = Vector(rotate_vec2(dx, dy, -bone_world.rot))
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
