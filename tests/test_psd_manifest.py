"""Unit tests for the PSD manifest v1 parser (SPEC 006 Wave 6.0).

Pure Python; no Blender. Covers the in-process shape validation that
ships in Blender's bundled Python (the dedicated CI ``validate-schema``
job covers strict JSON Schema enforcement separately).

Run from the repo root::

    pytest tests/test_psd_manifest.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "blender-addon"))

from core import psd_manifest  # noqa: E402
from core.psd_manifest import (  # noqa: E402
    Manifest,
    ManifestError,
    PolygonLayer,
    SpriteFrameLayer,
)


def _valid_doc() -> dict:
    return {
        "format_version": 1,
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


def test_parse_returns_manifest_with_typed_layers() -> None:
    manifest = psd_manifest.parse(_valid_doc())
    assert isinstance(manifest, Manifest)
    assert manifest.format_version == 1
    assert manifest.doc == "doll.psd"
    assert manifest.size == (1024, 1024)
    assert manifest.pixels_per_unit == 100.0
    assert len(manifest.layers) == 2

    polygon, sprite_frame = manifest.layers
    assert isinstance(polygon, PolygonLayer)
    assert polygon.name == "torso"
    assert polygon.position == (120, 340)
    assert polygon.size == (180, 240)
    assert polygon.z_order == 0

    assert isinstance(sprite_frame, SpriteFrameLayer)
    assert sprite_frame.name == "eye"
    assert len(sprite_frame.frames) == 2
    assert sprite_frame.frames[0].index == 0
    assert sprite_frame.frames[0].path == "doll/images/eye/0.png"


def test_load_reads_from_disk(tmp_path: Path) -> None:
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(_valid_doc()), encoding="utf-8")
    manifest = psd_manifest.load(p)
    assert manifest.source_path == p
    assert len(manifest.layers) == 2


def test_resolve_path_resolves_relative_to_manifest(tmp_path: Path) -> None:
    p = tmp_path / "deep" / "manifest.json"
    p.parent.mkdir()
    p.write_text(json.dumps(_valid_doc()), encoding="utf-8")
    manifest = psd_manifest.load(p)
    resolved = psd_manifest.resolve_path(manifest, "doll/images/torso.png")
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
    doc["format_version"] = 2
    with pytest.raises(ManifestError, match="format_version"):
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
    doc["layers"][0]["kind"] = "wibble"
    with pytest.raises(ManifestError, match="kind"):
        psd_manifest.parse(doc)


def test_reject_polygon_with_extra_field() -> None:
    doc = _valid_doc()
    doc["layers"][0]["frames"] = []  # frames is illegal on polygon
    with pytest.raises(ManifestError, match="unexpected key"):
        psd_manifest.parse(doc)


def test_reject_sprite_frame_with_one_frame() -> None:
    doc = _valid_doc()
    doc["layers"][1]["frames"] = [{"index": 0, "path": "x.png"}]
    with pytest.raises(ManifestError, match=">= 2"):
        psd_manifest.parse(doc)


def test_reject_negative_z_order() -> None:
    doc = _valid_doc()
    doc["layers"][0]["z_order"] = -1
    with pytest.raises(ManifestError, match="z_order"):
        psd_manifest.parse(doc)


def test_reject_size_with_three_elements() -> None:
    doc = _valid_doc()
    doc["size"] = [1024, 1024, 1]
    with pytest.raises(ManifestError, match="size"):
        psd_manifest.parse(doc)


def test_reject_frame_with_unknown_field() -> None:
    doc = _valid_doc()
    doc["layers"][1]["frames"][0]["foo"] = "bar"
    with pytest.raises(ManifestError, match="unexpected key"):
        psd_manifest.parse(doc)


def test_reject_layers_not_array() -> None:
    doc = _valid_doc()
    doc["layers"] = {"not": "array"}
    with pytest.raises(ManifestError, match="layers"):
        psd_manifest.parse(doc)
