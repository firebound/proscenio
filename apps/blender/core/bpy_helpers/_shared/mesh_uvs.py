"""Active-UV-layer loop walk.

bpy-bound by duck typing only (no bpy import): flattens a mesh's active
UV layer into raw Blender-convention ``(u, v)`` tuples. Callers that need
Godot / texture-region space flip ``v`` to ``1.0 - v`` afterwards.
"""

from __future__ import annotations

from typing import Any


def collect_mesh_loop_uvs(mesh: Any) -> list[tuple[float, float]]:
    """Flatten the active UV layer's per-loop coords into ``[(u, v), ...]``.

    Raw Blender convention (bottom-left origin, ``v`` NOT flipped). Returns
    an empty list when there is no active UV layer or its ``.data`` is
    empty. Defensive against partially-initialized meshes: a UV-layer
    marker whose ``.data`` is shorter than the loop count (seen on Blender
    5.x after the apply operator on shared-material objects) skips the
    out-of-range loops instead of raising ``IndexError``.
    """
    uv_layers = getattr(mesh, "uv_layers", None)
    if uv_layers is None:
        return []
    active = uv_layers.active
    if active is None or len(active.data) == 0:
        return []
    data_len = len(active.data)
    out: list[tuple[float, float]] = []
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            if li >= data_len:
                continue
            u, v = active.data[li].uv
            out.append((float(u), float(v)))
    return out


def planar_uv_from_positions(
    positions: list[tuple[float, float, float]],
) -> list[tuple[float, float]]:
    """Project per-loop ``(x, y, z)`` positions to UVs on the dominant plane.

    Deterministic replacement for Smart UV Project. Smart UV Project derives
    the projection frame from face normals, so an XZ picture-plane quad (its
    normal points -Y) comes back rotated 90 degrees and mirrored relative to a
    hand-authored layout. This instead picks the smallest-extent axis as the
    projection normal and maps the other two axes - in ascending axis order --
    to ``(u, v)``, each normalized over its bounding-box range.

    For the standard XZ mesh the normal is Y, so ``u`` comes from X
    (left -> 0, right -> 1) and ``v`` from Z (bottom -> 0, top -> 1) - the same
    mapping the PSD importer authors on a fresh quad (``planes._build_quad``)
    and every fixture authors by hand, so a re-projection never rotates or
    mirrors the texture the way Smart UV Project does. A zero-extent in-plane
    axis (a degenerate edge) maps to 0.0 rather than dividing by zero.
    """
    if not positions:
        return []
    axis_min = [min(p[axis] for p in positions) for axis in range(3)]
    axis_max = [max(p[axis] for p in positions) for axis in range(3)]
    extents = [axis_max[axis] - axis_min[axis] for axis in range(3)]
    normal_axis = min(range(3), key=lambda axis: extents[axis])
    in_plane = [axis for axis in range(3) if axis != normal_axis]
    u_axis, v_axis = in_plane[0], in_plane[1]

    def _norm(value: float, axis: int) -> float:
        span = extents[axis]
        if span <= 0.0:
            return 0.0
        return (value - axis_min[axis]) / span

    return [(_norm(p[u_axis], u_axis), _norm(p[v_axis], v_axis)) for p in positions]
