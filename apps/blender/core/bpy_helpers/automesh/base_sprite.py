"""Vertex-group bookkeeping for the original quad corners (SPEC 013 D3).

Every automesh regen preserves the user's UV-pinned base quad by
tagging the original 4 corner verts in a named vertex group and
deleting only verts NOT in that group. Lifted from COA Tools 2's
``coa_base_sprite`` pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import bmesh

if TYPE_CHECKING:
    from bpy.types import Object


BASE_SPRITE_GROUP_NAME = "proscenio_base_sprite"
"""Vertex group flagged on the original 4 quad corners so automesh
regen knows which verts to preserve. Lifted from COA Tools 2's
``coa_base_sprite`` pattern per SPEC 013 D3."""


def initialize_base_sprite_group(obj: Object) -> tuple[int, bool]:
    """Ensure ``proscenio_base_sprite`` exists; flag current verts only on first run.

    Returns ``(group_index, is_fresh)``. ``is_fresh`` is True when the
    group did not exist before this call - meaning every vertex
    currently on the mesh is part of the original UV-pinned base + we
    flag them all so the regen-delete step preserves them.

    On subsequent runs (group already present) we do NOT re-flag the
    current verts. The previously-generated automesh geometry already
    sits in the mesh; flagging it now would promote it to "base" and
    the next ``delete_non_base_geometry`` call would skip it, causing
    the mesh to accumulate vertices unbounded across reruns (regression
    caught in PR #51 review).
    """
    group = obj.vertex_groups.get(BASE_SPRITE_GROUP_NAME)
    if group is not None:
        return group.index, False
    group = obj.vertex_groups.new(name=BASE_SPRITE_GROUP_NAME)
    mesh = obj.data
    indices = list(range(len(mesh.vertices)))
    if indices:
        group.add(indices, 1.0, "REPLACE")
    return group.index, True


def delete_non_base_geometry(obj: Object, group_index: int) -> None:
    """Remove every vertex NOT in the base-sprite group from the mesh.

    First step of a regen so the original 4 quad corners survive while
    everything automesh generated is wiped. Goes through bmesh because
    plain ``mesh.vertices`` does not support per-vertex removal cleanly.
    """
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    deform_layer = bm.verts.layers.deform.verify()
    to_remove = [
        vert
        for vert in bm.verts
        if group_index not in vert[deform_layer] or vert[deform_layer].get(group_index, 0.0) <= 0.0
    ]
    bmesh.ops.delete(bm, geom=to_remove, context="VERTS")
    bm.to_mesh(mesh)
    bm.free()


def remove_base_sprite_verts(obj: Object, group_index: int) -> None:
    """Delete the 4 verts flagged in proscenio_base_sprite via bmesh.

    Called by default after the automesh build so the original quad
    corners do not linger as loose vertices. Toggle off via the
    ``preserve_base_quad`` operator option when the user has UV /
    weight customization on the original quad that they want to
    keep around for manual stitching.
    """
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    deform_layer = bm.verts.layers.deform.verify()
    to_remove = [
        vert
        for vert in bm.verts
        if group_index in vert[deform_layer] and vert[deform_layer].get(group_index, 0.0) > 0.0
    ]
    if to_remove:
        bmesh.ops.delete(bm, geom=to_remove, context="VERTS")
    bm.to_mesh(mesh)
    bm.free()
