"""Viewport math helpers (SPEC 009 wave 9.2).

bpy-bound - imports ``bpy_extras.view3d_utils`` and ``mathutils``.
Lives in ``core/bpy_helpers/`` (wave 9.6).
"""

from __future__ import annotations

from typing import Literal

import bpy

PlaneAxis = Literal["X", "Y", "Z"]


def mouse_event_to_plane_point(
    context: bpy.types.Context,
    event: bpy.types.Event,
    plane_axis: PlaneAxis = "Z",
) -> tuple[float, float, float] | None:
    """Project a viewport mouse event onto the world plane ``axis=0``.

    ``plane_axis`` selects which axis is held at 0. Proscenio's 2D-cutout
    workflow lays bones in the XZ picture plane (Y=0); top-down workflows
    use the ground plane (Z=0). The default ``"Z"`` preserves the
    historical behaviour from when this helper assumed top-down only.

    Returns ``None`` only when the active region is not a 3D viewport
    (no region or no region_data). When the view direction is parallel
    to the picked plane or when the intersection lies behind the camera,
    the helper falls back to ``region_2d_to_location_3d`` at depth 0 -
    it never returns ``None`` for those cases. Callers that want to
    distinguish "viewport missing" from "fallback used" should treat the
    fallback as a normal success path.
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
    axis_index = {"X": 0, "Y": 1, "Z": 2}[plane_axis]
    if abs(view_vec[axis_index]) < 1e-6:
        return _fallback_point(region, rv3d, coord, axis_index)
    t = -origin[axis_index] / view_vec[axis_index]
    if t < 0.0:
        return _fallback_point(region, rv3d, coord, axis_index)
    point = origin + view_vec * t
    out = [float(point.x), float(point.y), float(point.z)]
    out[axis_index] = 0.0
    return (out[0], out[1], out[2])


def _fallback_point(
    region: bpy.types.Region,
    rv3d: bpy.types.RegionView3D,
    coord: tuple[float, float],
    axis_index: int,
) -> tuple[float, float, float]:
    from bpy_extras import view3d_utils
    from mathutils import Vector

    fallback = view3d_utils.region_2d_to_location_3d(
        region, rv3d, coord, Vector((0.0, 0.0, 0.0))
    )
    out = [float(fallback.x), float(fallback.y), float(fallback.z)]
    out[axis_index] = 0.0
    return (out[0], out[1], out[2])
