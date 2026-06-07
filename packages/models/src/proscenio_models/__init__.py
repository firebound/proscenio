"""Pydantic models for the .proscenio interchange format.

Source of truth for the JSON Schema (dumped by ``proscenio_codegen``),
the Photoshop TypeScript bindings, and the Godot Resource bindings.
"""

from __future__ import annotations

from proscenio_models.proscenio import (
    Animation,
    Bone,
    Element,
    Key,
    MeshElement,
    ProscenioDocument,
    Skeleton,
    Slot,
    SpriteElement,
    Track,
    Weight,
)
from proscenio_models.psd_manifest import (
    BlendMode,
    FrameEntry,
    Layer,
    MeshLayer,
    PsdManifest,
    SpriteLayer,
)

__all__ = [
    "Animation",
    "BlendMode",
    "Bone",
    "Element",
    "FrameEntry",
    "Key",
    "Layer",
    "MeshElement",
    "MeshLayer",
    "ProscenioDocument",
    "PsdManifest",
    "Skeleton",
    "Slot",
    "SpriteElement",
    "SpriteLayer",
    "Track",
    "Weight",
]
