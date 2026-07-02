"""Rigid sprite bone-attach: keep-transform bone parent + picture-plane guard.

bpy-bound (manipulates ``Object`` parenting + reads pose matrices), so this
module imports bpy at top per the bpy_helpers contract. A sprite is a rigid
Sprite2D; the only non-slot way to make it follow one bone is a real
``parent_type == "BONE"`` parent, which the exporter reads via
``resolve_sprite_bone``. The parent is authored keep-transform so the sprite
does not snap to the bone tail (Blender's bone parenting anchors the child at
the tail with the bone's rest orientation).
"""

from __future__ import annotations

import bpy

from ..._shared.armature_resolve import resolve_target_armature
from .._shared.bone_orientation import bone_in_picture_plane

__all__ = [
    "bone_in_picture_plane",
    "clear_bone_parent_keep_world",
    "current_bone_parent",
    "parent_to_bone_keep_world",
    "resolve_sprite_armature",
]


def resolve_sprite_armature(
    context: bpy.types.Context, obj: bpy.types.Object
) -> bpy.types.Object | None:
    """The armature a sprite should bone-parent to, or None.

    The sprite-facing name for the shared :func:`resolve_target_armature`:
    parent-if-ARMATURE, then the Skeleton picker, then the scene's export
    armature - the same resolution order the slot bone-follow uses, so the two
    never disagree on the rig.
    """
    return resolve_target_armature(context, obj)


def current_bone_parent(obj: bpy.types.Object) -> str:
    """The bone this object is parented to, or "" when it is not bone-parented."""
    if getattr(obj, "parent_type", "") == "BONE" and getattr(obj, "parent_bone", ""):
        return str(obj.parent_bone)
    return ""


def parent_to_bone_keep_world(
    child: bpy.types.Object, armature: bpy.types.Object, bone_name: str
) -> None:
    """Bone-parent ``child`` to ``bone_name`` of ``armature`` without moving it.

    Snapshots the child's world matrix, sets the BONE parent, then restores the
    world transform so the child stays exactly where it was on screen (the
    programmatic form of Blender's "Set Parent > Bone, Keep Transform"). The
    identity ``matrix_parent_inverse`` lets Blender derive the basis from its own
    bone-parent space (which anchors at the bone tail), so the world write-back
    is what cancels the tail jump and the rest rotation.

    Raises ``RuntimeError`` when the armature lacks ``bone_name``.
    """
    if armature.pose.bones.get(bone_name) is None:
        raise RuntimeError(f"armature '{armature.name}' has no bone '{bone_name}'")
    world = child.matrix_world.copy()
    child.parent = armature
    child.parent_type = "BONE"
    child.parent_bone = bone_name
    child.matrix_parent_inverse.identity()
    child.matrix_world = world


def clear_bone_parent_keep_world(child: bpy.types.Object) -> None:
    """Reverse :func:`parent_to_bone_keep_world`: drop the bone parent, keep world.

    Leaves the object unparented at the same on-screen position - the pre-attach
    state, ready to re-parent elsewhere or attach to a slot.
    """
    world = child.matrix_world.copy()
    child.parent = None
    child.parent_type = "OBJECT"
    child.parent_bone = ""
    child.matrix_parent_inverse.identity()
    child.matrix_world = world
