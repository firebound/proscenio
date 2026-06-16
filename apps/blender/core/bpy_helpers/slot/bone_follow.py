"""Slot bone-follow: the Blender twin of the Godot importer's slot anchor.

bpy-bound (manipulates ``Object.constraints`` + reads pose matrices), so this
module imports bpy at top per the bpy_helpers contract. The convention it
authors - object-parent + a Child Of constraint whose inverse cancels the
bone rest - keeps slot attachment quads flat in the picture plane while the
slot rides only the bone's pose delta, mirroring slot_builder.gd's
``get_skeleton_rest().affine_inverse()`` cancel in Godot.
"""

from __future__ import annotations

import bpy

from ..._shared.cp_keys import PROSCENIO_SLOT_BONE
from ..._shared.props_access import active_armature, resolve_export_armature

SLOT_FOLLOW_CONSTRAINT = "Proscenio Slot Follow"


def resolve_slot_armature(
    context: bpy.types.Context, empty: bpy.types.Object
) -> bpy.types.Object | None:
    """The armature a slot Empty should follow a bone of, or None.

    Priority: the Empty's own object-parent when it is an ARMATURE (the slot
    convention parents the Empty to the rig), then the Skeleton picker, then
    the scene's export armature.
    """
    parent = getattr(empty, "parent", None)
    if parent is not None and getattr(parent, "type", None) == "ARMATURE":
        return parent
    picker = active_armature(context)
    if picker is not None:
        return picker
    scene = getattr(context, "scene", None)
    return resolve_export_armature(scene) if scene is not None else None


def _follow_constraint(empty: bpy.types.Object) -> bpy.types.Constraint | None:
    """The single named follow constraint we own on ``empty``, or None."""
    con = empty.constraints.get(SLOT_FOLLOW_CONSTRAINT)
    return con if con is not None and con.type == "CHILD_OF" else None


def _drop_legacy_bone_parent(empty: bpy.types.Object) -> None:
    """Convert a legacy real BONE parent to an object parent, preserving world.

    A slot authored by the old create_slot bone path is ``parent_type ==
    "BONE"``. Layering a Child Of follow on top of that would double-drive the
    slot, and unbinding would leave it bone-driven; flip it to the object-parent
    convention first so the follow (or its removal) is the only bone influence.
    No-op on a slot already on the convention.
    """
    if empty.parent_type != "BONE":
        return
    world = empty.matrix_world.copy()
    empty.parent_type = "OBJECT"
    empty.parent_bone = ""
    if empty.parent is not None:
        empty.matrix_parent_inverse = empty.parent.matrix_world.inverted()
    empty.matrix_world = world


def bind_slot_to_bone(empty: bpy.types.Object, armature: bpy.types.Object, bone_name: str) -> None:
    """Wire ``empty`` to follow ``bone_name`` of ``armature`` in Blender.

    Re-runnable: an existing follow constraint is removed first so the inverse
    recomputes at the current pose (the Set-Inverse caveat - rebind after
    moving the slot). Writes ``slot_bone`` dual (PG + Custom Property) so the
    writer's preferred field carries the follow even on a headless re-open.

    Raises ``RuntimeError`` when the armature lacks ``bone_name``.
    """
    pose_bone = armature.pose.bones.get(bone_name)
    if pose_bone is None:
        raise RuntimeError(f"armature '{armature.name}' has no bone '{bone_name}'")

    _drop_legacy_bone_parent(empty)
    existing = _follow_constraint(empty)
    if existing is not None:
        empty.constraints.remove(existing)

    con = empty.constraints.new(type="CHILD_OF")
    con.name = SLOT_FOLLOW_CONSTRAINT
    con.target = armature
    con.subtarget = bone_name
    # Headless Set-Inverse: cancel the full bone rest (location + rotation +
    # scale) so only the pose delta moves the slot - the affine_inverse() cancel
    # slot_builder.gd applies in Godot.
    con.inverse_matrix = (armature.matrix_world @ pose_bone.matrix).inverted()

    _write_slot_bone(empty, bone_name)


def unbind_slot_from_bone(empty: bpy.types.Object) -> None:
    """Reverse :func:`bind_slot_to_bone`: drop the constraint + clear slot_bone.

    Leaves the Empty object-parented and inert (the pre-bind state). A legacy
    real BONE parent is dropped too, so a slot from the old convention does not
    stay bone-driven after unbind.
    """
    _drop_legacy_bone_parent(empty)
    existing = _follow_constraint(empty)
    if existing is not None:
        empty.constraints.remove(existing)
    _write_slot_bone(empty, "")


def _write_slot_bone(empty: bpy.types.Object, bone_name: str) -> None:
    """Write slot_bone PG-first + Custom Property; clear both on empty string."""
    props = getattr(empty, "proscenio", None)
    if props is not None:
        props.slot_bone = bone_name
    if bone_name:
        empty[PROSCENIO_SLOT_BONE] = bone_name
    elif PROSCENIO_SLOT_BONE in empty:
        del empty[PROSCENIO_SLOT_BONE]
