"""Pydantic models for the PSD manifest v2 format.

Output of the Proscenio Photoshop UXP exporter, input of the Proscenio
Blender importer. v2 introduces the tag-driven taxonomy from the
photoshop tag system (anchor, per-entry origin, blend_mode, subfolder,
the ``kind: "mesh"`` polygon variant).

Same encoding choices as ``proscenio.py``: ``UintPair`` typed as
``list[int]`` with constrained length so the emitted JSON Schema uses
``items`` + ``minItems`` / ``maxItems`` instead of pydantic's default
``prefixItems``. ``Layer`` is a discriminated union on ``kind``;
polygon and mesh share a class because they only differ at the
discriminator level, mirroring the schema's ``enum: ["polygon",
"mesh"]`` on a single object.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Discriminator, Field, Tag

UintPair = Annotated[
    list[int],
    Field(min_length=2, max_length=2),
]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


BlendMode = Literal["normal", "multiply", "screen", "additive"]


class FrameEntry(_Strict):
    index: int = Field(
        ge=0,
        description="Frame index, 0-based, contiguous, ordered.",
    )
    path: str = Field(
        min_length=1,
        description="Path to the frame PNG, relative to the manifest file.",
    )


class PolygonLayer(_Strict):
    """Single PNG, single quad mesh.

    ``kind: "mesh"`` is a polygon superset flagged as a deformable mesh
    source; renders as polygon when no rig is bound.
    """

    kind: Literal["polygon", "mesh"]
    name: str = Field(min_length=1)
    path: str = Field(
        min_length=1,
        description="Path to the layer PNG, relative to the manifest file.",
    )
    position: UintPair = Field(
        description="PSD top-left bbox of the layer in pixels.",
    )
    size: UintPair = Field(description="Layer bbox size in pixels.")
    z_order: int = Field(ge=0, description="Stack index, 0 = top.")
    origin: UintPair | None = Field(
        default=None,
        description=(
            "Optional pivot in PSD pixels. Set by the [origin:x,y] tag "
            "or by an [origin] marker layer inside the group. Importer "
            "uses this as the mesh's Object.location when present; "
            "falls back to bbox center otherwise."
        ),
    )
    blend_mode: BlendMode | None = Field(
        default=None,
        description=(
            "Layer blend mode emitted from the PSD; importer maps to "
            "material blend mode."
        ),
    )
    subfolder: str | None = Field(
        default=None,
        min_length=1,
        description=(
            "Optional output sub-folder under images/, set by the "
            "[folder:name] tag. Importer ignores; this is purely a "
            "disk-layout hint reflected in `path`."
        ),
    )


class SpriteFrameLayer(_Strict):
    """N frames, single quad mesh, animated via ``proscenio.frame``.

    Authored as a LayerSet tagged ``[spritesheet]``.
    """

    kind: Literal["sprite_frame"]
    name: str = Field(min_length=1)
    position: UintPair = Field(
        description="PSD top-left bbox of the largest frame.",
    )
    size: UintPair = Field(
        description=(
            "Largest frame bbox size in pixels (importer pads smaller frames to match)."
        ),
    )
    z_order: int = Field(ge=0)
    frames: list[FrameEntry] = Field(min_length=2)
    origin: UintPair | None = Field(
        default=None,
        description="Optional pivot in PSD pixels (see polygon_layer.origin).",
    )
    blend_mode: BlendMode | None = None
    subfolder: str | None = Field(default=None, min_length=1)


def _layer_discriminator(payload: Any) -> str:
    """Route polygon and mesh kinds to the same class; sprite_frame to its own."""
    if isinstance(payload, dict):
        kind = payload.get("kind")
    else:
        kind = getattr(payload, "kind", None)
    if kind == "sprite_frame":
        return "sprite_frame"
    if kind in {"polygon", "mesh"}:
        return "polygon_or_mesh"
    return "unknown"


Layer = Annotated[
    Union[
        Annotated[PolygonLayer, Tag("polygon_or_mesh")],
        Annotated[SpriteFrameLayer, Tag("sprite_frame")],
    ],
    Discriminator(_layer_discriminator),
]


class PsdManifest(_Strict):
    """Root of a PSD manifest v2 document."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "$id": (
                "https://space-wizard-studios.github.io/proscenio/schemas/"
                "psd_manifest.schema.json"
            ),
        },
        title="Proscenio PSD manifest",
    )

    format_version: Literal[2] = Field(
        description=(
            "Bump on any breaking change to the shape of this document. "
            "v2 introduces the tag-driven taxonomy in the photoshop tag "
            "system (anchor, per-entry origin, blend_mode, subfolder, "
            'kind: "mesh").'
        ),
    )
    doc: str = Field(
        min_length=1,
        description="Original PSD filename. Display only - not a resolvable path.",
    )
    size: UintPair = Field(description="[doc_width_px, doc_height_px].")
    pixels_per_unit: float = Field(
        gt=0,
        description=(
            "Importer divides PSD pixels by this when stamping mesh size and position."
        ),
    )
    anchor: UintPair | None = Field(
        default=None,
        description=(
            "Document anchor in PSD pixels. Set by the first horizontal "
            "+ vertical PSD guide; importer places the root bone here. "
            "Omitted when no guides were authored."
        ),
    )
    layers: list[Layer] = Field(
        description=(
            "Z-ordered top-to-bottom. Each entry is a single mesh in "
            "Blender after import."
        ),
    )
