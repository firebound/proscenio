"""Schema-shaped TypedDicts for the writer (SPEC 009 wave 9.4).

Mirrors the JSON shapes emitted by the writer. The values are closed
over the schema literals from ``schemas/proscenio.schema.json`` so a
schema bump forces the writer to update both the literal sets and the
TypedDict definitions in lockstep.

When SPEC 008 lands the ``texture_region`` track type, this module
gains the matching ``TextureRegionTrack`` TypedDict + the
``TrackType`` literal extends.
"""

from __future__ import annotations

from typing import Literal, TypedDict

SCHEMA_VERSION = 1
DEFAULT_PIXELS_PER_UNIT = 100.0

TrackType = Literal["bone_transform", "sprite_frame", "slot_attachment", "visibility"]
InterpType = Literal["linear", "constant"]
SpriteType = Literal["polygon", "sprite_frame"]


class BoneDict(TypedDict):
    name: str
    parent: str | None
    position: list[float]
    rotation: float
    scale: list[float]
    length: float


class RestLocal(TypedDict):
    position: tuple[float, float]
    rotation: float
    scale: tuple[float, float]


class SpriteFrameDict(TypedDict, total=False):
    type: Literal["sprite_frame"]
    name: str
    bone: str
    hframes: int
    vframes: int
    frame: int
    centered: bool
    texture_region: list[float]


class WeightDict(TypedDict):
    bone: str
    values: list[float]
