"""Headless tests for the Manual Draw operator (Draw with vertices, spec 070).

The modal click flow is not headless-testable; these cover registration, the
poll gate, and the mutual-exclusivity guard with the Automesh modal. The apply
path (manual outer -> mesh) is covered by
``test_automesh_authoring.test_apply_mesh_manual_outer_overrides_alpha_trace`` -
Manual Draw's apply runs the same ``apply_mesh`` with ``outer_is_manual=True``.
"""

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


def test_draw_mesh_vertices_registered(automesh_fixture):
    """The Manual Draw operator registers as proscenio.draw_mesh_vertices."""
    assert hasattr(bpy.ops.proscenio, "draw_mesh_vertices")


def test_draw_mesh_vertices_poll_requires_mesh_with_image(automesh_fixture):
    obj = _activate("hand")
    assert bpy.ops.proscenio.draw_mesh_vertices.poll() is True
    for slot in obj.material_slots:
        slot.material = None
    assert bpy.ops.proscenio.draw_mesh_vertices.poll() is False


def test_draw_mesh_vertices_excludes_a_running_automesh_modal(automesh_fixture):
    """The mesh-gen modes are mutually exclusive: while an Automesh modal is
    marked running, Manual Draw's poll refuses (and clears when it stops)."""
    from proscenio.operators.automesh._authoring_modal_guard import (  # type: ignore[import-not-found]
        mark_running,
        mark_stopped,
    )

    _activate("hand")
    assert bpy.ops.proscenio.draw_mesh_vertices.poll() is True
    mark_running("automesh")
    try:
        assert bpy.ops.proscenio.draw_mesh_vertices.poll() is False
    finally:
        mark_stopped("automesh")
    assert bpy.ops.proscenio.draw_mesh_vertices.poll() is True


def test_automesh_modal_excludes_a_running_manual_draw(automesh_fixture):
    """The reverse guard: while Manual Draw is marked running, the Automesh
    Interactive modal's poll refuses."""
    from proscenio.operators.automesh._authoring_modal_guard import (  # type: ignore[import-not-found]
        mark_running,
        mark_stopped,
    )

    _activate("hand")
    assert bpy.ops.proscenio.automesh_authoring.poll() is True
    mark_running("manual_draw")
    try:
        assert bpy.ops.proscenio.automesh_authoring.poll() is False
    finally:
        mark_stopped("manual_draw")
    assert bpy.ops.proscenio.automesh_authoring.poll() is True


def test_manual_contour_cp_round_trips(automesh_fixture):
    """Spec 070 C2: the manual-contour CP stores + reloads the source ring
    (points + per-edge subdivs); clear drops it."""
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        clear_manual_contour,
        read_manual_contour,
        write_manual_contour,
    )

    obj = _activate("hand")
    assert read_manual_contour(obj) == ([], [])
    pts = [(-0.2, -0.2), (0.2, -0.2), (0.2, 0.2), (-0.2, 0.2)]
    subs = [0, 1, 2]
    write_manual_contour(obj, pts, subs)
    got_pts, got_subs = read_manual_contour(obj)
    assert got_pts == pts
    assert got_subs == subs
    clear_manual_contour(obj)
    assert read_manual_contour(obj) == ([], [])


def test_finish_clears_guard_when_a_teardown_step_raises(automesh_fixture, monkeypatch):
    """A teardown step raising inside ``_finish`` must NOT leave the modal marked
    running - the guard set by ``mark_running`` would stay stuck and lock out
    BOTH authoring modes (Automesh + Manual Draw) until an addon reload."""
    from types import SimpleNamespace

    from proscenio.operators.automesh import (
        draw_mesh_vertices as mod,  # type: ignore[import-not-found]
    )
    from proscenio.operators.automesh._authoring_modal_guard import (  # type: ignore[import-not-found]
        is_running,
        mark_running,
        mark_stopped,
    )

    def _boom(_handles: object) -> None:
        raise RuntimeError("overlay teardown failed")

    monkeypatch.setattr(mod, "unregister_overlay", _boom)
    # A bpy Operator cannot be constructed headlessly, so drive the real _finish
    # with a minimal stand-in self (the operator instance is the I/O boundary).
    ctx = SimpleNamespace(window=SimpleNamespace(cursor_set=lambda *_: None), window_manager=None)
    stub = SimpleNamespace(
        _handles={}, _session=None, _remove_statusbar=lambda: None, _tag_redraw=lambda _c: None
    )

    mark_running("manual_draw")
    try:
        # Call _finish directly (no test-side suppress): the production contract is
        # that _finish itself swallows the teardown RuntimeError *and* clears the
        # guard, so a leaked exception here is a regression the test must catch.
        mod.PROSCENIO_OT_draw_mesh_vertices._finish(stub, ctx, cancel=True)  # type: ignore[arg-type]
        assert is_running("manual_draw") is False
    finally:
        mark_stopped("manual_draw")


