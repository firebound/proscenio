"""Slot bpy-helpers - bone-follow authoring (object-parent + Child Of)."""

from __future__ import annotations

from .bone_follow import (
    SLOT_FOLLOW_CONSTRAINT,
    bind_slot_to_bone,
    resolve_slot_armature,
    unbind_slot_from_bone,
)

__all__ = [
    "SLOT_FOLLOW_CONSTRAINT",
    "bind_slot_to_bone",
    "resolve_slot_armature",
    "unbind_slot_from_bone",
]
