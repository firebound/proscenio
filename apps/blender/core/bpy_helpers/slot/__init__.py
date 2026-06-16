"""Slot bpy-helpers - bone-follow authoring (object-parent + Child Of)."""

from __future__ import annotations

from .bone_follow import (
    SLOT_FOLLOW_CONSTRAINT,
    bind_slot_to_bone,
    bone_parent_collapses,
    resolve_slot_armature,
    slot_follow_shape,
    unbind_slot_from_bone,
)

__all__ = [
    "SLOT_FOLLOW_CONSTRAINT",
    "bind_slot_to_bone",
    "bone_parent_collapses",
    "resolve_slot_armature",
    "slot_follow_shape",
    "unbind_slot_from_bone",
]
