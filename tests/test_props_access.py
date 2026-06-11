"""Unit tests for the code-modularity work - core._shared.props_access helpers.

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

from core._shared.props_access import (  # noqa: E402
    object_props,
    resolve_export_armature,
    scene_props,
)


def _armature(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, type="ARMATURE")


def _mesh(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, type="MESH")


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
    pg = SimpleNamespace(element_type="mesh")
    obj = SimpleNamespace(proscenio=pg)
    assert object_props(obj) is pg


def test_object_props_none_when_proscenio_missing() -> None:
    obj = SimpleNamespace()
    assert object_props(obj) is None


def test_object_props_handles_none_obj() -> None:
    assert object_props(None) is None


def test_resolve_export_armature_prefers_the_picker() -> None:
    first = _armature("Rig.A")
    picked = _armature("Rig.B")
    scene = SimpleNamespace(
        objects=[first, picked],
        proscenio=SimpleNamespace(active_armature=picked),
    )
    assert resolve_export_armature(scene) is picked


def test_resolve_export_armature_falls_back_to_first_when_picker_unset() -> None:
    first = _armature("Rig.A")
    second = _armature("Rig.B")
    scene = SimpleNamespace(
        objects=[first, second],
        proscenio=SimpleNamespace(active_armature=None),
    )
    assert resolve_export_armature(scene) is first


def test_resolve_export_armature_falls_back_when_proscenio_unregistered() -> None:
    # Headless --background: the Scene PropertyGroup is not registered.
    first = _armature("Rig.A")
    scene = SimpleNamespace(objects=[_mesh("torso"), first])
    assert resolve_export_armature(scene) is first


def test_resolve_export_armature_ignores_a_picker_outside_the_scene() -> None:
    # Stale pointer: armature unlinked from this scene but still in bpy.data.
    in_scene = _armature("Rig.A")
    orphan = _armature("Rig.Orphan")
    scene = SimpleNamespace(
        objects=[in_scene],
        proscenio=SimpleNamespace(active_armature=orphan),
    )
    assert resolve_export_armature(scene) is in_scene


def test_resolve_export_armature_ignores_a_non_armature_picker() -> None:
    arm = _armature("Rig.A")
    not_arm = _mesh("Cube")
    scene = SimpleNamespace(
        objects=[arm, not_arm],
        proscenio=SimpleNamespace(active_armature=not_arm),
    )
    assert resolve_export_armature(scene) is arm


def test_resolve_export_armature_none_when_scene_has_no_armature() -> None:
    scene = SimpleNamespace(
        objects=[_mesh("torso")],
        proscenio=SimpleNamespace(active_armature=None),
    )
    assert resolve_export_armature(scene) is None
