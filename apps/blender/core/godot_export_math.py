"""Pure Blender-world -> Godot-2D coordinate + angle math.

bpy-free: the Godot writer's per-bone, per-vertex, and per-frame projection all
sit on these four helpers - the XZ->XY screen mapping, the parent-local
``rotate_vec2``, the direction->angle, and the ``wrap_pi`` range-wrap. They live
here rather than in the bpy-bound ``exporters/godot/writer/skeleton`` module so
the pure writer tests exercise them without Blender; ``skeleton`` re-exports all
four so its existing importers stay stable.
"""

from __future__ import annotations

import math

from mathutils import Vector


def world_to_godot_xy(p: Vector, ppu: float) -> Vector:
    """Blender world (XZ plane, Y into screen) -> Godot world XY."""
    return Vector((p.x * ppu, -p.z * ppu))


def godot_world_angle_from_dir(dir_blender: Vector) -> float:
    """Angle in Godot 2D from +X axis to the projection of `dir_blender` on XZ."""
    return math.atan2(-dir_blender.z, dir_blender.x)


def rotate_vec2(dx: float, dy: float, angle: float) -> tuple[float, float]:
    """Rotate the 2D vector ``(dx, dy)`` by ``angle`` radians (CCW).

    The one home for the parent-local projection the writers share: a world
    delta rotated by ``-parent_rot`` lands in the parent's local frame (Bone2D
    position / vertex / animation-delta tracks all live parent-local).
    """
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return (dx * cos_a - dy * sin_a, dx * sin_a + dy * cos_a)


def wrap_pi(a: float) -> float:
    """Normalise an angle (radians) into the ``[-pi, pi]`` range."""
    while a > math.pi:
        a -= 2.0 * math.pi
    while a < -math.pi:
        a += 2.0 * math.pi
    return a
