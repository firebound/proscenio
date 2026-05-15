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
    """SPEC 012.2 contract: picker is the only source of truth.

    Heuristics (active object, single-armature scene) live in the
    auto-populate handler, not in this resolver. Once the user clears
    the picker, the resolver returns ``None`` and the operator falls
    back to ``Proscenio.QuickRig``.
    """

    def test_explicit_pointer_returns_armature(self) -> None:
        explicit = _obj("MainRig")
        ctx = _ctx(explicit_armature=explicit, scene_objects=[explicit])
        assert resolve_skeleton_target(ctx) is explicit

    def test_no_explicit_returns_none_even_with_active_armature(self) -> None:
        active = _obj("MainRig")
        ctx = _ctx(active=active, scene_objects=[active])
        # Active object NOT used as fallback - picker is the contract.
        assert resolve_skeleton_target(ctx) is None

    def test_no_explicit_returns_none_even_with_single_scene_armature(self) -> None:
        only_arm = _obj("MainRig")
        ctx = _ctx(active=None, scene_objects=[only_arm])
        # Single-armature heuristic also dropped from the resolver.
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

    def test_no_proscenio_pg_returns_none(self) -> None:
        only_arm = _obj("MainRig")
        scene = SimpleNamespace(objects=[only_arm])
        view_layer = SimpleNamespace(objects=SimpleNamespace(active=only_arm))
        ctx = SimpleNamespace(scene=scene, view_layer=view_layer)
        # No .proscenio attr -> no picker to read -> None.
        assert resolve_skeleton_target(ctx) is None
