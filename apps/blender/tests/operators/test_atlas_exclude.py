"""Headless test for the exclude-from-atlas pack filter.

Runs INSIDE Blender via ``run_operator_tests.py``. Pack Atlas walks every
sprite mesh unconditionally; a sprite flagged ``exclude_from_atlas`` should
keep its own texture and material instead of joining the shared atlas. The
filter that Pack applies is exercised directly so the assertion needs no
on-disk atlas write.
"""

from __future__ import annotations

import bpy


def _mesh_obj(name: str) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(f"{name}_data")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def test_excluded_mesh_is_not_packable(automesh_fixture):
    from proscenio.operators.atlas_pack.pack import (  # type: ignore[import-not-found]
        packable_atlas_meshes,
    )

    keep = _mesh_obj("keep_mesh")
    drop = _mesh_obj("drop_mesh")
    drop.proscenio.exclude_from_atlas = True

    names = {o.name for o in packable_atlas_meshes([keep, drop])}
    assert "keep_mesh" in names, "an unflagged mesh must stay packable"
    assert "drop_mesh" not in names, "an excluded mesh must drop out of the pack"


def test_unflagged_mesh_packable_by_default(automesh_fixture):
    from proscenio.operators.atlas_pack.pack import (  # type: ignore[import-not-found]
        packable_atlas_meshes,
    )

    obj = _mesh_obj("default_mesh")
    assert obj.proscenio.exclude_from_atlas is False
    names = {o.name for o in packable_atlas_meshes([obj])}
    assert "default_mesh" in names
