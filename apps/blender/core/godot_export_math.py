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

from mathutils import Matrix, Vector


def world_to_godot_xy(p: Vector, ppu: float) -> Vector:
    """Blender world (XZ plane, Y into screen) -> Godot world XY."""
    return Vector((p.x * ppu, -p.z * ppu))


def sprite_off_picture_plane(matrix_world: Matrix, tolerance: float = 0.1) -> bool:
    """True when a sprite quad is tilted off the picture plane (edge-on risk).

    A picture-plane quad has its normal along the camera/depth axis (world Y),
    so that normal projects to zero on screen while the two quad axes project
    with full magnitude. ``sprite_rest_transform`` takes local X as horizontal
    and the longer of local Y / Z as vertical; the remaining (shorter) axis is
    the presumed normal, which must project to near zero when the quad is flat
    in the picture plane. When BOTH local Y and Z project appreciably, the
    normal is not aligned with the depth axis - the quad is tilted (a snap bone
    parent to an in-plane bone, or a hand-tilted object), and its rest
    transform would come out foreshortened. Flags exactly that case, and stays
    quiet for an in-plane rotation (which spins about the depth axis and keeps
    the normal aligned). Bpy-free; reads the world matrix by index so a
    list-of-lists test fake and a live ``mathutils.Matrix`` both work.
    """
    m = matrix_world
    y_screen = math.hypot(m[0][1], m[2][1])
    z_screen = math.hypot(m[0][2], m[2][2])
    normal_screen = min(y_screen, z_screen)
    vertical_screen = max(y_screen, z_screen)
    if vertical_screen < 1e-6:
        return False  # degenerate; mesh-flatness owns a zero-area quad
    return normal_screen > tolerance * vertical_screen


def sprite_rest_transform(
    matrix_world: Matrix,
    sign_x: float,
    ppu: float,
) -> tuple[tuple[float, float], float, tuple[float, float]]:
    """Absolute Godot rest transform (position px, rotation rad, scale) of a sprite.

    Reads the object's 4x4 world matrix by row/column indexing (works for
    ``mathutils.Matrix`` and the nested-sequence test stand-in): translation
    from the fourth column through the XZ->XY screen mapping, the screen
    rotation as the angle of the local X axis projected on the picture plane,
    and the scale as the screen-projected lengths of the horizontal and
    vertical in-plane axes. Sprite quads carry two authoring conventions
    (PSD-imported planes are flat in local XZ; a hand-made Blender plane is
    local XY stood up 90 degrees on X), so which local axis is the screen
    vertical differs per object - but the screen projection zeroes whichever
    local axis points into the depth (world Y), so the vertical basis is
    simply the longer of the two projected candidates. ``sign_x`` (the sign
    of the object's local X scale) cancels an authored horizontal mirror
    before the angle read so a flipped sprite does not masquerade as a
    180-degree rotation - mirrors travel as ``flip_h`` / ``flip_v`` flags and
    the returned scale is magnitudes only.
    """
    m = matrix_world
    position = (m[0][3] * ppu, -m[2][3] * ppu)
    # Screen projection (x, -z) of the three local basis columns.
    x_screen = (m[0][0], -m[2][0])
    y_screen = (m[0][1], -m[2][1])
    z_screen = (m[0][2], -m[2][2])
    rotation = math.atan2(x_screen[1] * sign_x, x_screen[0] * sign_x)
    vertical = max(y_screen, z_screen, key=lambda v: math.hypot(*v))
    scale = (math.hypot(*x_screen), math.hypot(*vertical))
    return position, rotation, scale


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
