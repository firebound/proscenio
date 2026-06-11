"""World-space geometry helpers.

bpy-bound (reads ``matrix_world`` / ``bound_box`` off the passed objects and
builds ``mathutils`` vectors), but the ``mathutils`` import is lazy so the
module stays off the package-level bpy-free contract until a helper is called -
the same pattern :mod:`viewport_math` in this package uses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy
    from mathutils import Vector


def world_geometry_center(objects: list[bpy.types.Object]) -> Vector:
    """The midpoint of the world-space axis-aligned bounds of ``objects``.

    Each object's local ``bound_box`` corners are lifted into world space
    through its ``matrix_world`` and the union AABB is taken, so the result is
    the center of the visible geometry - not any object origin, which a mesh
    with an unapplied origin leaves offset from its vertices. Returns the world
    origin when ``objects`` is empty or carries no bounds.
    """
    from mathutils import Vector

    corners: list[Vector] = []
    for obj in objects:
        matrix_world = obj.matrix_world
        corners.extend(matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not corners:
        return Vector((0.0, 0.0, 0.0))
    low = Vector(
        (
            min(c.x for c in corners),
            min(c.y for c in corners),
            min(c.z for c in corners),
        )
    )
    high = Vector(
        (
            max(c.x for c in corners),
            max(c.y for c in corners),
            max(c.z for c in corners),
        )
    )
    return (low + high) * 0.5
