"""Quick armature modal operator (SPEC 005.1.d.3, SPEC 012.1).

Note: this file deliberately does NOT use ``from __future__ import
annotations``. Blender 5.1's RNA metaclass evaluates operator
annotations eagerly via ``isinstance(value, _PropertyDeferred)``;
PEP 563 leaves the values as strings and the check fails silently,
so ``bpy.props.*Property`` annotations never promote to RNA properties.
Same constraint applies to every other ``bpy.types.Operator`` /
``PropertyGroup`` / ``Panel`` subclass in the addon - see SPEC 012.1
post-mortem in ``tests/BUGS_FOUND.md``.
"""

import contextlib
from typing import Any, ClassVar

import bpy
from bpy.props import BoolProperty
from mathutils import Quaternion, Vector

from ..core.bpy_helpers.modal_overlay import (  # type: ignore[import-not-found]
    PanelAlign,
    draw_circle_3d,
    draw_line_3d,
    draw_text_panel_2d,
)
from ..core.bpy_helpers.viewport_math import (  # type: ignore[import-not-found]
    mouse_event_to_plane_point,
)
from ..core.report import report_error, report_info, report_warn  # type: ignore[import-not-found]
from ..core.viewport_state import is_front_ortho  # type: ignore[import-not-found]

_QUICK_RIG_NAME = "Proscenio.QuickRig"

_PREVIEW_COLOR = (1.0, 0.6, 0.0, 0.9)
_PREVIEW_COLOR_INVALID = (0.9, 0.25, 0.25, 0.85)
_ANCHOR_RADIUS = 0.05
_ANCHOR_SEGMENTS = 12
_PREVIEW_LINE_WIDTH = 2.0

_CHEATSHEET_LINES = (
    "Quick Armature",
    "drag = bone  |  Shift = chain  |  Esc/RMB = exit  |  Enter = confirm",
)
_CHEATSHEET_OUTSIDE_WARNING = "cursor outside canvas - move back to author bones"
_CHEATSHEET_MARGIN_PX = 24
_CHEATSHEET_ALIGN: PanelAlign = "bottom-center"
_CHEATSHEET_WARNING_TEXT_COLOR = (1.0, 0.55, 0.55, 1.0)

_FRONT_ORTHO_TOLERANCE = 1e-4


