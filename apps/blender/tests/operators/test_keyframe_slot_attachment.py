"""Headless tests for keyframing the active slot attachment (spec 079).

Runs INSIDE Blender via ``run_operator_tests.py``. The slot swap is now authored
as direct visibility keyframes on the attachment meshes: "show only this
attachment" keys ``hide_render`` + ``hide_viewport`` (hard cut) on every sibling
- the chosen one shown, the rest hidden - on the animation the swap follows.
``build_slot_animations`` collapses those per-mesh visibility keys back into one
exclusive ``slot_attachment`` track. These tests pin the operator to that writer
contract so a key authored in Blender is exactly the swap exported to Godot.
"""

from __future__ import annotations

import bpy


def _box_mesh(name: str) -> bpy.types.Mesh:
    coords = [(x, y, z) for x in (-1.0, 1.0) for y in (-1.0, 1.0) for z in (-1.0, 1.0)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(coords, [], [])
    mesh.update()
    return mesh


def _new_mesh_object(name: str, location: tuple[float, float, float]) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, _box_mesh(name + "_m"))
    obj.location = location
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _make_slot_with_two_attachments() -> tuple[bpy.types.Object, str, str]:
    """Build a slot Empty wrapping two MESH attachments via the create operator."""
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for other in list(bpy.context.selected_objects):
        other.select_set(False)
    sword = _new_mesh_object("sword", (0.0, 0.0, 0.0))
    axe = _new_mesh_object("axe", (0.0, 0.0, 1.0))
    bpy.context.view_layer.update()
    sword.select_set(True)
    axe.select_set(True)
    bpy.context.view_layer.objects.active = sword
    bpy.ops.proscenio.create_slot()
    empty = bpy.context.view_layer.objects.active
    return empty, sword.name, axe.name


def _own_fcurve(obj: bpy.types.Object, data_path: str):
    from proscenio.core._shared.action_fcurves import (  # type: ignore[import-not-found]
        object_action_fcurves,
    )

    return next((fc for fc in object_action_fcurves(obj) if fc.data_path == data_path), None)


def _hide_render_at(obj: bpy.types.Object, frame: float) -> float | None:
    fcurve = _own_fcurve(obj, "hide_render")
    if fcurve is None:
        return None
    return next(
        (round(kp.co.y, 3) for kp in fcurve.keyframe_points if round(kp.co.x, 3) == frame),
        None,
    )


def _slot_track_keys(empty: bpy.types.Object) -> list:
    from proscenio.exporters.godot.writer.slot_animations import (  # type: ignore[import-not-found]
        build_slot_animations,
    )

    anims = build_slot_animations(bpy.context.scene)
    return [k for a in anims for t in a.tracks if t.target == empty.name for k in t.keys]


def test_keyframe_shows_only_the_chosen_attachment(automesh_fixture):
    _empty, sword, axe = _make_slot_with_two_attachments()
    bpy.context.scene.frame_set(5)
    result = bpy.ops.proscenio.keyframe_slot_attachment(attachment_name=axe)
    assert "FINISHED" in result

    axe_obj = bpy.data.objects[axe]
    sword_obj = bpy.data.objects[sword]
    # hide_render is the export truth: chosen shown (0.0), sibling hidden (1.0).
    assert _hide_render_at(axe_obj, 5.0) == 0.0, "chosen attachment must be shown"
    assert _hide_render_at(sword_obj, 5.0) == 1.0, "the sibling must be hidden"
    # hide_viewport is mirrored so the viewport preview matches the export.
    assert _own_fcurve(axe_obj, "hide_viewport") is not None
    assert _own_fcurve(sword_obj, "hide_viewport") is not None


