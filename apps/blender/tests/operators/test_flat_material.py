"""Headless tests for the flat / unlit import material + color management.

Runs INSIDE Blender via ``run_operator_tests.py``. Cutout art is flat 2D, so the
importer builds an unlit Emission material (no Principled BSDF / IOR sheen),
decodes the texture as sRGB, and switches the scene view transform to Standard,
so the viewport shows the source PNG color 1:1 instead of the AgX-washed
Principled look.
"""

from __future__ import annotations

from pathlib import Path

import bpy


def _make_png(tmp_path: Path) -> Path:
    img = bpy.data.images.new("flat_src", 2, 2, alpha=True)
    img.pixels = [0.82, 0.39, 0.46, 1.0] * 4  # one opaque colour, alpha 1
    path = tmp_path / "flat_src.png"
    img.filepath_raw = str(path)
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)  # so _attach_material loads it fresh from disk
    return path


def _mesh_object(name: str) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], [], [(0, 1, 2, 3)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def test_attach_material_is_unlit_emission(automesh_fixture, tmp_path):
    from proscenio.importers.photoshop.planes import _attach_material

    obj = _mesh_object("flat_obj")
    _attach_material(obj, _make_png(tmp_path))
    mat = obj.data.materials[0]
    types = {n.type for n in mat.node_tree.nodes}
    # Unlit: an Emission gated by the alpha, never the Principled BSDF (its IOR
    # Fresnel highlight was what washed the cutout out).
    assert "EMISSION" in types
    assert "BSDF_PRINCIPLED" not in types
    tex = next(n for n in mat.node_tree.nodes if n.type == "TEX_IMAGE")
    assert tex.image.colorspace_settings.name == "sRGB"


def test_import_sets_standard_view_transform(automesh_fixture):
    from proscenio.importers.photoshop import _apply_flat_color_management

    bpy.context.scene.view_settings.view_transform = "AgX"
    _apply_flat_color_management()
    assert bpy.context.scene.view_settings.view_transform == "Standard"
