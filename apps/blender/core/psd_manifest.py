"""PSD manifest v1 parser (SPEC 006 Wave 6.0).

Reads the JSON document emitted by the Photoshop JSX exporter and
returns typed records. Pure Python - no bpy, no Pillow, no jsonschema
required at runtime (validation falls back to a minimal in-process
shape check when ``jsonschema`` is absent - Blender's bundled Python
typically does not ship it; the dedicated CI ``validate-schema`` job
covers strict schema validation).

Usage::

    from blender_addon.core import psd_manifest
    manifest = psd_manifest.load(Path("firebound/firebound.json"))
    for layer in manifest.layers:
        if layer.kind == "polygon":
            stamp_polygon(layer)
        else:
            stamp_sprite_frame(layer)

The data classes mirror the JSON Schema 2020-12 contract under
``schemas/psd_manifest.schema.json``. Bumping the schema requires
bumping ``MANIFEST_FORMAT_VERSION`` here in lockstep.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

MANIFEST_FORMAT_VERSION = 2

_ROOT = "<root>"

LayerKind = Literal["polygon", "sprite_frame", "mesh"]


@dataclass(frozen=True)
class FrameRef:
    """One frame inside a sprite_frame layer."""

    index: int
    path: str  # relative to the manifest file


BlendMode = Literal["normal", "multiply", "screen", "additive"]


@dataclass(frozen=True)
class PolygonLayer:
    """Single PNG → single quad mesh. ``mesh`` is a deformable polygon hint."""

    kind: Literal["polygon", "mesh"]
    name: str
    path: str
    position: tuple[int, int]
    size: tuple[int, int]
    z_order: int
    origin: tuple[int, int] | None = None
    blend_mode: BlendMode | None = None
    subfolder: str | None = None


@dataclass(frozen=True)
class SpriteFrameLayer:
    """N frames → single quad mesh sized to the largest frame."""

    kind: Literal["sprite_frame"]
    name: str
    position: tuple[int, int]
    size: tuple[int, int]
    z_order: int
    frames: tuple[FrameRef, ...]
    origin: tuple[int, int] | None = None
    blend_mode: BlendMode | None = None
    subfolder: str | None = None


Layer = PolygonLayer | SpriteFrameLayer


@dataclass(frozen=True)
class Manifest:
    """Top-level manifest record."""

    format_version: int
    doc: str
    size: tuple[int, int]
    pixels_per_unit: float
    layers: tuple[Layer, ...]
    source_path: Path  # the manifest file itself; used to resolve relative paths
    anchor: tuple[int, int] | None = None


class ManifestError(Exception):
    """Raised when the manifest cannot be parsed or is structurally invalid.

    Strict JSON Schema validation lives in CI (``check-jsonschema``);
    this class surfaces the in-process shape failures that survive
    Blender's bundled Python (no jsonschema dependency assumed).
    """


def load(path: Path | str) -> Manifest:
    """Load and parse a manifest from disk. Raises ``ManifestError`` on shape mismatch."""
    p = Path(path)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"could not read manifest at {p}: {exc}") from exc
    return parse(raw, source_path=p)


def parse(raw: Any, source_path: Path | None = None) -> Manifest:
    """Parse a pre-loaded JSON document into a :class:`Manifest`."""
    _require_dict(raw, _ROOT)
    fv = _require_field(raw, "format_version", _ROOT)
    if fv != MANIFEST_FORMAT_VERSION:
        raise ManifestError(
            f"unsupported manifest format_version {fv!r}; expected {MANIFEST_FORMAT_VERSION}"
        )
    doc = _require_field(raw, "doc", _ROOT)
    if not isinstance(doc, str) or not doc:
        raise ManifestError(f"{_ROOT}.doc must be a non-empty string, got {doc!r}")
    size = _parse_uint_pair(_require_field(raw, "size", _ROOT), f"{_ROOT}.size")
    ppu = _require_field(raw, "pixels_per_unit", _ROOT)
    if not isinstance(ppu, (int, float)) or ppu <= 0:
        raise ManifestError(f"{_ROOT}.pixels_per_unit must be a positive number, got {ppu!r}")
    layers_raw = _require_field(raw, "layers", _ROOT)
    if not isinstance(layers_raw, list):
        raise ManifestError(f"{_ROOT}.layers must be an array, got {type(layers_raw).__name__}")
    layers = tuple(_parse_layer(entry, idx) for idx, entry in enumerate(layers_raw))
    anchor = None
    if "anchor" in raw:
        anchor = _parse_uint_pair(raw["anchor"], f"{_ROOT}.anchor")
    return Manifest(
        format_version=fv,
        doc=doc,
        size=size,
        pixels_per_unit=float(ppu),
        layers=layers,
        source_path=Path(source_path) if source_path is not None else Path("."),
        anchor=anchor,
    )


def resolve_path(manifest: Manifest, relative: str) -> Path:
    """Resolve a layer- or frame-relative path against the manifest's directory."""
    return (manifest.source_path.parent / relative).resolve()


_BLEND_MODES: frozenset[str] = frozenset(("normal", "multiply", "screen", "additive"))
_POLYGON_KEYS: frozenset[str] = frozenset(
    (
        "kind",
        "name",
        "path",
        "position",
        "size",
        "z_order",
        "origin",
        "blend_mode",
        "subfolder",
    )
)
_SPRITE_FRAME_KEYS: frozenset[str] = frozenset(
    (
        "kind",
        "name",
        "position",
        "size",
        "z_order",
        "frames",
        "origin",
        "blend_mode",
        "subfolder",
    )
)


