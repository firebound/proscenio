"""Unit tests for SPEC 009 wave 9.1 -- core.props_access helpers.

Pure pytest, no Blender. Uses SimpleNamespace mocks shaped to mirror
the real Blender Context/Object/PropertyGroup so the helpers exercise
the same getattr paths.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.props_access import object_props, scene_props  # noqa: E402


def test_scene_props_returns_pg() -> None:
    pg = SimpleNamespace(last_export_path="//out.proscenio")
    scene = SimpleNamespace(proscenio=pg)
    context = SimpleNamespace(scene=scene)
    assert scene_props(context) is pg


def test_scene_props_none_when_proscenio_missing() -> None:
    scene = SimpleNamespace()
    context = SimpleNamespace(scene=scene)
    assert scene_props(context) is None


def test_scene_props_none_when_scene_missing() -> None:
    context = SimpleNamespace()
    assert scene_props(context) is None


def test_object_props_returns_pg() -> None:
    pg = SimpleNamespace(sprite_type="polygon")
    obj = SimpleNamespace(proscenio=pg)
    assert object_props(obj) is pg


def test_object_props_none_when_proscenio_missing() -> None:
    obj = SimpleNamespace()
    assert object_props(obj) is None


def test_object_props_handles_none_obj() -> None:
    assert object_props(None) is None
