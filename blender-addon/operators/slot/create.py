"""Slot creation operator (SPEC 004 D8)."""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import StringProperty

from ...core.bpy_helpers.select import select_only  # type: ignore[import-not-found]
from ...core.report import report_info  # type: ignore[import-not-found]


def _slot_bone_target(
    context: bpy.types.Context,
    selected_meshes: list[bpy.types.Object],
) -> tuple[str, bpy.types.Object | None]:
    """Resolve the (bone_name, armature) the new slot Empty should parent to.

    Priority:

    1. Active pose bone if the user is in pose mode of an armature.
    2. The first selected mesh's bone parent (when ``parent_type=='BONE'``).
    3. Empty string + None when neither applies (slot anchored at world).
    """
    active_bone = getattr(context, "active_pose_bone", None)
    if (
        active_bone is not None
        and context.active_object is not None
        and context.active_object.type == "ARMATURE"
    ):
        return active_bone.name, context.active_object
    for mesh in selected_meshes:
        if mesh.parent is not None and mesh.parent_type == "BONE" and mesh.parent_bone:
            return str(mesh.parent_bone), mesh.parent
    return "", None


class PROSCENIO_OT_create_slot(bpy.types.Operator):
    """Create or wrap meshes into a Proscenio slot (SPEC 004 D8)."""

    bl_idname = "proscenio.create_slot"
    bl_label = "Proscenio: Create Slot"
    bl_description = (
        "Create a new slot Empty. With no mesh selected, anchors at the active "
        "pose bone. With meshes selected, wraps them as attachments under a fresh "
        "Empty parented to the active mesh's bone."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    slot_name: StringProperty(  # type: ignore[valid-type]
        name="Slot name",
        description="Name of the new Empty. Defaults to '<bone>.slot' or 'slot'.",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.scene is not None

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene = context.scene
        selected_meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]

        bone_name, armature = _slot_bone_target(context, selected_meshes)
        empty_name = self._resolve_name(bone_name)
        empty = bpy.data.objects.new(empty_name, None)
        empty.empty_display_type = "PLAIN_AXES"
        empty.empty_display_size = 0.1
        scene.collection.objects.link(empty)

        if armature is not None and bone_name:
            empty.parent = armature
            empty.parent_type = "BONE"
            empty.parent_bone = bone_name
        elif selected_meshes:
            seed = selected_meshes[0]
            if seed.parent is not None:
                empty.parent = seed.parent
                empty.parent_type = seed.parent_type
                empty.parent_bone = seed.parent_bone
            empty.location = seed.matrix_world.to_translation()

        if hasattr(empty, "proscenio"):
            empty.proscenio.is_slot = True

        for mesh_obj in selected_meshes:
            world_matrix = mesh_obj.matrix_world.copy()
            mesh_obj.parent = empty
            mesh_obj.parent_type = "OBJECT"
            mesh_obj.matrix_parent_inverse = empty.matrix_world.inverted()
            mesh_obj.matrix_world = world_matrix

        select_only(context, empty)

        if selected_meshes:
            report_info(
                self,
                f"created slot '{empty.name}' wrapping {len(selected_meshes)} attachment(s)",
            )
        else:
            report_info(self, f"created empty slot '{empty.name}'")
        return {"FINISHED"}

    def _resolve_name(self, bone_name: str) -> str:
        if self.slot_name:
            return str(self.slot_name)
        return f"{bone_name}.slot" if bone_name else "slot"


_classes: tuple[type, ...] = (PROSCENIO_OT_create_slot,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
