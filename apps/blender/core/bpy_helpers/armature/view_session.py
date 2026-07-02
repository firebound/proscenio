"""3D-view snapshot / restore for the Quick Armature modal session.

Captures the pre-invoke view, optionally snaps to Front Orthographic, and on
exit restores the pre-snap view unless the user orbited mid-modal. Held by the
operator as a single collaborator so the view lifecycle is one object rather
than a dozen parallel ClassVars.
"""

from __future__ import annotations

from collections.abc import Callable

import bpy
from mathutils import Quaternion, Vector

from .._shared.viewport_math import (  # type: ignore[import-not-found]
    rv3d_is_front_ortho,
    view_pose_equal,
)

_Report = Callable[[str], None]


def _log_view(label: str, rv3d: bpy.types.RegionView3D) -> None:
    """Print a one-line view state snapshot to the console.

    Logs persistent (location, rotation, distance) + the active
    perspective enum. Use ``System Console`` (Window > Toggle System
    Console) to inspect the trace while authoring.
    """
    loc = rv3d.view_location
    rot = rv3d.view_rotation
    print(
        f"[Proscenio.QuickArmature] {label}: "
        f"perspective={rv3d.view_perspective} "
        f"location=({loc.x:.3f}, {loc.y:.3f}, {loc.z:.3f}) "
        f"rotation=(w={rot.w:.3f}, x={rot.x:.3f}, y={rot.y:.3f}, z={rot.z:.3f}) "
        f"distance={rv3d.view_distance:.3f}"
    )


class ViewSnapshot:
    """Records + restores the region's view around a Quick Armature session."""

    def __init__(self) -> None:
        self.region_data: bpy.types.RegionView3D | None = None
        self.perspective: str | None = None
        self.location: Vector | None = None
        self.rotation: Quaternion | None = None
        self.distance: float = 0.0
        self.post_snap_location: Vector | None = None
        self.post_snap_rotation: Quaternion | None = None
        self.post_snap_distance: float = 0.0
        self.did_auto_snap: bool = False

    def capture(self, context: bpy.types.Context) -> None:
        rv3d = getattr(context, "region_data", None)
        if rv3d is None:
            return
        self.region_data = rv3d
        self.perspective = rv3d.view_perspective
        self.location = rv3d.view_location.copy()
        self.rotation = rv3d.view_rotation.copy()
        self.distance = float(rv3d.view_distance)
        _log_view("invoke (pre-snap)", rv3d)

    def snap_to_front_ortho(self, context: bpy.types.Context, report: _Report) -> None:
        rv3d = getattr(context, "region_data", None)
        if rv3d is None:
            return
        if rv3d_is_front_ortho(rv3d):
            self.did_auto_snap = False
            return
        # ``view3d.view_axis`` honors the active region; the operator
        # poll already guaranteed VIEW_3D context.
        bpy.ops.view3d.view_axis(type="FRONT")
        self.did_auto_snap = True
        self.post_snap_location = rv3d.view_location.copy()
        self.post_snap_rotation = rv3d.view_rotation.copy()
        self.post_snap_distance = float(rv3d.view_distance)
        report("snapped to Front Orthographic")
        _log_view("post-snap", rv3d)

    def restore(self, report: _Report) -> None:
        rv3d = self.region_data
        if rv3d is None:
            return
        _log_view("exit (before restore decision)", rv3d)
        if not self.did_auto_snap:
            # User did not request snap, nothing to restore.
            self.clear()
            return
        # Compare via decomposed values (location, rotation, distance)
        # rather than the raw 4x4 view_matrix. The matrix accumulates
        # float precision drift across mode-toggle round-trips even when
        # the user does not actually move the camera; decomposed values
        # stay stable.
        if not view_pose_equal(
            rv3d.view_location,
            rv3d.view_rotation,
            float(rv3d.view_distance),
            self.post_snap_location,
            self.post_snap_rotation,
            self.post_snap_distance,
        ):
            report("view kept (user-moved during modal)")
            self.clear()
            return
        if self.location is not None:
            rv3d.view_location = self.location
        if self.rotation is not None:
            rv3d.view_rotation = self.rotation
        rv3d.view_distance = self.distance
        if self.perspective is not None:
            rv3d.view_perspective = self.perspective
        report("view restored to pre-snap")
        _log_view("exit (after restore)", rv3d)
        self.clear()

    def clear(self) -> None:
        self.__init__()
