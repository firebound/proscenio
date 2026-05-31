"""Pure-Python 2D geometry helpers shared across Proscenio features.

bpy-free. Lives in ``core/`` so unit tests + the headless validator
can import without booting Blender. Domain-agnostic; anything
beyond a primitive XZ math op belongs in a feature module.

Conventions for the XZ plane (the quick-armature spec D11 axis lock + the weight-paint-automesh spec
automesh):

- Coordinates are ``(x, z)`` tuples in world units (Y is locked
  to the picture plane).
- "Point" = ``Point2D`` alias = ``tuple[float, float]``.
- "Triangle" = three ``Point2D`` vertices in any winding order.
"""

from __future__ import annotations

Point2D = tuple[float, float]
Triangle2D = tuple[Point2D, Point2D, Point2D]


def point_in_triangle_xz(point: Point2D, triangle: Triangle2D) -> bool:
    """Half-plane test for a point against an XZ-projected triangle.

    Returns True for the closed triangle (boundary included). Order
    of triangle vertices does not matter (the test compares signs of
    the three sub-triangle cross products and accepts the point when
    all three have the same sign or any is zero).
    """
    px, pz = point
    (ax, az), (bx, bz), (cx, cz) = triangle
    d1 = (px - bx) * (az - bz) - (ax - bx) * (pz - bz)
    d2 = (px - cx) * (bz - cz) - (bx - cx) * (pz - cz)
    d3 = (px - ax) * (cz - az) - (cx - ax) * (pz - az)
    has_neg = d1 < 0.0 or d2 < 0.0 or d3 < 0.0
    has_pos = d1 > 0.0 or d2 > 0.0 or d3 > 0.0
    return not (has_neg and has_pos)
