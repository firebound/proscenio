"""Auto-UV stamping for the generated automesh (SPEC 013).

After triangulation the brand-new verts have no UVs; the textured
material would render garbage per face. This module stamps a linear
XZ -> UV mapping over every loop matching the sprite plane's world
extent, so the texture lines up pixel-for-pixel with the silhouette.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy


def stamp_uvs(
    mesh: bpy.types.Mesh,
    source_width: int,
    source_height: int,
    world_scale: float,
) -> None:
    """Auto-stamp UV coordinates on every loop via linear XZ -> UV mapping.

    Sprite plane convention (matches fixture build_blend.py): direct
    UV mapping (no flip on either axis). Math:

        u = (x + half_w) / (2 * half_w)  -- x in [-half_w, +half_w]
        v = (z + half_h) / (2 * half_h)  -- z in [-half_h, +half_h]

    Without this stamp, automesh-generated verts inherit no UVs and
    the textured material renders garbage / wrong region per face.

    Earlier iterations flipped U; the flip was a misapplied workaround
    for Blender's Front Ortho view direction and produced a horizontal
    mirror on textured sprite planes (regression caught in PR #51
    smoke). The current direct mapping matches the shared_atlas
    fixture convention.
    """
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    uv_layer = mesh.uv_layers.active
    if uv_layer is None:
        return
    half_w = source_width * world_scale / 2.0
    half_h = source_height * world_scale / 2.0
    if half_w <= 0.0 or half_h <= 0.0:
        return
    for poly in mesh.polygons:
        for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
            vert_index = mesh.loops[loop_index].vertex_index
            co = mesh.vertices[vert_index].co
            u = (co.x + half_w) / (2.0 * half_w)
            v = (co.z + half_h) / (2.0 * half_h)
            uv_layer.data[loop_index].uv = (u, v)