def test_finish_survives_a_closed_window(automesh_fixture, monkeypatch):
    """On the window-close cancel path context.window is None; _finish must still
    clear the guard AND run the overlay teardown - not AttributeError on
    cursor_set (which would skip the teardown and leak the draw handlers)."""
    from types import SimpleNamespace

    from proscenio.operators.automesh import (
        draw_mesh_vertices as mod,  # type: ignore[import-not-found]
    )
    from proscenio.operators.automesh._authoring_modal_guard import (  # type: ignore[import-not-found]
        is_running,
        mark_running,
        mark_stopped,
    )

    teardown_calls: list[bool] = []
    monkeypatch.setattr(mod, "unregister_overlay", lambda _h: teardown_calls.append(True))
    ctx = SimpleNamespace(window=None, window_manager=None)
    stub = SimpleNamespace(
        _handles={}, _session=None, _remove_statusbar=lambda: None, _tag_redraw=lambda _c: None
    )

    mark_running("manual_draw")
    try:
        mod.PROSCENIO_OT_draw_mesh_vertices._finish(stub, ctx, cancel=True)  # type: ignore[arg-type]
        assert is_running("manual_draw") is False
        assert teardown_calls == [True], "cursor_set on a None window aborted the teardown"
    finally:
        mark_stopped("manual_draw")


def test_empty_overlay_handles_has_every_key(automesh_fixture):
    """The shared empty-handles factory must cover every OverlayHandles key. The
    operators seed self._handles from it, and unregister_overlay walks the key
    set - a missing key (the historical 'outer_preview' gap) silently skips that
    handler's teardown, leaking it on cleanup."""
    from proscenio.core.bpy_helpers.automesh.authoring_overlay import (  # type: ignore[import-not-found]
        OverlayHandles,
        empty_overlay_handles,
    )

    handles = empty_overlay_handles()
    assert set(handles) == set(OverlayHandles.__annotations__)
    assert all(value is None for value in handles.values())


def test_register_manual_draw_overlay_rolls_back_on_partial_failure(automesh_fixture, monkeypatch):
    """If a draw_handler_add midway through registration raises, the handlers
    already added must be removed before the error propagates - a partial set
    left registered leaks GPU draw handlers for the rest of the session."""
    from proscenio.core.bpy_helpers.automesh import (  # type: ignore[import-not-found]
        authoring_overlay as ov,
    )

    added: list[object] = []
    removed: list[object] = []
    state = {"n": 0}

    def fake_add(_func: object, _args: object, _region: object, _event: object) -> object:
        state["n"] += 1
        if state["n"] == 2:  # first add (triangulation) lands, second (live_preview) fails
            raise RuntimeError("simulated GPU handler failure")
        handle = object()
        added.append(handle)
        return handle

    monkeypatch.setattr(ov.bpy.types.SpaceView3D, "draw_handler_add", fake_add)
    monkeypatch.setattr(
        ov.bpy.types.SpaceView3D, "draw_handler_remove", lambda h, _region: removed.append(h)
    )

    with pytest.raises(RuntimeError, match="simulated"):
        ov.register_manual_draw_overlay(
            triangulation=[((0.0, 0.0), (1.0, 0.0))],
            live_preview_ref={},
            tooltip_mouse_ref=[(0, 0)],
            tooltip_text_ref=[""],
            tooltip_color_ref=[(0.0, 0.0, 0.0, 1.0)],
        )
    assert added, "test did not exercise a partial registration"
    assert removed == added, "partial overlay registration leaked the added handlers"


