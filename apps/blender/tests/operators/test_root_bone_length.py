"""Headless tests for the importer root-bone length (spec 068).

Runs INSIDE Blender via ``run_operator_tests.py``. The importer builds a single
root bone; spec 068 bumps its default length to 1 unit and threads a per-import
override (``root_bone_length`` -> ``import_manifest`` -> ``build_root_armature``).
A re-import reuses the existing root in place, so a later length never resizes it.
"""

from __future__ import annotations

import json

import bpy


def _root_tail_z(arm: bpy.types.Object) -> float:
    return float(arm.data.bones[0].tail_local.z)


def test_build_root_armature_default_length_is_one(automesh_fixture):
    from proscenio.importers.photoshop.armature import (  # type: ignore[import-not-found]
        ROOT_BONE_LENGTH,
        build_root_armature,
    )

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    assert ROOT_BONE_LENGTH == 1.0
    arm = build_root_armature("len_default.rig")
    assert _root_tail_z(arm) == 1.0


def test_build_root_armature_honors_custom_length(automesh_fixture):
    from proscenio.importers.photoshop.armature import (  # type: ignore[import-not-found]
        build_root_armature,
    )

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    arm = build_root_armature("len_custom.rig", length=2.5)
    assert _root_tail_z(arm) == 2.5


def test_build_root_armature_reuse_keeps_original_length(automesh_fixture):
    # A second build reuses the existing armature in place (spec 055), so a
    # different length must not retro-resize the already-built root.
    from proscenio.importers.photoshop.armature import (  # type: ignore[import-not-found]
        build_root_armature,
    )

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    first = build_root_armature("len_reuse.rig", length=1.0)
    again = build_root_armature("len_reuse.rig", length=4.0)
    assert again is first
    assert _root_tail_z(first) == 1.0, "re-import retro-resized the existing root"


def test_import_manifest_threads_root_bone_length(automesh_fixture, tmp_path):
    from proscenio.importers.photoshop import import_manifest  # type: ignore[import-not-found]

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    png = tmp_path / "torso.png"
    img = bpy.data.images.new("torso_len", 4, 4)
    img.filepath_raw = str(png)
    img.file_format = "PNG"
    img.save()
    manifest = {
        "format_version": 1,
        "doc": "len_thread.psd",
        "size": [64, 64],
        "pixels_per_unit": 100.0,
        "layers": [
            {
                "kind": "mesh",
                "name": "torso",
                "path": "torso.png",
                "position": [10, 10],
                "size": [20, 20],
                "z_order": 0,
            }
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = import_manifest(manifest_path, root_bone_length=3.0)
    assert result.armature is not None
    assert _root_tail_z(result.armature) == 3.0
