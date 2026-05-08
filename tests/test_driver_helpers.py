"""Unit tests for the SPEC 005.1.d.1 driver-shortcut helpers.

Pure pytest, no Blender. Covers the bpy-free defaults + selection
walker that decide *what* the driver operator should wire when the
user clicks the panel button.

Run from the repo root::

    pytest tests/test_driver_helpers.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "blender-addon"))

from core.driver_helpers import (  # noqa: E402
    default_target_for_sprite,
    find_armature_with_active_bone,
)


def _props(sprite_type: str) -> SimpleNamespace:
    return SimpleNamespace(sprite_type=sprite_type)


def _bone(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name)


def _armature(active_bone: SimpleNamespace | None) -> SimpleNamespace:
    return SimpleNamespace(
        type="ARMATURE",
        data=SimpleNamespace(bones=SimpleNamespace(active=active_bone)),
    )


def _mesh() -> SimpleNamespace:
    return SimpleNamespace(type="MESH", data=SimpleNamespace())


def test_default_target_polygon_picks_region_x() -> None:
    assert default_target_for_sprite(_props("polygon")) == "region_x"


def test_default_target_sprite_frame_picks_frame() -> None:
    assert default_target_for_sprite(_props("sprite_frame")) == "frame"


def test_default_target_none_props_falls_back_to_region_x() -> None:
    assert default_target_for_sprite(None) == "region_x"


def test_default_target_unknown_kind_falls_back_to_region_x() -> None:
    assert default_target_for_sprite(_props("wibble")) == "region_x"


def test_find_armature_returns_first_with_active_bone() -> None:
    armature = _armature(_bone("forearm.L"))
    obj, name = find_armature_with_active_bone([_mesh(), armature])
    assert obj is armature
    assert name == "forearm.L"


def test_find_armature_skips_armature_without_active_bone() -> None:
    obj, name = find_armature_with_active_bone([_armature(None), _mesh()])
    assert obj is None
    assert name == ""


def test_find_armature_skips_armature_with_no_bones_attr() -> None:
    no_bones = SimpleNamespace(type="ARMATURE", data=SimpleNamespace())
    obj, name = find_armature_with_active_bone([no_bones])
    assert obj is None
    assert name == ""


def test_find_armature_skips_active_bone_with_empty_name() -> None:
    obj, name = find_armature_with_active_bone([_armature(_bone(""))])
    assert obj is None
    assert name == ""


def test_find_armature_returns_first_match_in_iteration_order() -> None:
    first = _armature(_bone("first"))
    second = _armature(_bone("second"))
    obj, name = find_armature_with_active_bone([first, second])
    assert obj is first
    assert name == "first"


def test_find_armature_empty_selection_returns_none() -> None:
    obj, name = find_armature_with_active_bone([])
    assert obj is None
    assert name == ""


def test_find_armature_only_meshes_returns_none() -> None:
    obj, name = find_armature_with_active_bone([_mesh(), _mesh()])
    assert obj is None
    assert name == ""
