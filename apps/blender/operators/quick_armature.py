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
from dataclasses import dataclass
from typing import Any, ClassVar

import bpy
from bpy.props import BoolProperty
from mathutils import Quaternion, Vector

from ..core.bpy_helpers.modal_overlay import (  # type: ignore[import-not-found]
    draw_circle_3d,
    draw_dashed_line_3d,
    draw_line_3d,
    draw_text_panel_2d,
)
from ..core.bpy_helpers.viewport_math import (  # type: ignore[import-not-found]
    mouse_event_to_plane_point,
)
from ..core.quick_armature_math import (  # type: ignore[import-not-found]
    DEFAULT_NAME_PREFIX as _DEFAULT_NAME_PREFIX_CORE,
)
from ..core.quick_armature_math import (  # type: ignore[import-not-found]
    AxisLock as _AxisLockCore,
)
from ..core.quick_armature_math import (  # type: ignore[import-not-found]
    PressMode,
)
from ..core.quick_armature_math import (  # type: ignore[import-not-found]
    apply_axis_lock as _apply_axis_lock,
)
from ..core.quick_armature_math import (  # type: ignore[import-not-found]
    format_bone_name as _format_bone_name,
)
from ..core.quick_armature_math import (  # type: ignore[import-not-found]
    resolve_press_mode as _resolve_press_mode,
)
from ..core.quick_armature_math import (  # type: ignore[import-not-found]
    resolve_press_mode_label as _resolve_press_mode_label,
)
from ..core.quick_armature_math import (  # type: ignore[import-not-found]
    sanitize_prefix as _sanitize_prefix,
)
from ..core.quick_armature_math import (  # type: ignore[import-not-found]
    snap_world_point_xz as _snap_world_point_xz,
)
from ..core.report import report_error, report_info, report_warn  # type: ignore[import-not-found]
from ..core.skeleton_target import resolve_skeleton_target  # type: ignore[import-not-found]
from ..core.viewport_state import is_front_ortho  # type: ignore[import-not-found]

AxisLock = _AxisLockCore

_QUICK_RIG_NAME = "Proscenio.QuickRig"

_PREVIEW_COLOR = (1.0, 0.6, 0.0, 0.9)  # connected (Blender modal-progress orange)
_PREVIEW_COLOR_UNPARENTED = (0.4, 0.8, 1.0, 0.9)  # cyan = no parent
_PREVIEW_COLOR_DISCONNECTED = (1.0, 0.85, 0.2, 0.9)  # yellow = parent + free head
_PREVIEW_COLOR_INVALID = (0.9, 0.25, 0.25, 0.85)
_AXIS_LINE_COLOR_X = (1.0, 0.3, 0.3, 0.9)
_AXIS_LINE_COLOR_Z = (0.3, 0.55, 1.0, 0.9)
_AXIS_LINE_HALF_LENGTH = 1000.0
_ANCHOR_RADIUS = 0.05
_ANCHOR_SEGMENTS = 12
_PREVIEW_LINE_WIDTH = 2.0

_CHEATSHEET_OUTSIDE_LABEL = "outside canvas"
_CHEATSHEET_WARNING_TEXT_COLOR = (1.0, 0.55, 0.55, 1.0)

_FRONT_ORTHO_TOLERANCE = 1e-4
_BONE_TOO_SHORT_TOLERANCE = 1e-4
_DEFAULT_NAME_PREFIX = _DEFAULT_NAME_PREFIX_CORE