def test_finish_removes_registered_overlay_handles(automesh_fixture, monkeypatch):
    """The invoke setup-failure path now routes through _finish (mirroring the
    automesh modal): _finish must remove every overlay handler it holds. Guards
    the leak where a failed setup returned CANCELLED with the draw handlers the
    earlier _register_overlay added still live. The full modal invoke is not
    headless-testable, so this exercises the _finish teardown the except calls."""
    from types import SimpleNamespace

    from proscenio.core.bpy_helpers.automesh import (  # type: ignore[import-not-found]
        authoring_overlay as ov,
    )
    from proscenio.operators.automesh import (  # type: ignore[import-not-found]
        draw_mesh_vertices as mod,
    )

    removed: list[object] = []
    monkeypatch.setattr(
        ov.bpy.types.SpaceView3D, "draw_handler_remove", lambda h, _r: removed.append(h)
    )
    handle = object()
    handles = ov.empty_overlay_handles()
    handles["live_preview"] = handle  # a handler a partial setup had registered
    ctx = SimpleNamespace(window=None, window_manager=None)
    stub = SimpleNamespace(
        _handles=handles, _session=None, _remove_statusbar=lambda: None, _tag_redraw=lambda _c: None
    )

    mod.PROSCENIO_OT_draw_mesh_vertices._finish(stub, ctx, cancel=True)  # type: ignore[arg-type]
    assert removed == [handle], "finish left the registered overlay handler leaked"


def test_authoring_modal_guard_tracks_running_state(automesh_fixture):
    """The guard drives the toggle (button -> 'Exit') + mutual exclusivity: a
    marked-running modal reads as running to itself (is_running) and as the
    'other' to its sibling (other_running). The operator invoke turns a re-invoke
    while is_running into the Exit handshake (CANCELLED); the live modal flow is
    not headless-testable, so the guard contract stands in for it."""
    from proscenio.operators.automesh._authoring_modal_guard import (  # type: ignore[import-not-found]
        is_running,
        mark_running,
        mark_stopped,
        other_running,
    )

    assert is_running("manual_draw") is False
    mark_running("manual_draw")
    try:
        assert is_running("manual_draw") is True  # toggle: button shows "Exit"
        assert other_running("automesh") is True  # sibling poll refuses
        assert other_running("manual_draw") is False  # not the other to itself
    finally:
        mark_stopped("manual_draw")
    assert is_running("manual_draw") is False


def test_output_pins_manual_outer_and_folds_the_provisional_chain(automesh_fixture):
    """`_output` is the StageOutput shared by APPLY + the live preview. Drive it on
    a plain _Probe (a bpy.types.Operator subclass cannot be instantiated in 5.1):
    it must flag outer_is_manual, keep the committed strokes, and fold an
    in-progress FOLD click-chain (>= 2 verts) in as a provisional stroke so the
    preview updates as the fold is built."""
    from proscenio.operators.automesh.draw_mesh_vertices import (  # type: ignore[import-not-found]
        PROSCENIO_OT_draw_mesh_vertices as OP,
    )

    class _Probe:
        _output = OP._output  # method stolen by reference; state set per instance

    probe = _Probe()
    probe._user_strokes = [{"kind": "point", "points": [(0.5, 0.5)]}]
    probe._fold_chain = [(0.1, 0.1), (0.9, 0.9)]  # >= 2 verts -> provisional stroke
    probe._fold_subdivs = [0]
    ring = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]

    out = probe._output(ring)
    assert out.outer == ring
    assert out.outer_is_manual is True
    assert out.user_strokes[0]["kind"] == "point", "committed stroke dropped"
    assert any(
        s["kind"] == "stroke" for s in out.user_strokes[1:]
    ), "in-progress fold chain did not ride in as a provisional stroke"

    # A chain shorter than 2 verts contributes no provisional stroke.
    probe._fold_chain = [(0.1, 0.1)]
    assert len(probe._output(ring).user_strokes) == 1
