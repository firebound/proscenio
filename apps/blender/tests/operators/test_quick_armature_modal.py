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

from typing import Any, ClassVar

import bpy
import pytest


@pytest.fixture
def quick_armature_session(automesh_fixture):
    from proscenio.operators.armature.quick_armature import (  # type: ignore[import-not-found]
        PROSCENIO_OT_quick_armature as QA,
    )

    class _Probe:
        # Real method implementations, hosted on an instantiable plain class.
        _create_bone = QA._create_bone
        _undo_last_bone = QA._undo_last_bone
        _redo_last_bone = QA._redo_last_bone
        _post_process_world_point = QA._post_process_world_point
        _switch_mode = QA._switch_mode
        _world_tail_tips = QA._world_tail_tips
        _handle_reparent_pick = QA._handle_reparent_pick
        _seed_chain_parent_from_active = QA._seed_chain_parent_from_active
        _PICK_RADIUS_PX = QA._PICK_RADIUS_PX

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
        _mode = "DRAW"
        _pick_target_name = ""

    arm_data = bpy.data.armatures.new("QA_TEST")
    arm = bpy.data.objects.new("QA_TEST", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    _Probe._target_armature_name = arm.name

    return _Probe(), arm, _Probe


def _bone_names(arm: bpy.types.Object) -> list[str]:
    return [b.name for b in arm.data.bones]


def test_create_bone_appends_to_session_stack(quick_armature_session):
    op, arm, cls = quick_armature_session
    op._create_bone(
        bpy.context, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), parent_to_last=False, connect=False
    )
    assert len(cls._session_records) == 1
    assert len(arm.data.bones) == 1
    assert cls._last_bone_name == arm.data.bones[0].name


def test_chained_bone_parents_to_previous(quick_armature_session):
    op, arm, _cls = quick_armature_session
    op._create_bone(
        bpy.context, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), parent_to_last=False, connect=False
    )
    root_name = arm.data.bones[0].name
    op._create_bone(
        bpy.context, (0.0, 0.0, 1.0), (0.0, 0.0, 2.0), parent_to_last=True, connect=True
    )
    child = arm.data.bones[1]
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
    assert len(arm.data.bones) == 1
    assert len(cls._redo_records) == 1
    op._undo_last_bone(bpy.context)
    assert len(arm.data.bones) == 0
    assert cls._last_bone_name == ""

    op._redo_last_bone(bpy.context)
    op._redo_last_bone(bpy.context)
    assert _bone_names(arm) == full, "redo did not restore the same bones in order"
    assert len(cls._redo_records) == 0
    assert arm.data.bones[1].parent is not None, "redo lost the chain parenting"


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


def test_switch_mode_cycles_draw_to_reparent_and_back(quick_armature_session):
    op, _arm, cls = quick_armature_session
    assert cls._mode == "DRAW"
    op._switch_mode(bpy.context)
    assert cls._mode == "REPARENT"
    op._switch_mode(bpy.context)
    assert cls._mode == "DRAW"


def test_switch_mode_drops_in_flight_drag_and_pick(quick_armature_session):
    op, _arm, cls = quick_armature_session
    # A drag in progress + a stale pick highlight must not survive a mode flip.
    cls._drag_head = (0.0, 0.0, 1.0)
    cls._drag_press_point = (0.0, 0.0, 0.0)
    cls._pick_target_name = "stale"
    op._switch_mode(bpy.context)
    assert cls._drag_head is None
    assert cls._drag_press_point is None
    assert cls._pick_target_name == ""


def test_world_tail_tips_projects_bone_tails_to_xz(quick_armature_session):
    op, _arm, _cls = quick_armature_session
    # Author two bones with known tails; the tips list pairs each name with its
    # world tail projected to the Y=0 XZ plane - the input the pick resolver scans.
    op._create_bone(
        bpy.context, (0.0, 0.0, 0.0), (2.0, 0.0, 3.0), parent_to_last=False, connect=False
    )
    op._create_bone(
        bpy.context, (5.0, 0.0, 0.0), (5.0, 0.0, 7.0), parent_to_last=False, connect=False
    )
    tips = op._world_tail_tips()
    by_name = dict(tips)
    assert len(tips) == 2
    assert by_name[_arm.data.bones[0].name] == pytest.approx((2.0, 3.0))
    assert by_name[_arm.data.bones[1].name] == pytest.approx((5.0, 7.0))


def test_world_tail_tips_empty_without_an_armature(quick_armature_session):
    op, _arm, cls = quick_armature_session
    cls._target_armature_name = "does-not-exist"
    assert op._world_tail_tips() == []


def test_reparent_pick_sets_chain_parent_without_authoring_a_bone(quick_armature_session):
    op, _arm, cls = quick_armature_session
    # A Reparent pick re-points the chain parent (_last_bone_name) but authors
    # no bone, so the session-authored signal (_session_records, which the Esc
    # label + cancel determination key on) must stay empty. Stub only the
    # viewport-math pick so the real field-writing path runs headless.
    op._resolve_pick_at_cursor = lambda _context, _event: "picked_bone"  # type: ignore[method-assign]
    op._handle_reparent_pick(bpy.context, object())
    assert cls._last_bone_name == "picked_bone", "pick did not set the chain parent"
    assert cls._session_records == [], "a Reparent pick must not author a bone"


def test_reparent_pick_miss_keeps_chain_parent(quick_armature_session):
    op, _arm, cls = quick_armature_session
    cls._last_bone_name = "existing"
    # A miss (no tip within the radius) is a no-op: keep the current parent and
    # never touch the session-authored signal.
    op._resolve_pick_at_cursor = lambda _context, _event: ""  # type: ignore[method-assign]
    op._handle_reparent_pick(bpy.context, object())
    assert cls._last_bone_name == "existing", "a miss must not clear the chain parent"
    assert cls._session_records == [], "a miss must not author a bone"


def test_seed_chain_parent_from_active_bone(quick_armature_session):
    op, arm, cls = quick_armature_session
    # Author a bone and make it the armature's active bone (the importer root is
    # the motivating case). Reset the chain parent the way invoke does, then seed.
    op._create_bone(
        bpy.context, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), parent_to_last=False, connect=False
    )
    root_name = arm.data.bones[0].name
    arm.data.bones.active = arm.data.bones[0]
    cls._last_bone_name = ""
    op._seed_chain_parent_from_active()
    assert cls._last_bone_name == root_name, "seed did not adopt the active bone"
    # The next connected Draw chains onto the seeded bone.
    op._create_bone(
        bpy.context, (0.0, 0.0, 1.0), (0.0, 0.0, 2.0), parent_to_last=True, connect=True
    )
    child = arm.data.bones[1]
    assert child.parent is not None and child.parent.name == root_name


def test_seed_chain_parent_noop_without_active_bone(quick_armature_session):
    op, arm, cls = quick_armature_session
    # No active bone: the seed must leave _last_bone_name untouched ("") so the
    # first bone stays unparented exactly as before this feature.
    arm.data.bones.active = None
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
