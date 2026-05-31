"""Pydantic models for the .proscenio v1 interchange format.

This module is the **source of truth** for the wire shape. The JSON
Schema artifact at ``packages/models/schemas/proscenio.schema.json``
is regenerated from these classes by ``proscenio_codegen``; any change
to the wire shape lands here first. The Blender writer constructs the
output document via ``ProscenioDocument.model_dump_json(...)`` and the
Photoshop + Godot consumers read the schema artifact downstream.

Encoding choices:

- ``Vec2`` and ``Rect`` are typed as ``list[float]`` with
  ``min_length`` / ``max_length`` rather than ``tuple[float, float]``
  so the emitted JSON Schema uses the ``items`` + ``minItems`` /
  ``maxItems`` shape consumers already expect. Pydantic's default
  tuple serialization emits ``prefixItems`` (draft 2020-12); swapping
  to that shape would force every existing consumer to re-parse.
- ``model_config["extra"] = "forbid"`` mirrors the
  ``additionalProperties: false`` clause on every object in the
  schema; pydantic's default ``"ignore"`` would silently drop unknown
  fields.
- ``Sprite`` is a discriminated union on the ``type`` literal. The
  polygon variant defaults to ``"polygon"`` so pre-discriminator v1
  documents (``type`` absent) round-trip cleanly.
- Field declaration order in each class matches the historical writer
  dict insertion order so ``model_dump_json(exclude_unset=True)``
  reproduces the goldens byte-for-byte.
- ``ProscenioDocument`` is the document root. Use ``model_dump_json``
  to serialize, ``model_validate`` to parse.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Discriminator, Field, Tag, model_validator

Vec2 = Annotated[list[float], Field(min_length=2, max_length=2)]
Rect = Annotated[
    list[float],
    Field(
        min_length=4,
        max_length=4,
        description="[x, y, width, height] in atlas pixels.",
    ),
]


class _Strict(BaseModel):
    """Base class: forbid extra fields (mirrors additionalProperties: false)."""

    model_config = ConfigDict(extra="forbid")


class Bone(_Strict):
    name: str = Field(min_length=1)
    parent: str | None = None
    position: Vec2 | None = None
    rotation: float | None = None
    scale: Vec2 | None = None
    length: float | None = Field(default=None, ge=0)


class Skeleton(_Strict):
    bones: list[Bone]


class Weight(_Strict):
    bone: str
    values: list[Annotated[float, Field(ge=0, le=1)]]


class PolygonSprite(_Strict):
    """Cutout-style sprite rendered as a Godot Polygon2D - vertices + UV.

    Default sprite kind when ``type`` is omitted (backwards-compatible
    with v1 documents).

    Field declaration order mirrors the writer's dict insertion order
    so ``model_dump_json(exclude_unset=True)`` reproduces the golden
    fixtures byte-for-byte once the writer migrates.
    """

    type: Literal["polygon"] = Field(
        default="polygon",
        description="Discriminator. Optional; absence means `polygon`.",
    )
    name: str = Field(min_length=1)
    bone: str | None = None
    texture_region: Rect
    polygon: list[Vec2]
    uv: list[Vec2]
    texture: str | None = Field(
        default=None,
        description=(
            "Optional per-sprite texture filename, resolved relative to "
            "the .proscenio document. Multi-PNG fixtures use this so each "
            "sprite picks its own image instead of slicing a shared "
            "atlas. Importers fall back to the top-level `atlas` field "
            "when absent."
        ),
    )
    weights: list[Weight] | None = None

    @model_validator(mode="after")
    def _polygon_uv_lengths_match(self) -> PolygonSprite:
        """Every polygon vertex needs its own UV coordinate.

        The schema-level constraint does not exist (JSON Schema cannot
        express ``len(a) == len(b)``); pydantic carries it instead.
        """
        if len(self.polygon) != len(self.uv):
            raise ValueError(
                f"polygon has {len(self.polygon)} vertices but uv has "
                f"{len(self.uv)}; counts must match"
            )
        return self


class SpriteFrameSprite(_Strict):
    """Spritesheet sprite rendered as a Godot Sprite2D.

    ``frame`` indexes into an ``hframes`` x ``vframes`` grid carved
    out of the atlas (or out of ``texture_region`` when present).

    Field declaration order mirrors the writer's dict insertion order
    so ``model_dump_json(exclude_unset=True)`` reproduces the golden
    fixtures byte-for-byte once the writer migrates.
    """

    type: Literal["sprite_frame"] = Field(
        description="Discriminator. Required and constant.",
    )
    name: str = Field(min_length=1)
    bone: str
    hframes: int = Field(ge=1)
    vframes: int = Field(ge=1)
    frame: int = Field(
        default=0,
        ge=0,
        description=(
            "Initial frame index (row-major). Animation tracks override at runtime."
        ),
    )
    centered: bool = True
    texture_region: Rect | None = Field(
        default=None,
        description=(
            "Optional sub-rectangle within the atlas where the "
            "spritesheet lives. Absent means use the full atlas."
        ),
    )
    texture: str | None = Field(
        default=None,
        description=(
            "Optional per-sprite texture filename, resolved relative to "
            "the .proscenio document. Mirrors the polygon-sprite field. "
            "Importers fall back to the top-level `atlas` field when "
            "absent."
        ),
    )
    offset: Vec2 = Field(default=[0.0, 0.0])

    @model_validator(mode="after")
    def _frame_within_grid(self) -> SpriteFrameSprite:
        """``frame`` indexes a row-major ``hframes`` x ``vframes`` grid.

        The schema-level ``minimum: 0`` only catches negatives; the
        upper bound depends on the sibling ``hframes`` / ``vframes``
        and cannot be expressed in JSON Schema. Pydantic carries it.
        """
        cells = self.hframes * self.vframes
        if self.frame >= cells:
            raise ValueError(
                f"frame={self.frame} is out of range for a "
                f"{self.hframes}x{self.vframes} grid (max valid index: "
                f"{cells - 1})"
            )
        return self


def _sprite_discriminator(payload: Any) -> str:
    """Return the discriminator tag for a Sprite payload.

    ``type`` is optional on the polygon variant (v1 backwards
    compatibility) and required on the sprite_frame variant. Pydantic's
    field-string discriminator extracts the tag before defaults run, so
    a missing ``type`` would fail union resolution. A callable
    discriminator runs against the raw input, lets us default to
    ``"polygon"``, and rejects unknown tags up front.
    """
    if isinstance(payload, dict):
        tag = payload.get("type", "polygon")
    else:
        tag = getattr(payload, "type", "polygon")
    if tag not in {"polygon", "sprite_frame"}:
        return "unknown"
    return str(tag)


Sprite = Annotated[
    Union[
        Annotated[PolygonSprite, Tag("polygon")],
        Annotated[SpriteFrameSprite, Tag("sprite_frame")],
    ],
    Discriminator(_sprite_discriminator),
]


class Slot(_Strict):
    # Field order matches the writer's dict emission order so
    # `model_dump_json(exclude_unset=True)` reproduces the goldens.
    name: str = Field(min_length=1)
    attachments: list[str]
    bone: str | None = None
    default: str | None = None


class Key(_Strict):
    time: float = Field(ge=0)
    interp: Literal["linear", "constant"] | None = None
    position: Vec2 | None = None
    rotation: float | None = None
    scale: Vec2 | None = None
    frame: int | None = Field(default=None, ge=0)
    attachment: str | None = None
    visible: bool | None = None


class Track(_Strict):
    type: Literal["bone_transform", "sprite_frame", "slot_attachment", "visibility"]
    target: str = Field(min_length=1)
    keys: list[Key]


class Animation(_Strict):
    name: str = Field(min_length=1)
    length: float = Field(gt=0)
    loop: bool | None = None
    tracks: list[Track]


class ProscenioDocument(_Strict):
    """Root of a .proscenio v1 document.

    Schema id mirrors the hand-maintained file so consumer ajv
    validators that key off ``$id`` continue to resolve.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "$id": (
                "https://space-wizard-studios.github.io/proscenio/schemas/"
                "proscenio.schema.json"
            ),
        },
        title="Proscenio character",
    )

    # Field declaration order matches the writer's dict insertion order so
    # `model_dump_json()` round-trips against the existing golden fixtures.
    # Domain order (skeleton -> sprites -> slots -> atlas -> animations)
    # is also a natural read for a `.proscenio` file: bones before what
    # rides them, group memberships, then the texture and the timelines.
    format_version: Literal[1] = Field(
        description="Bump on any breaking change to the shape of this document.",
    )
    name: str = Field(min_length=1)
    pixels_per_unit: float = Field(gt=0)
    skeleton: Skeleton
    sprites: list[Sprite]
    slots: list[Slot] | None = None
    atlas: str | None = None
    animations: list[Animation] | None = None
