"""Headless tests for the attach-mesh-to-slot picker (spec 046).

The picker decouples the attach target from the active object: with
single-object selection you cannot have the slot active AND a mesh
selected at once, so the old add-selected path deadlocked.
"""

from __future__ import annotations

import bpy


def _new_mesh(name: str) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)], [], [(0, 1, 2)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _new_slot(name: str) -> bpy.types.Object:
    empty = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(empty)
    empty.proscenio.is_slot = True
    return empty


def _activate_only(obj: bpy.types.Object) -> None:
    for other in list(bpy.context.selected_objects):
        other.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def test_attaches_named_mesh_with_only_slot_active(automesh_fixture):
    slot = _new_slot("pick_slot")
    mesh = _new_mesh("pick_mesh")
    # The deadlock: only the slot is active/selected, no mesh selected.
    _activate_only(slot)

    assert bpy.ops.proscenio.attach_mesh_to_slot.poll() is True
    result = bpy.ops.proscenio.attach_mesh_to_slot(mesh_name="pick_mesh")

    assert "FINISHED" in result
    assert mesh.parent is slot


def test_cancels_when_name_is_not_a_mesh(automesh_fixture):
    slot = _new_slot("pick_slot2")
    _activate_only(slot)

    result = bpy.ops.proscenio.attach_mesh_to_slot(mesh_name="pick_slot2")  # the slot itself

    assert "CANCELLED" in result


def test_poll_false_without_active_slot(automesh_fixture):
    mesh = _new_mesh("lonely_mesh")
    _activate_only(mesh)

    assert bpy.ops.proscenio.attach_mesh_to_slot.poll() is False
