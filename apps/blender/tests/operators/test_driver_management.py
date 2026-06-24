"""Headless tests for the element-driver management list + remove operator.

Runs INSIDE Blender via ``run_operator_tests.py``. Covers the spec 049 driver
management surface: reading the sprite's proscenio.* drivers into list rows
(data path + label + source bone) and the remove operator that drops one.
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


def test_driver_rows_list_proscenio_drivers(automesh_fixture):
    from proscenio.core.bpy_helpers.armature.driver_list import proscenio_driver_rows

    obj = _activate("hand")
    bpy.ops.proscenio.create_driver(
        armature_name="automesh.hand_rig",
        bone_name="wrist",
        target_property="region_x",
        source_axis="ROT_Y",
    )
    bpy.ops.proscenio.create_driver(
        armature_name="automesh.hand_rig",
        bone_name="palm",
        target_property="frame",
        source_axis="ROT_Y",
    )

    rows = proscenio_driver_rows(obj)
    by_path = {row.data_path: row for row in rows}

    assert '["proscenio_region_x"]' in by_path
    assert '["proscenio_frame"]' in by_path
    assert by_path['["proscenio_region_x"]'].label == "Region X"
    assert by_path['["proscenio_region_x"]'].bone == "wrist"
    assert by_path['["proscenio_frame"]'].bone == "palm"


def test_remove_driver_drops_one_leaving_the_rest(automesh_fixture):
    from proscenio.core.bpy_helpers.armature.driver_list import proscenio_driver_rows

    obj = _activate("hand")
    bpy.ops.proscenio.create_driver(
        armature_name="automesh.hand_rig",
        bone_name="wrist",
        target_property="region_x",
        source_axis="ROT_Y",
    )
    bpy.ops.proscenio.create_driver(
        armature_name="automesh.hand_rig",
        bone_name="palm",
        target_property="frame",
        source_axis="ROT_Y",
    )

    result = bpy.ops.proscenio.remove_driver(data_path='["proscenio_region_x"]')

    assert "FINISHED" in result
    remaining = {row.data_path for row in proscenio_driver_rows(obj)}
    assert '["proscenio_region_x"]' not in remaining
    assert '["proscenio_frame"]' in remaining


def test_remove_driver_cancels_when_absent(automesh_fixture):
    _activate("hand")

    result = bpy.ops.proscenio.remove_driver(data_path='["proscenio_region_w"]')

    assert "CANCELLED" in result


def test_remove_driver_rejects_non_proscenio_path(automesh_fixture):
    _activate("hand")

    # A non-proscenio path must be refused so the operator cannot strip an
    # unrelated driver when called directly.
    result = bpy.ops.proscenio.remove_driver(data_path="location")

    assert "CANCELLED" in result
