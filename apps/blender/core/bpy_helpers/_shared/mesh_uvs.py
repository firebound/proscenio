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
