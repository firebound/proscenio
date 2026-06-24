"""In-Blender tests for the Custom-Property-backed PropertyGroup proxies.

Runs INSIDE Blender via ``run_operator_tests.py``. Since the storage split
(spec 037) each CP-canonical per-Object field stores in its ``proscenio_*``
Custom Property (idprop) and surfaces in the panel through a ``get``/``set``
PropertyGroup proxy. These tests pin the proxy <-> idprop round trip, the
frame clamp in the setter, and the Drive-from-Bone driver landing on the
idprop path - the live wiring the bpy-free suite cannot exercise.
"""

from __future__ import annotations

import bpy
import pytest


@pytest.fixture
def sprite_obj(automesh_fixture: None) -> bpy.types.Object:
    """A registered mesh whose proscenio proxies are live."""
    obj = bpy.data.objects["hand"]
    bpy.context.view_layer.objects.active = obj
    return obj


def test_enum_proxy_writes_the_idprop(sprite_obj: bpy.types.Object) -> None:
    sprite_obj.proscenio.element_type = "sprite"
    # The proxy stores nothing itself - the value lives in the idprop.
    assert sprite_obj["proscenio_type"] == "sprite"
    assert sprite_obj.proscenio.element_type == "sprite"


def test_idprop_write_reads_back_through_the_proxy(sprite_obj: bpy.types.Object) -> None:
    sprite_obj["proscenio_frame"] = 3
    sprite_obj["proscenio_hframes"] = 4
    sprite_obj["proscenio_vframes"] = 2
    assert sprite_obj.proscenio.frame == 3
    assert sprite_obj.proscenio.hframes == 4


def test_frame_setter_clamps_into_the_grid(sprite_obj: bpy.types.Object) -> None:
    sprite_obj.proscenio.hframes = 2
    sprite_obj.proscenio.vframes = 1  # 2 cells, last index 1
    sprite_obj.proscenio.frame = 5
    assert sprite_obj["proscenio_frame"] == 1


def test_shrinking_the_grid_pulls_frame_back_in(sprite_obj: bpy.types.Object) -> None:
    sprite_obj.proscenio.hframes = 4
    sprite_obj.proscenio.vframes = 2  # 8 cells, last index 7
    sprite_obj.proscenio.frame = 7
    assert sprite_obj["proscenio_frame"] == 7
    sprite_obj.proscenio.hframes = 2  # now 2x2 = 4 cells -> frame re-clamps to 3
    assert sprite_obj["proscenio_frame"] == 3


def test_bool_proxy_round_trips(sprite_obj: bpy.types.Object) -> None:
    sprite_obj.proscenio.is_slot = True
    assert bool(sprite_obj["proscenio_is_slot"]) is True
    sprite_obj.proscenio.is_slot = False
    assert bool(sprite_obj["proscenio_is_slot"]) is False


def test_drive_from_bone_lands_on_the_idprop_path(sprite_obj: bpy.types.Object) -> None:
    result = bpy.ops.proscenio.create_driver(
        armature_name="automesh.hand_rig",
        bone_name="wrist",
        target_property="frame",
        source_axis="ROT_Y",
    )
    assert "FINISHED" in result
    paths = {fc.data_path for fc in sprite_obj.animation_data.drivers}
    assert '["proscenio_frame"]' in paths
    # The seeded idprop exists so the driver resolves.
    assert "proscenio_frame" in sprite_obj
