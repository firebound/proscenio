"""Unit tests for slot armature resolution.

Pure pytest - bone_follow imports bpy at module top (the bpy_helpers
contract), so a MagicMock stands in before the import the same way
``tests/automesh/test_extra_edges_cdt.py`` does. resolve_slot_armature does
attribute access only, so SimpleNamespace mocks exercise the priority order
without Blender.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

# bone_follow does a top-level ``import bpy``; stub it before importing.
sys.modules["bpy"] = MagicMock()

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.bpy_helpers.slot.bone_follow import resolve_slot_armature  # noqa: E402


def _armature(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, type="ARMATURE")


def _context(*, scene_objects=(), picker=None) -> SimpleNamespace:
    proscenio = SimpleNamespace(active_armature=picker)
    scene = SimpleNamespace(objects=list(scene_objects), proscenio=proscenio)
    return SimpleNamespace(scene=scene)


def test_prefers_empty_object_parent_armature() -> None:
    arm = _armature("rig_parent")
    empty = SimpleNamespace(parent=arm)
    ctx = _context(scene_objects=[arm, _armature("other")], picker=_armature("picked"))
    assert resolve_slot_armature(ctx, empty) is arm


def test_falls_back_to_picker_when_parent_not_armature() -> None:
    picked = _armature("picked")
    empty = SimpleNamespace(parent=SimpleNamespace(type="MESH"))
    ctx = _context(scene_objects=[picked], picker=picked)
    assert resolve_slot_armature(ctx, empty) is picked


def test_falls_back_to_scene_export_armature() -> None:
    only = _armature("only_rig")
    empty = SimpleNamespace(parent=None)
    ctx = _context(scene_objects=[only], picker=None)
    assert resolve_slot_armature(ctx, empty) is only


def test_returns_none_when_no_armature() -> None:
    empty = SimpleNamespace(parent=None)
    ctx = _context(scene_objects=[SimpleNamespace(name="m", type="MESH")], picker=None)
    assert resolve_slot_armature(ctx, empty) is None
