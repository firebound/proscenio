"""Element bone-attach helpers.

The non-slot path for pinning a rigid element to a single bone. Authoring is
constraint-first via the shared bone-follow core (spec 080); this package
keeps the element-facing armature resolution plus the picture-plane check.
Mirrors the slot ``bone_follow`` split - bpy helpers here, operators in
``operators/sprite``.
"""

from __future__ import annotations

from .bone_attach import (
    bone_in_picture_plane,
    resolve_sprite_armature,
)

__all__ = [
    "bone_in_picture_plane",
    "resolve_sprite_armature",
]
