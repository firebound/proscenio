"""Slot attachment operators: add attachment, set default."""

from __future__ import annotations

import json
from typing import ClassVar

import bpy
from bpy.props import StringProperty

from ...core._shared.action_fcurves import action_fcurves  # type: ignore[import-not-found]
from ...core._shared.cp_keys import (  # type: ignore[import-not-found]
    PROSCENIO_SLOT_ATTACHMENT_ORDER,
    PROSCENIO_SLOT_INDEX,
)
from ...core._shared.report import report_info, report_warn  # type: ignore[import-not-found]
from ...core.bpy_helpers._shared._bpy_compat import (  # type: ignore[import-not-found]
    iter_keyframe_points,
)
from ...core.bpy_helpers._shared.parenting import (  # type: ignore[import-not-found]
    parent_keep_world,
)


def _set_slot_index_constant(empty: bpy.types.Object, data_path: str) -> None:
    """Force every key on the slot-index fcurve to a hard cut.

    An integer attachment index must not tween between swaps, so the whole
    curve is CONSTANT - matching the ``interp="constant"`` the writer emits
    unconditionally for ``slot_attachment`` keys.
    """
    anim = getattr(empty, "animation_data", None)
    action = getattr(anim, "action", None) if anim is not None else None
    if action is None:
        return
    for fcurve in action_fcurves(action):
        if fcurve.data_path != data_path:
            continue
        for keyframe in iter_keyframe_points(fcurve):
            keyframe.interpolation = "CONSTANT"
        fcurve.update()


class PROSCENIO_OT_add_slot_attachment(bpy.types.Operator):
    """Re-parent the active mesh into the active slot Empty."""

    bl_idname = "proscenio.add_slot_attachment"
    bl_label = "Proscenio: Add Slot Attachment"
    bl_description = "Re-parent the selected mesh as a child of the active slot Empty"
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        empty = context.active_object
        if empty is None or empty.type != "EMPTY":
            return False
        props = getattr(empty, "proscenio", None)
        if props is None or not bool(getattr(props, "is_slot", False)):
            return False
        return any(obj.type == "MESH" and obj is not empty for obj in context.selected_objects)

    def execute(self, context: bpy.types.Context) -> set[str]:
        empty = context.active_object
        meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if not meshes:
            report_warn(self, "no MESH objects selected")
            return {"CANCELLED"}
        for mesh in meshes:
            parent_keep_world(mesh, empty)
        report_info(self, f"added {len(meshes)} attachment(s) to slot '{empty.name}'")
        return {"FINISHED"}


class PROSCENIO_OT_attach_mesh_to_slot(bpy.types.Operator):
    """Pick a mesh by name and re-parent it into the active slot.

    The picker breaks the single-selection deadlock: you cannot have the
    slot active AND a target mesh selected at the same time, so
    ``add_slot_attachment`` (which re-parents the selection) has no path
    when the slot is what you just clicked. This dialog chooses the target
    by name instead, leaving the active object alone.
    """

    bl_idname = "proscenio.attach_mesh_to_slot"
    bl_label = "Proscenio: Attach Mesh to Slot"
    bl_description = (
        "Pick a mesh by name and attach it to the active slot, without having to select it first"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    mesh_name: StringProperty(  # type: ignore[valid-type]
        name="Mesh",
        description="Mesh to attach to the active slot",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        empty = context.active_object
        if empty is None or empty.type != "EMPTY":
            return False
        props = getattr(empty, "proscenio", None)
        return props is not None and bool(getattr(props, "is_slot", False))

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: bpy.types.Context) -> None:
        # prop_search over the scene's objects; execute validates the pick is
        # a mesh. (There is no mesh-only collection to search directly.)
        self.layout.prop_search(self, "mesh_name", context.scene, "objects", text="Mesh")

    def execute(self, context: bpy.types.Context) -> set[str]:
        empty = context.active_object
        if empty is None or empty.type != "EMPTY":
            return {"CANCELLED"}
        mesh = bpy.data.objects.get(self.mesh_name)
        if mesh is None or mesh.type != "MESH":
            report_warn(self, f"'{self.mesh_name}' is not a mesh")
            return {"CANCELLED"}
        parent_keep_world(mesh, empty)
        report_info(self, f"attached '{mesh.name}' to slot '{empty.name}'")
        return {"FINISHED"}


class PROSCENIO_OT_set_slot_default(bpy.types.Operator):
    """Mark the named attachment as the slot's default."""

    bl_idname = "proscenio.set_slot_default"
    bl_label = "Proscenio: Set Slot Default"
    bl_description = "Make this attachment the slot's default visible child at scene load"
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    attachment_name: StringProperty(  # type: ignore[valid-type]
        name="Attachment name",
        description="Name of the mesh child to flag as default",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        empty = context.active_object
        if empty is None or empty.type != "EMPTY":
            return False
        props = getattr(empty, "proscenio", None)
        return props is not None and bool(getattr(props, "is_slot", False))

    def execute(self, context: bpy.types.Context) -> set[str]:
        empty = context.active_object
        props = empty.proscenio
        children_names = {child.name for child in empty.children if child.type == "MESH"}
        if self.attachment_name not in children_names:
            report_warn(
                self,
                f"'{self.attachment_name}' is not a child of slot '{empty.name}'",
            )
            return {"CANCELLED"}
        props.slot_default = self.attachment_name
        report_info(self, f"slot '{empty.name}' default = '{self.attachment_name}'")
        return {"FINISHED"}


class PROSCENIO_OT_keyframe_slot_attachment(bpy.types.Operator):
    """Keyframe the slot's visible attachment at the current frame."""

    bl_idname = "proscenio.keyframe_slot_attachment"
    bl_label = "Proscenio: Keyframe Slot Attachment"
    bl_description = (
        "Key the chosen attachment visible from the current frame - the "
        "constant-interpolation slot swap the exporter projects into a Godot "
        "slot_attachment track"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    attachment_name: StringProperty(  # type: ignore[valid-type]
        name="Attachment name",
        description="Name of the mesh child to make visible from this frame",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        empty = context.active_object
        if empty is None or empty.type != "EMPTY":
            return False
        props = getattr(empty, "proscenio", None)
        return props is not None and bool(getattr(props, "is_slot", False))

    def execute(self, context: bpy.types.Context) -> set[str]:
        empty = context.active_object
        attachments = [child.name for child in empty.children if child.type == "MESH"]
        if self.attachment_name not in attachments:
            report_warn(
                self,
                f"'{self.attachment_name}' is not an attachment of slot '{empty.name}'",
            )
            return {"CANCELLED"}
        index = attachments.index(self.attachment_name)
        data_path = f'["{PROSCENIO_SLOT_INDEX}"]'
        frame = context.scene.frame_current
        # Snapshot the attachment name order the index is resolved against, so the
        # writer maps the keyed index to a name via this stable list instead of
        # the live child order. Deleting an earlier attachment then no longer
        # slides this and every later keyframe onto the wrong child.
        empty[PROSCENIO_SLOT_ATTACHMENT_ORDER] = json.dumps(attachments)
        empty[PROSCENIO_SLOT_INDEX] = index
        empty.keyframe_insert(data_path=data_path, frame=frame)
        _set_slot_index_constant(empty, data_path)
        report_info(
            self,
            f"keyed '{self.attachment_name}' (index {index}) at frame {frame}",
        )
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_add_slot_attachment,
    PROSCENIO_OT_attach_mesh_to_slot,
    PROSCENIO_OT_set_slot_default,
    PROSCENIO_OT_keyframe_slot_attachment,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
