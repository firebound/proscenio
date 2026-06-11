"""Headless test for the PSD-import pixels-per-unit sync.

Runs INSIDE Blender via ``run_operator_tests.py``. A PSD import sizes
every mesh by ``manifest.pixels_per_unit``; if the scene's own
``pixels_per_unit`` kept its default while an import used 1000, an
export would emit a 10x-scale mismatch. The importer syncs the scene
property from the manifest so the round-trip holds. The manifest is
written with an empty ``layers`` list (valid per the model) so the sync
is exercised without any PNG dependencies.
"""

from __future__ import annotations

import json
from pathlib import Path

import bpy
import pytest


def _write_manifest(directory: Path, pixels_per_unit: float) -> Path:
    manifest = {
        "format_version": 1,
        "doc": "ppu_probe.psd",
        "size": [64, 64],
        "pixels_per_unit": pixels_per_unit,
        "layers": [],
    }
    path = directory / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_import_syncs_scene_pixels_per_unit(automesh_fixture, tmp_path):
    from proscenio.importers.photoshop import import_manifest  # type: ignore[import-not-found]

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    scene_props = bpy.context.scene.proscenio
    scene_props.pixels_per_unit = 100.0  # the untouched default

    manifest_path = _write_manifest(tmp_path, 1000.0)
    import_manifest(manifest_path)

    synced = scene_props.pixels_per_unit
    assert synced == pytest.approx(1000.0), "import did not sync the scene PPU"
