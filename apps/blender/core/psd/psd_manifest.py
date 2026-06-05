"""PSD manifest v2 reader (the photoshop importer).

Reads the JSON document emitted by the Photoshop UXP plugin and
returns typed pydantic records. Pure Python - no bpy, no Pillow.

Usage::

    from blender_addon.core import psd_manifest
    loaded = psd_manifest.load(Path("firebound/firebound.json"))
    for layer in loaded.manifest.layers:
        if layer.kind in ("polygon", "mesh"):
            stamp_polygon(layer, loaded)
        else:
            stamp_sprite_frame(layer, loaded)

The data shape is defined by ``proscenio_models.PsdManifest`` (the
``packages/models/`` pydantic source of truth). The JSON Schema artifact
at ``packages/models/schemas/psd_manifest.schema.json`` is regenerated
from that model.

v1 manifests (pre-the photoshop tag system, JSX-era exporter) are no
longer supported. v1 has been retired with the JSX exporter; the
``format_version`` field is now constrained to ``2`` at the pydantic
layer, and v1 documents fail validation at parse time.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from proscenio_models import (
    BlendMode,
    FrameEntry,
    Layer,
    PolygonLayer,
    PsdManifest,
    SpriteFrameLayer,
)
from pydantic import ValidationError

MANIFEST_FORMAT_VERSION = 2

# Re-exported for callers that still import these names through this module.
__all__ = [
    "MANIFEST_FORMAT_VERSION",
    "BlendMode",
    "FrameEntry",
    "FrameRef",
    "Layer",
    "LoadedManifest",
    "ManifestError",
    "PolygonLayer",
    "PsdManifest",
    "SpriteFrameLayer",
    "load",
    "parse",
    "resolve_path",
]

# Back-compat alias: legacy callers used the dataclass name ``FrameRef``;
# pydantic ships the same record under ``FrameEntry``. The alias keeps
# import sites working while the public name on the model stays aligned
# with the schema.
FrameRef = FrameEntry


class ManifestError(Exception):
    """Raised when the manifest cannot be read or fails pydantic validation.

    Wraps both IO / JSON-decode failures and ``pydantic.ValidationError``
    so callers have a single exception type to handle.
    """


@dataclass(frozen=True)
class LoadedManifest:
    """A parsed PSD manifest plus its on-disk source path.

    ``source_path`` lets the importer resolve layer-relative paths
    (``layer.path``, ``frame.path``) against the manifest's directory.
    """

    manifest: PsdManifest
    source_path: Path

    # The pydantic ``PsdManifest`` fields are exposed as plain delegating
    # properties so the importer can write ``loaded.layers``,
    # ``loaded.size``, etc, without dereferencing the inner model at
    # every call site. Read-only by design.

    @property
    def format_version(self) -> int:
        return self.manifest.format_version

    @property
    def doc(self) -> str:
        return self.manifest.doc

    @property
    def size(self) -> list[int]:
        return self.manifest.size

    @property
    def pixels_per_unit(self) -> float:
        return self.manifest.pixels_per_unit

    @property
    def anchor(self) -> list[int] | None:
        return self.manifest.anchor

    @property
    def layers(self) -> list[Layer]:
        return self.manifest.layers


def load(path: Path | str) -> LoadedManifest:
    """Load and validate a manifest from disk.

    Raises ``ManifestError`` on IO failure, JSON decode failure, or
    pydantic validation failure.
    """
    p = Path(path)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"could not read manifest at {p}: {exc}") from exc
    manifest = parse(raw)
    return LoadedManifest(manifest=manifest, source_path=p)


def parse(raw: object) -> PsdManifest:
    """Parse a pre-loaded JSON document into a :class:`PsdManifest`.

    Raises ``ManifestError`` when the document fails pydantic validation
    (unsupported format_version, missing required field, malformed
    layer entry, etc).
    """
    try:
        return PsdManifest.model_validate(raw)
    except ValidationError as exc:
        raise ManifestError(_format_validation_error(exc)) from exc


def resolve_path(loaded: LoadedManifest, relative: str) -> Path:
    """Resolve a layer- or frame-relative path against the manifest's directory."""
    return (loaded.source_path.parent / relative).resolve()


def _format_validation_error(exc: ValidationError) -> str:
    """Render a pydantic ValidationError into a single ManifestError message.

    Picks the first error so the message stays a single sentence; the
    full report is still available via ``ManifestError.__cause__.errors()``
    when callers want the structured view.
    """
    errors = exc.errors()
    if not errors:
        return "PSD manifest failed validation"
    first = errors[0]
    loc = ".".join(str(part) for part in first["loc"])
    msg = first["msg"]
    label = loc or "<root>"
    return f"{label}: {msg}"
