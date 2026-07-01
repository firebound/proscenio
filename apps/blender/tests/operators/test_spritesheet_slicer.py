"""Headless tests for the spritesheet preview slicer shader.

Runs INSIDE Blender via ``run_operator_tests.py``. Covers two edges:

- the slicer node graph wraps the ROW by V Frames (mirror of the column path's
  MODULO on H Frames) so an out-of-range frame wraps to the top rows instead of
  walking off the bottom of the sheet - matching the pure
  ``spritesheet_math.cell_offset_y``;
- removing the slicer drops the drivers it left on the material's NODE TREE
  (where node-socket drivers live), not the material's own animation_data.
"""

from __future__ import annotations

import bpy


def _material_with_image() -> bpy.types.Material:
    mat = bpy.data.materials.new("slicer_mat")
    mat.use_nodes = True
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.new("slice_img", width=4, height=4)
    return mat


def _mesh_with_material(mat: bpy.types.Material) -> bpy.types.Object:
    mesh = bpy.data.meshes.new("slice_mesh")
    obj = bpy.data.objects.new("slice_obj", mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(mat)
    return obj


def test_slicer_group_wraps_the_row_by_vframes(automesh_fixture) -> None:
    from proscenio.core.bpy_helpers.spritesheet.spritesheet_shader import (  # type: ignore[import-not-found]
        _SOCK_VFRAMES,
        ensure_slicer_group,
    )

    group = ensure_slicer_group(bpy.data.node_groups)

    def _fed_by_vframes(node: object) -> bool:
        socket = node.inputs[1]
        return bool(socket.is_linked and socket.links[0].from_socket.name == _SOCK_VFRAMES)

    modulos = [n for n in group.nodes if n.type == "MATH" and n.operation == "MODULO"]
    has_row_wrap = any(_fed_by_vframes(n) for n in modulos)
    assert has_row_wrap, "row path has no MODULO-by-V-Frames wrap (mirror of the column path)"


def test_removing_slicer_drops_its_node_tree_drivers(automesh_fixture) -> None:
    from proscenio.core.bpy_helpers.spritesheet.spritesheet_shader import (  # type: ignore[import-not-found]
        apply_slicer_to_material,
        remove_slicer_from_material,
    )

    mat = _material_with_image()
    obj = _mesh_with_material(mat)

    assert apply_slicer_to_material(mat, obj=obj, node_groups=bpy.data.node_groups)
    anim = mat.node_tree.animation_data
    drivers_on_tree = anim is not None and len(anim.drivers) > 0
    assert drivers_on_tree, "slicer drivers must live on the material's node tree"

    assert remove_slicer_from_material(mat)
    anim = mat.node_tree.animation_data
    remaining = 0 if anim is None else len(anim.drivers)
    assert remaining == 0, "slicer left orphan drivers on the node tree after removal"
