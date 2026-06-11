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
- ``Element`` is a discriminated union on the ``type`` literal. The
  mesh variant defaults to ``"mesh"`` so documents that omit ``type``
  round-trip cleanly.
- Field declaration order reproduces the goldens (see the architecture
  docs, "Where to tread carefully").
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


class MeshElement(_Strict):
    """Deformable cutout element rendered as a Godot Polygon2D - vertices + UV.

    Default element kind when ``type`` is omitted. Field order reproduces
    the goldens.
    """

    type: Literal["mesh"] = Field(
        default="mesh",
        description="Discriminator. Optional; absence means `mesh`.",
    )
    name: str = Field(min_length=1)
    bone: str | None = None
    texture_region: Rect
    polygon: list[Vec2]
    uv: list[Vec2]
    texture: str | None = Field(
        default=None,
        description=(
            "Optional per-element texture filename, resolved relative to "
            "the .proscenio document. Multi-PNG fixtures use this so each "
            "element picks its own image instead of slicing a shared "
            "atlas. Importers fall back to the top-level `atlas` field "
            "when absent."
        ),
    )
    weights: list[Weight] | None = None

    @model_validator(mode="after")
    def _polygon_uv_lengths_match(self) -> MeshElement:
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


class SpriteElement(_Strict):
    """Rigid sprite rendered as a Godot Sprite2D.

    ``frame`` indexes into an ``hframes`` x ``vframes`` grid carved
    out of the atlas (or out of ``texture_region`` when present). A
    single-frame sprite (``hframes`` = ``vframes`` = 1) is the static
    case. Field order reproduces the goldens.
    """

    type: Literal["sprite"] = Field(
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
            "Optional per-element texture filename, resolved relative to "
            "the .proscenio document. Mirrors the mesh-element field. "
            "Importers fall back to the top-level `atlas` field when "
            "absent."
        ),
    )
    offset: Vec2 = Field(default=[0.0, 0.0])

    @model_validator(mode="after")
    def _frame_within_grid(self) -> SpriteElement:
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


def _element_discriminator(payload: Any) -> str | None:
    """Return the discriminator tag for an Element payload.

    ``type`` is optional on the mesh variant (absence means mesh) and
    required on the sprite variant. Pydantic's field-string
    discriminator extracts the tag before defaults run, so a missing
    ``type`` would fail union resolution. A callable discriminator runs
    against the raw input, lets us default to ``"mesh"``, and rejects
    unknown tags up front.

    Returns ``None`` for unexpected ``type`` values so pydantic raises
    a ``union_tag_not_found`` ValidationError rather than dispatching
    to a non-existent variant.
    """
    if isinstance(payload, dict):
        tag = payload.get("type", "mesh")
    else:
        tag = getattr(payload, "type", "mesh")
    if tag not in {"mesh", "sprite"}:
        return None
    return str(tag)


Element = Annotated[
    Union[
        Annotated[MeshElement, Tag("mesh")],
        Annotated[SpriteElement, Tag("sprite")],
    ],
    Discriminator(_element_discriminator),
]


class Slot(_Strict):
    # Field order reproduces the goldens.
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
                "https://firebound.github.io/proscenio/schemas/"
                "proscenio.schema.json"
            ),
        },
        title="Proscenio character",
    )

    # Field order reproduces the goldens.
    format_version: Literal[1] = Field(
        description="Bump on any breaking change to the shape of this document.",
    )
    name: str = Field(min_length=1)
    pixels_per_unit: float = Field(gt=0)
    skeleton: Skeleton
    elements: list[Element]
    slots: list[Slot] | None = None
    atlas: str | None = None
    animations: list[Animation] | None = None