class PROSCENIO_OT_quick_armature(bpy.types.Operator):
    """Click-drag in the viewport to author bones rapidly (5.1.d.3, 012.1)."""

    bl_idname = "proscenio.quick_armature"
    bl_label = "Proscenio: Quick Armature"
    bl_description = (
        "Click-drag in the 3D viewport to draw a bone (head -> tail). "
        "Hold Shift to chain onto the previous bone. Esc or right-click to exit."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO", "BLOCKING"}

    lock_to_front_ortho: BoolProperty(  # type: ignore[valid-type]
        name="Lock to Front Orthographic",
        description=(
            "Switch to Front Orthographic on invoke and restore the previous "
            "view on exit. Uncheck to author from any view (the picture plane "
            "is still locked to Y=0)."
        ),
        default=True,
    )

    # Modal state - set in invoke, mutated in modal. Class-level defaults
    # exist so mypy can resolve the attributes; per-invoke assignment in
    # invoke() ensures every modal session starts clean.
    _drag_head: ClassVar[tuple[float, float, float] | None] = None
    _last_bone_name: ClassVar[str] = ""
    _shift_held: ClassVar[bool] = False
    _cursor_world: ClassVar[tuple[float, float, float] | None] = None
    _preview_handle_3d: ClassVar[Any] = None
    _cheatsheet_handle_2d: ClassVar[Any] = None
    _created_armature_this_session: ClassVar[bool] = False
    _restore_view_perspective: ClassVar[str | None] = None
    _restore_view_location: ClassVar[Vector | None] = None
    _restore_view_rotation: ClassVar[Quaternion | None] = None
    _restore_view_distance: ClassVar[float] = 0.0
    _restore_region_data: ClassVar[bpy.types.RegionView3D | None] = None
    _post_snap_view_location: ClassVar[Vector | None] = None
    _post_snap_view_rotation: ClassVar[Quaternion | None] = None
    _post_snap_view_distance: ClassVar[float] = 0.0
    _restore_selected_names: ClassVar[tuple[str, ...]] = ()
    _restore_active_name: ClassVar[str] = ""
    _did_auto_snap: ClassVar[bool] = False
    _invoke_area: ClassVar[bpy.types.Area | None] = None
    _invoke_region: ClassVar[bpy.types.Region | None] = None
    _cursor_in_canvas: ClassVar[bool] = True
    _cursor_screen_x: ClassVar[int] = 0
    _cursor_screen_y: ClassVar[int] = 0
    _cursor_warning_handle_2d: ClassVar[Any] = None

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.area is not None and context.area.type == "VIEW_3D")

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        if context.area is None or context.area.type != "VIEW_3D":
            report_warn(self, "must run in a 3D viewport")
            return {"CANCELLED"}
        cls = type(self)
        # Defend against double-invoke: if a previous modal is still
        # alive (handlers registered, ClassVar state lingering), sweep
        # the stale handlers before starting a fresh session. Without
        # this, the cheatsheet/preview overlays stack and the previous
        # modal session continues running invisibly.
        if (
            cls._preview_handle_3d is not None
            or cls._cheatsheet_handle_2d is not None
            or cls._cursor_warning_handle_2d is not None
        ):
            self._unregister_handlers()
            workspace = context.workspace
            if workspace is not None:
                workspace.status_text_set(None)

        cls._drag_head = None
        cls._last_bone_name = ""
        cls._shift_held = False
        cls._cursor_world = None
        cls._cursor_in_canvas = True
        cls._cursor_screen_x = 0
        cls._cursor_screen_y = 0
        cls._preview_handle_3d = None
        cls._cheatsheet_handle_2d = None
        cls._cursor_warning_handle_2d = None
        cls._created_armature_this_session = False
        cls._restore_view_perspective = None
        cls._restore_region_data = None
        cls._restore_view_location = None
        cls._restore_view_rotation = None
        cls._restore_view_distance = 0.0
        cls._post_snap_view_location = None
        cls._post_snap_view_rotation = None
        cls._post_snap_view_distance = 0.0
        cls._restore_selected_names = ()
        cls._restore_active_name = ""
        cls._did_auto_snap = False
        cls._invoke_area = context.area
        # ``context.region`` is whichever region had focus when the
        # operator fired. When invoked via the N-panel button it points
        # at the UI sidebar, not the main 3D WINDOW region. Filtering
        # bone-creation events against the UI region would block every
        # click in the viewport, so resolve to the WINDOW region of
        # the same area.
        cls._invoke_region = _find_window_region(context.area)

        if self._ensure_armature(context) is None:
            report_error(self, "failed to create QuickRig armature")
            return {"CANCELLED"}

        self._snapshot_view(context)
        self._snapshot_selection(context)
        if self.lock_to_front_ortho:
            self._snap_to_front_ortho(context)

        workspace = context.workspace
        if workspace is not None:
            workspace.status_text_set(
                "Quick Armature: drag = bone | Shift = chain "
                "| Enter = confirm | Esc/RMB = exit"
            )
        self._register_handlers(context)
        context.window_manager.modal_handler_add(self)
        report_info(self, "modal active")
        return {"RUNNING_MODAL"}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        # Esc / RMB / Enter must work from any area so the user can
        # always exit the modal even if focus drifted to the Outliner.
        if _is_exit_event(event):
            cancelled = type(self)._drag_head is None and type(self)._last_bone_name == ""
            return self._exit(context, cancelled=cancelled)
        if _is_confirm_event(event):
            return self._exit(context, cancelled=False)
        in_canvas = self._event_in_invoke_region(context, event)
        # Bone authoring events only apply when the user is actually
        # interacting with the invoking 3D viewport canvas. Clicks /
        # drags over the N-panel, toolbar, header, or other overlays
        # must not turn into bone creation attempts.
        if event.type == "MOUSEMOVE":
            self._handle_mousemove(context, event, in_canvas=in_canvas)
            return {"PASS_THROUGH"}
        if event.type == "LEFTMOUSE":
            return self._handle_leftmouse_dispatch(context, event, in_canvas=in_canvas)
        return {"PASS_THROUGH"}

    def _handle_mousemove(
        self,
        context: bpy.types.Context,
        event: bpy.types.Event,
        *,
        in_canvas: bool,
    ) -> None:
        cls = type(self)
        # Track cursor position regardless of in_canvas so the preview
        # line, anchor circle, and tooltip can render at the cursor's
        # actual world / screen position. The colour + warning copy
        # signal the "outside work zone" state.
        cls._cursor_world = mouse_event_to_plane_point(
            context, event, plane_axis="Y"
        )
        cls._cursor_in_canvas = in_canvas
        cls._cursor_screen_x = event.mouse_x
        cls._cursor_screen_y = event.mouse_y
        if context.area is not None:
            context.area.tag_redraw()

    def _handle_leftmouse_dispatch(
        self,
        context: bpy.types.Context,
        event: bpy.types.Event,
        *,
        in_canvas: bool,
    ) -> set[str]:
        cls = type(self)
        if in_canvas:
            return self._handle_leftmouse(context, event)
        # PRESS over an overlay is ignored entirely. RELEASE over an
        # overlay cancels the in-flight drag so the next bone
        # authoring restarts cleanly without "bone too short" noise.
        if event.value == "RELEASE" and cls._drag_head is not None:
            cls._drag_head = None
            if context.area is not None:
                context.area.tag_redraw()
        return {"PASS_THROUGH"}

    def _event_in_invoke_region(
        self,
        _context: bpy.types.Context,
        event: bpy.types.Event,
    ) -> bool:
        # In a modal handler, ``context.region`` stays pointed at the
        # *invoke-time* region. When invoked from the N-panel button,
        # that region is the UI sidebar - filtering by ``context.region``
        # would reject every viewport click forever. Filter by the
        # cursor's window coords against the WINDOW region rect we
        # resolved at invoke time, then exclude any overlay regions
        # (UI sidebar, toolbar, header, asset shelf) that Blender
        # paints on top of the WINDOW.
        cls = type(self)
        window_region = cls._invoke_region
        area = cls._invoke_area
        if window_region is None or area is None:
            return True
        x = event.mouse_x
        y = event.mouse_y
        if not _point_in_region_rect(x, y, window_region):
            return False
        for region in area.regions:
            if region.type == "WINDOW":
                continue
            if _point_in_region_rect(x, y, region):
                return False
        return True

    def _handle_leftmouse(
        self,
        context: bpy.types.Context,
        event: bpy.types.Event,
    ) -> set[str]:
        # Proscenio's 2D-cutout convention authors bones in the XZ
        # picture plane (Y=0). The legacy Y=Z-up projection put bones in
        # the ground plane, which collapses in Front Ortho - see
        # tests/BUGS_FOUND.md.
        cls = type(self)
        if event.value == "PRESS":
            cls._drag_head = mouse_event_to_plane_point(context, event, plane_axis="Y")
            cls._shift_held = bool(event.shift)
            if context.area is not None:
                context.area.tag_redraw()
            return {"RUNNING_MODAL"}
        if event.value != "RELEASE":
            return {"RUNNING_MODAL"}
        head = cls._drag_head
        cls._drag_head = None
        if head is None:
            return {"RUNNING_MODAL"}
        tail = mouse_event_to_plane_point(context, event, plane_axis="Y")
        if tail is None:
            return {"RUNNING_MODAL"}
        if (Vector(tail) - Vector(head)).length < 1e-4:
            report_info(self, "bone too short, skipped")
            if context.area is not None:
                context.area.tag_redraw()
            return {"RUNNING_MODAL"}
        self._create_bone(context, head, tail, parent_to_last=cls._shift_held)
        if context.area is not None:
            context.area.tag_redraw()
        return {"RUNNING_MODAL"}

    def execute(self, _context: bpy.types.Context) -> set[str]:
        # Quick armature is modal-only; F3 search routes through invoke.
        return {"FINISHED"}

    def cancel(self, context: bpy.types.Context) -> None:
        # Blender calls ``cancel`` when the modal is killed externally
        # (window close, file load). Mirror the user-driven exit path.
        self._exit(context, cancelled=True)

    def _ensure_armature(self, context: bpy.types.Context) -> bpy.types.Object | None:
        existing = context.scene.objects.get(_QUICK_RIG_NAME)
        if existing is not None and existing.type == "ARMATURE":
            return existing
        arm_data = bpy.data.armatures.new(_QUICK_RIG_NAME)
        arm_obj = bpy.data.objects.new(_QUICK_RIG_NAME, arm_data)
        context.scene.collection.objects.link(arm_obj)
        type(self)._created_armature_this_session = True
        return arm_obj

    def _create_bone(
        self,
        context: bpy.types.Context,
        head: tuple[float, float, float],
        tail: tuple[float, float, float],
        *,
        parent_to_last: bool,
    ) -> None:
        armature = context.scene.objects.get(_QUICK_RIG_NAME)
        if armature is None:
            return
        prev_active = context.view_layer.objects.active
        prev_selected = [
            obj for obj in context.view_layer.objects if obj.select_get()
        ]
        for obj in context.view_layer.objects:
            obj.select_set(False)
        armature.select_set(True)
        context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode="EDIT")
        bone_name = ""
        try:
            edit_bones = armature.data.edit_bones
            bone_name = f"qbone.{len(edit_bones):03d}"
            new_bone = edit_bones.new(bone_name)
            new_bone.head = Vector(head)
            new_bone.tail = Vector(tail)
            last = type(self)._last_bone_name
            if parent_to_last and last and last in edit_bones:
                new_bone.parent = edit_bones[last]
                new_bone.use_connect = False
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")
            # Restore prior selection set + active so the user's "frame
            # selected" (numpad-period) keeps working outside the modal.
            for obj in context.view_layer.objects:
                obj.select_set(False)
            for obj in prev_selected:
                obj.select_set(True)
            if prev_active is not None:
                context.view_layer.objects.active = prev_active
        if bone_name:
            type(self)._last_bone_name = bone_name
            report_info(self, f"'{bone_name}' added to {_QUICK_RIG_NAME}")

    def _snapshot_view(self, context: bpy.types.Context) -> None:
        rv3d = getattr(context, "region_data", None)
        if rv3d is None:
            return
        cls = type(self)
        cls._restore_region_data = rv3d
        cls._restore_view_perspective = rv3d.view_perspective
        cls._restore_view_location = rv3d.view_location.copy()
        cls._restore_view_rotation = rv3d.view_rotation.copy()
        cls._restore_view_distance = float(rv3d.view_distance)
        _log_view("invoke (pre-snap)", rv3d)

    def _snapshot_selection(self, context: bpy.types.Context) -> None:
        cls = type(self)
        selected = [obj.name for obj in context.view_layer.objects if obj.select_get()]
        cls._restore_selected_names = tuple(selected)
        active = context.view_layer.objects.active
        cls._restore_active_name = active.name if active is not None else ""

    def _snap_to_front_ortho(self, context: bpy.types.Context) -> None:
        rv3d = getattr(context, "region_data", None)
        if rv3d is None:
            return
        cls = type(self)
        if _rv3d_is_front_ortho(rv3d):
            cls._did_auto_snap = False
            return
        # ``view3d.view_axis`` honors the active region; the operator
        # poll already guaranteed VIEW_3D context.
        bpy.ops.view3d.view_axis(type="FRONT")
        cls._did_auto_snap = True
        cls._post_snap_view_location = rv3d.view_location.copy()
        cls._post_snap_view_rotation = rv3d.view_rotation.copy()
        cls._post_snap_view_distance = float(rv3d.view_distance)
        report_info(self, "snapped to Front Orthographic")
        _log_view("post-snap", rv3d)

    def _restore_view(self) -> None:
        cls = type(self)
        rv3d = cls._restore_region_data
        if rv3d is None:
            return
        _log_view("exit (before restore decision)", rv3d)
        if not cls._did_auto_snap:
            # User did not request snap, nothing to restore.
            self._clear_view_snapshot()
            return
        # Compare via decomposed values (location, rotation, distance)
        # rather than the raw 4x4 view_matrix. The matrix accumulates
        # float precision drift across mode-toggle round-trips even when
        # the user does not actually move the camera; decomposed values
        # stay stable.
        if not _view_pose_equal(
            rv3d.view_location,
            rv3d.view_rotation,
            float(rv3d.view_distance),
            cls._post_snap_view_location,
            cls._post_snap_view_rotation,
            cls._post_snap_view_distance,
        ):
            report_info(self, "view kept (user-moved during modal)")
            self._clear_view_snapshot()
            return
        if cls._restore_view_location is not None:
            rv3d.view_location = cls._restore_view_location
        if cls._restore_view_rotation is not None:
            rv3d.view_rotation = cls._restore_view_rotation
        rv3d.view_distance = cls._restore_view_distance
        if cls._restore_view_perspective is not None:
            rv3d.view_perspective = cls._restore_view_perspective
        report_info(self, "view restored to pre-snap")
        _log_view("exit (after restore)", rv3d)
        self._clear_view_snapshot()

    def _clear_view_snapshot(self) -> None:
        cls = type(self)
        cls._restore_view_location = None
        cls._restore_view_rotation = None
        cls._restore_view_distance = 0.0
        cls._restore_view_perspective = None
        cls._restore_region_data = None
        cls._post_snap_view_location = None
        cls._post_snap_view_rotation = None
        cls._post_snap_view_distance = 0.0
        cls._did_auto_snap = False
        cls._invoke_area = None
        cls._invoke_region = None

    def _restore_selection(self, context: bpy.types.Context) -> None:
        cls = type(self)
        names = cls._restore_selected_names
        active_name = cls._restore_active_name
        for obj in context.view_layer.objects:
            obj.select_set(obj.name in names)
        if active_name:
            target = context.view_layer.objects.get(active_name)
            if target is not None:
                context.view_layer.objects.active = target
        cls._restore_selected_names = ()
        cls._restore_active_name = ""

    def _register_handlers(self, context: bpy.types.Context) -> None:
        cls = type(self)
        cls._preview_handle_3d = bpy.types.SpaceView3D.draw_handler_add(
            _draw_preview_3d, (cls,), "WINDOW", "POST_VIEW"
        )
        cls._cheatsheet_handle_2d = bpy.types.SpaceView3D.draw_handler_add(
            _draw_cheatsheet_2d, (cls, context.region), "WINDOW", "POST_PIXEL"
        )
        cls._cursor_warning_handle_2d = bpy.types.SpaceView3D.draw_handler_add(
            _draw_cursor_warning_2d, (cls,), "WINDOW", "POST_PIXEL"
        )

    def _unregister_handlers(self) -> None:
        cls = type(self)
        if cls._preview_handle_3d is not None:
            with contextlib.suppress(ValueError, RuntimeError):
                bpy.types.SpaceView3D.draw_handler_remove(
                    cls._preview_handle_3d, "WINDOW"
                )
            cls._preview_handle_3d = None
        if cls._cheatsheet_handle_2d is not None:
            with contextlib.suppress(ValueError, RuntimeError):
                bpy.types.SpaceView3D.draw_handler_remove(
                    cls._cheatsheet_handle_2d, "WINDOW"
                )
            cls._cheatsheet_handle_2d = None
        if cls._cursor_warning_handle_2d is not None:
            with contextlib.suppress(ValueError, RuntimeError):
                bpy.types.SpaceView3D.draw_handler_remove(
                    cls._cursor_warning_handle_2d, "WINDOW"
                )
            cls._cursor_warning_handle_2d = None

    def _count_session_bones(self) -> int:
        armature = bpy.data.objects.get(_QUICK_RIG_NAME)
        if armature is None or armature.type != "ARMATURE":
            return 0
        return len(armature.data.bones)

    def _sweep_empty_armature(self) -> None:
        cls = type(self)
        if not cls._created_armature_this_session:
            return
        armature = bpy.data.objects.get(_QUICK_RIG_NAME)
        if armature is None or armature.type != "ARMATURE":
            return
        if len(armature.data.bones) > 0:
            return
        data = armature.data
        bpy.data.objects.remove(armature, do_unlink=True)
        if data.users == 0:
            bpy.data.armatures.remove(data)
        cls._created_armature_this_session = False

    def _exit(self, context: bpy.types.Context, *, cancelled: bool) -> set[str]:
        cls = type(self)
        bones_created = self._count_session_bones()
        self._unregister_handlers()
        workspace = context.workspace
        if workspace is not None:
            workspace.status_text_set(None)
        self._restore_view()
        self._restore_selection(context)
        self._sweep_empty_armature()
        cls._drag_head = None
        cls._cursor_world = None
        cls._last_bone_name = ""
        cls._shift_held = False
        if context.area is not None:
            context.area.tag_redraw()
        verb = "cancelled" if cancelled else "confirmed"
        report_info(self, f"{verb} ({bones_created} bone(s) authored)")
        return {"CANCELLED"} if cancelled else {"FINISHED"}


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


