"""Skeleton emission: per-bone Godot world transforms + Skeleton model + math helpers."""

from __future__ import annotations

import math
from dataclasses import dataclass

import bpy
from mathutils import Vector
from proscenio_models import Bone, Skeleton

from ....core.bpy_helpers._shared._bpy_compat import expect_armature, iter_bones


@dataclass(frozen=True)
class BoneRestLocal:
    """Bone2D-local rest pose. Carried between the skeleton builder and the
    animation builder so animation tracks can emit absolute Godot values
    (rest + delta) instead of raw fcurve deltas."""

    position: tuple[float, float]
    rotation: float
    scale: tuple[float, float]


@dataclass(frozen=True)
class BoneWorld:
    """Per-bone Godot world transform: head position + rotation + bone length."""

    x: float
    y: float
    rot: float
    length: float


def world_to_godot_xy(p: Vector, ppu: float) -> Vector:
    """Blender world (XZ plane, Y into screen) -> Godot world XY."""
    return Vector((p.x * ppu, -p.z * ppu))


def godot_world_angle_from_dir(dir_blender: Vector) -> float:
    """Angle in Godot 2D from +X axis to the projection of `dir_blender` on XZ."""
    return math.atan2(-dir_blender.z, dir_blender.x)


def wrap_pi(a: float) -> float:
    while a > math.pi:
        a -= 2.0 * math.pi
    while a < -math.pi:
        a += 2.0 * math.pi
    return a


def compute_bone_world_godot(armature_obj: bpy.types.Object, ppu: float) -> dict[str, BoneWorld]:
    """Return per-bone Godot world position (Vector2-ish) and rotation in radians."""
    armature = expect_armature(armature_obj)
    arm_world = armature_obj.matrix_world

    out: dict[str, BoneWorld] = {}
    for bone in iter_bones(armature):
        head_world_blender = arm_world @ bone.head_local
        tail_world_blender = arm_world @ bone.tail_local
        head_godot = world_to_godot_xy(head_world_blender, ppu)
        dir_blender = tail_world_blender - head_world_blender
        angle = godot_world_angle_from_dir(dir_blender)
        # Use `bone.length * ppu` (the armature-local rest length), NOT the
        # head->tail distance in Godot space. The Godot projection drops the
        # Blender Y axis (depth), so a bone pointing into the screen - the
        # common shape for a root/control bone - projects head and tail to
        # the same XZ point and would yield length 0. `bone.length` is the
        # true rest length the importer expects. (Trade-off: a non-uniformly
        # scaled armature object is not reflected here; fixtures author rigs
        # at unit scale, and the goldens lock this value.)
        out[bone.name] = BoneWorld(
            x=head_godot.x,
            y=head_godot.y,
            rot=angle,
            length=bone.length * ppu,
        )
    return out


def build_skeleton(
    armature_obj: bpy.types.Object,
    world_godot: dict[str, BoneWorld],
) -> tuple[Skeleton, dict[str, BoneRestLocal]]:
    """Return the Skeleton model and a per-bone rest dict in Bone2D-local space.

    The rest dict is keyed by bone name and provides ``position``,
    ``rotation``, ``scale`` so the animation builder can emit absolute
    Godot animation values (rest + delta) instead of raw deltas.
    """
    armature = expect_armature(armature_obj)
    bones_out: list[Bone] = []
    rest_local: dict[str, BoneRestLocal] = {}

    for bone in iter_bones(armature):
        w = world_godot[bone.name]
        if bone.parent is None:
            local_pos = (w.x, w.y)
            local_rot = w.rot
        else:
            p = world_godot[bone.parent.name]
            dx = w.x - p.x
            dy = w.y - p.y
            cos_p = math.cos(-p.rot)
            sin_p = math.sin(-p.rot)
            local_pos = (dx * cos_p - dy * sin_p, dx * sin_p + dy * cos_p)
            local_rot = wrap_pi(w.rot - p.rot)

        bones_out.append(
            Bone(
                name=bone.name,
                parent=bone.parent.name if bone.parent else None,
                position=[round(local_pos[0], 6), round(local_pos[1], 6)],
                rotation=round(local_rot, 6),
                scale=[1.0, 1.0],
                length=round(w.length, 6),
            )
        )
        rest_local[bone.name] = BoneRestLocal(
            position=(local_pos[0], local_pos[1]),
            rotation=local_rot,
            scale=(1.0, 1.0),
        )

    return Skeleton(bones=bones_out), rest_local
