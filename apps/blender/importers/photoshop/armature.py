"""Stub armature builder for the Photoshop importer (SPEC 006 D3).

Single root-level bone at the world origin. Default name is ``root``,
but rigs that prefer ``spine`` (or any other identifier) can pass a
custom name - the importer surfaces this via the operator's
``root_bone_name`` property. Every stamped mesh is parented to the
armature object (``parent_type='OBJECT'``); per-bone weights for
posing land in a future wave.
"""

from __future__ import annotations

import bpy

DEFAULT_ROOT_BONE_NAME = "root"
ROOT_BONE_LENGTH = 0.05


def build_root_armature(
    name: str,
    root_bone_name: str = DEFAULT_ROOT_BONE_NAME,
) -> bpy.types.Object:
    """Create a fresh armature with a single root-level bone, return the object."""
    arm_data = bpy.data.armatures.new(name)
    arm_obj = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    bone = arm_data.edit_bones.new(root_bone_name)
    bone.head = (0.0, 0.0, 0.0)
    bone.tail = (0.0, 0.0, ROOT_BONE_LENGTH)
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj
