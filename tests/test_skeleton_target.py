"""Unit tests for SPEC 012.2 hybrid armature targeting.

bpy-free. Mocks ``bpy.types.Context`` / ``Scene`` / ``Object`` via
``SimpleNamespace`` to exercise the resolution order without booting
Blender.

Run from the repo root:

    pytest tests/test_skeleton_target.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.skeleton_target import (  # noqa: E402  - sys.path setup above
    resolve_skeleton_target,
)


def _obj(name: str, obj_type: str = "ARMATURE") -> SimpleNamespace:
    return SimpleNamespace(name=name, type=obj_type)


def _ctx(
    *,
    explicit_armature: SimpleNamespace | None = None,
    active: SimpleNamespace | None = None,
    scene_objects: list[SimpleNamespace] | None = None,
) -> SimpleNamespace:
    proscenio = SimpleNamespace(active_armature=explicit_armature)
    scene = SimpleNamespace(proscenio=proscenio, objects=scene_objects or [])
    view_layer = SimpleNamespace(objects=SimpleNamespace(active=active))
    return SimpleNamespace(scene=scene, view_layer=view_layer)


class TestResolveOrder:
    def test_explicit_pointer_wins_over_active(self) -> None:
        explicit = _obj("MainRig")
        active = _obj("OtherRig")
        ctx = _ctx(explicit_armature=explicit, active=active, scene_objects=[explicit, active])
        assert resolve_skeleton_target(ctx) is explicit

    def test_active_armature_used_when_no_explicit(self) -> None:
        active = _obj("MainRig")
        ctx = _ctx(active=active, scene_objects=[active])
        assert resolve_skeleton_target(ctx) is active

    def test_active_non_armature_falls_through(self) -> None:
        only_arm = _obj("MainRig")
        active_mesh = _obj("body", obj_type="MESH")
        ctx = _ctx(active=active_mesh, scene_objects=[only_arm, active_mesh])
        # Mesh active does not qualify; single-armature heuristic picks MainRig.
        assert resolve_skeleton_target(ctx) is only_arm

    def test_single_scene_armature_auto_target(self) -> None:
        only_arm = _obj("MainRig")
        ctx = _ctx(active=None, scene_objects=[only_arm])
        assert resolve_skeleton_target(ctx) is only_arm

    def test_multiple_armatures_no_active_returns_none(self) -> None:
        a = _obj("RigA")
        b = _obj("RigB")
        ctx = _ctx(active=None, scene_objects=[a, b])
        assert resolve_skeleton_target(ctx) is None

    def test_zero_armatures_returns_none(self) -> None:
        mesh = _obj("body", obj_type="MESH")
        ctx = _ctx(active=mesh, scene_objects=[mesh])
        assert resolve_skeleton_target(ctx) is None

    def test_explicit_pointer_with_non_armature_type_ignored(self) -> None:
        # Defensive: PointerProperty poll should reject non-armatures
        # at write time, but if something slipped through (legacy
        # blend, manual fiddle) we still ignore it instead of crashing.
        broken = _obj("Broken", obj_type="MESH")
        ctx = _ctx(explicit_armature=broken, active=None, scene_objects=[broken])
        assert resolve_skeleton_target(ctx) is None

    def test_no_scene_returns_none(self) -> None:
        ctx = SimpleNamespace(scene=None, view_layer=None)
        assert resolve_skeleton_target(ctx) is None

    def test_no_proscenio_pg_falls_through(self) -> None:
        only_arm = _obj("MainRig")
        scene = SimpleNamespace(objects=[only_arm])
        view_layer = SimpleNamespace(objects=SimpleNamespace(active=only_arm))
        ctx = SimpleNamespace(scene=scene, view_layer=view_layer)
        # Scene has no .proscenio attr - getattr returns None and
        # resolution falls through to the active-armature path.
        assert resolve_skeleton_target(ctx) is only_arm
