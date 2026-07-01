"""Skeleton emission: per-bone Godot world transforms + Skeleton model + math helpers."""

from __future__ import annotations

from dataclasses import dataclass, field

import bpy
from mathutils import Matrix
from proscenio_models import Bone, Skeleton

from ....core.bone_export import bone_is_exported
from ....core.bpy_helpers._shared._bpy_compat import expect_armature, iter_bones
from ....core.godot_export_math import (
    godot_world_angle_from_dir,
    rotate_vec2,
    world_to_godot_xy,
    wrap_pi,
)

# Re-exported so the writer's existing importers (sprites, animations,
# tests/writer/test_skeleton) keep importing these from ``skeleton``.
__all__ = [
    "godot_world_angle_from_dir",
    "rotate_vec2",
    "world_to_godot_xy",
    "wrap_pi",
]


@dataclass(frozen=True)
class BoneRestLocal:
    """Bone2D-local rest pose. Carried between the skeleton builder and the
    animation builder so animation tracks can emit absolute Godot values
    (rest + delta) instead of raw fcurve deltas.

    ``rest_basis`` is the bone's 3x3 rest orientation in armature space; the
    animation builder rotates the bone-local Y axis by it (and by a keyframe's
    local rotation) to recover the bone's screen direction for any in-plane bone
    orientation, instead of assuming bone-Y aligns with the camera axis.

    ``parent_world_rot`` is the parent bone's Godot world rotation (0.0 when
    there is no parent). ``Bone2D.position`` is parent-local, so the animation
    builder rotates the screen-space position delta by it before adding to the
    rest - matching how the rest position itself was rotated into parent-local
    space. Without it, a screen-vertical bob on a bone whose parent is rotated
    lands on the wrong local axis and reads sideways in Godot.
    """

    position: tuple[float, float]
    rotation: float
    scale: tuple[float, float]
    rest_basis: Matrix | None = field(default=None, compare=False)
    parent_world_rot: float = 0.0


@dataclass(frozen=True)
class BoneWorld:
    """Per-bone Godot world transform: head position + rotation + bone length."""

    x: float
    y: float
    rot: float
    length: float


def _nearest_deform_ancestor(bone: bpy.types.Bone) -> bpy.types.Bone | None:
    """First exported ancestor of ``bone``, or None.

    A bone parented under a filtered-out bone (a non-deform control or a rig
    helper pinned off the export) re-parents to this ancestor so the exported
    skeleton has no dangling parent reference (Godot rejects a Bone2D whose
    ``parent`` names a bone the document never emits).
    """
    parent = bone.parent
    while parent is not None:
        if bone_is_exported(parent):
            return parent
        parent = parent.parent
    return None


def compute_bone_world_godot(armature_obj: bpy.types.Object, ppu: float) -> dict[str, BoneWorld]:
    """Return per-bone Godot world position (Vector2-ish) and rotation in radians.

    Bones that do not export (``.IK`` / ``.pole`` control scaffolding, any
    non-deform control, and rig helpers the rigger pinned off the export) are
    skipped: the export is a deform skeleton for ``Polygon2D`` skinning, matching
    the :func:`bone_is_exported` gate the skinning code already follows.
    """
    armature = expect_armature(armature_obj)
    arm_world = armature_obj.matrix_world

    out: dict[str, BoneWorld] = {}
    for bone in iter_bones(armature):
        if not bone_is_exported(bone):
            continue
        head_world_blender = arm_world @ bone.head_local
        tail_world_blender = arm_world @ bone.tail_local
        head_godot = world_to_godot_xy(head_world_blender, ppu)
        dir_blender = tail_world_blender - head_world_blender
        angle = godot_world_angle_from_dir(dir_blender)
        # Use bone.length * ppu (armature-local rest length), NOT the head->tail
        # distance in Godot space: the projection drops the depth axis, so a bone
        # pointing into the screen would project to length 0.
        out[bone.name] = BoneWorld(
            x=head_godot.x,
            y=head_godot.y,
            rot=angle,
            length=bone.length * ppu,
        )
    return out


def build_skeleton(
    armature_obj: bpy.types.Object,
    world_godot: dict[str, BoneWorld],
) -> tuple[Skeleton, dict[str, BoneRestLocal]]:
    """Return the Skeleton model and a per-bone rest dict in Bone2D-local space.

    The rest dict is keyed by bone name and provides ``position``,
    ``rotation``, ``scale`` so the animation builder can emit absolute
    Godot animation values (rest + delta) instead of raw deltas.
    """
    armature = expect_armature(armature_obj)
    bones_out: list[Bone] = []
    rest_local: dict[str, BoneRestLocal] = {}

    for bone in iter_bones(armature):
        # Non-exported bones (control scaffolding, rig helpers pinned off the
        # export) never enter the deform skeleton. An exported child of a
        # filtered bone re-parents to its nearest exported ancestor so no Bone2D
        # references a parent the document never emits.
        if not bone_is_exported(bone):
            continue
        w = world_godot[bone.name]
        parent_bone = _nearest_deform_ancestor(bone)
        if parent_bone is None:
            local_pos = (w.x, w.y)
            local_rot = w.rot
            parent_world_rot = 0.0
        else:
            p = world_godot[parent_bone.name]
            dx = w.x - p.x
            dy = w.y - p.y
            local_pos = rotate_vec2(dx, dy, -p.rot)
            local_rot = wrap_pi(w.rot - p.rot)
            parent_world_rot = p.rot

        bones_out.append(
            Bone(
                name=bone.name,
                parent=parent_bone.name if parent_bone else None,
                position=[round(local_pos[0], 6), round(local_pos[1], 6)],
                rotation=round(local_rot, 6),
                scale=[1.0, 1.0],
                length=round(w.length, 6),
            )
        )
        rest_local[bone.name] = BoneRestLocal(
            position=(local_pos[0], local_pos[1]),
            rotation=local_rot,
            scale=(1.0, 1.0),
            rest_basis=bone.matrix_local.to_3x3(),
            parent_world_rot=parent_world_rot,
        )

    return Skeleton(bones=bones_out), rest_local