@dataclass(frozen=True)
class _BoneRecord:
    """Snapshot of a bone authored during the modal session.

    Used by the in-modal undo/redo stack so we can recreate the same
    bone (or remove it) without losing geometry / parenting context.
    """

    name: str
    head: tuple[float, float, float]
    tail: tuple[float, float, float]
    parent_to_last_name: str
    connect: bool


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
    _drag_press_point: ClassVar[tuple[float, float, float] | None] = None
    _last_bone_name: ClassVar[str] = ""
    _shift_held: ClassVar[bool] = False
    _alt_held: ClassVar[bool] = False
    _press_mode: ClassVar[PressMode] = "connected"
    _target_armature_name: ClassVar[str] = _QUICK_RIG_NAME
    _cursor_world: ClassVar[tuple[float, float, float] | None] = None
    _preview_handle_3d: ClassVar[Any] = None
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
    _statusbar_appended: ClassVar[bool] = False
    _view3d_header_appended: ClassVar[bool] = False
    # Wave 12.2 state: chord vocabulary, axis lock, grid snap, undo
    _default_chain: ClassVar[bool] = True
    _name_prefix: ClassVar[str] = _DEFAULT_NAME_PREFIX
    _snap_increment: ClassVar[float] = 1.0
    _ctrl_held: ClassVar[bool] = False
    _axis_lock: ClassVar[AxisLock] = None
    _session_records: ClassVar[list[_BoneRecord]] = []
    _redo_records: ClassVar[list[_BoneRecord]] = []

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
            or cls._cursor_warning_handle_2d is not None
            or cls._statusbar_appended
            or cls._view3d_header_appended
        ):
            self._unregister_handlers()

        cls._drag_head = None
        cls._drag_press_point = None
        cls._last_bone_name = ""
        cls._shift_held = False
        cls._alt_held = False
        cls._press_mode = "connected"
        cls._target_armature_name = _QUICK_RIG_NAME
        cls._cursor_world = None
        cls._cursor_in_canvas = True
        cls._cursor_screen_x = 0
        cls._cursor_screen_y = 0
        cls._preview_handle_3d = None
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
        cls._ctrl_held = False
        cls._axis_lock = None
        cls._session_records = []
        cls._redo_records = []
        # Read PG defaults so the modal honours the document-level
        # configuration without forcing each invocation through F3
        # redo. Per-invoke override goes through the existing operator
        # options (only ``lock_to_front_ortho`` for Wave 12.2).
        pg = _resolve_quick_armature_props(context)
        cls._default_chain = bool(pg.default_chain) if pg is not None else True
        cls._name_prefix = _sanitize_prefix(
            pg.name_prefix if pg is not None else _DEFAULT_NAME_PREFIX
        )
        cls._snap_increment = (
            float(pg.snap_increment) if pg is not None else 1.0
        )
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

        # Status bar text intentionally NOT set: the STATUSBAR header
        # append (registered in _register_handlers) renders the chord
        # vocabulary with real Blender event icons in the same bar,
        # so an extra plain-text status line would just duplicate.
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
        cls = type(self)
        # Track Ctrl state on every event so MOUSEMOVE can apply grid
        # snap without waiting for a press / release transition.
        cls._ctrl_held = bool(event.ctrl)
        if _is_undo_event(event):
            self._undo_last_bone(context)
            return {"RUNNING_MODAL"}
        if _is_redo_event(event):
            self._redo_last_bone(context)
            return {"RUNNING_MODAL"}
        if _is_axis_lock_event(event):
            self._toggle_axis_lock(context, event.type)
            return {"RUNNING_MODAL"}
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

    def _toggle_axis_lock(self, context: bpy.types.Context, axis: str) -> None:
        cls = type(self)
        new_lock: AxisLock = axis if axis in {"X", "Z"} else None
        if cls._axis_lock == new_lock:
            cls._axis_lock = None
        else:
            cls._axis_lock = new_lock
        if context.area is not None:
            context.area.tag_redraw()
        report_info(self, f"axis lock = {cls._axis_lock or 'off'}")

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
        raw_point = mouse_event_to_plane_point(context, event, plane_axis="Y")
        cls._cursor_world = self._post_process_world_point(raw_point)
        cls._cursor_in_canvas = in_canvas
        cls._cursor_screen_x = event.mouse_x
        cls._cursor_screen_y = event.mouse_y
        if context.area is not None:
            context.area.tag_redraw()

    def _post_process_world_point(
        self,
        point: tuple[float, float, float] | None,
    ) -> tuple[float, float, float] | None:
        """Apply axis lock + grid snap to a raw cursor projection.

        Order matters: grid snap first (so X / Z values land on the
        configured increment), then axis lock (so the locked component
        clamps to the head position). The drag head is captured with
        the same post-processing on PRESS so head and tail share the
        snapped frame of reference.
        """
        if point is None:
            return None
        cls = type(self)
        if cls._ctrl_held:
            point = _snap_world_point_xz(point, cls._snap_increment)
        head = cls._drag_head
        if head is not None and cls._axis_lock is not None:
            point = _apply_axis_lock(head, point, cls._axis_lock)
        return point

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
            raw_press_point = mouse_event_to_plane_point(
                context, event, plane_axis="Y"
            )
            # Apply grid snap to head so chained bones share an aligned
            # origin. Axis lock is only meaningful between PRESS and
            # RELEASE so head itself is unaffected by the lock.
            if raw_press_point is not None and cls._ctrl_held:
                raw_press_point = _snap_world_point_xz(
                    raw_press_point, cls._snap_increment
                )
            cls._drag_press_point = raw_press_point
            cls._shift_held = bool(event.shift)
            cls._alt_held = bool(event.alt)
            cls._press_mode = _resolve_press_mode_label(
                shift_held=cls._shift_held,
                alt_held=cls._alt_held,
                default_chain=cls._default_chain,
            )
            # In connected mode the bone's head will snap to the parent
            # tail at commit time; reflect that in the live preview so
            # the user sees the actual bone shape (parent.tail -> cursor)
            # rather than a misleading press_point -> cursor line.
            cls._drag_head = self._effective_drag_head(
                raw_press_point, cls._press_mode
            )
            if context.area is not None:
                context.area.tag_redraw()
            return {"RUNNING_MODAL"}
        if event.value != "RELEASE":
            return {"RUNNING_MODAL"}
        head = cls._drag_head
        cls._drag_head = None
        cls._drag_press_point = None
        if head is None:
            return {"RUNNING_MODAL"}
        raw_tail = mouse_event_to_plane_point(context, event, plane_axis="Y")
        tail = self._resolve_release_tail(head, raw_tail)
        if tail is None:
            return {"RUNNING_MODAL"}
        if (Vector(tail) - Vector(head)).length < _BONE_TOO_SHORT_TOLERANCE:
            report_info(self, "bone too short, skipped")
            if context.area is not None:
                context.area.tag_redraw()
            return {"RUNNING_MODAL"}
        parent_to_last, connect = _resolve_press_mode(
            shift_held=cls._shift_held,
            alt_held=cls._alt_held,
            default_chain=cls._default_chain,
        )
        self._create_bone(
            context,
            head,
            tail,
            parent_to_last=parent_to_last,
            connect=connect,
        )
        if context.area is not None:
            context.area.tag_redraw()
        return {"RUNNING_MODAL"}

    def _effective_drag_head(
        self,
        press_point: tuple[float, float, float] | None,
        mode: PressMode,
    ) -> tuple[float, float, float] | None:
        """Pick the live preview head for a press based on the chord.

        Connected chords commit with ``head = parent.tail`` so the
        preview must show that anchor (not the user's press point) to
        avoid misleading the user. Unparented / disconnected chords
        keep the user's press point as head.
        """
        if press_point is None:
            return None
        if mode != "connected":
            return press_point
        cls = type(self)
        if not cls._last_bone_name:
            return press_point
        armature = bpy.data.objects.get(cls._target_armature_name)
        if armature is None or armature.type != "ARMATURE":
            return press_point
        bone = armature.data.bones.get(cls._last_bone_name)
        if bone is None:
            return press_point
        # Bone tail in world space accounts for the armature object's
        # transform; QuickRig sits at the origin in this addon, but
        # multiplying by ``matrix_world`` is safe regardless.
        tail_world = armature.matrix_world @ bone.tail_local
        return (float(tail_world.x), float(tail_world.y), float(tail_world.z))

    def _resolve_release_tail(
        self,
        head: tuple[float, float, float],
        raw_tail: tuple[float, float, float] | None,
    ) -> tuple[float, float, float] | None:
        """Apply grid snap then axis lock to a release-time tail."""
        if raw_tail is None:
            return None
        cls = type(self)
        tail: tuple[float, float, float] = raw_tail
        if cls._ctrl_held:
            tail = _snap_world_point_xz(tail, cls._snap_increment)
        if cls._axis_lock is not None:
            tail = _apply_axis_lock(head, tail, cls._axis_lock)
        return tail

    def execute(self, _context: bpy.types.Context) -> set[str]:
        # Quick armature is modal-only; F3 search routes through invoke.
        return {"FINISHED"}

    def cancel(self, context: bpy.types.Context) -> None:
        # Blender calls ``cancel`` when the modal is killed externally
        # (window close, file load). Mirror the user-driven exit path.
        self._exit(context, cancelled=True)

    def _ensure_armature(self, context: bpy.types.Context) -> bpy.types.Object | None:
        cls = type(self)
        target = resolve_skeleton_target(context)
        if target is not None:
            cls._target_armature_name = target.name
            # Propagate the resolved target to the explicit pointer so
            # the Skeleton picker visibly reflects it on the next
            # redraw. Skip when the pointer already matches to avoid
            # a redundant write triggering a depsgraph update.
            scene_props = getattr(context.scene, "proscenio", None)
            if scene_props is not None and scene_props.active_armature is not target:
                scene_props.active_armature = target
            return target
        # No explicit pointer, no active armature, no single-armature
        # heuristic - fall back to Proscenio.QuickRig (creating it on
        # first invoke).
        existing = context.scene.objects.get(_QUICK_RIG_NAME)
        if existing is not None and existing.type == "ARMATURE":
            # Always store the actual scene-object name (after Blender's
            # dedupe pass), never the literal _QUICK_RIG_NAME. If a
            # stale orphan data block exists in bpy.data, ``bpy.data
            # .objects.new(_QUICK_RIG_NAME, ...)`` returns a name like
            # ``"Proscenio.QuickRig.001"`` and storing the literal here
            # would make ``_create_bone`` silently drop every drag
            # because ``scene.objects.get("Proscenio.QuickRig")`` would
            # not find the freshly linked .001 object.
            cls._target_armature_name = existing.name
            return existing
        arm_data = bpy.data.armatures.new(_QUICK_RIG_NAME)
        arm_obj = bpy.data.objects.new(_QUICK_RIG_NAME, arm_data)
        context.scene.collection.objects.link(arm_obj)
        cls._created_armature_this_session = True
        cls._target_armature_name = arm_obj.name
        # Auto-promote the freshly created QuickRig to the explicit
        # active_armature pointer so subsequent skeleton ops see the
        # same target without surprise.
        scene_props = getattr(context.scene, "proscenio", None)
        if scene_props is not None and scene_props.active_armature is None:
            scene_props.active_armature = arm_obj
        return arm_obj

    def _create_bone(
        self,
        context: bpy.types.Context,
        head: tuple[float, float, float],
        tail: tuple[float, float, float],
        *,
        parent_to_last: bool,
        connect: bool,
    ) -> None:
        cls = type(self)
        armature = context.scene.objects.get(cls._target_armature_name)
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
        actual_head: tuple[float, float, float] = head
        try:
            edit_bones = armature.data.edit_bones
            bone_name = _format_bone_name(cls._name_prefix, len(edit_bones))
            new_bone = edit_bones.new(bone_name)
            last = cls._last_bone_name
            parent_bone = edit_bones[last] if (
                parent_to_last and last and last in edit_bones
            ) else None
            if parent_bone is not None and connect:
                # Snap head to the parent's tail so chained bones share
                # an exact junction (Blender E extrude convention).
                actual_head = (
                    float(parent_bone.tail.x),
                    float(parent_bone.tail.y),
                    float(parent_bone.tail.z),
                )
            new_bone.head = Vector(actual_head)
            new_bone.tail = Vector(tail)
            if parent_bone is not None:
                new_bone.parent = parent_bone
                new_bone.use_connect = bool(connect)
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
            cls._last_bone_name = bone_name
            cls._session_records.append(
                _BoneRecord(
                    name=bone_name,
                    head=actual_head,
                    tail=tail,
                    parent_to_last_name=last if parent_to_last else "",
                    connect=connect,
                )
            )
            # Any new bone clears the redo stack (standard semantics).
            cls._redo_records = []
            report_info(self, f"'{bone_name}' added to {cls._target_armature_name}")

    def _undo_last_bone(self, context: bpy.types.Context) -> None:
        cls = type(self)
        if not cls._session_records:
            report_info(self, "nothing to undo")
            return
        record = cls._session_records.pop()
        cls._redo_records.append(record)
        armature = context.scene.objects.get(cls._target_armature_name)
        if armature is None or armature.type != "ARMATURE":
            return
        prev_active = context.view_layer.objects.active
        armature.select_set(True)
        context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode="EDIT")
        try:
            edit_bones = armature.data.edit_bones
            if record.name in edit_bones:
                edit_bones.remove(edit_bones[record.name])
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")
            if prev_active is not None:
                context.view_layer.objects.active = prev_active
        cls._last_bone_name = (
            cls._session_records[-1].name if cls._session_records else ""
        )
        report_info(self, f"undone '{record.name}'")
        if context.area is not None:
            context.area.tag_redraw()

    def _redo_last_bone(self, context: bpy.types.Context) -> None:
        cls = type(self)
        if not cls._redo_records:
            report_info(self, "nothing to redo")
            return
        record = cls._redo_records.pop()
        # Re-create using the captured geometry. ``_create_bone`` will
        # push the record onto the session stack and clear the redo
        # stack as a side effect; restore the redo state we just popped
        # before the call so the rest of the redo history survives.
        saved_redo = list(cls._redo_records)
        self._create_bone(
            context,
            record.head,
            record.tail,
            parent_to_last=bool(record.parent_to_last_name),
            connect=record.connect,
        )
        cls._redo_records = saved_redo

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
        cls._cursor_warning_handle_2d = bpy.types.SpaceView3D.draw_handler_add(
            _draw_cursor_warning_2d, (cls,), "WINDOW", "POST_PIXEL"
        )
        # Two icon-rich hint surfaces, both sourced from Blender's
        # native UILayout API so the icons match the rest of the
        # editor: the bottom STATUSBAR (canonical modal hint home,
        # like knife tool / loop cut) and the 3D viewport header
        # (so the user does not have to look away from the canvas).
        # POST_PIXEL cheatsheet was retired - the unicode-glyph
        # approximation could never match the native icons here.
        if not cls._statusbar_appended:
            # Prepend (left) so the cheatsheet sits where Blender's
            # own modal tools place their hints; right side stays for
            # Blender's statistics widgets.
            bpy.types.STATUSBAR_HT_header.prepend(_draw_statusbar_quick_armature)
            cls._statusbar_appended = True
        if not cls._view3d_header_appended:
            bpy.types.VIEW3D_HT_header.append(_draw_view3d_header_quick_armature)
            cls._view3d_header_appended = True

    def _unregister_handlers(self) -> None:
        cls = type(self)
        if cls._preview_handle_3d is not None:
            with contextlib.suppress(ValueError, RuntimeError):
                bpy.types.SpaceView3D.draw_handler_remove(
                    cls._preview_handle_3d, "WINDOW"
                )
            cls._preview_handle_3d = None
        if cls._cursor_warning_handle_2d is not None:
            with contextlib.suppress(ValueError, RuntimeError):
                bpy.types.SpaceView3D.draw_handler_remove(
                    cls._cursor_warning_handle_2d, "WINDOW"
                )
            cls._cursor_warning_handle_2d = None
        if cls._statusbar_appended:
            with contextlib.suppress(ValueError, RuntimeError):
                bpy.types.STATUSBAR_HT_header.remove(_draw_statusbar_quick_armature)
            cls._statusbar_appended = False
        if cls._view3d_header_appended:
            with contextlib.suppress(ValueError, RuntimeError):
                bpy.types.VIEW3D_HT_header.remove(_draw_view3d_header_quick_armature)
            cls._view3d_header_appended = False

    def _count_session_bones(self) -> int:
        cls = type(self)
        armature = bpy.data.objects.get(cls._target_armature_name)
        if armature is None or armature.type != "ARMATURE":
            return 0
        return len(armature.data.bones)

    def _sweep_empty_armature(self) -> None:
        cls = type(self)
        # Only sweep the auto-created Proscenio.QuickRig - never touch
        # an active armature the user picked as target.
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
        self._restore_view()
        self._restore_selection(context)
        self._sweep_empty_armature()
        cls._drag_head = None
        cls._cursor_world = None
        cls._last_bone_name = ""
        cls._shift_held = False
        cls._ctrl_held = False
        cls._axis_lock = None
        cls._session_records = []
        cls._redo_records = []
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


