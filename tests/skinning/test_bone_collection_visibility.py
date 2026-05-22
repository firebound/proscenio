"""Pure tests for bone collection visibility snapshot (SPEC 013.2 paint, T4)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

# Module lives under bpy_helpers/skinning/ for organization, but the package
# __init__.py eagerly imports bpy-bound siblings. Load the bpy-free file
# directly via importlib.util to bypass the package init.
_MOD_PATH = REPO_ROOT / "apps/blender/core/bpy_helpers/skinning/bone_collection_visibility.py"
_spec = importlib.util.spec_from_file_location("bone_collection_visibility", _MOD_PATH)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
sys.modules["bone_collection_visibility"] = _mod
_spec.loader.exec_module(_mod)

BoneCollectionSnapshot = _mod.BoneCollectionSnapshot
restore = _mod.restore
snapshot = _mod.snapshot


def _armature_4x(visible_names: list[str], all_names: list[str]) -> SimpleNamespace:
    """Blender 4.0+ armature: data.collections + is_visible per collection."""
    collections = [
        SimpleNamespace(name=name, is_visible=(name in visible_names)) for name in all_names
    ]
    return SimpleNamespace(
        data=SimpleNamespace(
            collections=collections,
            bones=[],
        )
    )


def _armature_3x(bone_hide: dict[str, bool]) -> SimpleNamespace:
    """Blender 3.x armature: no collections attr, per-bone hide."""
    bones = [SimpleNamespace(name=name, hide=hide) for name, hide in bone_hide.items()]
    return SimpleNamespace(data=SimpleNamespace(bones=bones))


def test_snapshot_4x_captures_visible_collection_names():
    arm = _armature_4x(visible_names=["arms", "legs"], all_names=["arms", "legs", "face"])
    snap = snapshot(arm)
    assert snap.visible_names == ["arms", "legs"]
    assert snap.bone_hide_states == {}


def test_snapshot_3x_fallback_captures_bone_hide():
    arm = _armature_3x({"wrist": False, "palm": True, "fingertip": False})
    snap = snapshot(arm)
    assert snap.visible_names == []
    assert snap.bone_hide_states == {"wrist": False, "palm": True, "fingertip": False}


def test_restore_4x_round_trip():
    arm = _armature_4x(visible_names=["arms"], all_names=["arms", "legs"])
    snap = snapshot(arm)
    # mutate: hide arms, show legs
    arm.data.collections[0].is_visible = False
    arm.data.collections[1].is_visible = True
    restore(arm, snap)
    assert arm.data.collections[0].is_visible is True
    assert arm.data.collections[1].is_visible is False
