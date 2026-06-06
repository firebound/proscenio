"""Edit Weights modal operator.

One-button entry into a 2D-safe weight paint context with provenance
overlay + per-stroke user_paint flip. ESC hard-exits via try/finally.
Wraps cumulative paint in a single undo push so Ctrl+Z reverts the
entire modal session.
"""

from __future__ import annotations

import contextlib
import traceback
from typing import ClassVar

import bpy

from ...core._shared.cp_keys import (  # type: ignore[import-not-found]
    PROSCENIO_WEIGHT_SIDECAR as _SIDECAR_KEY,
)
from ...core._shared.report import (  # type: ignore[import-not-found]
    report_error,
    report_info,
)
from ...core.bpy_helpers.skinning import (  # type: ignore[import-not-found]
    StrokeDiffTracker,
    apply_paint_preset,
    capture_session,
    read_mirror_flag,
    register_handler,
    restore_session,
    snapshot_bone_visibility,
    snapshot_paint_preset,
    unregister_handler,
)
from ...core.skinning.sidecar_schema import (  # type: ignore[import-not-found]
    from_json,
)


class PROSCENIO_OT_edit_weights_modal(bpy.types.Operator):
    """Enter a 2D-safe weight paint context with provenance overlay."""

    bl_idname = "proscenio.edit_weights"
    bl_label = "Proscenio: Edit Weights"
    bl_description = (
        "Enter a 2D-safe weight paint context for the active mesh. Applies a "
        "weight-paint preset tuned for 2D sprites (Front Faces off, mirror from "
        "picker rig), shows the provenance overlay (cyan=reprojected / white=user "
        "paint / gray=auto seed), and tags brushed verts as user_paint in the "
        "sidecar via per-stroke diff. ESC hard-exits and restores brush + bone "
        "visibility + mode + selection"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    _overlay_handle: object | None = None
    _statusbar_appended: bool = False

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return False
        scene_props = getattr(context.scene, "proscenio", None)
        armature = getattr(scene_props, "active_armature", None) if scene_props else None
        if armature is None or armature.type != "ARMATURE":
            return False
        return obj.get(_SIDECAR_KEY) is not None

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        preconditions = _validate_invoke_preconditions(self, context)
        if preconditions is None:
            return {"CANCELLED"}
        obj, armature, scene_props, sidecar = preconditions

        skinning = getattr(scene_props, "skinning", None)
        prior_overlay = (
            bool(getattr(skinning, "show_provenance_overlay", False)) if skinning else False
        )
        prior_preset = snapshot_paint_preset(context)
        prior_visibility = snapshot_bone_visibility(armature)
        self._session = capture_session(
            context, obj, armature, prior_preset, prior_visibility, prior_overlay
        )

        mirror_x = read_mirror_flag(armature)
        try:
            armature.select_set(True)
            context.view_layer.objects.active = armature
            if armature.mode != "POSE":
                bpy.ops.object.mode_set(mode="POSE")
            context.view_layer.objects.active = obj
            obj.select_set(True)
            if obj.mode != "WEIGHT_PAINT":
                bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
            apply_paint_preset(context, mirror_x=mirror_x)
            _auto_select_active_group(obj, armature)
            if skinning is not None and hasattr(skinning, "show_provenance_overlay"):
                skinning.show_provenance_overlay = True
            self._overlay_handle = register_handler(obj, mode="provenance")
            self._stroke_tracker = StrokeDiffTracker(obj, sidecar)
            self._append_statusbar()
        except Exception as exc:
            report_error(self, f"Edit Weights setup failed: {exc} - restoring state")
            self._finish(context, cancel=True)
            return {"CANCELLED"}

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        try:
            if event.type == "ESC":
                return self._finish(context, cancel=True)
            if event.type == "LEFTMOUSE" and event.value == "PRESS":
                self._stroke_tracker.snapshot_active_vg()
                return {"PASS_THROUGH"}
            if event.type == "LEFTMOUSE" and event.value == "RELEASE":
                touched = self._stroke_tracker.flip_touched_after_stroke()
                if touched and context.area is not None:
                    context.area.tag_redraw()
                return {"PASS_THROUGH"}
            if event.type == "WINDOW_DEACTIVATE":
                self._stroke_tracker.flip_touched_after_stroke()
                return {"PASS_THROUGH"}
            if event.type == "MOUSEMOVE" and getattr(event, "pressure", 1.0) < 1e-6:
                self._stroke_tracker.flip_touched_after_stroke()
                return {"PASS_THROUGH"}
        except Exception:
            traceback.print_exc()
            return self._finish(context, cancel=True)
        return {"PASS_THROUGH"}

    def _finish(self, context: bpy.types.Context, *, cancel: bool) -> set[str]:
        try:
            with contextlib.suppress(RuntimeError):
                bpy.ops.ed.undo_push(message="Edit Weights")
            if self._overlay_handle is not None:
                unregister_handler(self._overlay_handle)
                self._overlay_handle = None
            self._remove_statusbar()
            restore_session(context, self._session)
        finally:
            report_info(self, "Edit Weights modal restored")
        return {"CANCELLED" if cancel else "FINISHED"}

    def _append_statusbar(self) -> None:
        if not type(self)._statusbar_appended:
            bpy.types.STATUSBAR_HT_header.prepend(_draw_statusbar_edit_weights)
            type(self)._statusbar_appended = True

    def _remove_statusbar(self) -> None:
        if type(self)._statusbar_appended:
            with contextlib.suppress(ValueError, RuntimeError):
                bpy.types.STATUSBAR_HT_header.remove(_draw_statusbar_edit_weights)
            type(self)._statusbar_appended = False


def _validate_invoke_preconditions(
    operator: bpy.types.Operator, context: bpy.types.Context
) -> tuple[bpy.types.Object, bpy.types.Object, bpy.types.PropertyGroup, object] | None:
    """Run all invoke-time guards; return (obj, armature, scene_props, sidecar) or None.

    Reports the relevant ERROR via the operator on each failure path so the
    caller just returns CANCELLED on None.
    """
    obj = context.active_object
    if obj is None or obj.type != "MESH":
        report_error(operator, "active object must be a mesh")
        return None
    scene_props = getattr(context.scene, "proscenio", None)
    armature = getattr(scene_props, "active_armature", None) if scene_props else None
    if armature is None or armature.type != "ARMATURE":
        report_error(operator, "no picker armature - pick one in Skeleton panel first")
        return None
    payload = obj.get(_SIDECAR_KEY)
    if payload is None:
        report_error(operator, "no sidecar - run Bind to Picker Armature first")
        return None
    try:
        sidecar = from_json(payload)
    except ValueError as exc:
        report_error(operator, f"existing sidecar is corrupt: {exc} - re-bind to reset")
        return None
    if not sidecar.entries:
        report_error(operator, "sidecar has no entries (legacy bind) - re-bind to populate")
        return None
    if len(sidecar.entries) != len(obj.data.vertices):
        report_error(
            operator,
            "sidecar/topology mismatch - re-bind to the current mesh topology",
        )
        return None
    if len(obj.vertex_groups) == 0:
        report_error(operator, "mesh has no vertex groups - run Bind first")
        return None
    return obj, armature, scene_props, sidecar


def _auto_select_active_group(obj: bpy.types.Object, armature: bpy.types.Object) -> None:
    """Pick the active vertex group from the first selected pose bone.

    Best-effort - any AttributeError on the pose API (Blender version
    drift around Bone.select / PoseBone.select) is swallowed; the modal
    still opens with whatever vertex group was active before invoke.
    """
    pose = getattr(armature, "pose", None)
    if pose is None:
        return
    try:
        selected_bones = [b for b in pose.bones if _is_pose_bone_selected(b)]
    except AttributeError:
        return
    if not selected_bones:
        return
    first = selected_bones[0].name
    if first in obj.vertex_groups:
        obj.vertex_groups.active_index = obj.vertex_groups[first].index


def _is_pose_bone_selected(pose_bone: bpy.types.PoseBone) -> bool:
    """Read selection state across Blender API generations.

    5.1+ exposes the flag on PoseBone directly; earlier versions kept
    it on the underlying Bone data block. getattr with default=False
    keeps the helper a no-op when both attribute paths are absent.
    """
    bone = getattr(pose_bone, "bone", None)
    if bone is not None and hasattr(bone, "select"):
        return bool(bone.select)
    return bool(getattr(pose_bone, "select", False))


def _draw_statusbar_edit_weights(self: bpy.types.Header, _context: bpy.types.Context) -> None:
    layout = self.layout
    row = layout.row(align=True)
    row.label(text="", icon="BRUSHES_ALL")
    row.label(text="Edit Weights:")
    row = layout.row(align=True)
    row.label(text="", icon="EVENT_ESC")
    row.label(text="exit")
    row = layout.row(align=True)
    row.label(text="", icon="MOD_MIRROR")
    row.label(text="mirror = picker.proscenio_mirror_x")


_classes: tuple[type, ...] = (PROSCENIO_OT_edit_weights_modal,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
