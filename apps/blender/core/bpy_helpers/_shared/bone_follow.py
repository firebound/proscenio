"""Shared bone-follow authoring core: bind / unbind / shape for elements + slots.

bpy-bound (manipulates ``Object.constraints`` + parenting, reads matrices), so
this module imports bpy at top per the bpy_helpers contract. The single home
for the object-parent + Child Of follow convention (spec 080 D6): the slot
wrapper and the element attach operators are thin callers parametrized by
constraint name.

The Child Of ``inverse_matrix`` is computed from the bone REST
(``Bone.matrix_local``), never the posed matrix (D7): the Godot side always
cancels the rest, so an inverse baked from a posed rig would author a
Blender-only offset that silently diverges on import. Binding on a posed rig
therefore snaps the object in the viewport to where Godot will actually put
it - :func:`bind_to_bone_rest` reports that so the operator can warn.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import bpy
from mathutils import Matrix

from ..._shared.bone_follow_resolve import follow_subtarget

__all__ = [
    "bind_to_bone_rest",
    "bone_is_posed",
    "drop_bone_parent_keep_world",
    "expected_rest_inverse",
    "follow_constraint",
    "follow_is_stale",
    "follow_shape",
    "followed_bone_of",
    "unbind_keep_world",
]


def follow_constraint(obj: bpy.types.Object, constraint_name: str) -> bpy.types.Constraint | None:
    """The named Proscenio Child Of follow on ``obj``, or None."""
    con = obj.constraints.get(constraint_name)
    return con if con is not None and con.type == "CHILD_OF" else None


def follow_shape(obj: bpy.types.Object, constraint_name: str) -> str:
    """How ``obj`` currently follows a bone: the live authoring shape.

    - ``"constraint"`` - the Proscenio object-parent + Child Of follow (the
      canonical route).
    - ``"bone_parent"`` - a real bone parent (``parent_type == "BONE"``); the
      supported power-user fallback.
    - ``"none"`` - follows no bone.

    Both follow shapes are first-class exportable; this is the single
    definition the panels and the operators read so they never disagree
    about which one is live.
    """
    if follow_constraint(obj, constraint_name) is not None:
        return "constraint"
    if getattr(obj, "parent_type", "") == "BONE" and getattr(obj, "parent_bone", ""):
        return "bone_parent"
    return "none"


def expected_rest_inverse(armature: bpy.types.Object, bone_name: str) -> Matrix:
    """The Child Of inverse that cancels ``bone_name``'s CURRENT rest.

    This value can be recomputed at any time, which is what makes the
    stale-follow check possible: a stored ``inverse_matrix`` that no longer
    equals it means the rig's rest (or the rig object's own transform)
    changed since the bind.

    Raises ``RuntimeError`` when the armature lacks ``bone_name``.
    """
    bone = armature.data.bones.get(bone_name)
    if bone is None:
        raise RuntimeError(f"armature '{armature.name}' has no bone '{bone_name}'")
    return (armature.matrix_world @ bone.matrix_local).inverted()


def bone_is_posed(armature: bpy.types.Object, bone_name: str) -> bool:
    """True when ``bone_name``'s evaluated pose differs from its rest."""
    pose_bone = armature.pose.bones.get(bone_name)
    bone = armature.data.bones.get(bone_name)
    if pose_bone is None or bone is None:
        return False
    rest = bone.matrix_local
    posed = pose_bone.matrix
    return any(abs(posed[i][j] - rest[i][j]) > 1e-5 for i in range(4) for j in range(4))


def follow_is_stale(
    obj: bpy.types.Object, armature: bpy.types.Object, constraint_name: str
) -> bool:
    """True when the stored follow inverse no longer cancels the current rest.

    Silent drift class (D7): editing the bone rest in Edit Mode - or moving
    the rig object - leaves the snapshot inverse cancelling the OLD rest, so
    the follower sits offset at rest with no error anywhere. Rebinding
    recomputes the inverse and clears the condition.
    """
    con = follow_constraint(obj, constraint_name)
    if con is None or not con.subtarget:
        return False
    if armature.data.bones.get(con.subtarget) is None:
        return True
    expected = expected_rest_inverse(armature, con.subtarget)
    stored = con.inverse_matrix
    return any(abs(stored[i][j] - expected[i][j]) > 1e-5 for i in range(4) for j in range(4))


