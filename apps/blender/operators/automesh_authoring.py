"""Interactive modal automesh authoring operator (SPEC 013.2).

5-stage modal that previews each pipeline stage with a GPU overlay
so the artist iterates on the mesh shape before any geometry commits.
Coexists with the one-shot automesh_from_sprite operator.
"""

from __future__ import annotations

import contextlib
import traceback
from typing import ClassVar

import bpy

from ..core.bpy_helpers.automesh.authoring_overlay import (  # type: ignore[import-not-found]
    OverlayHandles,
    refresh_overlay,
    register_overlay,
    unregister_overlay,
)
from ..core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
    apply_mesh,
    compute_all_steiners,
    compute_inner_loops_for_stage,
    compute_outer,
    read_user_steiners,
    write_user_steiners,
)
from ..core.bpy_helpers.automesh.authoring_session import (  # type: ignore[import-not-found]
    AuthoringSession,
)
from ..core.bpy_helpers.automesh.authoring_session import (
    capture as capture_session,
)
from ..core.bpy_helpers.automesh.authoring_session import (
    restore as restore_session,
)
from ..core.bpy_helpers.automesh.bridge import (  # type: ignore[import-not-found]
    collect_bone_segments,
)
from ..core.report import (  # type: ignore[import-not-found]
    report_error,
    report_info,
)
from ..core.skinning.authoring_stages import (  # type: ignore[import-not-found]
    AuthoringStage,
    Point2D,
    StageOutput,
    StageParams,
)

_TIMER_INTERVAL = 0.1
_STEINER_DELETE_THRESHOLD_WORLD = 0.05
_STAGE_NAMES = {
    AuthoringStage.OUTER: "1/5 Outer contour",
    AuthoringStage.INNER_LOOPS: "2/5 Inner loops",
    AuthoringStage.USER_STEINERS: "3/5 User Steiner points (LMB add / Shift+LMB delete)",
    AuthoringStage.STEINER_PREVIEW: "4/5 Steiner preview",
    AuthoringStage.APPLY: "5/5 Apply",
}


