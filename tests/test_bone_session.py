"""Pure tests for the Quick Armature undo/redo record stack (BoneSession).

The stack semantics - create clears redo, undo moves onto redo, take_redo does
not consume until readd, readd preserves the rest - are pure bookkeeping, so they
are unit-tested here without a viewport. The bpy edit-bone mutation is covered by
the in-Blender ``test_quick_armature_modal`` suite.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

# bone_session imports bpy / mathutils (via author_edit_bone); mock before import.
sys.modules["bpy"] = MagicMock()
sys.modules["mathutils"] = MagicMock()

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.bpy_helpers.armature.bone_session import BoneRecord, BoneSession  # noqa: E402


def _rec(name: str, parent: str = "") -> BoneRecord:
    return BoneRecord(
        name=name,
        head=(0.0, 0.0, 0.0),
        tail=(0.0, 0.0, 1.0),
        parent_to_last_name=parent,
        connect=bool(parent),
    )


def test_record_created_appends_and_clears_redo():
    s = BoneSession()
    s.redo.append(_rec("stale"))  # a pending redo from an earlier undo
    s.record_created(_rec("a"))
    assert [r.name for r in s.records] == ["a"]
    assert s.redo == [], "a freshly authored bone must clear the redo stack"


def test_undo_moves_the_top_record_onto_redo():
    s = BoneSession()
    s.record_created(_rec("a"))
    s.record_created(_rec("b"))
    popped = s.undo()
    assert popped is not None and popped.name == "b"
    assert [r.name for r in s.records] == ["a"]
    assert [r.name for r in s.redo] == ["b"]


def test_undo_on_empty_is_none():
    assert BoneSession().undo() is None


def test_take_redo_does_not_readd_until_asked():
    s = BoneSession()
    s.record_created(_rec("a"))
    s.undo()
    rec = s.take_redo()
    assert rec is not None and rec.name == "a"
    # Not re-added yet: a failed re-author must not silently consume the redo entry.
    assert s.records == []
    s.readd(rec)
    assert [r.name for r in s.records] == ["a"]


def test_readd_preserves_the_rest_of_the_redo_stack():
    s = BoneSession()
    s.record_created(_rec("a"))
    s.record_created(_rec("b"))
    s.undo()  # redo = [b]
    s.undo()  # redo = [b, a]
    first = s.take_redo()  # pops "a"
    assert first is not None and first.name == "a"
    s.readd(first)
    assert [r.name for r in s.redo] == ["b"], "re-adding one redo must keep the rest"


def test_last_authored_name_tracks_the_top():
    s = BoneSession()
    assert s.last_authored_name() == ""
    s.record_created(_rec("a"))
    s.record_created(_rec("b"))
    assert s.last_authored_name() == "b"
    s.undo()
    assert s.last_authored_name() == "a"


def test_clear_empties_both_stacks():
    s = BoneSession()
    s.record_created(_rec("a"))
    s.undo()
    s.clear()
    assert s.records == [] and s.redo == []