def _is_undo_event(event: bpy.types.Event) -> bool:
    return (
        event.type == "Z"
        and event.value == "PRESS"
        and event.ctrl
        and not event.shift
    )


def _is_redo_event(event: bpy.types.Event) -> bool:
    return (
        event.type == "Z"
        and event.value == "PRESS"
        and event.ctrl
        and event.shift
    )


def _is_axis_lock_event(event: bpy.types.Event) -> bool:
    """X / Z press without modifiers toggles axis lock.

    Pressing with Ctrl reaches ``_is_undo_event`` first (operator
    intercepts that branch). Pressing with Shift would conflict with
    the chain modifier; for now we ignore Shift+X / Shift+Z.
    """
    return (
        event.type in {"X", "Z"}
        and event.value == "PRESS"
        and not event.ctrl
        and not event.shift
        and not event.alt
    )


def _resolve_quick_armature_props(
    context: bpy.types.Context,
) -> Any | None:
    """Return ``scene.proscenio.quick_armature`` PG, ``None`` if missing.

    Defensive lookup so headless tests / mid-reload contexts never
    crash the operator. The fallback path uses module-level defaults.
    """
    scene = getattr(context, "scene", None)
    if scene is None:
        return None
    proscenio = getattr(scene, "proscenio", None)
    if proscenio is None:
        return None
    return getattr(proscenio, "quick_armature", None)


