"""Headless: the first export honors the scene pixels-per-unit field.

Runs INSIDE Blender via ``run_operator_tests.py``. The export operator used
to carry its own ``pixels_per_unit`` property defaulting to 100, so the very
first export ignored whatever the panel field held - editing it did nothing
until a re-export (which already read the scene value). This drives the
operator with the scene field set away from the default and asserts the
written document carries that value.
"""

from __future__ import annotations

import json
from pathlib import Path

import bpy
import pytest


def test_first_export_uses_scene_pixels_per_unit(automesh_fixture: None, tmp_path: Path) -> None:
    bpy.context.scene.proscenio.pixels_per_unit = 250.0
    out = tmp_path / "out.proscenio"

    result = bpy.ops.proscenio.export_godot(filepath=str(out))

    assert result == {"FINISHED"}, result
    data = json.loads(out.read_text())
    assert data["pixels_per_unit"] == pytest.approx(250.0)
