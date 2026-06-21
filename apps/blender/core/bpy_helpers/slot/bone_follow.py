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
from ..._shared.pg_cp_fallback import read_field
from ..._shared.props_access import resolve_target_armature

SLOT_FOLLOW_CONSTRAINT = "Proscenio Slot Follow"

# A bone whose world direction lies within this much of the picture plane (XZ)
# collapses a bone-parented attachment quad edge-on. The camera looks down -Y,
# so a bone pointing into the screen (world +/-Y) stays flat; abs(dir.y) below
# this cosine threshold (~45 degrees off Y) is the collapse-risk band.
_INTO_SCREEN_MIN_Y = 0.7


def resolve_slot_armature(
    context: bpy.types.Context, empty: bpy.types.Object
) -> bpy.types.Object | None:
    """The armature a slot Empty should follow a bone of, or None.

    The slot-facing name for the shared :func:`resolve_target_armature`:
    parent-if-ARMATURE, then the Skeleton picker, then the scene's export
    armature.
    """
    return resolve_target_armature(context, empty)


def _follow_constraint(empty: bpy.types.Object) -> bpy.types.Constraint | None:
    """The single named follow constraint we own on ``empty``, or None."""
    con = empty.constraints.get(SLOT_FOLLOW_CONSTRAINT)
    return con if con is not None and con.type == "CHILD_OF" else None


def slot_follow_shape(empty: bpy.types.Object) -> str:
    """How the slot currently follows a bone: the live authoring shape.

    - ``"constraint"`` - the Proscenio object-parent + Child Of follow (the safe
      route, flat for any bone orientation).
    - ``"bone_parent"`` - a hand-authored real bone parent (``parent_type ==
      "BONE"``). Exports fine, but collapses the attachment quads when the bone
      lies in the picture plane (see :func:`bone_parent_collapses`).
    - ``"field_inert"`` - a ``slot_bone`` field is set but nothing drives the
      Empty in Blender (object-parented, no constraint): exports, yet the
      authoring view does not follow. Bind to Bone wires the live follow.
    - ``"none"`` - the slot follows no bone.

    Both ``constraint`` and ``bone_parent`` are first-class exportable shapes;
    this is the single definition the panel and the bind operator read so they
    never disagree about which one is live.
    """
    if _follow_constraint(empty) is not None:
        return "constraint"
    if getattr(empty, "parent_type", "") == "BONE" and getattr(empty, "parent_bone", ""):
        return "bone_parent"
    field = str(read_field(empty, pg_field="slot_bone", cp_key=PROSCENIO_SLOT_BONE, default=""))
    return "field_inert" if field else "none"


def bone_parent_collapses(empty: bpy.types.Object) -> bool:
    """True when a bone-parented slot's bone lies in the picture plane.

    A real bone parent inherits the bone's rest orientation. For a bone pointing
    into the screen (world +/-Y, the slot/cutout convention) the flat attachment
    quads stay flat; for an in-plane bone (+X / +Z) the parent rotation tilts the
    quads edge-on and the export collapses them to zero area. The constraint
    follow cancels the rest, so it never collapses - this flags the bone-parent
    case that should switch to it.
    """
    if getattr(empty, "parent_type", "") != "BONE":
        return False
    armature = getattr(empty, "parent", None)
    if armature is None or getattr(armature, "type", None) != "ARMATURE":
        return False
    pose_bone = armature.pose.bones.get(empty.parent_bone)
    if pose_bone is None:
        return False
    world = armature.matrix_world
    direction = (world @ pose_bone.tail) - (world @ pose_bone.head)
    if direction.length == 0.0:
        return False
    direction.normalize()
    return abs(direction.y) < _INTO_SCREEN_MIN_Y


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

    Assumes ``empty`` is object-parented or unparented - never a live BONE
    parent (the bind operator refuses that, routing the user through Unbind
    first, and ``create_slot`` object-parents before calling here). Any prior
    Proscenio follow constraint is removed first so a standalone re-call
    recomputes the inverse at the current pose. Writes ``slot_bone`` dual (PG +
    Custom Property) so the writer's preferred field carries the follow even on
    a headless re-open.

    Raises ``RuntimeError`` when the armature lacks ``bone_name``.
    """
    pose_bone = armature.pose.bones.get(bone_name)
    if pose_bone is None:
        raise RuntimeError(f"armature '{armature.name}' has no bone '{bone_name}'")

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