def _build_status_bar_text(cls: type[PROSCENIO_OT_quick_armature]) -> str:
    """Short canonical form of the cheatsheet for the bottom status bar."""
    chord = (
        "drag = connected | Shift = unparented | Alt = disconnected"
        if cls._default_chain
        else "drag = unparented | Shift = connected | Alt = disconnected"
    )
    return (
        f"Quick Armature: {chord} | X/Z = axis lock | Ctrl = grid snap "
        "| Ctrl+Z = undo | Enter = confirm | Esc/RMB = exit"
    )


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
    # Axis lock guideline renders even before the drag starts so the
    # user sees the constraint before pressing.
    if head is not None and cls._axis_lock is not None:
        _draw_axis_guideline(head, cls._axis_lock)
    if head is None or cursor is None:
        return
    color = _preview_color_for(cls)
    # Disconnected mode (Alt+drag): bone gets a parent but its head
    # stays at the user's press point. Render a dashed line from the
    # parent's tail to the new head so the parent relationship stays
    # visible despite the gap.
    if cls._press_mode == "disconnected":
        parent_tail = _resolve_parent_tail_world(cls)
        if parent_tail is not None:
            draw_dashed_line_3d(parent_tail, head, color)
    draw_line_3d(head, cursor, color, line_width=_PREVIEW_LINE_WIDTH)
    draw_circle_3d(
        head,
        _ANCHOR_RADIUS,
        color,
        plane_axis="Y",
        segments=_ANCHOR_SEGMENTS,
        line_width=_PREVIEW_LINE_WIDTH,
    )
    # When the connected-mode head was snapped to the parent's tail,
    # also surface the "rejected" press point as a faint marker so the
    # user can see how far Blender dragged the head from the click.
    press_point = cls._drag_press_point
    if (
        press_point is not None
        and cls._press_mode == "connected"
        and (Vector(press_point) - Vector(head)).length > _BONE_TOO_SHORT_TOLERANCE
    ):
        draw_circle_3d(
            press_point,
            _ANCHOR_RADIUS * 0.6,
            (color[0], color[1], color[2], 0.35),
            plane_axis="Y",
            segments=_ANCHOR_SEGMENTS,
            line_width=1.0,
        )


