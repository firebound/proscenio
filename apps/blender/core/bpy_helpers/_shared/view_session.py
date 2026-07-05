"""3D-view snapshot / restore + a front-ortho modal mixin.

``ViewSnapshot`` captures the pre-invoke view, optionally snaps to Front
Orthographic, and on exit restores the pre-snap view unless the user orbited
mid-modal. ``FrontOrthoModalMixin`` wraps that lifecycle for any interactive
authoring operator: the tools author on the flat Y=0 picture plane, so entering
from a front view removes depth ambiguity (spec 078). Quick Armature was the
first user; the mixin lets Automesh / Manual Mesh / Edit Weights share it.

Note: no ``from __future__ import annotations`` here. Blender 5.1's RNA metaclass
evaluates the ``lock_to_front_ortho`` BoolProperty annotation eagerly; PEP 563
would leave it a string and the property would silently never register (the same
constraint the operator modules document).
"""

from collections.abc import Callable

import bpy
from bpy.props import BoolProperty
from mathutils import Quaternion, Vector

from .viewport_math import (  # type: ignore[import-not-found]
    rv3d_is_front_ortho,
    view_pose_equal,
)

_Report = Callable[[str], None]


def _log_view(tag: str, label: str, rv3d: bpy.types.RegionView3D) -> None:
    """Print a one-line view state snapshot to the console.

    Logs persistent (location, rotation, distance) + the active
    perspective enum. Use ``System Console`` (Window > Toggle System
    Console) to inspect the trace while authoring.
    """
    loc = rv3d.view_location
    rot = rv3d.view_rotation
    print(
        f"[Proscenio.{tag}] {label}: "
        f"perspective={rv3d.view_perspective} "
        f"location=({loc.x:.3f}, {loc.y:.3f}, {loc.z:.3f}) "
        f"rotation=(w={rot.w:.3f}, x={rot.x:.3f}, y={rot.y:.3f}, z={rot.z:.3f}) "
        f"distance={rv3d.view_distance:.3f}"
    )


class ViewSnapshot:
    """Records + restores the region's view around an interactive session."""

    def __init__(self, tag: str = "Proscenio") -> None:
        self.tag = tag
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
        _log_view(self.tag, "invoke (pre-snap)", rv3d)

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
        _log_view(self.tag, "post-snap", rv3d)

    def restore(self, report: _Report) -> None:
        rv3d = self.region_data
        if rv3d is None:
            return
        _log_view(self.tag, "exit (before restore decision)", rv3d)
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
        _log_view(self.tag, "exit (after restore)", rv3d)
        self.clear()

    def clear(self) -> None:
        tag = self.tag
        self.__init__(tag)


class FrontOrthoModalMixin:
    """Snap the view to Front Orthographic for a modal authoring session.

    Mix into a modal operator that authors on the Y=0 picture plane. Call
    ``enter_front_ortho`` in ``invoke`` (after the precondition gate) and
    ``exit_front_ortho`` in ``_finish`` / ``cancel``. The ``lock_to_front_ortho``
    property (default on) lets the artist author from the current view instead.
    """

    # Same msgid as Quick Armature's own toggle (already translated), so sharing
    # the string keeps this mixin out of the i18n catalog as a new entry.
    lock_to_front_ortho: BoolProperty(  # type: ignore[valid-type]
        name="Lock to Front Orthographic",
        description=(
            "Switch to Front Orthographic on invoke and restore the previous "
            "view on exit. Uncheck to author from any view (the picture plane "
            "is still locked to Y=0)."
        ),
        default=True,
    )

    _front_ortho_view: ViewSnapshot | None = None

    def enter_front_ortho(
        self,
        context: bpy.types.Context,
        report: _Report,
        *,
        tag: str = "Proscenio",
    ) -> None:
        self._front_ortho_view = ViewSnapshot(tag=tag)
        self._front_ortho_view.capture(context)
        if self.lock_to_front_ortho:
            self._front_ortho_view.snap_to_front_ortho(context, report)

    def exit_front_ortho(self, report: _Report) -> None:
        view = getattr(self, "_front_ortho_view", None)
        if view is not None:
            view.restore(report)
            self._front_ortho_view = None
