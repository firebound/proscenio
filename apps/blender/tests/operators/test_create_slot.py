"""Headless tests for slot placement (Path B) - geometry-center landing.

Runs INSIDE Blender via ``run_operator_tests.py``. The shipped ``create_slot``
wrote a world-space translation into the parent-LOCAL ``empty.location`` with no
``matrix_parent_inverse``, so a parented seed compounded the offset through the
parent matrix; and it used ``matrix_world.to_translation()`` (the object origin)
rather than the visible geometry center, so an unapplied-origin mesh placed the
slot away from its geometry. The fix writes the world-space geometry center
through ``empty.matrix_world`` after parenting, the same write-through pattern
``parent_keep_world`` applies to the wrapped attachments.
"""

from __future__ import annotations

import bpy
import pytest


def _box_mesh(name: str, center: tuple[float, float, float], half: float = 1.0) -> bpy.types.Mesh:
    """A box whose 8 corners sit at ``center`` +/- ``half`` in LOCAL space."""
    cx, cy, cz = center
    coords = [
        (cx + sx * half, cy + sy * half, cz + sz * half)
        for sx in (-1.0, 1.0)
        for sy in (-1.0, 1.0)
        for sz in (-1.0, 1.0)
    ]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(coords, [], [])
    mesh.update()
    return mesh


def _new_object(name: str, mesh: bpy.types.Mesh) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _select_only(objs: list[bpy.types.Object]) -> None:
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for other in list(bpy.context.selected_objects):
        other.select_set(False)
    for obj in objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


def test_parented_seed_slot_lands_at_geometry_center(automesh_fixture):
    # Parent at world (5,0,0); seed centered, placed at parent-local (1,0,0)
    # => seed world geometry center (6,0,0). The buggy path wrote that world
    # value into the empty's parent-LOCAL location, compounding to ~(11,0,0).
    parent = _new_object("slot_parent", _box_mesh("pm", (0.0, 0.0, 0.0)))
    parent.location = (5.0, 0.0, 0.0)
    seed = _new_object("slot_seed", _box_mesh("sm", (0.0, 0.0, 0.0)))
    seed.parent = parent
    seed.location = (1.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    _select_only([seed])
    result = bpy.ops.proscenio.create_slot()
    assert "FINISHED" in result
    bpy.context.view_layer.update()

    empty = bpy.context.view_layer.objects.active
    assert empty.proscenio.is_slot is True
    world = empty.matrix_world.to_translation()
    assert world.x == pytest.approx(6.0, abs=1e-4), "slot compounded through the parent matrix"
    assert world.y == pytest.approx(0.0, abs=1e-4)
    assert world.z == pytest.approx(0.0, abs=1e-4)


def test_unapplied_origin_slot_lands_at_geometry_not_origin(automesh_fixture):
    # Object origin at world (0,0,0) but geometry centered at local (3,0,0):
    # an unapplied origin. The buggy path used the origin (0,0,0); the fix uses
    # the geometry center (3,0,0).
    seed = _new_object("origin_seed", _box_mesh("om", (3.0, 0.0, 0.0)))
    seed.location = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    _select_only([seed])
    result = bpy.ops.proscenio.create_slot()
    assert "FINISHED" in result
    bpy.context.view_layer.update()

    empty = bpy.context.view_layer.objects.active
    world = empty.matrix_world.to_translation()
    assert world.x == pytest.approx(3.0, abs=1e-4), "slot landed at the object origin, not geometry"
    assert world.y == pytest.approx(0.0, abs=1e-4)
    assert world.z == pytest.approx(0.0, abs=1e-4)


def test_wrapped_attachment_keeps_world_transform(automesh_fixture):
    # The seed mesh must not move on screen when it is wrapped under the slot.
    seed = _new_object("keep_seed", _box_mesh("km", (2.0, 0.0, 0.0)))
    seed.location = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    before = seed.matrix_world.to_translation().copy()

    _select_only([seed])
    result = bpy.ops.proscenio.create_slot()
    assert "FINISHED" in result
    bpy.context.view_layer.update()

    after = seed.matrix_world.to_translation()
    assert after.x == pytest.approx(before.x, abs=1e-4)
    assert after.y == pytest.approx(before.y, abs=1e-4)
    assert after.z == pytest.approx(before.z, abs=1e-4)
