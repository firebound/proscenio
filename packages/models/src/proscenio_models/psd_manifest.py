"""Pydantic models for the PSD manifest format.

Output of the Proscenio Photoshop UXP exporter, input of the Proscenio
Blender importer. Carries the tag-driven taxonomy from the photoshop
tag system (anchor, per-entry origin, blend_mode, subfolder) over two
element kinds: ``mesh`` (-> Polygon2D) and ``sprite`` (-> Sprite2D).

Same encoding choices as ``proscenio.py``: ``UintPair`` typed as
``list[int]`` with constrained length so the emitted JSON Schema uses
``items`` + ``minItems`` / ``maxItems`` instead of pydantic's default
``prefixItems``. ``Layer`` is a discriminated union on ``kind`` with
one class per kind.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Discriminator, Field, Tag

UintPair = Annotated[
    list[Annotated[int, Field(ge=0)]],
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


class MeshLayer(_Strict):
    """Single PNG, deformable cutout element (-> Polygon2D).

    Tagged ``[mesh]`` / ``[poly]`` in Photoshop. Renders as a static
    quad until a rig binds vertex weights.
    """

    kind: Literal["mesh"]
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


class SpriteLayer(_Strict):
    """Rigid sprite element (-> Sprite2D), one or more frames.

    A single layer tagged ``[sprite]`` yields one frame (a static
    sprite); a LayerSet tagged ``[spritesheet]`` yields N frames the
    importer composes into a grid, animated via ``proscenio.frame``.
    """

    kind: Literal["sprite"]
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
    frames: list[FrameEntry] = Field(min_length=1)
    origin: UintPair | None = Field(
        default=None,
        description="Optional pivot in PSD pixels (see MeshLayer.origin).",
    )
    blend_mode: BlendMode | None = None
    subfolder: str | None = Field(default=None, min_length=1)


def _layer_discriminator(payload: Any) -> str | None:
    """Route the ``mesh`` and ``sprite`` kinds to their classes.

    Returns ``None`` for unexpected ``kind`` values so pydantic raises
    a ``union_tag_not_found`` ValidationError rather than dispatching
    to a non-existent variant. The error message names the bad tag in
    the validation report.
    """
    if isinstance(payload, dict):
        kind = payload.get("kind")
    else:
        kind = getattr(payload, "kind", None)
    if kind in {"mesh", "sprite"}:
        return str(kind)
    return None


Layer = Annotated[
    Union[
        Annotated[MeshLayer, Tag("mesh")],
        Annotated[SpriteLayer, Tag("sprite")],
    ],
    Discriminator(_layer_discriminator),
]


class PsdManifest(_Strict):
    """Root of a PSD manifest v1 document."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "$id": (
                "https://firebound.github.io/proscenio/schemas/"
                "psd_manifest.schema.json"
            ),
        },
        title="Proscenio PSD manifest",
    )

    format_version: Literal[1] = Field(
        description="Bump on any breaking change to the shape of this document.",
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
            "Z-ordered top-to-bottom. Each entry is a single element in "
            "Blender after import."
        ),
    )
