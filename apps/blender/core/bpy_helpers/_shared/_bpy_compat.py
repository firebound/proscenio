"""Shared stub-bug shims for the addon's writer + importer.

fake-bpy-module-latest ships PEP 561 stubs but omits ``__iter__`` and
``__getitem__`` declarations on the bpy_prop_collection wrappers
(SceneObjects, ArmatureBones, MeshVertices, etc). Those collections
ARE iterable and indexable at runtime; the stub generator just loses
the magic methods because they live on the C-level base class
``bpy_prop_collection`` which is not surfaced in the .pyi tree.

The shims here are the single place we acknowledge the gap. Each
helper takes the collection by Iterable / Sequence Protocol so the
call site stays readable, and casts internally so the stub-blind
region is one well-named function instead of a ``cast`` sprinkled at
every loop. Both the Godot writer (``exporters/godot/writer``) and the
Photoshop importer (``importers/photoshop``) consume these shims.

When fake-bpy fixes the upstream stubs, delete this module and inline
the iteration.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TypeVar, cast

import bpy

_T = TypeVar("_T")


def iter_objects(scene: bpy.types.Scene) -> Iterator[bpy.types.Object]:
    """Iterate ``scene.objects`` (stub omits __iter__ on SceneObjects)."""
    return iter(cast(Iterator[bpy.types.Object], scene.objects))


def iter_materials() -> Iterator[bpy.types.Material]:
    """Iterate ``bpy.data.materials`` (stub omits __iter__ on BlendDataMaterials)."""
    return iter(cast(Iterator[bpy.types.Material], bpy.data.materials))


def iter_actions() -> Iterator[bpy.types.Action]:
    """Iterate ``bpy.data.actions`` (stub omits __iter__ on BlendDataActions)."""
    return iter(cast(Iterator[bpy.types.Action], bpy.data.actions))


def iter_bones(armature: bpy.types.Armature) -> Iterator[bpy.types.Bone]:
    """Iterate ``armature.bones`` (stub omits __iter__ on ArmatureBones)."""
    return iter(cast(Iterator[bpy.types.Bone], armature.bones))


def iter_vertex_groups(obj: bpy.types.Object) -> Iterator[bpy.types.VertexGroup]:
    """Iterate ``obj.vertex_groups`` (stub omits __iter__ on VertexGroups)."""
    return iter(cast(Iterator[bpy.types.VertexGroup], obj.vertex_groups))


def vertex_at(mesh: bpy.types.Mesh, index: int) -> bpy.types.MeshVertex:
    """Subscript ``mesh.vertices[index]`` (stub omits __getitem__ on MeshVertices)."""
    return cast(bpy.types.MeshVertex, mesh.vertices[index])  # type: ignore[index]


def polygon_at(mesh: bpy.types.Mesh, index: int) -> bpy.types.MeshPolygon:
    """Subscript ``mesh.polygons[index]`` (stub omits __getitem__ on MeshPolygons)."""
    return cast(bpy.types.MeshPolygon, mesh.polygons[index])  # type: ignore[index]


def iter_polygons(mesh: bpy.types.Mesh) -> Iterator[bpy.types.MeshPolygon]:
    """Iterate ``mesh.polygons`` (stub omits __iter__ on MeshPolygons)."""
    return iter(cast(Iterator[bpy.types.MeshPolygon], mesh.polygons))


def vertex_group_at(obj: bpy.types.Object, index: int) -> bpy.types.VertexGroup:
    """Subscript ``obj.vertex_groups[index]`` (stub omits __getitem__ on VertexGroups)."""
    return cast(bpy.types.VertexGroup, obj.vertex_groups[index])  # type: ignore[index]


def iter_action_layers(action: bpy.types.Action) -> Iterator[bpy.types.ActionLayer]:
    """Iterate ``action.layers`` (stub omits __iter__ on ActionLayers)."""
    return iter(cast(Iterator[bpy.types.ActionLayer], action.layers))


def iter_action_strips(layer: bpy.types.ActionLayer) -> Iterator[bpy.types.ActionStrip]:
    """Iterate ``layer.strips`` (stub omits __iter__ on ActionStrips)."""
    return iter(cast(Iterator[bpy.types.ActionStrip], layer.strips))


def iter_shader_nodes(tree: bpy.types.NodeTree) -> Iterator[bpy.types.Node]:
    """Iterate ``tree.nodes`` (stub omits __iter__ on Nodes)."""
    return iter(cast(Iterator[bpy.types.Node], tree.nodes))


def iter_poly_vertices(poly: bpy.types.MeshPolygon) -> Iterator[int]:
    """Iterate ``poly.vertices`` (bpy_prop_array carries no Iterable in stub)."""
    return iter(cast(Iterator[int], poly.vertices))


def iter_poly_loop_indices(poly: bpy.types.MeshPolygon) -> Iterator[int]:
    """Iterate ``poly.loop_indices`` (bpy_prop_array carries no Iterable in stub)."""
    return iter(cast(Iterator[int], poly.loop_indices))


def iter_keyframe_points(
    fcurve: bpy.types.FCurve,
) -> Iterator[bpy.types.Keyframe]:
    """Iterate ``fcurve.keyframe_points`` (stub omits __iter__ on FCurveKeyframePoints)."""
    return iter(cast(Iterator[bpy.types.Keyframe], fcurve.keyframe_points))


def expect_mesh(obj: bpy.types.Object) -> bpy.types.Mesh:
    """Narrow ``obj.data`` to ``bpy.types.Mesh`` when ``obj.type == 'MESH'``.

    The stub types ``Object.data`` as a 12-way union over every ID datablock
    Blender allows on an object. Callers in the writer have already filtered
    on ``obj.type``; this helper just satisfies the type system by asserting
    the narrowing the runtime contract already guarantees.
    """
    data = obj.data
    if not isinstance(data, bpy.types.Mesh):
        raise TypeError(f"expected Mesh on object {obj.name!r}, got {type(data).__name__}")
    return data


def expect_armature(obj: bpy.types.Object) -> bpy.types.Armature:
    """Narrow ``obj.data`` to ``bpy.types.Armature`` when ``obj.type == 'ARMATURE'``."""
    data = obj.data
    if not isinstance(data, bpy.types.Armature):
        raise TypeError(f"expected Armature on object {obj.name!r}, got {type(data).__name__}")
    return data


def iter_blend_objects() -> Iterator[bpy.types.Object]:
    """Iterate ``bpy.data.objects`` (stub omits __iter__ on BlendDataObjects)."""
    return iter(cast(Iterator[bpy.types.Object], bpy.data.objects))


def material_by_name(name: str) -> bpy.types.Material | None:
    """Look up a material by name (stub omits ``.get`` on BlendDataMaterials)."""
    table = cast(dict[str, bpy.types.Material], bpy.data.materials)
    return table.get(name)


def uv_loop_at(layer: bpy.types.MeshUVLoopLayer, index: int) -> bpy.types.MeshUVLoop:
    """Subscript ``layer.data[index]`` (kept as a helper to mirror the other
    `*_at` shims and so the call sites read uniformly)."""
    return layer.data[index]


def first_uv_layer(mesh: bpy.types.Mesh) -> bpy.types.MeshUVLoopLayer | None:
    """First entry of ``mesh.uv_layers`` (stub omits __getitem__ on UVLoopLayers)."""
    if not mesh.uv_layers:
        return None
    layers = cast(list[bpy.types.MeshUVLoopLayer], mesh.uv_layers)
    return layers[0]


def iter_collection_children(
    collection: bpy.types.Collection,
) -> Iterator[bpy.types.Collection]:
    """Iterate ``collection.children`` (stub omits __iter__ on CollectionChildren)."""
    return iter(cast(Iterator[bpy.types.Collection], collection.children))


def node_output_by_name(node: bpy.types.Node, name: str) -> bpy.types.NodeSocket:
    """Subscript ``node.outputs[name]`` (stub omits __getitem__ on NodeOutputs)."""
    table = cast(dict[str, bpy.types.NodeSocket], node.outputs)
    return table[name]


def node_input_by_name(node: bpy.types.Node, name: str) -> bpy.types.NodeSocket:
    """Subscript ``node.inputs[name]`` (stub omits __getitem__ on NodeInputs)."""
    table = cast(dict[str, bpy.types.NodeSocket], node.inputs)
    return table[name]


def set_material_at(mesh: bpy.types.Mesh, index: int, material: bpy.types.Material) -> None:
    """Assign ``mesh.materials[index] = material`` (stub rejects indexed assign)."""
    cast(list[bpy.types.Material], mesh.materials)[index] = material


def expect_scene(scene: bpy.types.Scene | None) -> bpy.types.Scene:
    """Narrow ``bpy.context.scene`` from ``Scene | None`` to ``Scene``.

    Blender always has at least one scene at addon-run time. The stub
    types ``bpy.context.scene`` as optional because the C-side getter
    can theoretically return None during headless edge cases.
    """
    if scene is None:
        raise RuntimeError("Proscenio: bpy.context.scene is None - no active scene")
    return scene
