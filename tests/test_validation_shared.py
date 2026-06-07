"""Pure-pytest tests for the validation read helpers (PG-first / CP fallback).

bpy-free: the PropertyGroup path uses SimpleNamespace mocks; the Custom
Property path uses a dict subclass that satisfies the lookup Protocol.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.validation._shared import (  # noqa: E402
    abspath_or_none,
    armature_bone_names,
    read_element_type,
    read_int,
)


class _CP(dict):  # type: ignore[type-arg]
    """Custom-Property carrier: dict already has get / __contains__ / __getitem__."""


def test_read_element_type_prefers_property_group() -> None:
    obj = SimpleNamespace(proscenio=SimpleNamespace(element_type="sprite"))
    assert read_element_type(obj) == "sprite"


def test_read_element_type_custom_property_fallback() -> None:
    assert read_element_type(_CP({"proscenio_type": "sprite"})) == "sprite"


def test_read_element_type_defaults_to_mesh() -> None:
    assert read_element_type(SimpleNamespace()) == "mesh"


def test_read_int_prefers_property_group() -> None:
    obj = SimpleNamespace(proscenio=SimpleNamespace(hframes=4))
    assert read_int(obj, "hframes", "proscenio_hframes", 1) == 4


def test_read_int_tolerates_float_form_custom_property() -> None:
    assert read_int(_CP({"proscenio_hframes": "3.0"}), "hframes", "proscenio_hframes", 1) == 3


def test_read_int_falls_back_on_non_numeric_custom_property() -> None:
    assert read_int(_CP({"proscenio_hframes": "abc"}), "hframes", "proscenio_hframes", 1) == 1


def test_read_int_default_when_absent() -> None:
    assert read_int(SimpleNamespace(), "hframes", "proscenio_hframes", 7) == 7


def test_armature_bone_names_collects_the_set() -> None:
    arm = SimpleNamespace(
        data=SimpleNamespace(bones=[SimpleNamespace(name="root"), SimpleNamespace(name="arm")]),
    )
    assert armature_bone_names(arm) == {"root", "arm"}


def test_armature_bone_names_empty_when_malformed() -> None:
    assert armature_bone_names(SimpleNamespace(data=None)) == set()


def test_abspath_or_none_returns_plain_path_without_bpy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "bpy", None)
    assert abspath_or_none("textures/atlas.png") == "textures/atlas.png"


def test_abspath_or_none_none_for_blender_relative_without_bpy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "bpy", None)
    assert abspath_or_none("//atlas.png") is None
