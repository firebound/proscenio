"""Headless tests for Edit Weights modal."""

from __future__ import annotations

import bpy
import pytest


def _activate(name: str) -> bpy.types.Object:
    obj = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    return obj


def _set_picker(name: str) -> None:
    bpy.context.scene.proscenio.active_armature = bpy.data.objects[name]


def test_invoke_aborts_without_sidecar(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    # Do NOT bind - sidecar absent. The operator's poll() gate refuses
    # the call before invoke even fires, which surfaces as a poll-failed
    # RuntimeError from bpy.ops. Either way, the abort guarantee is the
    # same: no mode transition, no side effects on the active object.
    assert bpy.ops.proscenio.edit_weights.poll() is False
    with pytest.raises(RuntimeError, match=r"poll|sidecar|context"):
        bpy.ops.proscenio.edit_weights("INVOKE_DEFAULT")
    assert obj.mode != "WEIGHT_PAINT"


def test_invoke_enters_weight_paint_with_preset_applied(automesh_fixture):
    obj = _activate("hand")
    armature = bpy.data.objects["automesh.hand_rig"]
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    # Headless Blender cannot run modal operators end-to-end (no event loop, and
    # a bpy.types.Operator subclass cannot be instantiated). Drive the REAL
    # extracted _enter_weight_paint - the headless half of invoke() - instead of
    # re-implementing its block inline, so a regression in that wiring is caught
    # here rather than slipping past a copy. The modal-only wiring is covered by
    # the modal/_finish lifecycle tests below.
    from proscenio.core.bpy_helpers.skinning import (  # type: ignore[import-not-found]
        read_mirror_flag,
    )
    from proscenio.operators.skinning.edit_weights import (  # type: ignore[import-not-found]
        _enter_weight_paint,
    )

    _enter_weight_paint(bpy.context, obj, armature, mirror_x=read_mirror_flag(armature))
    assert obj.mode == "WEIGHT_PAINT"
    brush = bpy.context.tool_settings.weight_paint.brush
    assert bool(getattr(brush, "use_frontface", True)) is False


def test_stroke_flips_provenance_to_user_paint(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    # Drive the operator's stroke logic via the underlying class
    # rather than firing events (which the headless framework cannot pump).
    from proscenio.core.bpy_helpers.skinning import (
        StrokeDiffTracker,  # type: ignore[import-not-found]
    )
    from proscenio.core.skinning.sidecar_schema import from_json  # type: ignore[import-not-found]

    sidecar_before = from_json(obj["proscenio_weight_sidecar"])
    tracker = StrokeDiffTracker(obj, sidecar_before)
    obj.vertex_groups.active_index = obj.vertex_groups["wrist"].index
    tracker.snapshot_active_vg()
    # Mutate weights on the wrist group to simulate a stroke
    wrist = obj.vertex_groups["wrist"]
    target_verts = [v.index for v in obj.data.vertices[:5]]
    for vert_idx in target_verts:
        wrist.add([vert_idx], 0.42, "REPLACE")
    touched = tracker.flip_touched_after_stroke()
    assert touched >= 1
    sidecar_after = from_json(obj["proscenio_weight_sidecar"])
    user_paint_count = sum(1 for e in sidecar_after.entries if e.provenance == "user_paint")
    assert user_paint_count >= 1


def test_session_capture_restore_round_trip(automesh_fixture):
    obj = _activate("hand")
    armature = bpy.data.objects["automesh.hand_rig"]
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    from proscenio.core.bpy_helpers.skinning import (  # type: ignore[import-not-found]
        capture_session,
        restore_session,
        snapshot_bone_visibility,
        snapshot_paint_preset,
    )

    prior_mode = obj.mode
    prior_preset = snapshot_paint_preset(bpy.context)
    prior_visibility = snapshot_bone_visibility(armature)
    session = capture_session(
        bpy.context, obj, armature, prior_preset, prior_visibility, overlay_flag=False
    )
    # Mutate: switch to WEIGHT_PAINT
    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    assert obj.mode == "WEIGHT_PAINT"
    restore_session(bpy.context, session)
    assert obj.mode == prior_mode


def test_restore_returns_overlay_flag_to_prior(automesh_fixture):
    # The external-exit fix relies on _finish -> restore_session putting the
    # provenance-overlay flag back to its pre-modal value. Lock that contract:
    # whatever the modal turned it to, restore returns it to what was captured.
    obj = _activate("hand")
    armature = bpy.data.objects["automesh.hand_rig"]
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    from proscenio.core.bpy_helpers.skinning import (  # type: ignore[import-not-found]
        capture_session,
        restore_session,
        snapshot_bone_visibility,
        snapshot_paint_preset,
    )

    skinning = bpy.context.scene.proscenio.skinning
    skinning.show_provenance_overlay = False
    session = capture_session(
        bpy.context,
        obj,
        armature,
        snapshot_paint_preset(bpy.context),
        snapshot_bone_visibility(armature),
        overlay_flag=False,
    )
    skinning.show_provenance_overlay = True  # modal turns it on

    restore_session(bpy.context, session)

    assert skinning.show_provenance_overlay is False


def test_panel_button_present_when_sidecar_populated(automesh_fixture):
    _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    # The panel draw runs in the UI layer; we only assert the operator is
    # registered + poll-passes for the active obj.
    assert bpy.ops.proscenio.edit_weights.poll() is True


def test_midstroke_pressure_dip_keeps_tracking_tail_verts(automesh_fixture, monkeypatch):
    """A tablet pressure dip mid-stroke must NOT end the stroke: verts painted
    AFTER the dip must still flip to user_paint on release. The bug let a
    pressure<1e-6 MOUSEMOVE flip+reset the tracker mid-stroke, so the release
    became a no-op and the post-dip tail kept its old (non-user_paint) provenance."""
    from types import SimpleNamespace

    from proscenio.core.bpy_helpers.skinning import (  # type: ignore[import-not-found]
        StrokeDiffTracker,
    )
    from proscenio.core.skinning.sidecar_schema import from_json  # type: ignore[import-not-found]
    from proscenio.operators.skinning import edit_weights as mod  # type: ignore[import-not-found]

    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    wrist = obj.vertex_groups["wrist"]
    obj.vertex_groups.active_index = wrist.index
    # Clean wrist group so each painted vert is an unambiguous touch vs the snapshot.
    for vert in obj.data.vertices:
        wrist.add([vert.index], 0.0, "REPLACE")

    monkeypatch.setattr(mod, "_tag_redraw_view3d", lambda _c: None)
    tracker = StrokeDiffTracker(obj, from_json(obj["proscenio_weight_sidecar"]))
    stub = SimpleNamespace(_stroke_tracker=tracker, _stroke_active=False)
    cls = mod.PROSCENIO_OT_edit_weights_modal
    ctx = SimpleNamespace()

    def event(type_: str, value: str = "", pressure: float = 1.0) -> object:
        return SimpleNamespace(type=type_, value=value, pressure=pressure)

    cls.modal(stub, ctx, event("LEFTMOUSE", "PRESS"))  # snapshot the (empty) baseline
    for i in (0, 1):  # head of the stroke
        wrist.add([i], 0.9, "REPLACE")
    cls.modal(stub, ctx, event("MOUSEMOVE", pressure=0.0))  # mid-stroke pressure dip
    tail = (2, 3)
    for i in tail:  # painted AFTER the dip
        wrist.add([i], 0.9, "REPLACE")
    cls.modal(stub, ctx, event("LEFTMOUSE", "RELEASE"))  # flips the whole stroke

    final = from_json(obj["proscenio_weight_sidecar"])
    tail_user_paint = all(final.entries[i].provenance == "user_paint" for i in tail)
    assert tail_user_paint, "mid-stroke pressure dip dropped the tail verts' user_paint flip"


def test_cancel_delegates_to_finish():
    """Blender calls cancel() when the modal is killed externally (window close,
    file load). Edit Weights must delegate it to _finish(cancel=True) so the
    timer, overlay, statusbar, and session restore all run - without cancel()
    that cleanup never happens and the paint session leaks."""
    from types import SimpleNamespace

    from proscenio.operators.skinning import (  # type: ignore[import-not-found]
        edit_weights as mod,
    )

    calls: list[bool] = []
    stub = SimpleNamespace(_finish=lambda _context, *, cancel: calls.append(cancel))
    mod.PROSCENIO_OT_edit_weights_modal.cancel(stub, context=None)
    assert calls == [True], "cancel must delegate to _finish(cancel=True)"


# --- modal() dispatch + _finish() teardown lifecycle (the audit's one medium) --
#
# The invoke/modal/_finish lifecycle proper is not headless-runnable, so drive
# modal() and _finish() directly on a plain SimpleNamespace stub (a
# bpy.types.Operator subclass cannot be instantiated in 5.1) with fabricated
# events and stubbed collaborators - the _Probe pattern from
# test_quick_armature_modal.py. This is the coverage spec 075 Phase C's D6 waits
# on before the large operator splits.


def _raise(exc: Exception):
    def _fn(*_args, **_kwargs):
        raise exc

    return _fn


def test_modal_timer_external_exit_finishes_non_cancel(automesh_fixture):
    from types import SimpleNamespace

    from proscenio.operators.skinning import edit_weights as mod  # type: ignore[import-not-found]

    cls = mod.PROSCENIO_OT_edit_weights_modal
    calls: list[bool] = []
    stub = SimpleNamespace(_finish=lambda _c, *, cancel: calls.append(cancel) or {"FINISHED"})

    # A native exit from weight-paint (header dropdown / tab) sends no event, so
    # the TIMER poll sees the mode changed and finishes NON-cancel.
    ctx = SimpleNamespace(active_object=SimpleNamespace(mode="OBJECT"))
    cls.modal(stub, ctx, SimpleNamespace(type="TIMER", value=""))
    assert calls == [False], "TIMER external-exit must finish non-cancel"

    # Still painting -> the timer just passes through, no finish.
    calls.clear()
    ctx = SimpleNamespace(active_object=SimpleNamespace(mode="WEIGHT_PAINT"))
    result = cls.modal(stub, ctx, SimpleNamespace(type="TIMER", value=""))
    assert calls == [] and result == {"PASS_THROUGH"}


def test_modal_esc_finishes_cancel(automesh_fixture):
    from types import SimpleNamespace

    from proscenio.operators.skinning import edit_weights as mod  # type: ignore[import-not-found]

    cls = mod.PROSCENIO_OT_edit_weights_modal
    calls: list[bool] = []
    stub = SimpleNamespace(_finish=lambda _c, *, cancel: calls.append(cancel) or {"CANCELLED"})
    cls.modal(stub, SimpleNamespace(), SimpleNamespace(type="ESC", value="PRESS"))
    assert calls == [True], "ESC must finish cancel"


def test_modal_exception_finishes_cancel(automesh_fixture):
    from types import SimpleNamespace

    from proscenio.operators.skinning import edit_weights as mod  # type: ignore[import-not-found]

    cls = mod.PROSCENIO_OT_edit_weights_modal
    calls: list[bool] = []
    # A raising tracker inside modal() must be caught and routed to a cancel
    # finish (never leak the paint session on an unexpected error).
    stub = SimpleNamespace(
        _finish=lambda _c, *, cancel: calls.append(cancel) or {"CANCELLED"},
        _stroke_active=False,
        _stroke_tracker=SimpleNamespace(snapshot_active_vg=_raise(RuntimeError("boom"))),
    )
    cls.modal(stub, SimpleNamespace(), SimpleNamespace(type="LEFTMOUSE", value="PRESS"))
    assert calls == [True], "an exception in modal must finish cancel"


def _finish_stub(events: list, **overrides):
    from types import SimpleNamespace

    base = {
        "_timer": "TIMER_OBJ",
        "_overlay_handle": "OVERLAY",
        "_session": "SESSION",
        "_remove_statusbar": lambda: events.append("statusbar"),
        "_capture_auto_snapshot": lambda: events.append("snapshot"),
        "report": lambda *_a, **_k: None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _finish_ctx(timer_removed: list):
    from types import SimpleNamespace

    wm = SimpleNamespace(event_timer_remove=lambda t: timer_removed.append(t))
    return SimpleNamespace(window_manager=wm)


def test_finish_tears_down_and_snapshots_on_non_cancel(automesh_fixture, monkeypatch):
    from proscenio.operators.skinning import edit_weights as mod  # type: ignore[import-not-found]

    cls = mod.PROSCENIO_OT_edit_weights_modal
    events: list[str] = []
    timer_removed: list[object] = []
    monkeypatch.setattr(mod, "unregister_handler", lambda h: events.append(f"unregister:{h}"))
    monkeypatch.setattr(mod, "restore_session", lambda _c, s: events.append(f"restore:{s}"))

    stub = _finish_stub(events)
    result = cls._finish(stub, _finish_ctx(timer_removed), cancel=False)

    assert result == {"FINISHED"}
    assert timer_removed == ["TIMER_OBJ"], "the mode-watch timer was not removed"
    assert "unregister:OVERLAY" in events, "the provenance overlay was not unregistered"
    assert "statusbar" in events, "the status bar draw was not removed"
    assert "snapshot" in events, "a normal finish must capture the auto-snapshot"
    assert "restore:SESSION" in events, "the session was not restored"
    assert stub._timer is None, "the timer handle was not cleared"
    assert stub._overlay_handle is None, "the overlay handle was not cleared"


def test_finish_suppresses_snapshot_on_cancel(automesh_fixture, monkeypatch):
    from proscenio.operators.skinning import edit_weights as mod  # type: ignore[import-not-found]

    cls = mod.PROSCENIO_OT_edit_weights_modal
    events: list[str] = []
    monkeypatch.setattr(mod, "unregister_handler", lambda h: events.append("unregister"))
    monkeypatch.setattr(mod, "restore_session", lambda _c, s: events.append("restore"))

    result = cls._finish(_finish_stub(events), _finish_ctx([]), cancel=True)

    assert result == {"CANCELLED"}
    assert "snapshot" not in events, "cancel must NOT capture an auto-snapshot"
    assert "restore" in events, "restore must run on every exit path"


def test_finish_suppresses_a_failing_snapshot(automesh_fixture, monkeypatch):
    from proscenio.operators.skinning import edit_weights as mod  # type: ignore[import-not-found]

    cls = mod.PROSCENIO_OT_edit_weights_modal
    events: list[str] = []
    monkeypatch.setattr(mod, "unregister_handler", lambda h: events.append("unregister"))
    monkeypatch.setattr(mod, "restore_session", lambda _c, s: events.append("restore"))

    # A snapshot failure must be swallowed so the mode/selection restore below it
    # still runs (cleanup must complete on every exit path).
    stub = _finish_stub(events, _capture_auto_snapshot=_raise(RuntimeError("snap fail")))
    result = cls._finish(stub, _finish_ctx([]), cancel=False)

    assert result == {"FINISHED"}, "a failing snapshot must not abort the finish"
    assert "restore" in events, "cleanup must continue past the snapshot failure"
