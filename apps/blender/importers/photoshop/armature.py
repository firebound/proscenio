"""Stub armature builder for the Photoshop importer (the photoshop importer).

Single root-level bone at the world origin. Default name is ``root``,
but rigs that prefer ``spine`` (or any other identifier) can pass a
custom name - the importer surfaces this via the operator's
``root_bone_name`` property. Every stamped mesh is parented to the
armature object (``parent_type='OBJECT'``); per-bone weights for
posing land in a future iteration.
"""

from __future__ import annotations

import bpy

from ...core.bpy_helpers._shared._bpy_compat import expect_scene, iter_blend_objects

DEFAULT_ROOT_BONE_NAME = "root"
# Default head->tail length (world units) of the importer's single root bone.
# A 1-unit bone is comfortably visible and easy to pick (the Quick Armature
# Reparent pick targets the tail; a sub-tenth-unit tail sits almost on the origin
# head and is awkward to hit). Re-import reuses an existing root in place (see
# build_root_armature / spec 055 reimport-contract), so this only sizes a freshly
# built root and never retro-resizes a rig already imported - which is correct,
# it must not disturb a rig the user grew. The import operator exposes a per-rig
# override that defaults to this.
ROOT_BONE_LENGTH = 1.0


def build_root_armature(
    name: str,
    root_bone_name: str = DEFAULT_ROOT_BONE_NAME,
    length: float = ROOT_BONE_LENGTH,
) -> bpy.types.Object:
    """Reuse the import's root armature when present, else create a fresh one.

    A second import of the same manifest must not orphan the first armature and
    strand any rig (bones, pose, constraints) the user grew on it. So when an
    armature object with this name already exists it is reused in place - the
    single ``root`` bone the manifest drives needs no reconciliation today - and
    only a missing one is built from scratch. Because of that reuse, ``length``
    sizes only a freshly built root; an existing root keeps its size on re-import.

    Under the photoshop tag system Spine-style anchor model the manifest's anchor
    re-zeros every layer's world position, so the bone always sits at
    (0, 0, 0) and represents the artist-chosen pivot.
    """
    existing = _find_existing_armature(name)
    if existing is not None:
        return existing
    arm_data = bpy.data.armatures.new(name)
    arm_obj = bpy.data.objects.new(name, arm_data)
    expect_scene(bpy.context.scene).collection.objects.link(arm_obj)
    view_layer = bpy.context.view_layer
    if view_layer is None:
        raise RuntimeError("Proscenio: bpy.context.view_layer is None - cannot enter Edit mode")
    view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    bone = arm_data.edit_bones.new(root_bone_name)
    bone.head = (0.0, 0.0, 0.0)
    bone.tail = (0.0, 0.0, length)
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def _find_existing_armature(name: str) -> bpy.types.Object | None:
    """Locate the import's root armature object built by a prior import.

    Keyed on the manifest-derived name (``_armature_name`` in the orchestrator);
    mirrors the mesh-reuse find-by-tag pattern in ``planes._find_existing``.
    """
    for obj in iter_blend_objects():
        if obj.type == "ARMATURE" and obj.name == name:
            return obj
    return None
