"""Pure tests for bone mode read/write (SPEC 013 O1/D16)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

bpy = pytest.importorskip("bpy")

from core.skinning.bone_modes import bone_mode_for, read_bone_modes, write_bone_modes  # noqa: E402


def test_default_when_unset():
    obj = bpy.data.objects.new("test_bm_default", bpy.data.meshes.new("m_bm_d"))
    assert bone_mode_for(obj, "any_bone", default="SOFT") == "SOFT"
    assert bone_mode_for(obj, "any_bone", default="HARD") == "HARD"


def test_round_trip():
    obj = bpy.data.objects.new("test_bm_rt", bpy.data.meshes.new("m_bm_rt"))
    write_bone_modes(obj, {"bone_a": "SOFT", "bone_b": "HARD"})
    modes = read_bone_modes(obj)
    assert modes == {"bone_a": "SOFT", "bone_b": "HARD"}


def test_invalid_values_filtered():
    obj = bpy.data.objects.new("test_bm_inv", bpy.data.meshes.new("m_bm_inv"))
    obj["proscenio_bone_modes"] = '{"bone_a": "SOFT", "bone_b": "INVALID"}'
    assert read_bone_modes(obj) == {"bone_a": "SOFT"}


def test_corrupt_json_returns_empty():
    obj = bpy.data.objects.new("test_bm_cor", bpy.data.meshes.new("m_bm_cor"))
    obj["proscenio_bone_modes"] = "not valid json"
    assert read_bone_modes(obj) == {}
