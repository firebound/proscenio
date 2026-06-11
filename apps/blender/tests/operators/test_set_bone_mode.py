"""Headless tests for the per-bone mode operator's clear path.

Runs INSIDE Blender via ``run_operator_tests.py`` for real Custom Property
persistence (fake-bpy does not persist assignments, so the CLEAR enum wiring
needs a live object). The pure read / write / clear logic is covered in
``tests/skinning/test_bone_modes.py``.
"""

from __future__ import annotations

import bpy


def test_set_bone_mode_clear_pops_the_override(automesh_fixture):
    from proscenio.core.skinning.bone_modes import read_bone_modes  # type: ignore[import-not-found]

    obj = bpy.data.objects["hand"]
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    bpy.ops.proscenio.set_bone_mode(bone_name="wrist", mode="SOFT")
    assert read_bone_modes(obj).get("wrist") == "SOFT"

    bpy.ops.proscenio.set_bone_mode(bone_name="wrist", mode="CLEAR")
    assert "wrist" not in read_bone_modes(obj)
