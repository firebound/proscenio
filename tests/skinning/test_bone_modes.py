"""Pure tests for bone mode read/write (SPEC 013 O1/D16).

Uses a tiny dict-backed `_FakeObj` instead of `bpy.data.objects.new(...)`
because fake-bpy-module (installed in the editor for IDE support) does
not actually persist Custom Property assignments. The bone_modes
functions only call `obj.get(key)` and `obj[key] = value` which a plain
dict satisfies; this lets the tests stay pure (no bpy required).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.skinning.bone_modes import bone_mode_for, read_bone_modes, write_bone_modes  # noqa: E402


class _FakeObj:
    """Minimal stand-in for bpy.types.Object's Custom Property dict surface."""

    def __init__(self) -> None:
        self._props: dict[str, object] = {}

    def __setitem__(self, key: str, value: object) -> None:
        self._props[key] = value

    def __getitem__(self, key: str) -> object:
        return self._props[key]

    def get(self, key: str, default: object = None) -> object:
        return self._props.get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self._props


def test_default_when_unset():
    obj = _FakeObj()
    assert bone_mode_for(obj, "any_bone", default="SOFT") == "SOFT"
    assert bone_mode_for(obj, "any_bone", default="HARD") == "HARD"


def test_round_trip():
    obj = _FakeObj()
    write_bone_modes(obj, {"bone_a": "SOFT", "bone_b": "HARD"})
    modes = read_bone_modes(obj)
    assert modes == {"bone_a": "SOFT", "bone_b": "HARD"}


def test_invalid_values_filtered():
    obj = _FakeObj()
    obj["proscenio_bone_modes"] = '{"bone_a": "SOFT", "bone_b": "INVALID"}'
    assert read_bone_modes(obj) == {"bone_a": "SOFT"}


def test_corrupt_json_returns_empty():
    obj = _FakeObj()
    obj["proscenio_bone_modes"] = "not valid json"
    assert read_bone_modes(obj) == {}


def test_missing_key_returns_empty():
    obj = _FakeObj()
    assert read_bone_modes(obj) == {}


def test_per_bone_override_beats_default():
    obj = _FakeObj()
    write_bone_modes(obj, {"specific_bone": "HARD"})
    assert bone_mode_for(obj, "specific_bone", default="SOFT") == "HARD"
    assert bone_mode_for(obj, "other_bone", default="SOFT") == "SOFT"
