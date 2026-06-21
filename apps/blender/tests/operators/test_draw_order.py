"""Headless: Y Location (Draw Order) drives the object Y + the Re-space op.

Runs INSIDE Blender via ``run_operator_tests.py``. The order is a stored
integer that positions the object at ``order * spacing``; the writer reads the
integer (covered in ``tests/writer``). Here the bpy-coupled wiring is exercised
on real objects: the property update callback, the import tag, and the Re-space
operator.
"""

from __future__ import annotations

import bmesh
import bpy
import pytest

from .conftest import _load_addon_as_package

_QUAD = [(-0.5, 0.0, -0.5), (0.5, 0.0, -0.5), (0.5, 0.0, 0.5), (-0.5, 0.0, 0.5)]


@pytest.fixture
def addon() -> None:
    """Mount the addon (registers the operators) and start from an empty file."""
    _load_addon_as_package()
    bpy.ops.wm.read_homefile(use_empty=True)


def _quad(name: str) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(co) for co in _QUAD])
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _spacing() -> float:
    from proscenio.addon_prefs import y_location_spacing

    return y_location_spacing(bpy.context)


def test_setting_the_order_positions_the_object_in_y(addon: None) -> None:
    obj = _quad("torso")
    obj.proscenio.y_draw_order = 5
    assert obj.location.y == pytest.approx(5 * _spacing())


def test_negative_order_positions_in_front(addon: None) -> None:
    obj = _quad("front")
    obj.proscenio.y_draw_order = -2
    assert obj.location.y == pytest.approx(-2 * _spacing())


def test_import_tag_seeds_the_order_on_pg_and_cp(addon: None) -> None:
    from proscenio.importers.photoshop.planes import _tag_draw_order

    obj = _quad("imported")
    _tag_draw_order(obj, 3)
    # PG (panel + outliner) and CP (headless writer) both carry the order.
    assert obj.proscenio.y_draw_order == 3
    assert obj["proscenio_y_draw_order"] == 3


def test_respace_snaps_a_dragged_plane_back_onto_its_layer(addon: None) -> None:
    obj = _quad("dragged")
    obj["proscenio_type"] = "mesh"  # the op scans for elements by this CP
    obj.proscenio.y_draw_order = 3  # callback puts Y at 3 * spacing
    obj.location.y = 0.5  # manual drag off the layer
    bpy.ops.proscenio.respace_planes()
    assert obj.location.y == pytest.approx(3 * _spacing())


def test_respace_skips_slot_attached_meshes(addon: None) -> None:
    slot = bpy.data.objects.new("hand.slot", None)
    slot.proscenio.is_slot = True  # PG-first: the CP alone loses to the PG default
    bpy.context.scene.collection.objects.link(slot)
    obj = _quad("sword")
    obj["proscenio_type"] = "mesh"
    obj.parent = slot
    obj.location.y = 0.5  # slot owns placement - re-space must not touch it
    bpy.ops.proscenio.respace_planes()
    assert obj.location.y == pytest.approx(0.5)
