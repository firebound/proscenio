"""Quick armature modal operator (SPEC 005.1.d.3)."""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core.report import report_error, report_info, report_warn  # type: ignore[import-not-found]
from ..core.viewport_math import mouse_event_to_z0_point  # type: ignore[import-not-found]

_QUICK_RIG_NAME = "Proscenio.QuickRig"


class PROSCENIO_OT_quick_armature(bpy.types.Operator):
    """Click-drag in the viewport to author bones rapidly (5.1.d.3)."""

    bl_idname = "proscenio.quick_armature"
    bl_label = "Proscenio: Quick Armature"
    bl_description = (
        "Click-drag in the 3D viewport to draw a bone (head -> tail). "
        "Hold Shift to chain onto the previous bone. Esc or right-click to exit."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO", "BLOCKING"}

    # Modal state -- set in invoke, mutated in modal. Class-level defaults
    # exist so mypy can resolve the attributes; per-invoke assignment in
    # invoke() ensures every modal session starts clean.
    _drag_head: ClassVar[tuple[float, float, float] | None] = None
    _last_bone_name: ClassVar[str] = ""
    _shift_held: ClassVar[bool] = False

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.area is not None and context.area.type == "VIEW_3D"

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        if context.area is None or context.area.type != "VIEW_3D":
            report_warn(self, "must run in a 3D viewport")
            return {"CANCELLED"}
        type(self)._drag_head = None
        type(self)._last_bone_name = ""
        type(self)._shift_held = False
        if self._ensure_armature(context) is None:
            report_error(self, "failed to create QuickRig armature")
            return {"CANCELLED"}
        workspace = context.workspace
        if workspace is not None:
            workspace.status_text_set(
                "Quick Armature: drag = bone | Shift+drag = chain | Esc = exit"
            )
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        if event.type in {"ESC", "RIGHTMOUSE"} and event.value == "PRESS":
            return self._finish(context)
        if event.type == "LEFTMOUSE":
            return self._handle_leftmouse(context, event)
        return {"PASS_THROUGH"}

    def _handle_leftmouse(
        self,
        context: bpy.types.Context,
        event: bpy.types.Event,
    ) -> set[str]:
        if event.value == "PRESS":
            type(self)._drag_head = mouse_event_to_z0_point(context, event)
            type(self)._shift_held = bool(event.shift)
            return {"RUNNING_MODAL"}
        if event.value != "RELEASE":
            return {"RUNNING_MODAL"}
        head = type(self)._drag_head
        type(self)._drag_head = None
        if head is None:
            return {"RUNNING_MODAL"}
        tail = mouse_event_to_z0_point(context, event)
        if tail is None:
            return {"RUNNING_MODAL"}
        from mathutils import Vector

        if (Vector(tail) - Vector(head)).length < 1e-4:
            report_info(self, "bone too short, skipped")
            return {"RUNNING_MODAL"}
        self._create_bone(context, head, tail, parent_to_last=type(self)._shift_held)
        return {"RUNNING_MODAL"}

    def execute(self, _context: bpy.types.Context) -> set[str]:
        # Quick armature is modal-only; F3 search routes through invoke.
        return {"FINISHED"}

    def _ensure_armature(self, context: bpy.types.Context) -> bpy.types.Object | None:
        existing = context.scene.objects.get(_QUICK_RIG_NAME)
        if existing is not None and existing.type == "ARMATURE":
            return existing
        arm_data = bpy.data.armatures.new(_QUICK_RIG_NAME)
        arm_obj = bpy.data.objects.new(_QUICK_RIG_NAME, arm_data)
        context.scene.collection.objects.link(arm_obj)
        return arm_obj

    def _create_bone(
        self,
        context: bpy.types.Context,
        head: tuple[float, float, float],
        tail: tuple[float, float, float],
        *,
        parent_to_last: bool,
    ) -> None:
        from mathutils import Vector

        armature = context.scene.objects.get(_QUICK_RIG_NAME)
        if armature is None:
            return
        prev_active = context.view_layer.objects.active
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
            if prev_active is not None:
                context.view_layer.objects.active = prev_active
        if bone_name:
            type(self)._last_bone_name = bone_name
            report_info(self, f"'{bone_name}' added to {_QUICK_RIG_NAME}")

    def _finish(self, context: bpy.types.Context) -> set[str]:
        workspace = context.workspace
        if workspace is not None:
            workspace.status_text_set(None)
        type(self)._drag_head = None
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_quick_armature,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
