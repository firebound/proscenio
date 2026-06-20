"""Headless: Apply Packed Atlas does not count a no-UV sprite as rewritten.

Runs INSIDE Blender via ``run_operator_tests.py``. ``_apply_to_object`` used to
return True unconditionally for an ``element_type == "sprite"`` object, even when
``_rewrite_uvs`` found no UV layer to remap - so a broken sprite (atlas material
relinked over un-remapped UVs) was reported as a successful rewrite. The method
now gates on the UV rewrite, so a UV-less sprite is reported as skipped.
"""

from __future__ import annotations

import bpy


def _sprite_mesh_without_uv(name: str) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(f"{name}_mesh")  # no UV layer
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.proscenio.element_type = "sprite"
    return obj


def test_sprite_without_uv_is_not_counted_as_rewritten(automesh_fixture: None) -> None:
    from proscenio.operators.atlas_pack.apply import PROSCENIO_OT_apply_packed_atlas as Op

    obj = _sprite_mesh_without_uv("no_uv_sprite")

    # A registered bpy Operator cannot be instantiated directly, so borrow the
    # real collaborator methods onto a plain stand-in and call the real
    # `_apply_to_object` unbound - this exercises the actual UV-rewrite path
    # (which returns False on the missing UV layer), not a mock.
    class _Caller:
        _rewrite_uvs = Op._rewrite_uvs
        _apply_sprite = Op._apply_sprite

    # Placement is untouched: _rewrite_uvs bails on the missing UV layer before
    # it reads the placement, so a bare sentinel is enough.
    assert Op._apply_to_object(_Caller(), obj, object(), 100, 100) is False
