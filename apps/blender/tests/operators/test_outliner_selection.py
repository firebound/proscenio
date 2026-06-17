"""Headless tests for Outliner selection correctness (spec 043).

Runs INSIDE Blender via ``run_operator_tests.py``. Covers the three
headless-provable behaviors:

- the stale-row crash guard: clicking a row whose object is in
  ``bpy.data.objects`` but not linked into the view layer warns and
  cancels instead of raising ``RuntimeError: ... not in View Layer``;
- the shared identity->source-index helper used by both the click path
  and the viewport-follow handler;
- the viewport-follow sync: making a Proscenio-relevant object active
  moves the Outliner highlight, while a non-Proscenio active object
  (camera/light) leaves it untouched.

The visual highlight under sort/filter is GUI-only (BL-OUTLN-06 smoke).
"""

from __future__ import annotations

import bpy


def _mesh_obj(name: str, *, link: bool = True) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)], [], [(0, 1, 2)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    if link:
        bpy.context.scene.collection.objects.link(obj)
    return obj


def _camera_obj(name: str) -> bpy.types.Object:
    cam = bpy.data.cameras.new(name + "_cam")
    obj = bpy.data.objects.new(name, cam)
    bpy.context.scene.collection.objects.link(obj)
    return obj


# --- stale-row crash guard ------------------------------------------------


def test_select_outliner_object_cancels_when_absent_from_view_layer(automesh_fixture):
    # An object created in bpy.data but never linked into a collection is
    # in bpy.data.objects (so it can appear as an Outliner row) but not in
    # the view layer - the classic post-delete / post-undo state.
    _mesh_obj("ghost_row", link=False)
    assert bpy.context.view_layer.objects.get("ghost_row") is None

    result = bpy.ops.proscenio.select_outliner_object(obj_name="ghost_row")

    assert "CANCELLED" in result, "clicking a stale row must warn + cancel, not raise"


def test_select_outliner_object_selects_when_in_view_layer(automesh_fixture):
    obj = _mesh_obj("real_row", link=True)
    bpy.context.view_layer.update()

    result = bpy.ops.proscenio.select_outliner_object(obj_name="real_row")

    assert "FINISHED" in result
    assert bpy.context.view_layer.objects.active is obj
    assert obj.select_get() is True


# --- multi-select: Shift extends, Ctrl toggles ----------------------------


def test_plain_click_replaces_the_selection(automesh_fixture):
    a = _mesh_obj("ms_replace_a")
    b = _mesh_obj("ms_replace_b")
    bpy.context.view_layer.update()
    bpy.ops.proscenio.select_outliner_object(obj_name="ms_replace_a")

    # A plain click on b (no extend/toggle) clears a and selects only b.
    bpy.ops.proscenio.select_outliner_object(obj_name="ms_replace_b")

    assert b.select_get() is True
    assert a.select_get() is False
    assert bpy.context.view_layer.objects.active is b


def test_extend_keeps_the_prior_selection(automesh_fixture):
    a = _mesh_obj("ms_ext_a")
    b = _mesh_obj("ms_ext_b")
    bpy.context.view_layer.update()
    bpy.ops.proscenio.select_outliner_object(obj_name="ms_ext_a")

    # Shift-click (extend=True) adds b without dropping a.
    bpy.ops.proscenio.select_outliner_object(obj_name="ms_ext_b", extend=True)

    assert a.select_get() is True
    assert b.select_get() is True
    assert bpy.context.view_layer.objects.active is b


def test_toggle_deselects_an_already_selected_row(automesh_fixture):
    a = _mesh_obj("ms_tog_a")
    b = _mesh_obj("ms_tog_b")
    bpy.context.view_layer.update()
    bpy.ops.proscenio.select_outliner_object(obj_name="ms_tog_a")
    bpy.ops.proscenio.select_outliner_object(obj_name="ms_tog_b", extend=True)

    # Ctrl-click (toggle=True) on b, already selected, deselects only b.
    bpy.ops.proscenio.select_outliner_object(obj_name="ms_tog_b", toggle=True)

    assert b.select_get() is False
    assert a.select_get() is True


def test_toggle_adds_an_unselected_row(automesh_fixture):
    a = _mesh_obj("ms_toggle_on_a")
    b = _mesh_obj("ms_toggle_on_b")
    bpy.context.view_layer.update()
    bpy.ops.proscenio.select_outliner_object(obj_name="ms_toggle_on_a")

    # Ctrl-click on b, not yet selected, adds it and makes it active.
    bpy.ops.proscenio.select_outliner_object(obj_name="ms_toggle_on_b", toggle=True)

    assert a.select_get() is True
    assert b.select_get() is True
    assert bpy.context.view_layer.objects.active is b


# --- identity -> source-index helper --------------------------------------


def test_source_index_for_name_returns_position(automesh_fixture):
    from proscenio.core.outliner_view import source_index_for_name

    names = [o.name for o in bpy.data.objects]
    wanted = names[1] if len(names) > 1 else names[0]
    expected = names.index(wanted)

    assert source_index_for_name(bpy.data.objects, wanted) == expected


def test_source_index_for_name_none_when_absent(automesh_fixture):
    from proscenio.core.outliner_view import source_index_for_name

    assert source_index_for_name(bpy.data.objects, "does_not_exist_xyz") is None


def test_is_outliner_relevant_true_for_mesh_false_for_camera(automesh_fixture):
    from proscenio.core.outliner_view import is_outliner_relevant

    mesh = _mesh_obj("rel_mesh")
    cam = _camera_obj("rel_cam")

    assert is_outliner_relevant(mesh) is True
    assert is_outliner_relevant(cam) is False


# --- viewport-follow sync -------------------------------------------------


def test_sync_outliner_follows_active_proscenio_object(automesh_fixture):
    from proscenio.core.outliner_view import source_index_for_name
    from proscenio.properties._handlers import sync_outliner_to_active_object

    obj = _mesh_obj("follow_me")
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = obj
    scene = bpy.context.scene
    # Seed a value guaranteed to differ from the target so the early-out
    # cannot make this a false pass - the write path must run.
    idx = source_index_for_name(bpy.data.objects, "follow_me")
    assert idx is not None
    scene.proscenio.active_outliner_index = idx + 1

    sync_outliner_to_active_object(scene)

    assert scene.proscenio.active_outliner_index == idx


def test_sync_outliner_ignores_non_proscenio_active(automesh_fixture):
    from proscenio.properties._handlers import sync_outliner_to_active_object

    cam = _camera_obj("ignore_cam")
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = cam
    scene = bpy.context.scene
    scene.proscenio.active_outliner_index = 3

    sync_outliner_to_active_object(scene)

    assert scene.proscenio.active_outliner_index == 3, "a camera must not move the highlight"


def test_sync_outliner_noop_when_already_correct(automesh_fixture):
    from proscenio.core.outliner_view import source_index_for_name
    from proscenio.properties._handlers import sync_outliner_to_active_object

    obj = _mesh_obj("already_active")
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = obj
    scene = bpy.context.scene
    idx = source_index_for_name(bpy.data.objects, "already_active")
    scene.proscenio.active_outliner_index = idx

    sync_outliner_to_active_object(scene)

    assert scene.proscenio.active_outliner_index == idx
