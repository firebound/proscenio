"""Headless test for the export texture bundle.

Runs INSIDE Blender via ``run_operator_tests.py``. PSD-imported assets live
in images/ and _spritesheets/ subfolders, but the .proscenio references
textures by bare filename and the Godot importer resolves siblings only.
The bundle copies every referenced texture next to the .proscenio so the
imports resolve. The scene is built directly so the test needs no on-disk
.blend or a full export run.
"""

from __future__ import annotations

from pathlib import Path

import bpy


def _png_image(name: str, path: Path) -> bpy.types.Image:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = bpy.data.images.new(name, width=2, height=2, alpha=True)
    img.filepath_raw = str(path)
    img.file_format = "PNG"
    img.save()
    return img


def _textured_mesh(name: str, image: bpy.types.Image) -> bpy.types.Object:
    mat = bpy.data.materials.new(f"{name}_mat")
    mat.use_nodes = True
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = image
    mesh = bpy.data.meshes.new(f"{name}_data")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(mat)
    return obj


def test_bundle_copies_subfolder_textures_beside_the_file(automesh_fixture, tmp_path):
    from proscenio.exporters.godot.writer.bundle import (  # type: ignore[import-not-found]
        bundle_textures,
    )

    image = _png_image("torso", tmp_path / "images" / "torso.png")
    obj = _textured_mesh("torso", image)
    dest = tmp_path / "export"
    dest.mkdir()

    result = bundle_textures([obj], dest)

    assert "torso.png" in result.copied
    assert (dest / "torso.png").exists(), "referenced texture did not land beside the file"


def test_bundle_skips_a_texture_already_beside_the_file(automesh_fixture, tmp_path):
    from proscenio.exporters.godot.writer.bundle import (  # type: ignore[import-not-found]
        bundle_textures,
    )

    dest = tmp_path / "export"
    dest.mkdir()
    image = _png_image("hat", dest / "hat.png")  # already a sibling of the file
    obj = _textured_mesh("hat", image)

    result = bundle_textures([obj], dest)

    assert "hat.png" in result.skipped
    assert "hat.png" not in result.copied


def test_bundle_flags_two_sources_sharing_one_filename(automesh_fixture, tmp_path):
    from proscenio.exporters.godot.writer.bundle import (  # type: ignore[import-not-found]
        bundle_textures,
    )

    # Two distinct images from different folders resolve to the same bare name.
    # Godot resolves siblings by name, so only one can land; the collision must
    # be recorded, not silently dropped.
    a = _png_image("torso_a", tmp_path / "images" / "torso.png")
    b = _png_image("torso_b", tmp_path / "extra" / "torso.png")
    obj_a = _textured_mesh("figure_a", a)
    obj_b = _textured_mesh("figure_b", b)
    dest = tmp_path / "export"
    dest.mkdir()

    result = bundle_textures([obj_a, obj_b], dest)

    assert "torso.png" in result.collisions
    assert result.copied.count("torso.png") == 1, "both sources bundled under one name"
