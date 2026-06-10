"""Debug-stage companion-object emission for the automesh.

bpy-bound. Lives in ``core/bpy_helpers/``. Builds visualization
meshes the user can toggle stage-by-stage to inspect the pipeline
that ``automesh_bmesh.build_automesh`` runs - so when the final
mesh comes out wrong, the user can rewind through each stage's
intermediate output and pinpoint the failure mode visually
instead of guessing from final geometry.

Companion objects live in a dedicated ``Proscenio.Debug`` scene
collection so they can be hidden / shown / deleted in bulk
without disturbing the user's authored content. Each companion
is named ``<sprite>_debug_<stage>`` so the outliner clusters
them under the sprite they belong to.

All companions are wireframe meshes (vertices + edges, no faces)
so they overlay the sprite without occluding it. The user sees
the contour shape, vertex distribution, bridge edges, etc. in
the same viewport as the actual sprite.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import bpy

from ...automesh.geometry import cyclic_loop_edges, radial_bridge_edges

if TYPE_CHECKING:
    from bpy.types import Collection, Mesh, Object


_DEBUG_COLLECTION_NAME = "Proscenio.Debug"
"""Scene collection that hosts every automesh debug companion.
Hidden/shown/deleted in bulk from the outliner."""


def _ensure_debug_collection(scene: bpy.types.Scene) -> Collection:
    """Return the Proscenio.Debug collection, creating it if absent."""
    collection = bpy.data.collections.get(_DEBUG_COLLECTION_NAME)
    if collection is None:
        collection = bpy.data.collections.new(_DEBUG_COLLECTION_NAME)
        scene.collection.children.link(collection)
    return collection


def _debug_object_name(sprite_obj: Object, stage: str) -> str:
    """Companion-object naming: ``<sprite>_debug_<stage>``."""
    return f"{sprite_obj.name}_debug_{stage}"


def clear_debug_objects(sprite_obj: Object, stage: str | None = None) -> int:
    """Remove debug companions for ``sprite_obj``.

    When ``stage`` is provided, removes only that stage's companion.
    When ``None``, removes every companion matching the sprite's
    naming prefix. Returns the count removed.

    Defensive: missing collection / missing object is a no-op.
    """
    prefix = f"{sprite_obj.name}_debug_"
    target_name = _debug_object_name(sprite_obj, stage) if stage else None
    # Two-phase delete: collect matching objects first, then remove
    # them. Removing during iteration mutates ``bpy.data.objects``
    # and would skip elements / crash on the live iterator.
    to_remove = [
        obj
        for obj in bpy.data.objects
        if obj.name.startswith(prefix) and (target_name is None or obj.name == target_name)
    ]
    removed = 0
    for obj in to_remove:
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh is not None and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
        removed += 1
    return removed


def _new_debug_object(
    sprite_obj: Object,
    stage: str,
    verts: list[tuple[float, float, float]],
    edges: list[tuple[int, int]],
) -> Object:
    """Create / replace a debug companion mesh + link to debug collection.

    Mesh has no faces - companion stays wireframe so it overlays the
    sprite without occluding it. Display type is forced to WIRE so
    the user sees the debug structure even when not selected.
    """
    clear_debug_objects(sprite_obj, stage)
    name = _debug_object_name(sprite_obj, stage)
    mesh: Mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices=verts, edges=edges, faces=[])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = sprite_obj.location
    obj.display_type = "WIRE"
    obj.hide_render = True
    collection = _ensure_debug_collection(bpy.context.scene)
    collection.objects.link(obj)
    return obj


def _contour_loop_verts_edges(
    outer_world: list[tuple[float, float]],
    inner_world: list[tuple[float, float]],
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int]]]:
    """Build the shared verts + outer/inner cyclic edge loops for a contour
    companion.

    Verts are the outer ring (indices ``0..N-1``) then the inner ring
    (``N..N+M-1``), each lifted to ``(x, 0, y)``. Edges close the outer
    loop always and the inner loop when it has >= 2 verts.
    emit_bridges_debug appends its radial bridges on top of this base.
    """
    outer_count = len(outer_world)
    inner_count = len(inner_world)
    verts: list[tuple[float, float, float]] = [(x, 0.0, y) for (x, y) in outer_world]
    verts.extend((x, 0.0, y) for (x, y) in inner_world)
    edges: list[tuple[int, int]] = cyclic_loop_edges(0, outer_count)
    if inner_count >= 2:
        edges.extend(cyclic_loop_edges(outer_count, inner_count))
    return verts, edges


def emit_contour_debug(
    sprite_obj: Object,
    stage: str,
    outer_world: list[tuple[float, float]],
    inner_world: list[tuple[float, float]],
) -> Object:
    """Emit a companion that draws outer + inner contour edge loops.

    Outer indices 0..N-1, inner indices N..N+M-1. Edges connect
    each vertex to its cyclic neighbour so the loops render as
    closed line strips in the viewport. No faces so the sprite
    behind stays visible.
    """
    verts, edges = _contour_loop_verts_edges(outer_world, inner_world)
    return _new_debug_object(sprite_obj, stage, verts, edges)


def emit_points_debug(
    sprite_obj: Object,
    stage: str,
    points_world: list[tuple[float, float]],
) -> Object:
    """Emit a companion with one isolated vertex per debug point.

    Used for Steiner / interior points where the meaningful
    visualization is the distribution itself, not connectivity.
    Verts render as small dots in the viewport when the companion
    is selected.
    """
    verts: list[tuple[float, float, float]] = [(x, 0.0, y) for (x, y) in points_world]
    return _new_debug_object(sprite_obj, stage, verts, edges=[])


def emit_bridges_debug(
    sprite_obj: Object,
    stage: str,
    outer_world: list[tuple[float, float]],
    inner_world: list[tuple[float, float]],
    bridge_offset: int,
) -> Object:
    """Emit outer + inner verts + the bridge edges (no triangulation).

    The bridge edges are what the user needs to see when the final
    triangulation comes out lopsided - if the bridges already cross
    the annulus diagonally here, ``find_best_inner_rotation``
    failed and the downstream triangle_fill never had a chance.
    """
    verts, edges = _contour_loop_verts_edges(outer_world, inner_world)
    outer_count = len(outer_world)
    # Bridges - only when counts match (mirrors build_annulus_edge_pairs).
    if outer_count == len(inner_world):
        edges.extend(radial_bridge_edges(outer_count, outer_count, bridge_offset))
    return _new_debug_object(sprite_obj, stage, verts, edges)
