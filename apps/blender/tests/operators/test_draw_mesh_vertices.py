"""Headless tests for the Manual Draw operator (Draw with vertices, spec 070).

The modal click flow is not headless-testable; these cover registration, the
poll gate, and the mutual-exclusivity guard with the Automesh modal. The apply
path (manual outer -> mesh) is covered by
``test_automesh_authoring.test_apply_mesh_manual_outer_overrides_alpha_trace`` -
Manual Draw's apply runs the same ``apply_mesh`` with ``outer_is_manual=True``.
"""

from __future__ import annotations

import bpy


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
