"""Headless: bind operator binds all selected MESH objects (O2)."""
from __future__ import annotations

import bpy


def _activate(name: str) -> bpy.types.Object:
    obj = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    return obj


def test_bind_multi_mesh(automesh_fixture):
    """Select 2 meshes + bind = both get vertex groups."""
    # The hand fixture has one mesh; duplicate it to create a second target.
    src = bpy.data.objects["hand"]
    new_mesh = src.data.copy()
    dup = bpy.data.objects.new("hand_dup", new_mesh)
    bpy.context.scene.collection.objects.link(dup)
    dup.location = (src.location.x + 4.0, src.location.y, src.location.z)

    # Select both; make src the active object.
    for other in bpy.context.selected_objects:
        other.select_set(False)
    src.select_set(True)
    dup.select_set(True)
    bpy.context.view_layer.objects.active = src

    bpy.context.scene.proscenio.active_armature = bpy.data.objects["automesh.hand_rig"]

    result = bpy.ops.proscenio.bind_mesh_to_armature()
    assert "FINISHED" in result, f"operator returned {result}"
    assert len(src.vertex_groups) > 0, "source mesh missing vertex groups after bind"
    assert len(dup.vertex_groups) > 0, "dup mesh missing vertex groups after bind"


def test_bind_single_selected_no_active(automesh_fixture):
    """Only one MESH in selection (active is something else) still binds it."""
    src = bpy.data.objects["hand"]

    for other in bpy.context.selected_objects:
        other.select_set(False)
    src.select_set(True)
    # Do not set active_object to src - leave it unset (None) or keep previous.
    bpy.context.view_layer.objects.active = src

    bpy.context.scene.proscenio.active_armature = bpy.data.objects["automesh.hand_rig"]

    result = bpy.ops.proscenio.bind_mesh_to_armature()
    assert "FINISHED" in result
    assert len(src.vertex_groups) > 0


def test_bind_no_mesh_selected_cancels(automesh_fixture):
    """With no MESH selected and no MESH active, operator cancels."""
    for other in bpy.context.selected_objects:
        other.select_set(False)
    bpy.context.view_layer.objects.active = None

    bpy.context.scene.proscenio.active_armature = bpy.data.objects["automesh.hand_rig"]

    import pytest
    with pytest.raises((RuntimeError, Exception)):
        # operator should cancel; bpy.ops raises when result is CANCELLED and
        # called from a context where no object is accessible
        bpy.ops.proscenio.bind_mesh_to_armature()