def _resolve_parent_tail_world(
    cls: type[PROSCENIO_OT_quick_armature],
) -> tuple[float, float, float] | None:
    """Return the world-space tail of the most recent session bone.

    Used by the disconnected-mode dashed preview so the user sees the
    parent relationship even though the new bone's head sits at the
    press point (no auto-snap).
    """
    if not cls._last_bone_name:
        return None
    armature = bpy.data.objects.get(cls._target_armature_name)
    if armature is None or armature.type != "ARMATURE":
        return None
    bone = armature.data.bones.get(cls._last_bone_name)
    if bone is None:
        return None
    tail_world = armature.matrix_world @ bone.tail_local
    return (float(tail_world.x), float(tail_world.y), float(tail_world.z))


def _preview_color_for(
    cls: type[PROSCENIO_OT_quick_armature],
) -> tuple[float, float, float, float]:
    if not cls._cursor_in_canvas:
        return _PREVIEW_COLOR_INVALID
    if cls._press_mode == "unparented":
        return _PREVIEW_COLOR_UNPARENTED
    if cls._press_mode == "disconnected":
        return _PREVIEW_COLOR_DISCONNECTED
    return _PREVIEW_COLOR


def _draw_axis_guideline(
    head: tuple[float, float, float],
    axis: AxisLock,
) -> None:
    """Render an infinite-looking axis line through the drag head.

    Matches Blender's transform-axis-lock convention (X=red, Z=blue).
    The Y axis is excluded because Proscenio's authoring plane is
    Y=0 - locking Y would collapse to a point.
    """
    if axis == "X":
        start = (head[0] - _AXIS_LINE_HALF_LENGTH, head[1], head[2])
        end = (head[0] + _AXIS_LINE_HALF_LENGTH, head[1], head[2])
        color = _AXIS_LINE_COLOR_X
    elif axis == "Z":
        start = (head[0], head[1], head[2] - _AXIS_LINE_HALF_LENGTH)
        end = (head[0], head[1], head[2] + _AXIS_LINE_HALF_LENGTH)
        color = _AXIS_LINE_COLOR_Z
    else:
        return
    draw_line_3d(start, end, color, line_width=_PREVIEW_LINE_WIDTH)


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


