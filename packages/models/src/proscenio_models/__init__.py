"""Pydantic models for the .proscenio interchange format.

Source of truth for the JSON Schema (dumped by ``proscenio_codegen``),
the Photoshop TypeScript bindings, and the Godot Resource bindings.
"""

from __future__ import annotations

from proscenio_models.proscenio import (
    Animation,
    Bone,
    Key,
    PolygonSprite,
    ProscenioDocument,
    Skeleton,
    Slot,
    Sprite,
    SpriteFrameSprite,
    Track,
    Weight,
)

__all__ = [
    "Animation",
    "Bone",
    "Key",
    "PolygonSprite",
    "ProscenioDocument",
    "Skeleton",
    "Slot",
    "Sprite",
    "SpriteFrameSprite",
    "Track",
    "Weight",
]