def _is_exit_event(event: bpy.types.Event) -> bool:
    return event.type in {"ESC", "RIGHTMOUSE"} and event.value == "PRESS"


def _is_confirm_event(event: bpy.types.Event) -> bool:
    return event.type in {"RET", "NUMPAD_ENTER"} and event.value == "PRESS"


def _point_in_region_rect(x: int, y: int, region: bpy.types.Region) -> bool:
    """Return True when window-space ``(x, y)`` falls inside ``region``.

    All Blender regions report ``x``/``y``/``width``/``height`` in
    window pixel coords, matching ``event.mouse_x`` / ``mouse_y``.
    """
    return (
        region.x <= x <= region.x + region.width
        and region.y <= y <= region.y + region.height
    )


def _find_window_region(area: bpy.types.Area) -> bpy.types.Region | None:
    """Return the main WINDOW region of ``area`` (the actual viewport).

    The N-panel UI region, header region, and tool region all live
    inside the same area. When the operator fires from a panel button,
    ``context.region`` points at the panel, not the viewport canvas.
    """
    for region in area.regions:
        if region.type == "WINDOW":
            return region
    return None


def _view_pose_equal(
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
    precision drift across Blender mode-toggle round-trips inside the
    operator; decomposed values stay stable. Tolerances are wide enough
    to absorb that drift but tight enough that any user-driven camera
    move - including a tiny orbit - registers as a difference.
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
    return max(diff_w, diff_x, diff_y, diff_z) <= rotation_tolerance


def _rv3d_is_front_ortho(rv3d: bpy.types.RegionView3D) -> bool:
    rotation = rv3d.view_matrix.to_3x3()
    matrix_rows: list[list[float]] = [
        [float(rotation[row][col]) for col in range(3)] for row in range(3)
    ]
    return is_front_ortho(
        rv3d.view_perspective, matrix_rows, tolerance=_FRONT_ORTHO_TOLERANCE
    )


def _draw_preview_3d(cls: type[PROSCENIO_OT_quick_armature]) -> None:
    head = cls._drag_head
    cursor = cls._cursor_world
    if head is None or cursor is None:
        return
    color = _PREVIEW_COLOR if cls._cursor_in_canvas else _PREVIEW_COLOR_INVALID
    draw_line_3d(head, cursor, color, line_width=_PREVIEW_LINE_WIDTH)
    draw_circle_3d(
        head,
        _ANCHOR_RADIUS,
        color,
        plane_axis="Y",
        segments=_ANCHOR_SEGMENTS,
        line_width=_PREVIEW_LINE_WIDTH,
    )


def _draw_cheatsheet_2d(
    cls: type[PROSCENIO_OT_quick_armature],
    region: bpy.types.Region,
) -> None:
    if region is None:
        return
    lines: tuple[str, ...] = _CHEATSHEET_LINES
    if not cls._cursor_in_canvas:
        lines = (*lines, _CHEATSHEET_OUTSIDE_WARNING)
    draw_text_panel_2d(
        lines,
        region_width=region.width,
        region_height=region.height,
        align=_CHEATSHEET_ALIGN,
        margin=_CHEATSHEET_MARGIN_PX,
    )


def _draw_cursor_warning_2d(cls: type[PROSCENIO_OT_quick_armature]) -> None:
    """Render a tooltip near the cursor when it leaves the canvas."""
    if cls._cursor_in_canvas:
        return
    region = cls._invoke_region
    if region is None:
        return
    # Convert window coords to region-local coords.
    region_x = cls._cursor_screen_x - region.x
    region_y = cls._cursor_screen_y - region.y
    # Offset the tooltip so it does not sit under the cursor.
    tooltip_x = region_x + 16
    tooltip_y = region_y + 16
    draw_text_panel_2d(
        ("outside canvas",),
        region_width=region.width,
        region_height=region.height,
        align="top-left",
        margin=0,
        text_size=11,
        padding=4,
        bg_color=(0.35, 0.05, 0.05, 0.85),
        text_color=_CHEATSHEET_WARNING_TEXT_COLOR,
        origin_override=(tooltip_x, tooltip_y),
    )


def _sweep_orphan_handlers() -> None:
    """Remove draw handlers leaked across script reloads.

    Called from :func:`unregister`. Walks the operator's class
    attributes for stale handles and detaches them from
    ``SpaceView3D``. Safe to call repeatedly; missing handles are
    swallowed.
    """
    for attr in (
        "_preview_handle_3d",
        "_cheatsheet_handle_2d",
        "_cursor_warning_handle_2d",
    ):
        handle = getattr(PROSCENIO_OT_quick_armature, attr, None)
        if handle is None:
            continue
        with contextlib.suppress(ValueError, RuntimeError):
            bpy.types.SpaceView3D.draw_handler_remove(handle, "WINDOW")
        setattr(PROSCENIO_OT_quick_armature, attr, None)


_classes: tuple[type, ...] = (PROSCENIO_OT_quick_armature,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    _sweep_orphan_handlers()
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
