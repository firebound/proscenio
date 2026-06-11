"""Headless writer test: a multi-face mesh exports every face, not just the first.

Runs INSIDE Blender via ``run_operator_tests.py``. Builds real meshes (no
.blend fixture) and drives the writer's ``build_element`` so the bpy matrix /
mesh-polygon path - the part pure pytest cannot exercise - is covered. Before
the multi-polygon fix the writer emitted only ``polygon_at(mesh, 0)``, so a
triangulated or multi-island mesh silently truncated to its first face.
"""

from __future__ import annotations

import bmesh
import bpy
import pytest

from .conftest import _load_addon_as_package

_QUAD_CORNERS = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 1.0), (0.0, 0.0, 1.0)]


@pytest.fixture
def addon() -> None:
    """Mount the addon and start from an empty file.

    Skips when the bundled ``proscenio_models`` predates the ``polygons``
    field - Blender installs the wheel from ``apps/blender/wheels/`` into an
    isolated site-packages, so a stale cached install would fail the emit
    rather than exercise it. Rebuild via
    ``uv build packages/models --wheel --out-dir apps/blender/wheels``.
    """
    _load_addon_as_package()
    from proscenio_models import MeshElement

    if "polygons" not in MeshElement.model_fields:
        pytest.skip("bundled proscenio_models predates the polygons field")
    bpy.ops.wm.read_homefile(use_empty=True)


def _new_mesh_object(name: str, faces: list[tuple[int, ...]]) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    verts = [bm.verts.new(co) for co in _QUAD_CORNERS]
    for face in faces:
        bm.faces.new([verts[i] for i in face])
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def test_multi_face_mesh_exports_every_face(addon: None) -> None:
    from proscenio.exporters.godot.writer.sprites import build_element

    # Quad split into two triangles sharing the 0->2 diagonal.
    obj = _new_mesh_object("blob", [(0, 1, 2), (0, 2, 3)])
    element = build_element(obj, {}, ppu=100.0)

    assert element.type == "mesh"
    assert len(element.polygon) == 4  # all four unique verts, not the first three
    assert element.polygons == [[0, 1, 2], [0, 2, 3]]


def test_single_face_mesh_omits_polygons(addon: None) -> None:
    from proscenio.exporters.godot.writer.sprites import build_element

    obj = _new_mesh_object("quad", [(0, 1, 2, 3)])
    element = build_element(obj, {}, ppu=100.0)

    assert len(element.polygon) == 4
    assert element.polygons is None  # single face keeps the field-less shape
