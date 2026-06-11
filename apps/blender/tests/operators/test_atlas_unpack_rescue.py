"""Headless tests for Unpack Atlas material-rename rescue.

Runs INSIDE Blender via ``run_operator_tests.py``. The pre-pack snapshot
stores the original material by name, so a rename between Apply and Unpack
broke the by-name lookup and dropped the material (restoring UVs only).
Apply now stamps an origin marker on the material; Unpack scans for it
when the by-name lookup misses, restoring the renamed original. The
snapshot Custom Property is constructed directly (it is exactly what Apply
writes) so the rescue is exercised without a packed-atlas manifest fixture.
"""

from __future__ import annotations

import json

import bpy


def _marked_material(name: str) -> bpy.types.Material:
    """A material stamped with the origin marker, as Apply leaves it."""
    from proscenio.core._shared.cp_keys import (  # type: ignore[import-not-found]
        PROSCENIO_ATLAS_ORIGIN_MARKER,
    )

    mat = bpy.data.materials.new(name)
    mat[PROSCENIO_ATLAS_ORIGIN_MARKER] = name
    return mat


def _obj_in_slot(obj_name: str, slot_mat: bpy.types.Material) -> bpy.types.Object:
    """A mesh object whose single material slot holds ``slot_mat``."""
    mesh = bpy.data.meshes.new(f"{obj_name}_mesh")
    obj = bpy.data.objects.new(obj_name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(slot_mat)
    return obj


def _set_pre_pack(obj: bpy.types.Object, material_name: str) -> None:
    from proscenio.core._shared.cp_keys import (  # type: ignore[import-not-found]
        PROSCENIO_PRE_PACK,
    )

    obj[PROSCENIO_PRE_PACK] = json.dumps(
        {"material": material_name, "image": "", "uv_layer_snapshot": ""}
    )


def _object_mode() -> None:
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def test_unpack_rescues_a_renamed_material(automesh_fixture):
    _object_mode()
    original = _marked_material("rescue_skin")
    atlas_dummy = bpy.data.materials.new("rescue_atlas_dummy")
    obj = _obj_in_slot("rescue_obj", atlas_dummy)
    _set_pre_pack(obj, "rescue_skin")

    original.name = "rescue_body"  # renamed between Apply and Unpack

    bpy.context.view_layer.objects.active = obj
    result = bpy.ops.proscenio.unpack_atlas()
    assert "FINISHED" in result

    restored = obj.data.materials[0]
    assert restored is original, "rescue did not restore the renamed original material"
    assert restored.name == "rescue_body"


def test_unpack_restores_by_name_without_rename(automesh_fixture):
    _object_mode()
    original = _marked_material("byname_skin")
    atlas_dummy = bpy.data.materials.new("byname_atlas_dummy")
    obj = _obj_in_slot("byname_obj", atlas_dummy)
    _set_pre_pack(obj, "byname_skin")

    bpy.context.view_layer.objects.active = obj
    result = bpy.ops.proscenio.unpack_atlas()
    assert "FINISHED" in result
    assert obj.data.materials[0] is original


def test_unpack_leaves_slot_when_material_is_gone(automesh_fixture):
    _object_mode()
    atlas_dummy = bpy.data.materials.new("gone_atlas_dummy")
    obj = _obj_in_slot("gone_obj", atlas_dummy)
    _set_pre_pack(obj, "this_material_never_existed")

    bpy.context.view_layer.objects.active = obj
    result = bpy.ops.proscenio.unpack_atlas()
    assert "FINISHED" in result
    # No name match and no marker to rescue: the UVs-only path leaves the slot.
    assert obj.data.materials[0] is atlas_dummy
