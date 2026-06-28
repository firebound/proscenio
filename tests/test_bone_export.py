"""Unit tests for the bone export-gate predicate.

Pure pytest, no Blender. ``bone_is_exported`` is the bpy-free rule the Godot
writer and the Skeleton "won't export" cue both read: a bone exports when it
deforms and the rigger has not pinned it off the export.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.bone_export import bone_is_exported  # noqa: E402


def _bone(*, use_deform: bool = True, exclude: bool = False) -> SimpleNamespace:
    return SimpleNamespace(use_deform=use_deform, proscenio=SimpleNamespace(exclude_from_export=exclude))


def test_deform_bone_without_flag_exports() -> None:
    assert bone_is_exported(_bone()) is True


def test_non_deform_bone_never_exports() -> None:
    # A control bone (IK goal / pole) is out regardless of the flag.
    assert bone_is_exported(_bone(use_deform=False)) is False
    assert bone_is_exported(_bone(use_deform=False, exclude=True)) is False


def test_flagged_deform_bone_is_excluded() -> None:
    # A rig helper the rigger pinned off the export, even though it deforms.
    assert bone_is_exported(_bone(exclude=True)) is False


def test_missing_proscenio_group_degrades_to_use_deform() -> None:
    # No PropertyGroup (addon unregistered / older datablock): plain use_deform.
    assert bone_is_exported(SimpleNamespace(use_deform=True)) is True
    assert bone_is_exported(SimpleNamespace(use_deform=False)) is False


def test_missing_use_deform_attr_reads_as_not_exported() -> None:
    assert bone_is_exported(SimpleNamespace()) is False
