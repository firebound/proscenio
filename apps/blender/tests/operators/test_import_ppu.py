"""Headless: import surfaces (does not silently swallow) a pixels-per-unit change.

Runs INSIDE Blender via ``run_operator_tests.py``. The importer sizes meshes by
the manifest's pixels-per-unit and syncs that onto the scene so a re-export keeps
the same scale - but it used to overwrite a deliberately-set scene value
silently. The sync now returns a warning when it changes the value, which the
operator reports.
"""

from __future__ import annotations

from types import SimpleNamespace

import bpy


def test_sync_warns_and_updates_when_ppu_differs(automesh_fixture: None) -> None:
    from proscenio.importers.photoshop import _sync_scene_pixels_per_unit

    bpy.context.scene.proscenio.pixels_per_unit = 100.0
    warning = _sync_scene_pixels_per_unit(SimpleNamespace(pixels_per_unit=250.0))

    assert warning is not None
    assert "250" in warning
    assert bpy.context.scene.proscenio.pixels_per_unit == 250.0


def test_sync_is_silent_when_ppu_matches(automesh_fixture: None) -> None:
    from proscenio.importers.photoshop import _sync_scene_pixels_per_unit

    bpy.context.scene.proscenio.pixels_per_unit = 250.0
    warning = _sync_scene_pixels_per_unit(SimpleNamespace(pixels_per_unit=250.0))

    assert warning is None
    assert bpy.context.scene.proscenio.pixels_per_unit == 250.0