def _emit_chord_layout(
    layout: bpy.types.UILayout,
    cls: type[PROSCENIO_OT_quick_armature],
) -> None:
    """Shared chord rendering for the STATUSBAR + 3D viewport headers.

    Uses Blender's native ``EVENT_*`` / ``MOUSE_*`` icons via
    ``layout.label(icon=...)`` so the hint visually matches Blender's
    own modal status bar (knife tool, loop cut, etc).
    """
    if cls._default_chain:
        connect_label = "connected"
        unparented_label = "unparented"
    else:
        connect_label = "unparented"
        unparented_label = "connected"

    row = layout.row(align=True)
    row.label(text="", icon="MOUSE_LMB_DRAG")
    row.label(text=connect_label)

    row = layout.row(align=True)
    row.label(text="", icon="EVENT_SHIFT")
    row.label(text="+")
    row.label(text="", icon="MOUSE_LMB_DRAG")
    row.label(text=unparented_label)

    row = layout.row(align=True)
    row.label(text="", icon="EVENT_ALT")
    row.label(text="+")
    row.label(text="", icon="MOUSE_LMB_DRAG")
    row.label(text="disconnected")

    row = layout.row(align=True)
    row.label(text="", icon="EVENT_X")
    row.label(text="/")
    row.label(text="", icon="EVENT_Z")
    row.label(text="axis lock")

    row = layout.row(align=True)
    row.label(text="", icon="EVENT_CTRL")
    row.label(text="grid snap")

    row = layout.row(align=True)
    row.label(text="", icon="EVENT_CTRL")
    row.label(text="+")
    row.label(text="", icon="EVENT_Z")
    row.label(text="undo")

    row = layout.row(align=True)
    row.label(text="", icon="EVENT_RETURN")
    row.label(text="confirm")

    row = layout.row(align=True)
    row.label(text="", icon="EVENT_ESC")
    row.label(text="exit")


