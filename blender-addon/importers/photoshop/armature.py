"""Stub armature builder for the Photoshop importer (SPEC 006 D3).

Single ``root`` bone at the world origin. Every stamped mesh is
parented to it via ``parent_type='BONE'``. The user adds the rest of
the rig manually after import; the importer's job is to give every
mesh a parent so they move together when the user reposes the figure.
"""

from __future__ import annotations

import bpy

ROOT_BONE_NAME = "root"
ROOT_BONE_LENGTH = 0.05


def build_root_armature(name: str) -> bpy.types.Object:
    """Create a fresh armature with a single ``root`` bone, return the object."""
    arm_data = bpy.data.armatures.new(name)
    arm_obj = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    bone = arm_data.edit_bones.new(ROOT_BONE_NAME)
    bone.head = (0.0, 0.0, 0.0)
    bone.tail = (0.0, 0.0, ROOT_BONE_LENGTH)
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj
