"""Headless tests for the Quick Armature in-modal undo/redo + snap-lock order.

Runs INSIDE Blender via ``run_operator_tests.py``. The modal's
``_create_bone`` / ``_undo_last_bone`` / ``_redo_last_bone`` /
``_post_process_world_point`` are callable without the event loop, but a
``bpy.types.Operator`` subclass cannot be instantiated from Python in 5.1
(``bpy_struct.__new__`` rejects it). So a plain-Python ``_Probe`` double hosts
the real method functions (stolen by reference, not reimplemented) plus the
ClassVar state they mutate and a no-op ``report``. ``type(self)`` resolves to
``_Probe``, giving each test fresh stack state with no leak between runs.

This locks the undo/redo stack (create across a chain, undo to empty, redo to
full with names + parenting stable) and the snap-then-lock ordering. The pure
snap/lock/name math is unit-tested in ``tests/test_quick_armature_math.py``.
"""

from __future__ import annotations

import contextlib
from typing import Any, ClassVar

import bpy
import pytest


def _bones(arm: bpy.types.Object):
    """The live bone collection: ``edit_bones`` in Edit mode, else ``data.bones``.

    The Quick Armature session now stays in Edit mode, where ``data.bones`` is
    stale - reads must go through ``edit_bones`` until the session exits.
    """
    return arm.data.edit_bones if arm.mode == "EDIT" else arm.data.bones


def _bone_names(arm: bpy.types.Object) -> list[str]:
    return [b.name for b in _bones(arm)]


@pytest.fixture
def quick_armature_session(automesh_fixture):
    # A prior test may have left Blender in Edit mode on its armature; reset so
    # each session starts from Object mode (what the operator's invoke assumes).
    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
        with contextlib.suppress(RuntimeError):
            bpy.ops.object.mode_set(mode="OBJECT")
    from proscenio.operators.armature.quick_armature import (  # type: ignore[import-not-found]
        PROSCENIO_OT_quick_armature as QA,
    )

    class _Probe:
        # Real method implementations, hosted on an instantiable plain class.
        _create_bone = QA._create_bone
        _undo_last_bone = QA._undo_last_bone
        _redo_last_bone = QA._redo_last_bone
        _post_process_world_point = QA._post_process_world_point
        _seed_chain_parent_from_active = QA._seed_chain_parent_from_active
        _sync_chain_parent_to_active = QA._sync_chain_parent_to_active
        # Static on the real class - rewrap so the probe doesn't bind ``self``.
        _enter_armature_edit = staticmethod(QA._enter_armature_edit)
        _live_bone_tails = staticmethod(QA._live_bone_tails)
        modal = QA.modal

        def report(self, *_args, **_kwargs) -> None:
            return None

        # ClassVar state the methods read / mutate (fresh per test).
        _target_armature_name = ""
        _name_prefix = "qbone"
        _last_bone_name = ""
        _session_records: ClassVar[list[Any]] = []
        _redo_records: ClassVar[list[Any]] = []
        _ctrl_held = False
        _snap_increment = 1.0
        _drag_head = None
        _drag_press_point = None
        _axis_lock = None
        _exit_requested = False

    arm_data = bpy.data.armatures.new("QA_TEST")
    arm = bpy.data.objects.new("QA_TEST", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    _Probe._target_armature_name = arm.name

    return _Probe(), arm, _Probe


def test_enter_armature_edit_refuses_hidden_armature(quick_armature_session):
    """A hidden armature cannot become active, so _enter_armature_edit returns
    False instead of crashing bpy.ops.object.mode_set ('Context missing active
    object'). Guards Quick Armature against a hidden selected rig."""
    op, arm, _cls = quick_armature_session
    arm.hide_set(True)
    try:
        assert arm.visible_get() is False
        assert op._enter_armature_edit(bpy.context, arm) is False
    finally:
        arm.hide_set(False)


def test_create_bone_appends_to_session_stack(quick_armature_session):
    op, arm, cls = quick_armature_session
    op._create_bone(
        bpy.context, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), parent_to_last=False, connect=False
    )
    assert len(cls._session_records) == 1
    assert len(_bones(arm)) == 1
    assert cls._last_bone_name == _bones(arm)[0].name


def test_chained_bone_parents_to_previous(quick_armature_session):
    op, arm, _cls = quick_armature_session
    op._create_bone(
        bpy.context, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), parent_to_last=False, connect=False
    )
    root_name = _bones(arm)[0].name
    op._create_bone(
        bpy.context, (0.0, 0.0, 1.0), (0.0, 0.0, 2.0), parent_to_last=True, connect=True
    )
    child = _bones(arm)[1]
    assert child.parent is not None
    assert child.parent.name == root_name
    assert child.use_connect is True


def test_create_clears_the_redo_stack(quick_armature_session):
    op, _arm, cls = quick_armature_session
    op._create_bone(
        bpy.context, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), parent_to_last=False, connect=False
    )
    op._undo_last_bone(bpy.context)
    assert len(cls._redo_records) == 1
    op._create_bone(
        bpy.context, (1.0, 0.0, 0.0), (1.0, 0.0, 1.0), parent_to_last=False, connect=False
    )
    assert len(cls._redo_records) == 0, "a fresh bone must clear the redo history"


def test_undo_to_empty_then_redo_restores_chain(quick_armature_session):
    op, arm, cls = quick_armature_session
    op._create_bone(
        bpy.context, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), parent_to_last=False, connect=False
    )
    op._create_bone(
        bpy.context, (0.0, 0.0, 1.0), (0.0, 0.0, 2.0), parent_to_last=True, connect=True
    )
    full = _bone_names(arm)
    assert len(full) == 2

    op._undo_last_bone(bpy.context)
    assert len(_bones(arm)) == 1
    assert len(cls._redo_records) == 1
    op._undo_last_bone(bpy.context)
    assert len(_bones(arm)) == 0
    assert cls._last_bone_name == ""

    op._redo_last_bone(bpy.context)
    op._redo_last_bone(bpy.context)
    assert _bone_names(arm) == full, "redo did not restore the same bones in order"
    assert len(cls._redo_records) == 0
    assert _bones(arm)[1].parent is not None, "redo lost the chain parenting"


def test_redo_uses_the_records_parent_not_the_live_chain(quick_armature_session):
    """Redo must reparent the bone to the parent it was CREATED with (the
    record), not the live _last_bone_name - which a reparent-by-selection or the
    undo itself can have moved. Otherwise redo silently corrupts the authored
    bone chain (spec 069 reparent-by-selection makes this readily reachable)."""
    op, arm, cls = quick_armature_session
    # A (root), then B chained on A.
    op._create_bone(
        bpy.context, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), parent_to_last=False, connect=False
    )
    a_name = _bones(arm)[0].name
    op._create_bone(
        bpy.context, (0.0, 0.0, 1.0), (0.0, 0.0, 2.0), parent_to_last=True, connect=True
    )
    # Reparent-by-selection: pick A again as the chain parent.
    _bones(arm).active = _bones(arm)[0]
    op._sync_chain_parent_to_active()
    assert cls._last_bone_name == a_name
    # C drawn on A.
    op._create_bone(
        bpy.context, (1.0, 0.0, 0.0), (1.0, 0.0, 1.0), parent_to_last=True, connect=False
    )
    c_before = _bones(arm)[-1]
    assert c_before.parent is not None and c_before.parent.name == a_name
    # Undo C (this rewinds _last_bone_name to B), then redo it.
    op._undo_last_bone(bpy.context)
    op._redo_last_bone(bpy.context)
    c_after = _bones(arm)[-1]
    assert c_after.parent is not None, "redo lost C's parent"
    assert c_after.parent.name == a_name, "redo reparented C to the live chain, not its record"


def test_post_process_snaps_then_axis_locks(quick_armature_session):
    op, _arm, cls = quick_armature_session
    cls._ctrl_held = True
    cls._snap_increment = 1.0
    cls._axis_lock = "X"
    # Head's Z is deliberately off-grid (0.3). Snap-then-lock leaves Z at that
    # raw head value; lock-then-snap would round it to 0.0 - so Z == 0.3 proves
    # the snap runs first and the lock clamps the unsnapped head afterward.
    cls._drag_head = (0.0, 0.0, 0.3)
    result = op._post_process_world_point((1.4, 0.0, 1.6))
    assert result is not None
    assert result[0] == pytest.approx(1.0), "X was not grid-snapped before the lock"
    assert result[1] == pytest.approx(0.0), "Y left the picture plane"
    assert result[2] == pytest.approx(0.3), "lock did not run after snap (Z got re-snapped)"


def test_post_process_snaps_and_pins_y_without_a_lock(quick_armature_session):
    op, _arm, cls = quick_armature_session
    cls._ctrl_held = True
    cls._snap_increment = 1.0
    cls._axis_lock = None
    cls._drag_head = None
    result = op._post_process_world_point((1.2, 0.0, 0.8))
    assert result == pytest.approx((1.0, 0.0, 1.0))


