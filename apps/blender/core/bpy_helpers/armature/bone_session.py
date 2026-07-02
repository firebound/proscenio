"""Bone-authoring record + edit-bone creation for the Quick Armature modal.

The stateful undo/redo stack stays on the operator (its ClassVars are the tested
surface); this module owns the record shape and the bpy edit-bone mutation the
operator's ``_create_bone`` performs, so the operator keeps only the session
bookkeeping (append record, advance ``_last_bone_name``, clear redo, report).
"""

from __future__ import annotations

from dataclasses import dataclass

import bpy
from mathutils import Vector

from ...armature.quick_armature_math import format_bone_name


@dataclass(frozen=True)
class BoneRecord:
    """Snapshot of a bone authored during the modal session.

    Used by the in-modal undo/redo stack so we can recreate the same
    bone (or remove it) without losing geometry / parenting context.
    """

    name: str
    head: tuple[float, float, float]
    tail: tuple[float, float, float]
    parent_to_last_name: str
    connect: bool


def author_edit_bone(
    edit_bones: bpy.types.ArmatureEditBones,
    head: tuple[float, float, float],
    tail: tuple[float, float, float],
    *,
    last_name: str,
    name_prefix: str,
    parent_to_last: bool,
    connect: bool,
) -> tuple[str, tuple[float, float, float]]:
    """Create a fresh edit bone, parenting/connecting it to ``last_name``.

    Returns ``(bone_name, actual_head)`` - ``actual_head`` differs from ``head``
    only for a connected child, whose head snaps to the parent tail (Blender E
    extrude convention). Makes the new bone the active edit bone so it reads as
    selected. Pure bpy mutation; the caller owns the record + session state.
    """
    bone_name = format_bone_name(name_prefix, len(edit_bones))
    new_bone = edit_bones.new(bone_name)
    parent_bone = (
        edit_bones[last_name]
        if (parent_to_last and last_name and last_name in edit_bones)
        else None
    )
    actual_head: tuple[float, float, float] = head
    if parent_bone is not None and connect:
        # Snap head to the parent's tail so chained bones share an exact
        # junction (Blender E extrude convention).
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
    # Make the fresh bone the active edit bone so it reads as selected.
    edit_bones.active = new_bone
    return bone_name, actual_head
