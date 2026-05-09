"""Skeleton emission: per-bone Godot world transforms + skeleton dict + math helpers."""

from __future__ import annotations

import math
from typing import Any

import bpy
from mathutils import Vector


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


def compute_bone_world_godot(
    armature_obj: bpy.types.Object, ppu: float
) -> dict[str, dict[str, float]]:
    """Return per-bone Godot world position (Vector2-ish) and rotation in radians."""
    armature: bpy.types.Armature = armature_obj.data
    arm_world = armature_obj.matrix_world

    out: dict[str, dict[str, float]] = {}
    for bone in armature.bones:
        head_world_blender = arm_world @ bone.head_local
        tail_world_blender = arm_world @ bone.tail_local
        head_godot = world_to_godot_xy(head_world_blender, ppu)
        dir_blender = tail_world_blender - head_world_blender
        angle = godot_world_angle_from_dir(dir_blender)
        out[bone.name] = {
            "x": head_godot.x,
            "y": head_godot.y,
            "rot": angle,
            "length": bone.length * ppu,
        }
    return out


def build_skeleton(
    armature_obj: bpy.types.Object,
    world_godot: dict[str, dict[str, float]],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Return the skeleton JSON and a per-bone rest dict in Bone2D-local space.

    The rest dict is keyed by bone name and provides ``position``,
    ``rotation``, ``scale`` so the animation builder can emit absolute
    Godot animation values (rest + delta) instead of raw deltas.
    """
    armature: bpy.types.Armature = armature_obj.data
    bones_out: list[dict[str, Any]] = []
    rest_local: dict[str, dict[str, Any]] = {}

    for bone in armature.bones:
        w = world_godot[bone.name]
        if bone.parent is None:
            local_pos = (w["x"], w["y"])
            local_rot = w["rot"]
        else:
            p = world_godot[bone.parent.name]
            dx = w["x"] - p["x"]
            dy = w["y"] - p["y"]
            cos_p = math.cos(-p["rot"])
            sin_p = math.sin(-p["rot"])
            local_pos = (dx * cos_p - dy * sin_p, dx * sin_p + dy * cos_p)
            local_rot = w["rot"] - p["rot"]
            local_rot = wrap_pi(local_rot)

        bones_out.append(
            {
                "name": bone.name,
                "parent": bone.parent.name if bone.parent else None,
                "position": [round(local_pos[0], 6), round(local_pos[1], 6)],
                "rotation": round(local_rot, 6),
                "scale": [1.0, 1.0],
                "length": round(w["length"], 6),
            }
        )
        rest_local[bone.name] = {
            "position": (local_pos[0], local_pos[1]),
            "rotation": local_rot,
            "scale": (1.0, 1.0),
        }

    return {"bones": bones_out}, rest_local
