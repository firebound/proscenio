"""Headless tests for Incorporate as Element.

Runs INSIDE Blender via ``run_operator_tests.py``. A hand-authored Blender mesh
carries no Proscenio element data; the operator adopts it as a Mesh or Sprite -
the Auto choice picks Sprite for a single quad and Mesh otherwise - and stamps
the proscenio_type marker the panel + poll key on.
"""

from __future__ import annotations

import bpy

_QUAD_VERTS = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 1.0), (0.0, 0.0, 1.0)]
_QUAD_FACES = [(0, 1, 2, 3)]
_DENSE_VERTS = [*_QUAD_VERTS, (2.0, 0.0, 0.5)]
_DENSE_FACES = [(0, 1, 2, 3), (1, 4, 2)]


def _make_mesh_object(name: str, verts: list, faces: list) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj


def test_single_quad_heuristic_picks_sprite(automesh_fixture):
    from proscenio.operators.incorporate import _is_single_quad

    assert _is_single_quad(_make_mesh_object("quad", _QUAD_VERTS, _QUAD_FACES)) is True


def test_single_quad_heuristic_rejects_a_dense_mesh(automesh_fixture):
    from proscenio.operators.incorporate import _is_single_quad

    assert _is_single_quad(_make_mesh_object("dense", _DENSE_VERTS, _DENSE_FACES)) is False


def test_single_quad_heuristic_rejects_a_triangle_with_a_loose_vertex(automesh_fixture):
    from proscenio.operators.incorporate import _is_single_quad

    # Four verts and one face, but the face is a triangle (vert 3 is loose) -
    # a four-vert total is not enough; the face itself must be a quad.
    obj = _make_mesh_object("tri_loose", _QUAD_VERTS, [(0, 1, 2)])
    assert _is_single_quad(obj) is False


def test_auto_incorporates_a_quad_as_sprite_with_a_frame_grid(automesh_fixture):
    obj = _make_mesh_object("plain_quad", _QUAD_VERTS, _QUAD_FACES)
    result = bpy.ops.proscenio.incorporate_element()  # default choice is Auto
    assert "FINISHED" in result
    assert obj.proscenio.element_type == "sprite"
    assert (obj.proscenio.hframes, obj.proscenio.vframes) == (1, 1)
    # The Custom Property marker is stamped, so the panel + poll no longer
    # treat it as an unincorporated mesh.
    assert obj.get("proscenio_type") == "sprite"


def test_auto_incorporates_a_dense_mesh_as_mesh(automesh_fixture):
    obj = _make_mesh_object("dense", _DENSE_VERTS, _DENSE_FACES)
    result = bpy.ops.proscenio.incorporate_element()  # Auto, denser than a quad
    assert "FINISHED" in result
    assert obj.proscenio.element_type == "mesh"
    assert obj.get("proscenio_type") == "mesh"


def test_explicit_choice_overrides_the_quad_heuristic(automesh_fixture):
    # A quad would Auto-detect as Sprite; an explicit Mesh choice overrides it.
    obj = _make_mesh_object("forced_mesh", _QUAD_VERTS, _QUAD_FACES)
    result = bpy.ops.proscenio.incorporate_element(element_type="mesh")
    assert "FINISHED" in result
    assert obj.proscenio.element_type == "mesh"
    assert obj.get("proscenio_type") == "mesh"
