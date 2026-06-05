"""Unit tests for the PSD manifest v2 reader.

Pure Python; no Blender. Covers the pydantic-driven parser that ships
in Blender's bundled Python (the dedicated CI ``validate-schema`` job
covers strict JSON Schema enforcement separately).

v1 manifests (pre-the photoshop tag system, JSX-era exporter) are no
longer supported - v1 was retired with the JSX exporter and the pydantic
model now constrains ``format_version`` to ``2``.

Run from the repo root::

    pytest tests/test_psd_manifest.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.psd import psd_manifest  # noqa: E402
from core.psd.psd_manifest import (  # noqa: E402
    LoadedManifest,
    ManifestError,
    PolygonLayer,
    PsdManifest,
    SpriteFrameLayer,
)


def _valid_doc() -> dict[str, object]:
    return {
        "format_version": 2,
        "doc": "doll.psd",
        "size": [1024, 1024],
        "pixels_per_unit": 100,
        "layers": [
            {
                "kind": "polygon",
                "name": "torso",
                "path": "doll/images/torso.png",
                "position": [120, 340],
                "size": [180, 240],
                "z_order": 0,
            },
            {
                "kind": "sprite_frame",
                "name": "eye",
                "position": [350, 200],
                "size": [32, 32],
                "z_order": 1,
                "frames": [
                    {"index": 0, "path": "doll/images/eye/0.png"},
                    {"index": 1, "path": "doll/images/eye/1.png"},
                ],
            },
        ],
    }


def test_parse_returns_pydantic_manifest_with_typed_layers() -> None:
    manifest = psd_manifest.parse(_valid_doc())
    assert isinstance(manifest, PsdManifest)
    assert manifest.format_version == 2
    assert manifest.doc == "doll.psd"
    assert manifest.size == [1024, 1024]
    assert manifest.pixels_per_unit == pytest.approx(100.0)
    assert len(manifest.layers) == 2

    polygon, sprite_frame = manifest.layers
    assert isinstance(polygon, PolygonLayer)
    assert polygon.name == "torso"
    assert polygon.position == [120, 340]
    assert polygon.size == [180, 240]
    assert polygon.z_order == 0

    assert isinstance(sprite_frame, SpriteFrameLayer)
    assert sprite_frame.name == "eye"
    assert len(sprite_frame.frames) == 2
    assert sprite_frame.frames[0].index == 0
    assert sprite_frame.frames[0].path == "doll/images/eye/0.png"


def test_load_reads_from_disk_and_carries_source_path(tmp_path: Path) -> None:
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(_valid_doc()), encoding="utf-8")
    loaded = psd_manifest.load(p)
    assert isinstance(loaded, LoadedManifest)
    assert loaded.source_path == p
    assert len(loaded.layers) == 2


def test_resolve_path_resolves_relative_to_manifest(tmp_path: Path) -> None:
    p = tmp_path / "deep" / "manifest.json"
    p.parent.mkdir()
    p.write_text(json.dumps(_valid_doc()), encoding="utf-8")
    loaded = psd_manifest.load(p)
    resolved = psd_manifest.resolve_path(loaded, "doll/images/torso.png")
    assert resolved == (tmp_path / "deep" / "doll" / "images" / "torso.png").resolve()


def test_load_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ManifestError, match="could not read"):
        psd_manifest.load(tmp_path / "nope.json")


def test_load_invalid_json_raises(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(ManifestError, match="could not read"):
        psd_manifest.load(p)


def test_reject_unsupported_format_version() -> None:
    doc = _valid_doc()
    doc["format_version"] = 99
    with pytest.raises(ManifestError, match="format_version"):
        psd_manifest.parse(doc)


def test_reject_legacy_v1_format_version() -> None:
    """v1 manifests are retired with the JSX exporter; pydantic constrains
    ``format_version`` to ``2`` and rejects v1 documents up front."""
    doc = _valid_doc()
    doc["format_version"] = 1
    with pytest.raises(ManifestError, match="format_version"):
        psd_manifest.parse(doc)


def test_v2_accepts_anchor_and_per_layer_options() -> None:
    doc = _valid_doc()
    doc["anchor"] = [512, 768]
    layers = doc["layers"]
    assert isinstance(layers, list)
    first = layers[0]
    assert isinstance(first, dict)
    first["origin"] = [200, 400]
    first["blend_mode"] = "multiply"
    first["subfolder"] = "body/torso"
    first["kind"] = "mesh"
    manifest = psd_manifest.parse(doc)
    assert manifest.anchor == [512, 768]
    polygon = manifest.layers[0]
    assert isinstance(polygon, PolygonLayer)
    assert polygon.kind == "mesh"
    assert polygon.origin == [200, 400]
    assert polygon.blend_mode == "multiply"
    assert polygon.subfolder == "body/torso"


def test_v2_rejects_invalid_blend_mode() -> None:
    doc = _valid_doc()
    layers = doc["layers"]
    assert isinstance(layers, list)
    first = layers[0]
    assert isinstance(first, dict)
    first["blend_mode"] = "overlay"
    with pytest.raises(ManifestError, match="blend_mode"):
        psd_manifest.parse(doc)


def test_reject_missing_required_root_field() -> None:
    doc = _valid_doc()
    del doc["pixels_per_unit"]
    with pytest.raises(ManifestError, match="pixels_per_unit"):
        psd_manifest.parse(doc)


def test_reject_non_positive_pixels_per_unit() -> None:
    doc = _valid_doc()
    doc["pixels_per_unit"] = 0
    with pytest.raises(ManifestError, match="pixels_per_unit"):
        psd_manifest.parse(doc)


def test_reject_unknown_layer_kind() -> None:
    doc = _valid_doc()
    layers = doc["layers"]
    assert isinstance(layers, list)
    first = layers[0]
    assert isinstance(first, dict)
    first["kind"] = "wibble"
    with pytest.raises(ManifestError, match="discriminator"):
        psd_manifest.parse(doc)


def test_reject_polygon_with_extra_field() -> None:
    doc = _valid_doc()
    layers = doc["layers"]
    assert isinstance(layers, list)
    first = layers[0]
    assert isinstance(first, dict)
    first["frames"] = []  # frames is illegal on polygon
    with pytest.raises(ManifestError):
        psd_manifest.parse(doc)


def test_reject_sprite_frame_with_one_frame() -> None:
    doc = _valid_doc()
    layers = doc["layers"]
    assert isinstance(layers, list)
    second = layers[1]
    assert isinstance(second, dict)
    second["frames"] = [{"index": 0, "path": "x.png"}]
    with pytest.raises(ManifestError, match="frames"):
        psd_manifest.parse(doc)


def test_reject_negative_z_order() -> None:
    doc = _valid_doc()
    layers = doc["layers"]
    assert isinstance(layers, list)
    first = layers[0]
    assert isinstance(first, dict)
    first["z_order"] = -1
    with pytest.raises(ManifestError, match="z_order"):
        psd_manifest.parse(doc)


def test_reject_size_with_three_elements() -> None:
    doc = _valid_doc()
    doc["size"] = [1024, 1024, 1]
    with pytest.raises(ManifestError, match="size"):
        psd_manifest.parse(doc)


def test_reject_frame_with_unknown_field() -> None:
    doc = _valid_doc()
    layers = doc["layers"]
    assert isinstance(layers, list)
    second = layers[1]
    assert isinstance(second, dict)
    frames = second["frames"]
    assert isinstance(frames, list)
    first_frame = frames[0]
    assert isinstance(first_frame, dict)
    first_frame["foo"] = "bar"
    with pytest.raises(ManifestError):
        psd_manifest.parse(doc)


def test_reject_layers_not_array() -> None:
    doc = _valid_doc()
    doc["layers"] = {"not": "array"}
    with pytest.raises(ManifestError, match="layers"):
        psd_manifest.parse(doc)
