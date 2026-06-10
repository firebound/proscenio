"""Viewport math helpers.

bpy-bound - imports ``bpy_extras.view3d_utils`` and ``mathutils``.
Lives in ``core/bpy_helpers/`` (the code-modularity split).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import bpy

from ..._shared.viewport_state import is_front_ortho

if TYPE_CHECKING:
    from mathutils import Quaternion, Vector

PlaneAxis = Literal["X", "Y", "Z"]

_FRONT_ORTHO_TOLERANCE = 1e-4


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

    fallback = view3d_utils.region_2d_to_location_3d(region, rv3d, coord, Vector((0.0, 0.0, 0.0)))
    out = [float(fallback.x), float(fallback.y), float(fallback.z)]
    out[axis_index] = 0.0
    return (out[0], out[1], out[2])


def _region_event_to_xz_at(
    context: bpy.types.Context,
    event: bpy.types.Event,
    dx: int,
    dy: int,
    *,
    guard_behind: bool,
) -> tuple[float, float] | None:
    """Project a (possibly offset) mouse event onto the Y=0 XZ plane.

    ``None`` when there is no 3D viewport or the view direction is parallel
    to the plane. With ``guard_behind`` set, an intersection behind the
    camera (``t < 0``) also returns ``None``; otherwise the extrapolated
    point is returned.
    """
    from bpy_extras import view3d_utils

    region = context.region
    rv3d = context.region_data
    if region is None or rv3d is None:
        return None
    coord = (event.mouse_region_x + dx, event.mouse_region_y + dy)
    origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    if abs(direction.y) < 1e-9:
        return None
    t = -origin.y / direction.y
    if guard_behind and t < 0:
        return None
    hit = origin + direction * t
    return (hit.x, hit.z)


def region_event_to_xz(
    context: bpy.types.Context, event: bpy.types.Event
) -> tuple[float, float] | None:
    """Project a mouse event onto the Y=0 XZ plane, returning ``(x, z)``.

    Unlike :func:`mouse_event_to_plane_point`, this returns ``None`` (no
    region_2d_to_location_3d fallback) when the view direction is parallel
    to the plane - the automesh authoring modal treats that as "no pick".
    A behind-camera intersection is left unguarded here (the lenient main
    pick path).
    """
    return _region_event_to_xz_at(context, event, 0, 0, guard_behind=False)


def region_event_to_xz_offset(
    context: bpy.types.Context, event: bpy.types.Event, dx: int = 0, dy: int = 0
) -> tuple[float, float] | None:
    """Project an offset pixel position onto the Y=0 XZ plane.

    Converts a screen-space pixel radius into a world-space distance for
    pick hit-testing without assuming a fixed world threshold. Returns
    ``None`` on a parallel view or when the intersection lies behind the
    camera (``t < 0``).
    """
    return _region_event_to_xz_at(context, event, dx, dy, guard_behind=True)


def point_in_region_rect(x: int, y: int, region: bpy.types.Region) -> bool:
    """Return True when window-space ``(x, y)`` falls inside ``region``.

    All Blender regions report ``x``/``y``/``width``/``height`` in window
    pixel coords, matching ``event.mouse_x`` / ``mouse_y``.
    """
    return bool(
        region.x <= x <= region.x + region.width and region.y <= y <= region.y + region.height
    )


def find_window_region(area: bpy.types.Area) -> bpy.types.Region | None:
    """Return the main WINDOW region of ``area`` (the actual viewport).

    The N-panel UI region, header region, and tool region all live inside
    the same area. When an operator fires from a panel button,
    ``context.region`` points at the panel, not the viewport canvas.
    """
    for region in area.regions:
        if region.type == "WINDOW":
            return region
    return None


def view_pose_equal(
    loc: Vector,
    rot: Quaternion,
    dist: float,
    other_loc: Vector | None,
    other_rot: Quaternion | None,
    other_dist: float,
    location_tolerance: float = 1e-3,
    rotation_tolerance: float = 1e-3,
    distance_tolerance: float = 1e-3,
) -> bool:
    """Compare two RegionView3D poses via decomposed components.

    Matrix-based comparison (via ``view_matrix``) accumulates float
    precision drift across Blender mode-toggle round-trips; decomposed
    values stay stable. Tolerances are wide enough to absorb that drift
    but tight enough that any user-driven camera move - including a tiny
    orbit - registers as a difference.
    """
    if other_loc is None or other_rot is None:
        return True
    if (loc - other_loc).length > location_tolerance:
        return False
    if abs(dist - other_dist) > distance_tolerance:
        return False
    diff_w = abs(rot.w - other_rot.w)
    diff_x = abs(rot.x - other_rot.x)
    diff_y = abs(rot.y - other_rot.y)
    diff_z = abs(rot.z - other_rot.z)
    return bool(max(diff_w, diff_x, diff_y, diff_z) <= rotation_tolerance)


def rv3d_is_front_ortho(rv3d: bpy.types.RegionView3D) -> bool:
    """True when ``rv3d`` is in the Front Orthographic view (within tolerance)."""
    rotation = rv3d.view_matrix.to_3x3()
    matrix_rows: list[list[float]] = [
        [float(rotation[row][col]) for col in range(3)] for row in range(3)
    ]
    return bool(
        is_front_ortho(rv3d.view_perspective, matrix_rows, tolerance=_FRONT_ORTHO_TOLERANCE)
    )