def _parse_layer(entry: Any, idx: int) -> Layer:
    label = f"<root>.layers[{idx}]"
    _require_dict(entry, label)
    kind = _require_field(entry, "kind", label)
    if kind == "polygon" or kind == "mesh":
        return _parse_polygon(entry, label, kind)
    if kind == "sprite_frame":
        return _parse_sprite_frame(entry, label)
    raise ManifestError(f"{label}.kind must be 'polygon', 'mesh', or 'sprite_frame', got {kind!r}")


def _parse_polygon(
    entry: dict[str, Any],
    label: str,
    kind: Literal["polygon", "mesh"],
) -> PolygonLayer:
    name = _require_str(entry, "name", label)
    path = _require_str(entry, "path", label)
    position = _parse_uint_pair(_require_field(entry, "position", label), f"{label}.position")
    size = _parse_uint_pair(_require_field(entry, "size", label), f"{label}.size")
    z_order = _require_uint(entry, "z_order", label)
    extra = set(entry) - _POLYGON_KEYS
    if extra:
        raise ManifestError(f"{label} has unexpected key(s): {sorted(extra)}")
    return PolygonLayer(
        kind=kind,
        name=name,
        path=path,
        position=position,
        size=size,
        z_order=z_order,
        origin=_optional_uint_pair(entry, "origin", label),
        blend_mode=_optional_blend_mode(entry, label),
        subfolder=_optional_str(entry, "subfolder", label),
    )


def _parse_sprite_frame(entry: dict[str, Any], label: str) -> SpriteFrameLayer:
    name = _require_str(entry, "name", label)
    position = _parse_uint_pair(_require_field(entry, "position", label), f"{label}.position")
    size = _parse_uint_pair(_require_field(entry, "size", label), f"{label}.size")
    z_order = _require_uint(entry, "z_order", label)
    frames_raw = _require_field(entry, "frames", label)
    if not isinstance(frames_raw, list) or len(frames_raw) < 2:
        raise ManifestError(f"{label}.frames must be an array of >= 2 entries, got {frames_raw!r}")
    frames = tuple(_parse_frame(f, f"{label}.frames[{i}]") for i, f in enumerate(frames_raw))
    extra = set(entry) - _SPRITE_FRAME_KEYS
    if extra:
        raise ManifestError(f"{label} has unexpected key(s): {sorted(extra)}")
    return SpriteFrameLayer(
        kind="sprite_frame",
        name=name,
        position=position,
        size=size,
        z_order=z_order,
        frames=frames,
        origin=_optional_uint_pair(entry, "origin", label),
        blend_mode=_optional_blend_mode(entry, label),
        subfolder=_optional_str(entry, "subfolder", label),
    )


def _optional_uint_pair(entry: dict[str, Any], key: str, label: str) -> tuple[int, int] | None:
    if key not in entry:
        return None
    return _parse_uint_pair(entry[key], f"{label}.{key}")


def _optional_str(entry: dict[str, Any], key: str, label: str) -> str | None:
    if key not in entry:
        return None
    value = entry[key]
    if not isinstance(value, str) or not value:
        raise ManifestError(f"{label}.{key} must be a non-empty string, got {value!r}")
    return value


def _optional_blend_mode(entry: dict[str, Any], label: str) -> BlendMode | None:
    if "blend_mode" not in entry:
        return None
    value = entry["blend_mode"]
    if value not in _BLEND_MODES:
        raise ManifestError(
            f"{label}.blend_mode must be one of {sorted(_BLEND_MODES)}, got {value!r}"
        )
    return value  # type: ignore[return-value]


def _parse_frame(entry: Any, label: str) -> FrameRef:
    _require_dict(entry, label)
    index = _require_uint(entry, "index", label)
    path = _require_str(entry, "path", label)
    extra = set(entry) - {"index", "path"}
    if extra:
        raise ManifestError(f"{label} has unexpected key(s): {sorted(extra)}")
    return FrameRef(index=index, path=path)


def _require_dict(value: Any, label: str) -> None:
    if not isinstance(value, dict):
        raise ManifestError(f"{label} must be an object, got {type(value).__name__}")


def _require_field(entry: dict[str, Any], key: str, label: str) -> Any:
    if key not in entry:
        raise ManifestError(f"{label} is missing required field {key!r}")
    return entry[key]


def _require_str(entry: dict[str, Any], key: str, label: str) -> str:
    value = _require_field(entry, key, label)
    if not isinstance(value, str) or not value:
        raise ManifestError(f"{label}.{key} must be a non-empty string, got {value!r}")
    return value


def _require_uint(entry: dict[str, Any], key: str, label: str) -> int:
    value = _require_field(entry, key, label)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ManifestError(f"{label}.{key} must be a non-negative integer, got {value!r}")
    return value


def _parse_uint_pair(value: Any, label: str) -> tuple[int, int]:
    if not isinstance(value, list) or len(value) != 2:
        raise ManifestError(f"{label} must be a 2-element array, got {value!r}")
    a, b = value
    if (
        not isinstance(a, int)
        or isinstance(a, bool)
        or not isinstance(b, int)
        or isinstance(b, bool)
        or a < 0
        or b < 0
    ):
        raise ManifestError(f"{label} must contain non-negative integers, got {value!r}")
    return (a, b)
