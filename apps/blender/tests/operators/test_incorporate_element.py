"""Headless tests for Incorporate as Element.

Runs INSIDE Blender via ``run_operator_tests.py``. A hand-authored Blender mesh
carries no Proscenio element data; the operator adopts it as a Mesh or Sprite,
defaulting Sprite for a single quad and Mesh otherwise, and stamps the
proscenio_type marker the panel + poll key on.
"""

from __future__ import annotations

import bpy

_QUAD_VERTS = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 1.0), (0.0, 0.0, 1.0)]
_QUAD_FACES = [(0, 1, 2, 3)]


def _make_mesh_object(name: str, verts: list, faces: list) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj


def test_incorporate_quad_defaults_to_sprite(automesh_fixture):
    obj = _make_mesh_object("plain_quad", _QUAD_VERTS, _QUAD_FACES)
    result = bpy.ops.proscenio.incorporate_element("INVOKE_DEFAULT")
    assert "FINISHED" in result
    assert obj.proscenio.element_type == "sprite"
    assert (obj.proscenio.hframes, obj.proscenio.vframes) == (1, 1)
    # The Custom Property marker is stamped, so the panel + poll no longer
    # treat it as an unincorporated mesh.
    assert obj.get("proscenio_type") == "sprite"


def test_incorporate_dense_mesh_defaults_to_mesh(automesh_fixture):
    # 5 verts / 2 faces is not a single quad, so the heuristic picks Mesh.
    verts = [*_QUAD_VERTS, (2.0, 0.0, 0.5)]
    faces = [(0, 1, 2, 3), (1, 4, 2)]
    obj = _make_mesh_object("dense", verts, faces)
    result = bpy.ops.proscenio.incorporate_element("INVOKE_DEFAULT")
    assert "FINISHED" in result
    assert obj.proscenio.element_type == "mesh"
    assert obj.get("proscenio_type") == "mesh"


def test_incorporate_respects_an_explicit_mesh_choice(automesh_fixture):
    # A quad would default to Sprite; an explicit element_type overrides it
    # (the redo-panel override path, EXEC without the invoke heuristic).
    obj = _make_mesh_object("forced_mesh", _QUAD_VERTS, _QUAD_FACES)
    result = bpy.ops.proscenio.incorporate_element(element_type="mesh")
    assert "FINISHED" in result
    assert obj.proscenio.element_type == "mesh"
    assert obj.get("proscenio_type") == "mesh"
