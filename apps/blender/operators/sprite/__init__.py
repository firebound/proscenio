"""Sprite element operators.

Subpackage with:

- bone_parent.py - PROSCENIO_OT_parent_sprite_to_bone,
  PROSCENIO_OT_clear_sprite_bone_parent (the non-slot rigid bone attach)
"""

from __future__ import annotations

from . import bone_parent


def register() -> None:
    bone_parent.register()


def unregister() -> None:
    bone_parent.unregister()