def _draw_statusbar_quick_armature(
    self: bpy.types.Header,
    _context: bpy.types.Context,
) -> None:
    """Render the chord cheatsheet on the LEFT side of the STATUS BAR."""
    layout = self.layout
    _emit_chord_layout(layout, PROSCENIO_OT_quick_armature)
    # Push Blender's default statistics widgets to the right edge so
    # they keep their conventional spot.
    layout.separator_spacer()


def _draw_view3d_header_quick_armature(
    self: bpy.types.Header,
    _context: bpy.types.Context,
) -> None:
    """Render the chord cheatsheet inside the 3D viewport's own header.

    Same vocabulary + icons as the status bar; placed past Blender's
    existing header content via ``separator_spacer()`` so the hint
    sits on the right edge of the viewport header instead of pushing
    Blender's mode / select / view dropdowns around.
    """
    layout = self.layout
    layout.separator_spacer()
    _emit_chord_layout(layout, PROSCENIO_OT_quick_armature)


def _sweep_orphan_handlers() -> None:
    """Remove draw handlers leaked across script reloads.

    Called from :func:`unregister`. Walks the operator's class
    attributes for stale handles and detaches them from
    ``SpaceView3D``. Safe to call repeatedly; missing handles are
    swallowed.
    """
    for attr in (
        "_preview_handle_3d",
        "_cursor_warning_handle_2d",
    ):
        handle = getattr(PROSCENIO_OT_quick_armature, attr, None)
        if handle is None:
            continue
        with contextlib.suppress(ValueError, RuntimeError):
            bpy.types.SpaceView3D.draw_handler_remove(handle, "WINDOW")
        setattr(PROSCENIO_OT_quick_armature, attr, None)
    if getattr(PROSCENIO_OT_quick_armature, "_statusbar_appended", False):
        with contextlib.suppress(ValueError, RuntimeError):
            bpy.types.STATUSBAR_HT_header.remove(_draw_statusbar_quick_armature)
        PROSCENIO_OT_quick_armature._statusbar_appended = False
    if getattr(PROSCENIO_OT_quick_armature, "_view3d_header_appended", False):
        with contextlib.suppress(ValueError, RuntimeError):
            bpy.types.VIEW3D_HT_header.remove(_draw_view3d_header_quick_armature)
        PROSCENIO_OT_quick_armature._view3d_header_appended = False


_classes: tuple[type, ...] = (PROSCENIO_OT_quick_armature,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    _sweep_orphan_handlers()
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