def test_keyframe_uses_constant_interpolation(automesh_fixture):
    _empty, sword, axe = _make_slot_with_two_attachments()
    bpy.context.scene.frame_set(3)
    bpy.ops.proscenio.keyframe_slot_attachment(attachment_name=axe)

    for name in (axe, sword):
        obj = bpy.data.objects[name]
        for path in ("hide_render", "hide_viewport"):
            fcurve = _own_fcurve(obj, path)
            assert fcurve is not None, f"{name} left no {path} fcurve"
            all_constant = all(kp.interpolation == "CONSTANT" for kp in fcurve.keyframe_points)
            assert all_constant, f"{name}.{path} must hard-cut, not tween"


def test_keyframe_projects_to_the_writer_slot_attachment_track(automesh_fixture):
    empty, _sword, axe = _make_slot_with_two_attachments()
    bpy.context.scene.frame_set(7)
    bpy.ops.proscenio.keyframe_slot_attachment(attachment_name=axe)

    keys = _slot_track_keys(empty)
    assert keys, "writer projected no slot_attachment track from the keyed swap"
    hit = any(k.attachment == axe and k.interp == "constant" for k in keys)
    assert hit, f"keyed attachment '{axe}' did not reach the writer track: {keys}"


def test_hide_all_keys_the_none_state(automesh_fixture):
    from proscenio.exporters.godot.writer.slot_animations import (  # type: ignore[import-not-found]
        NONE_ATTACHMENT,
    )

    empty, _sword, _axe = _make_slot_with_two_attachments()
    bpy.context.scene.frame_set(4)
    result = bpy.ops.proscenio.keyframe_slot_attachment(hide_all=True)
    assert "FINISHED" in result

    keys = _slot_track_keys(empty)
    assert keys, "the (none) state produced no slot_attachment key"
    all_none = all(k.attachment == NONE_ATTACHMENT for k in keys)
    assert all_none, f"hiding every attachment must key the (none) state, got {keys}"


def test_keyframe_override_targets_the_named_animation(automesh_fixture):
    """The override picker binds the swap into a specific animation (D3)."""
    empty, _sword, axe = _make_slot_with_two_attachments()
    bpy.context.scene.frame_set(6)
    bpy.ops.proscenio.keyframe_slot_attachment(attachment_name=axe, animation_name="attack")

    from proscenio.exporters.godot.writer.slot_animations import (  # type: ignore[import-not-found]
        build_slot_animations,
    )

    anims = build_slot_animations(bpy.context.scene)
    slot_names = {a.name for a in anims if any(t.target == empty.name for t in a.tracks)}
    assert slot_names == {"attack"}, f"swap must follow the named animation, got {slot_names}"


def test_keyframe_rejects_a_non_attachment(automesh_fixture):
    _empty, sword, axe = _make_slot_with_two_attachments()
    result = bpy.ops.proscenio.keyframe_slot_attachment(attachment_name="not_a_child")
    assert "CANCELLED" in result
    # A rejected swap must not author any keyframe on any sibling.
    for name in (axe, sword):
        obj = bpy.data.objects[name]
        clean = obj.animation_data is None or obj.animation_data.action is None
        assert clean, f"rejected swap left animation data on {name}"


def test_converter_migrates_legacy_index_keys_to_visibility(automesh_fixture):
    """The one-shot migration reads a legacy proscenio_slot_index track and
    re-authors it as attachment visibility, clearing the legacy idprop."""
    empty, _sword, axe = _make_slot_with_two_attachments()
    order = [c.name for c in empty.children if c.type == "MESH"]

    empty.animation_data_create()
    empty.animation_data.action = bpy.data.actions.new("legacy_swing")
    empty["proscenio_slot_index"] = order.index(axe)
    empty.keyframe_insert(data_path='["proscenio_slot_index"]', frame=5)
    bpy.context.view_layer.objects.active = empty

    result = bpy.ops.proscenio.convert_slot_index_to_visibility()
    assert "FINISHED" in result

    keys = _slot_track_keys(empty)
    assert keys, "the converter produced no visibility-derived slot track"
    assert any(k.attachment == axe for k in keys), f"index -> '{axe}' not migrated: {keys}"
    assert "proscenio_slot_index" not in empty, "the legacy idprop must be cleared"
