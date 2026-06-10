"""Shared helpers for skinning bpy modules (the weight-paint productivity follow-up)."""

from __future__ import annotations

from collections.abc import Iterator

import bpy

from ..automesh.base_sprite import BASE_SPRITE_GROUP_NAME

Vec3 = tuple[float, float, float]


def iter_deform_bones(armature: bpy.types.Object) -> Iterator[bpy.types.Bone]:
    """Yield each deform-flagged bone of the armature's data.

    Control bones (IK targets, helpers) are skipped - only deform bones
    drive skinning weights, the proximity bbox, and the sidecar.
    """
    for bone in armature.data.bones:
        if bone.use_deform:
            yield bone


def deform_bone_world_segments(armature: bpy.types.Object) -> list[tuple[Vec3, Vec3, str]]:
    """World-space ``(head, tail, name)`` for every deform bone.

    ``head_local`` / ``tail_local`` are transformed by the armature's
    ``matrix_world`` so the segments share the world space of the sprite
    contours and mesh verts that consume them. The 2D-XZ consumers drop the
    Y component (``(p[0], p[2])``); the 3D consumers use the tuple as-is.
    """
    matrix_world = armature.matrix_world
    segments: list[tuple[Vec3, Vec3, str]] = []
    for bone in iter_deform_bones(armature):
        head = matrix_world @ bone.head_local
        tail = matrix_world @ bone.tail_local
        segments.append(((head.x, head.y, head.z), (tail.x, tail.y, tail.z), bone.name))
    return segments


def wipe_non_base_groups(obj: bpy.types.Object) -> int:
    """Remove every vertex group except the UV-anchor base sprite group.

    Returns the number of groups removed. Callers surface it when > 0
    so users notice manually-painted groups (e.g. ``extra_decoration``)
    that bind / apply_sidecar discards.
    """
    to_remove = [g for g in obj.vertex_groups if g.name != BASE_SPRITE_GROUP_NAME]
    for group in to_remove:
        obj.vertex_groups.remove(group)
    return len(to_remove)
