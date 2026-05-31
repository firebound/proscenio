"""GPU draw handler for per-vert weight + provenance overlay (the paint work, T9/T10/T11).

Two modes: 'weight' (6-stop colorband on active VG weight) and
'provenance' (cyan/white/gray per entry provenance). Only 'provenance'
is user-toggleable this wave; 'weight' data is supported for aspirational successor work.

POST_VIEW handler. Uses UNIFORM_COLOR shader (shared with modal_overlay).
Per-vert disc rendered as POINTS primitive with point_size.
"""

from __future__ import annotations

import contextlib
import json
from typing import Literal

import bpy
import gpu
from gpu_extras.batch import batch_for_shader

OverlayMode = Literal["weight", "provenance"]

_SIDECAR_KEY = "proscenio_weight_sidecar"
_DISC_SIZE = 6.0
_UNIFORM_COLOR_SHADER = "UNIFORM_COLOR"

_PROVENANCE_COLORS: dict[str, tuple[float, float, float, float]] = {
    "reprojected": (0.0, 0.8, 1.0, 0.9),
    "user_paint": (1.0, 1.0, 1.0, 0.9),
    "auto_seed": (0.5, 0.5, 0.5, 0.6),
}


def register_handler(obj: bpy.types.Object, mode: OverlayMode) -> object:
    """Add a POST_VIEW SpaceView3D draw handler. Return handle for unregister."""
    args = (obj, mode)
    return bpy.types.SpaceView3D.draw_handler_add(_draw_callback, args, "WINDOW", "POST_VIEW")


def unregister_handler(handle: object) -> None:
    """Remove the draw handler. No-op safe if already removed."""
    with contextlib.suppress(ValueError, RuntimeError):
        bpy.types.SpaceView3D.draw_handler_remove(handle, "WINDOW")


def _draw_callback(obj: bpy.types.Object, mode: OverlayMode) -> None:
    """Internal handler body. Reads sidecar + mesh + draws colored discs."""
    if obj is None or obj.data is None:
        return
    payload = obj.get(_SIDECAR_KEY)
    if payload is None:
        return
    try:
        data = json.loads(payload)
    except (ValueError, TypeError):
        return
    entries = data.get("entries") or []
    if not entries:
        return
    if mode != "provenance":
        return
    matrix_world = obj.matrix_world
    verts = obj.data.vertices
    if len(entries) != len(verts):
        return
    color_groups: dict[tuple[float, float, float, float], list[tuple[float, float, float]]] = {}
    for vert_idx, vert in enumerate(verts):
        entry = entries[vert_idx]
        provenance = entry.get("provenance") if isinstance(entry, dict) else None
        if not isinstance(provenance, str):
            continue
        color = _PROVENANCE_COLORS.get(provenance)
        if color is None:
            continue
        world_pos = matrix_world @ vert.co
        color_groups.setdefault(color, []).append((world_pos.x, world_pos.y, world_pos.z))
    shader = gpu.shader.from_builtin(_UNIFORM_COLOR_SHADER)
    gpu.state.blend_set("ALPHA")
    gpu.state.point_size_set(_DISC_SIZE)
    try:
        for color, positions in color_groups.items():
            batch = batch_for_shader(shader, "POINTS", {"pos": positions})
            shader.bind()
            shader.uniform_float("color", color)
            batch.draw(shader)
    finally:
        gpu.state.point_size_set(1.0)
        gpu.state.blend_set("NONE")