def test_exit_requested_finishes_modal_on_next_event(quick_armature_session):
    op, _arm, cls = quick_armature_session
    # The panel's "Exit Quick Armature" button sets _exit_requested from a
    # re-invoke; the running modal must honour it on its next event (finishing,
    # not authoring), then clear the flag. Stub _exit so no viewport teardown runs.
    calls: list[bool] = []

    def _fake_exit(_context, *, cancelled):
        calls.append(cancelled)
        return {"CANCELLED"}

    op._exit = _fake_exit  # type: ignore[method-assign]
    cls._drag_head = None
    cls._session_records = []
    cls._exit_requested = True

    result = op.modal(bpy.context, object())

    assert cls._exit_requested is False, "the flag must clear so it fires once"
    assert calls == [True], "an empty session exits cancelled (discards the empty rig)"
    assert result == {"CANCELLED"}


def test_sync_chain_parent_adopts_the_active_edit_bone(quick_armature_session):
    op, arm, cls = quick_armature_session
    # Reparent = selection: author two bones, then make the FIRST the active edit
    # bone (what a right-click would do). The press-time sync adopts it as the
    # chain parent, so the next connected draw chains from the selected bone.
    op._create_bone(
        bpy.context, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), parent_to_last=False, connect=False
    )
    op._create_bone(
        bpy.context, (0.0, 0.0, 1.0), (0.0, 0.0, 2.0), parent_to_last=True, connect=True
    )
    first = _bones(arm)[0]
    _bones(arm).active = first
    op._sync_chain_parent_to_active()
    assert cls._last_bone_name == first.name, "sync did not adopt the selected bone"

    op._create_bone(
        bpy.context, (1.0, 0.0, 0.0), (1.0, 0.0, 1.0), parent_to_last=True, connect=False
    )
    # The freshly drawn bone chains from the bone that was selected, not the
    # last-authored one.
    drawn = _bones(arm)[-1]
    assert drawn.parent is not None and drawn.parent.name == first.name


def test_sync_chain_parent_noop_without_an_active_bone(quick_armature_session):
    op, arm, cls = quick_armature_session
    op._create_bone(
        bpy.context, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), parent_to_last=False, connect=False
    )
    last = cls._last_bone_name
    _bones(arm).active = None
    op._sync_chain_parent_to_active()
    assert cls._last_bone_name == last, "no active bone must leave the chain parent unchanged"


def test_seed_chain_parent_from_active_bone(quick_armature_session):
    op, arm, cls = quick_armature_session
    # Author a bone and make it the armature's active bone (the importer root is
    # the motivating case). Reset the chain parent the way invoke does, then seed.
    op._create_bone(
        bpy.context, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), parent_to_last=False, connect=False
    )
    root_name = _bones(arm)[0].name
    _bones(arm).active = _bones(arm)[0]
    cls._last_bone_name = ""
    op._seed_chain_parent_from_active()
    assert cls._last_bone_name == root_name, "seed did not adopt the active bone"
    # The next connected Draw chains onto the seeded bone.
    op._create_bone(
        bpy.context, (0.0, 0.0, 1.0), (0.0, 0.0, 2.0), parent_to_last=True, connect=True
    )
    child = _bones(arm)[1]
    assert child.parent is not None and child.parent.name == root_name


def test_seed_chain_parent_noop_without_active_bone(quick_armature_session):
    op, arm, cls = quick_armature_session
    # No active bone: the seed must leave _last_bone_name untouched ("") so the
    # first bone stays unparented exactly as before this feature.
    _bones(arm).active = None
    cls._last_bone_name = ""
    op._seed_chain_parent_from_active()
    assert cls._last_bone_name == "", "seed wrote a parent with no active bone"


def test_seed_chain_parent_noop_when_target_missing(quick_armature_session):
    op, _arm, cls = quick_armature_session
    # A target that does not resolve must not crash the seed (degrades silently).
    cls._target_armature_name = "does-not-exist"
    cls._last_bone_name = ""
    op._seed_chain_parent_from_active()
    assert cls._last_bone_name == ""


def test_is_running_reflects_the_modal_sentinel():
    # The Skeleton panel reads liveness through is_running() rather than the
    # private _modal_running ClassVar; the accessor must mirror the sentinel.
    from proscenio.operators.armature.quick_armature import (  # type: ignore[import-not-found]
        PROSCENIO_OT_quick_armature as QA,
    )

    prior = QA._modal_running
    try:
        QA._modal_running = True
        assert QA.is_running() is True
        QA._modal_running = False
        assert QA.is_running() is False
    finally:
        QA._modal_running = prior