class PROSCENIO_OT_automesh_authoring(bpy.types.Operator):
    """Multi-stage modal preview of the automesh pipeline."""

    bl_idname = "proscenio.automesh_authoring"
    bl_label = "Proscenio: Automesh Authoring"
    bl_description = (
        "Multi-stage modal preview of the automesh pipeline. Each stage "
        "(outer contour / inner loops / user Steiner points / Steiner "
        "preview / apply) surfaces a GPU overlay + slider-driven re-run "
        "so the artist iterates on the mesh shape before any geometry "
        "commits. ENTER advances; BACKSPACE goes back; ESC cancels"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    _stage: AuthoringStage
    _output: StageOutput
    _handles: OverlayHandles
    _session: AuthoringSession | None
    _last_params: StageParams | None
    _timer: bpy.types.Timer | None
    _statusbar_appended: bool = False
    _current_stage_label: str = _STAGE_NAMES[AuthoringStage.OUTER]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return False
        return _resolve_image(obj) is not None

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            report_error(self, "active object must be a mesh")
            return {"CANCELLED"}
        image = _resolve_image(obj)
        if image is None:
            report_error(
                self,
                "active mesh has no image texture - add a material with a TEX_IMAGE node first",
            )
            return {"CANCELLED"}

        self._session = capture_session(context, obj)
        params = _snapshot_params(context)
        self._last_params = params
        self._stage = AuthoringStage.OUTER
        self._output = StageOutput()
        self._handles = {"outer": None, "inner": None, "steiners": None, "user_dots": None}
        self._timer = None

        try:
            self._output.outer = compute_outer(obj, image, params)
            self._handles = register_overlay(self._stage, self._output)
            type(self)._current_stage_label = _STAGE_NAMES[self._stage]
            self._timer = context.window_manager.event_timer_add(
                _TIMER_INTERVAL, window=context.window
            )
            self._append_statusbar()
            _tag_redraw_view3d(context)
        except Exception as exc:
            report_error(self, f"Authoring setup failed: {exc} - restoring state")
            self._finish(context, cancel=True)
            return {"CANCELLED"}

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        try:
            if event.type == "ESC":
                return self._finish(context, cancel=True)
            if event.type in {"RET", "NUMPAD_ENTER"} and event.value == "PRESS":
                return self._advance(context)
            if event.type == "BACK_SPACE" and event.value == "PRESS":
                return self._retreat(context)
            if (
                self._stage == AuthoringStage.USER_STEINERS
                and event.type == "LEFTMOUSE"
                and event.value == "PRESS"
            ):
                if event.shift:
                    return self._delete_nearest_steiner(context, event)
                return self._add_steiner(context, event)
            if event.type == "TIMER" and getattr(event, "timer", None) is self._timer:
                current = _snapshot_params(context)
                if current != self._last_params:
                    self._recompute_current_stage(context, current)
                    self._last_params = current
        except Exception:
            traceback.print_exc()
            return self._finish(context, cancel=True)
        return {"PASS_THROUGH"}

    def _advance(self, context: bpy.types.Context) -> set[str]:
        if self._stage == AuthoringStage.APPLY:
            return {"PASS_THROUGH"}
        obj = context.active_object
        image = _resolve_image(obj) if obj is not None else None
        if obj is None or image is None:
            return self._finish(context, cancel=True)
        params = _snapshot_params(context)
        next_stage = AuthoringStage(self._stage + 1)
        if next_stage == AuthoringStage.INNER_LOOPS:
            self._output.inner_loops = compute_inner_loops_for_stage(
                obj, image, self._output.outer, params
            )
        elif next_stage == AuthoringStage.USER_STEINERS:
            self._output.user_steiners = read_user_steiners(obj)
        elif next_stage == AuthoringStage.STEINER_PREVIEW:
            picker = _resolve_picker(context)
            bone_segments = collect_bone_segments(picker) if picker is not None else []
            self._output.all_steiners = compute_all_steiners(
                self._output.outer,
                self._output.inner_loops,
                self._output.user_steiners,
                bone_segments,
                params,
            )
        elif next_stage == AuthoringStage.APPLY:
            picker = _resolve_picker(context)
            try:
                counters = apply_mesh(obj, image, self._output, params, picker)
            except ValueError as exc:
                report_error(
                    self,
                    f"CDT failed: {exc} - reduce loop count or increase spacing",
                )
                return {"PASS_THROUGH"}
            report_info(
                self,
                f"Authoring applied: {counters.get('total_verts', 0)} verts, "
                f"{counters.get('total_faces', 0)} faces",
            )
            return self._finish(context, cancel=False)
        self._stage = next_stage
        type(self)._current_stage_label = _STAGE_NAMES[self._stage]
        self._handles = refresh_overlay(self._handles, self._stage, self._output)
        _tag_redraw_view3d(context)
        return {"PASS_THROUGH"}

    def _retreat(self, context: bpy.types.Context) -> set[str]:
        if self._stage == AuthoringStage.OUTER:
            return {"PASS_THROUGH"}
        self._stage = AuthoringStage(self._stage - 1)
        type(self)._current_stage_label = _STAGE_NAMES[self._stage]
        self._handles = refresh_overlay(self._handles, self._stage, self._output)
        _tag_redraw_view3d(context)
        return {"PASS_THROUGH"}

    def _recompute_current_stage(self, context: bpy.types.Context, params: StageParams) -> None:
        obj = context.active_object
        image = _resolve_image(obj) if obj is not None else None
        if obj is None or image is None:
            return
        if self._stage == AuthoringStage.OUTER:
            self._output.outer = compute_outer(obj, image, params)
        elif self._stage == AuthoringStage.INNER_LOOPS:
            self._output.inner_loops = compute_inner_loops_for_stage(
                obj, image, self._output.outer, params
            )
        elif self._stage == AuthoringStage.STEINER_PREVIEW:
            picker = _resolve_picker(context)
            bone_segments = collect_bone_segments(picker) if picker is not None else []
            self._output.all_steiners = compute_all_steiners(
                self._output.outer,
                self._output.inner_loops,
                self._output.user_steiners,
                bone_segments,
                params,
            )
        self._handles = refresh_overlay(self._handles, self._stage, self._output)
        _tag_redraw_view3d(context)

    def _add_steiner(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        obj = context.active_object
        if obj is None:
            return {"PASS_THROUGH"}
        world_xz = _region_to_world_xz(context, event)
        if world_xz is None:
            return {"PASS_THROUGH"}
        self._output.user_steiners.append(world_xz)
        write_user_steiners(obj, self._output.user_steiners)
        self._handles = refresh_overlay(self._handles, self._stage, self._output)
        _tag_redraw_view3d(context)
        return {"RUNNING_MODAL"}

    def _delete_nearest_steiner(
        self, context: bpy.types.Context, event: bpy.types.Event
    ) -> set[str]:
        obj = context.active_object
        if obj is None or not self._output.user_steiners:
            return {"PASS_THROUGH"}
        world_xz = _region_to_world_xz(context, event)
        if world_xz is None:
            return {"PASS_THROUGH"}
        nearest_idx = -1
        nearest_dist_sq = _STEINER_DELETE_THRESHOLD_WORLD * _STEINER_DELETE_THRESHOLD_WORLD
        for idx, point in enumerate(self._output.user_steiners):
            dx = point[0] - world_xz[0]
            dy = point[1] - world_xz[1]
            dist_sq = dx * dx + dy * dy
            if dist_sq <= nearest_dist_sq:
                nearest_dist_sq = dist_sq
                nearest_idx = idx
        if nearest_idx < 0:
            return {"PASS_THROUGH"}
        del self._output.user_steiners[nearest_idx]
        write_user_steiners(obj, self._output.user_steiners)
        self._handles = refresh_overlay(self._handles, self._stage, self._output)
        _tag_redraw_view3d(context)
        return {"RUNNING_MODAL"}

    def _finish(self, context: bpy.types.Context, *, cancel: bool) -> set[str]:
        try:
            unregister_overlay(self._handles)
            if self._timer is not None:
                context.window_manager.event_timer_remove(self._timer)
                self._timer = None
            self._remove_statusbar()
            if self._session is not None:
                restore_session(context, self._session)
        finally:
            report_info(self, "Authoring modal restored")
        return {"CANCELLED" if cancel else "FINISHED"}

    def _append_statusbar(self) -> None:
        if not type(self)._statusbar_appended:
            bpy.types.STATUSBAR_HT_header.prepend(_draw_statusbar_authoring)
            type(self)._statusbar_appended = True

    def _remove_statusbar(self) -> None:
        if type(self)._statusbar_appended:
            with contextlib.suppress(ValueError, RuntimeError):
                bpy.types.STATUSBAR_HT_header.remove(_draw_statusbar_authoring)
            type(self)._statusbar_appended = False


def _snapshot_params(context: bpy.types.Context) -> StageParams:
    skinning = context.scene.proscenio.skinning
    return StageParams(
        resolution=float(skinning.automesh_resolution),
        alpha_threshold=int(skinning.automesh_alpha_threshold),
        margin_pixels=int(skinning.automesh_margin_pixels),
        contour_vertices=int(skinning.automesh_contour_vertices),
        inner_loop_count=int(skinning.authoring_inner_loop_count),
        inner_loop_spacing=float(skinning.authoring_inner_loop_spacing),
        interior_spacing=float(skinning.automesh_interior_spacing),
        bone_radius=float(skinning.automesh_bone_radius),
        bone_factor=int(skinning.automesh_bone_factor),
    )


def _resolve_image(obj: bpy.types.Object | None) -> bpy.types.Image | None:
    """Reuse the same lookup automesh_from_sprite uses."""
    if obj is None or obj.data is None:
        return None
    active_material = getattr(obj, "active_material", None)
    image = _find_tex_image(active_material)
    if image is not None:
        return image
    for material in obj.data.materials:
        if material is active_material:
            continue
        image = _find_tex_image(material)
        if image is not None:
            return image
    return None


def _find_tex_image(material: bpy.types.Material | None) -> bpy.types.Image | None:
    if material is None or not material.use_nodes or material.node_tree is None:
        return None
    for node in material.node_tree.nodes:
        if node.type == "TEX_IMAGE" and node.image is not None:
            return node.image
    return None


def _resolve_picker(context: bpy.types.Context) -> bpy.types.Object | None:
    scene_props = getattr(context.scene, "proscenio", None)
    if scene_props is None:
        return None
    picker = getattr(scene_props, "active_armature", None)
    if picker is None or picker.type != "ARMATURE":
        return None
    return picker


def _region_to_world_xz(context: bpy.types.Context, event: bpy.types.Event) -> Point2D | None:
    """Project region pixel coords to Y=0 XZ plane (Proscenio convention)."""
    from bpy_extras import view3d_utils  # local: bpy_extras not always available at module load

    region = context.region
    rv3d = context.region_data
    if region is None or rv3d is None:
        return None
    coord = (event.mouse_region_x, event.mouse_region_y)
    origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    if abs(direction.y) < 1e-9:
        return None
    t = -origin.y / direction.y
    hit = origin + direction * t
    return (hit.x, hit.z)


def _draw_statusbar_authoring(self: bpy.types.Header, _context: bpy.types.Context) -> None:
    layout = self.layout
    row = layout.row(align=True)
    row.label(text="", icon="MOD_REMESH")
    row.label(text=f"Automesh Authoring: {PROSCENIO_OT_automesh_authoring._current_stage_label}")
    row = layout.row(align=True)
    row.label(text="", icon="EVENT_RETURN")
    row.label(text="next")
    row = layout.row(align=True)
    row.label(text="", icon="EVENT_BACKSPACE")
    row.label(text="back")
    row = layout.row(align=True)
    row.label(text="", icon="EVENT_ESC")
    row.label(text="cancel")


def _tag_redraw_view3d(context: bpy.types.Context) -> None:
    """Trigger a viewport repaint so GPU overlay updates land without
    user interaction (zoom/pan). Iterates every VIEW_3D area in every
    window since the modal may have been invoked from one but the user
    may be looking at another."""
    wm = context.window_manager
    if wm is None:
        return
    for window in wm.windows:
        if window.screen is None:
            continue
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


_classes: tuple[type, ...] = (PROSCENIO_OT_automesh_authoring,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
