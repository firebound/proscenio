"""Sprite bone-attach helpers.

The non-slot path for pinning a rigid sprite to a single bone: a real
``parent_type == "BONE"`` parent authored keep-transform (no jump to the bone
tail), plus the picture-plane check that warns when the chosen bone would
rotate the sprite out of the camera plane. Mirrors the slot ``bone_follow``
split - bpy helpers here, operators in ``operators/sprite``.
"""

from __future__ import annotations

from .bone_attach import (
    bone_in_picture_plane,
    clear_bone_parent_keep_world,
    current_bone_parent,
    parent_to_bone_keep_world,
    resolve_sprite_armature,
)

__all__ = [
    "bone_in_picture_plane",
    "clear_bone_parent_keep_world",
    "current_bone_parent",
    "parent_to_bone_keep_world",
    "resolve_sprite_armature",
]