@contextmanager
def _at_rest_pose(armature: bpy.types.Object | None) -> Iterator[None]:
    """Temporarily zero the armature's pose so world reads are REST worlds.

    Every keep-world snapshot inside bind / unbind must capture the REST
    placement, never the posed one: converting a bone-parented element while
    the rig sits on a posed frame would otherwise bake that frame's pose into
    the element's new rest (the corrupted-convert class). Mirrors the
    writer's ``_rest_pose_for_geometry`` basis-zeroing, restored on exit.
    """
    pose = getattr(armature, "pose", None)
    saved: dict[str, Matrix] = {}
    if pose is not None:
        for pose_bone in pose.bones:
            saved[pose_bone.name] = pose_bone.matrix_basis.copy()
            pose_bone.matrix_basis = Matrix()
    view_layer = bpy.context.view_layer
    if view_layer is not None:
        view_layer.update()
    try:
        yield
    finally:
        if pose is not None:
            for pose_bone in pose.bones:
                if pose_bone.name in saved:
                    pose_bone.matrix_basis = saved[pose_bone.name]
        if view_layer is not None:
            view_layer.update()


def drop_bone_parent_keep_world(obj: bpy.types.Object) -> None:
    """Convert a real BONE parent to an object parent, preserving world.

    Layering a Child Of follow on top of a live bone parent would
    double-drive the object (the bone's influence applies twice and the
    object flies off when posed), so every bind routes through this first.
    No-op on an object without a bone parent.
    """
    if obj.parent_type != "BONE":
        return
    world = obj.matrix_world.copy()
    obj.parent_type = "OBJECT"
    obj.parent_bone = ""
    if obj.parent is not None:
        obj.matrix_parent_inverse = obj.parent.matrix_world.inverted()
    obj.matrix_world = world


def bind_to_bone_rest(
    obj: bpy.types.Object,
    armature: bpy.types.Object,
    bone_name: str,
    constraint_name: str,
) -> bool:
    """Wire ``obj`` to follow ``bone_name`` via the named Child Of constraint.

    Drops a live bone parent keep-world first (never double-drive), removes
    any prior Proscenio follow of that name so a re-call recomputes the
    inverse, and bakes the inverse from the bone REST (D7). Returns True when
    the bone is currently posed - the caller should warn, because the object
    visibly snaps to the rest-relative placement Godot will reproduce.

    Raises ``RuntimeError`` when the armature lacks ``bone_name``.
    """
    inverse = expected_rest_inverse(armature, bone_name)
    posed = bone_is_posed(armature, bone_name)
    # Every keep-world step below runs against the REST pose: converting a
    # bone-parented element on a posed frame must bake the element's REST
    # placement into the new basis, never the current frame's pose (the
    # corrupted-convert class). The rest-world snapshot also survives the
    # removal of a prior (possibly stale) follow, so a re-bind keeps the
    # element where it rests on screen and only recomputes the inverse.
    with _at_rest_pose(armature):
        rest_world = obj.matrix_world.copy()
        drop_bone_parent_keep_world(obj)
        existing = follow_constraint(obj, constraint_name)
        if existing is not None:
            obj.constraints.remove(existing)
        obj.matrix_world = rest_world
        con = obj.constraints.new(type="CHILD_OF")
        con.name = constraint_name
        con.target = armature
        con.subtarget = bone_name
        con.inverse_matrix = inverse
    return posed


def unbind_keep_world(obj: bpy.types.Object, constraint_name: str) -> None:
    """Reverse any follow shape, keeping the REST on-screen position.

    Removes the named Proscenio constraint if present AND drops a real bone
    parent if present (whichever shape is live - or both, the double-drive
    case), restoring the world matrix so the object stays put. Runs against
    the REST pose so unbinding on a posed frame preserves the authored rest
    placement instead of baking the frame's pose into the freed object.
    """
    existing = follow_constraint(obj, constraint_name)
    armature = existing.target if existing is not None else None
    if armature is None and obj.parent_type == "BONE":
        armature = obj.parent
    with _at_rest_pose(armature):
        world = obj.matrix_world.copy()
        if existing is not None:
            obj.constraints.remove(existing)
        drop_bone_parent_keep_world(obj)
        obj.matrix_world = world


def followed_bone_of(obj: bpy.types.Object, constraint_name: str) -> str:
    """The bone ``obj`` follows via constraint or bone parent, or ""."""
    subtarget = follow_subtarget(obj, constraint_name)
    if subtarget:
        return subtarget
    if getattr(obj, "parent_type", "") == "BONE":
        return str(getattr(obj, "parent_bone", ""))
    return ""
