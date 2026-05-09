"""Viewport math helpers (SPEC 009 wave 9.2).

bpy-bound -- imports ``bpy_extras.view3d_utils`` and ``mathutils``.
Lives in ``core/`` for now so the operator that uses it can stay a
thin shell; will join the rest of the bpy-bound modules under
``core/bpy_helpers/`` once wave 9.6 lands.
"""

from __future__ import annotations

import bpy


def mouse_event_to_z0_point(
    context: bpy.types.Context,
    event: bpy.types.Event,
) -> tuple[float, float, float] | None:
    """Project a viewport mouse event onto the world z=0 plane.

    Returns ``None`` when the active region is not a 3D viewport or when
    the view direction is parallel to z=0 (orthographic top view edge
    case). Falls back to ``region_2d_to_location_3d`` at depth 0 when
    the plane intersection lies behind the camera.
    """
    from bpy_extras import view3d_utils
    from mathutils import Vector

    region = context.region
    rv3d = context.region_data
    if region is None or rv3d is None:
        return None
    coord = (event.mouse_region_x, event.mouse_region_y)
    view_vec = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    if abs(view_vec.z) < 1e-6:
        fallback = view3d_utils.region_2d_to_location_3d(
            region, rv3d, coord, Vector((0.0, 0.0, 0.0))
        )
        return (float(fallback.x), float(fallback.y), 0.0)
    t = -origin.z / view_vec.z
    if t < 0.0:
        fallback = view3d_utils.region_2d_to_location_3d(
            region, rv3d, coord, Vector((0.0, 0.0, 0.0))
        )
        return (float(fallback.x), float(fallback.y), 0.0)
    point = origin + view_vec * t
    return (float(point.x), float(point.y), float(point.z))
