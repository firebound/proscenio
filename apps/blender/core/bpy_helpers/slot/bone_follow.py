"""Slot bone-follow: the Blender twin of the Godot importer's slot anchor.

Thin slot-facing wrapper over the shared bone-follow core (spec 080 D6):
object-parent + a Child Of constraint whose inverse cancels the bone REST,
keeping slot attachment quads flat in the picture plane while the slot rides
only the bone's pose delta - mirroring slot_builder.gd's
``affine_inverse()`` cancel in Godot.

The constraint IS the binding (D5): the writer reads its ``subtarget``
directly, so there is no ``slot_bone`` field to keep in sync and no
"field set but nothing follows" state to represent. Bind and unbind still
clear a legacy ``proscenio_slot_bone`` Custom Property when one is present
so pre-080 files converge on the single source as they are touched.
"""

from __future__ import annotations

import bpy

from ..._shared.armature_resolve import resolve_target_armature
from ..._shared.bone_follow_resolve import SLOT_FOLLOW_CONSTRAINT
from ..._shared.cp_keys import PROSCENIO_SLOT_BONE
from .._shared.bone_follow import (
    bind_to_bone_rest,
    follow_shape,
    unbind_keep_world,
)
from .._shared.bone_orientation import bone_in_picture_plane

__all__ = [
    "SLOT_FOLLOW_CONSTRAINT",
    "bind_slot_to_bone",
    "bone_parent_collapses",
    "resolve_slot_armature",
    "slot_follow_shape",
    "unbind_slot_from_bone",
]


def resolve_slot_armature(
    context: bpy.types.Context, empty: bpy.types.Object
) -> bpy.types.Object | None:
    """The armature a slot Empty should follow a bone of, or None.

    The slot-facing name for the shared :func:`resolve_target_armature`:
    parent-if-ARMATURE, then the Skeleton picker, then the scene's export
    armature.
    """
    return resolve_target_armature(context, empty)


def slot_follow_shape(empty: bpy.types.Object) -> str:
    """How the slot currently follows a bone: ``constraint`` / ``bone_parent``
    / ``none`` (the shared shape vocabulary; both follow shapes export)."""
    return follow_shape(empty, SLOT_FOLLOW_CONSTRAINT)


def bone_parent_collapses(empty: bpy.types.Object) -> bool:
    """True when a bone-parented slot's bone lies in the picture plane.

    A real bone parent inherits the bone's rest orientation. For a bone pointing
    into the screen (world +/-Y, the slot/cutout convention) the flat attachment
    quads stay flat; for an in-plane bone (+X / +Z) the parent rotation tilts the
    quads edge-on and the export collapses them to zero area. The constraint
    follow cancels the rest, so it never collapses - this flags the bone-parent
    case that should switch to it. The in-plane test is the shared
    :func:`bone_in_picture_plane`; this adds the slot-specific guard that the
    Empty is a real BONE parent of an ARMATURE.
    """
    if getattr(empty, "parent_type", "") != "BONE":
        return False
    armature = getattr(empty, "parent", None)
    if armature is None or getattr(armature, "type", None) != "ARMATURE":
        return False
    return bone_in_picture_plane(armature, empty.parent_bone)


def bind_slot_to_bone(empty: bpy.types.Object, armature: bpy.types.Object, bone_name: str) -> bool:
    """Wire ``empty`` to follow ``bone_name`` of ``armature`` in Blender.

    Delegates to the shared core: drops a legacy real BONE parent keep-world
    (never double-drive), rebuilds the constraint, and bakes the inverse from
    the bone REST - not the posed matrix - so Blender and the Godot anchor
    cancel the same thing (D7). Returns True when the bone is posed at bind
    time (the caller warns; the Empty snaps to the placement Godot will
    reproduce). Clears a legacy ``proscenio_slot_bone`` Custom Property so
    the constraint stays the one source of truth.

    Raises ``RuntimeError`` when the armature lacks ``bone_name``.
    """
    posed = bind_to_bone_rest(empty, armature, bone_name, SLOT_FOLLOW_CONSTRAINT)
    _clear_legacy_slot_bone_field(empty)
    return posed


def unbind_slot_from_bone(empty: bpy.types.Object) -> None:
    """Reverse :func:`bind_slot_to_bone`: drop whichever follow shape is live.

    Keeps the on-screen position, leaves the Empty object-parented and inert
    (the pre-bind state), and clears a legacy ``proscenio_slot_bone`` Custom
    Property so the writer's read-fallback cannot resurrect the binding.
    """
    unbind_keep_world(empty, SLOT_FOLLOW_CONSTRAINT)
    _clear_legacy_slot_bone_field(empty)


def _clear_legacy_slot_bone_field(empty: bpy.types.Object) -> None:
    """Drop the pre-080 ``proscenio_slot_bone`` idprop when present."""
    if PROSCENIO_SLOT_BONE in empty:
        del empty[PROSCENIO_SLOT_BONE]
