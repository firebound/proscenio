"""Unit tests for the atlas manifest parser (bpy-free; runs without Blender)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.atlas.atlas_manifest import Placement, read_manifest  # noqa: E402
from core.atlas.atlas_packer import Rect  # noqa: E402


def _write(tmp_path: Path, payload: dict) -> Path:
    manifest = tmp_path / "atlas.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    return manifest


def test_read_manifest_parses_slot_and_slice(tmp_path):
    manifest = _write(
        tmp_path,
        {
            "atlas_w": 256,
            "atlas_h": 128,
            "padding": 2,
            "placements": {
                "hero": {
                    "x": 4,
                    "y": 8,
                    "w": 32,
                    "h": 48,
                    "slice_x": 1,
                    "slice_y": 2,
                    "slice_w": 30,
                    "slice_h": 44,
                    "source_w": 100,
                    "source_h": 120,
                }
            },
        },
    )
    atlas_w, atlas_h, padding, placements = read_manifest(manifest)
    assert (atlas_w, atlas_h, padding) == (256, 128, 2)
    assert placements["hero"] == Placement(
        slot=Rect(4, 8, 32, 48),
        source_w=100,
        source_h=120,
        slice=Rect(1, 2, 30, 44),
    )


def test_read_manifest_defaults_slice_to_full_slot(tmp_path):
    # A placement written without slice / source metadata (a slot-only entry)
    # defaults the slice to the full slot from its origin and source_w/h to the
    # slot size, keeping the apply operator's slice-aware path correct.
    manifest = _write(
        tmp_path,
        {
            "atlas_w": 64,
            "atlas_h": 64,
            "placements": {"prop": {"x": 0, "y": 0, "w": 16, "h": 16}},
        },
    )
    _atlas_w, _atlas_h, padding, placements = read_manifest(manifest)
    assert padding == 0  # absent -> 0
    p = placements["prop"]
    assert p.slice == Rect(0, 0, 16, 16)
    assert (p.source_w, p.source_h) == (16, 16)
