"""Headless tests for import placement: an authored anchor prevails over the
landed feet-shift.

Runs INSIDE Blender via ``run_operator_tests.py``. A manifest anchor is the
pivot/ground the artist deliberately placed, so a "landed" import must keep it
(no feet-shift); otherwise a figure whose lowest mesh is a prop hanging below
the feet (a held weapon) floats. Without an anchor, "landed" still drops the
lowest mesh onto Z=0.
"""

from __future__ import annotations

import json

import bpy
import pytest


def _png(tmp_path, name):
    png = tmp_path / f"{name}.png"
    img = bpy.data.images.new(f"{name}_probe", 4, 4)
    img.filepath_raw = str(png)
    img.file_format = "PNG"
    img.save()
    return png


def _manifest(tmp_path, *, anchor):
    # A "feet" layer at the ground line plus a "prop" hanging below it (a held
    # weapon dangling past the feet). With anchor=[100, 180] the feet bottom sits
    # on world Z=0 and the prop hangs to negative Z.
    _png(tmp_path, "feet")
    _png(tmp_path, "prop")
    manifest = {
        "format_version": 1,
        "doc": "placement.psd",
        "size": [200, 200],
        "pixels_per_unit": 100.0,
        "layers": [
            {
                "kind": "mesh",
                "name": "feet",
                "path": "feet.png",
                "position": [90, 160],
                "size": [20, 20],
                "z_order": 0,
            },
            {
                "kind": "mesh",
                "name": "prop",
                "path": "prop.png",
                "position": [90, 180],
                "size": [20, 30],
                "z_order": 1,
            },
        ],
    }
    if anchor is not None:
        manifest["anchor"] = anchor
    path = tmp_path / f"manifest_{'anchor' if anchor else 'none'}.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _by_origin(meshes, layer_name):
    target = f"psd:{layer_name}"
    for obj in meshes:
        if obj.get("proscenio_import_origin") == target:
            return obj
    raise AssertionError(f"no mesh stamped from layer {layer_name!r}")


def test_landed_with_anchor_keeps_the_anchor_placement(automesh_fixture, tmp_path):
    from proscenio.importers.photoshop import import_manifest  # type: ignore[import-not-found]

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    path = _manifest(tmp_path, anchor=[100, 180])
    result = import_manifest(path, placement="landed")
    feet = _by_origin(result.meshes, "feet")
    prop = _by_origin(result.meshes, "prop")
    # Anchor [100, 180] -> the feet centre lands at (180-170)/100 = 0.10 and the
    # prop centre at (180-195)/100 = -0.15 (hanging through the ground). The
    # anchor prevails: no feet-shift lifts the figure off its authored pivot.
    assert feet.location.z == pytest.approx(0.10)
    assert prop.location.z == pytest.approx(-0.15)


def test_landed_without_anchor_drops_lowest_mesh_to_zero(automesh_fixture, tmp_path):
    from proscenio.importers.photoshop import import_manifest  # type: ignore[import-not-found]

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    path = _manifest(tmp_path, anchor=None)
    result = import_manifest(path, placement="landed")
    prop = _by_origin(result.meshes, "prop")
    # No anchor: landed runs and lifts the figure so the lowest mesh (the prop,
    # half-height 0.15) sits its bottom on Z=0 -> the prop centre is at +0.15.
    assert prop.location.z == pytest.approx(0.15)
    # The prop's bottom (centre - half height) is on the ground.
    assert prop.location.z - 0.15 == pytest.approx(0.0, abs=1e-6)
