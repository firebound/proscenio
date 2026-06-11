"""Headless tests for keyframing the active slot attachment.

Runs INSIDE Blender via ``run_operator_tests.py``. Keying the slot's active
attachment is the format's standard part-swap mechanism: the operator sets
``proscenio_slot_index`` to the chosen attachment's writer-order index and
inserts a constant-interpolation keyframe, which ``build_slot_animations``
projects into a ``slot_attachment`` track. These tests pin the operator to that
writer contract so a key authored in Blender is exactly the swap exported to
Godot.
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


def _slot_index_fcurve(empty: bpy.types.Object):
    from proscenio.core._shared.cp_keys import (  # type: ignore[import-not-found]
        PROSCENIO_SLOT_INDEX,
    )
    from proscenio.exporters.godot.writer.animations import (  # type: ignore[import-not-found]
        action_fcurves,
    )

    action = empty.animation_data.action
    target = f'["{PROSCENIO_SLOT_INDEX}"]'
    return next((fc for fc in action_fcurves(action) if fc.data_path == target), None)


def test_keyframe_writes_the_writer_order_index(automesh_fixture):
    empty, _sword, axe = _make_slot_with_two_attachments()
    attachments = [c.name for c in empty.children if c.type == "MESH"]
    expected_index = attachments.index(axe)

    bpy.context.scene.frame_set(5)
    result = bpy.ops.proscenio.keyframe_slot_attachment(attachment_name=axe)
    assert "FINISHED" in result

    fcurve = _slot_index_fcurve(empty)
    assert fcurve is not None, "operator left no proscenio_slot_index fcurve"
    keyed = [(round(kp.co.x, 3), round(kp.co.y, 3)) for kp in fcurve.keyframe_points]
    detail = f"expected index {expected_index} keyed at frame 5, got {keyed}"
    assert (5.0, float(expected_index)) in keyed, detail


def test_keyframe_uses_constant_interpolation(automesh_fixture):
    empty, _sword, axe = _make_slot_with_two_attachments()
    bpy.context.scene.frame_set(3)
    bpy.ops.proscenio.keyframe_slot_attachment(attachment_name=axe)

    fcurve = _slot_index_fcurve(empty)
    assert fcurve is not None
    all_constant = all(kp.interpolation == "CONSTANT" for kp in fcurve.keyframe_points)
    assert all_constant, "an integer attachment index must hard-cut, not tween"


def test_keyframe_projects_to_the_writer_slot_attachment_track(automesh_fixture):
    from proscenio.exporters.godot.writer.slot_animations import (  # type: ignore[import-not-found]
        build_slot_animations,
    )

    empty, _sword, axe = _make_slot_with_two_attachments()
    bpy.context.scene.frame_set(7)
    bpy.ops.proscenio.keyframe_slot_attachment(attachment_name=axe)

    anims = build_slot_animations(bpy.context.scene)
    tracks = [t for a in anims for t in a.tracks if t.target == empty.name]
    assert tracks, "writer projected no slot_attachment track from the keyed swap"
    swap_keys = [k for t in tracks for k in t.keys]
    hit = any(k.attachment == axe and k.interp == "constant" for k in swap_keys)
    assert hit, f"keyed attachment '{axe}' did not reach the writer track: {swap_keys}"


def test_keyframe_rejects_a_non_attachment(automesh_fixture):
    empty, _sword, _axe = _make_slot_with_two_attachments()
    result = bpy.ops.proscenio.keyframe_slot_attachment(attachment_name="not_a_child")
    assert "CANCELLED" in result
    no_action = empty.animation_data is None or empty.animation_data.action is None
    assert no_action, "a rejected attachment must not author any keyframe"
