"""GPU draw handler for per-vert weight + provenance overlay.

Two modes: 'weight' (6-stop colorband on active VG weight) and
'provenance' (cyan/white/gray per entry provenance). Only 'provenance'
is user-toggleable now; 'weight' data is supported for aspirational successor work.

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

from ..._shared.cp_keys import PROSCENIO_WEIGHT_SIDECAR as _SIDECAR_KEY

OverlayMode = Literal["weight", "provenance"]

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


_PointColorGroups = dict[tuple[float, float, float, float], list[tuple[float, float, float]]]


def _read_provenance_entries(obj: bpy.types.Object, mode: OverlayMode) -> list[object] | None:
    """Return per-vert provenance entries when the overlay should draw.

    ``None`` (skip drawing) when there is no mesh, the sidecar is missing
    or malformed, the mode is not ``provenance``, or the entry count does
    not match the mesh vertex count.
    """
    if obj is None or obj.data is None:
        return None
    payload = obj.get(_SIDECAR_KEY)
    if payload is None:
        return None
    try:
        data = json.loads(payload)
    except (ValueError, TypeError):
        return None
    entries = data.get("entries") or []
    if not entries:
        return None
    if mode != "provenance":
        return None
    if len(entries) != len(obj.data.vertices):
        return None
    return entries


def _draw_color_groups(color_groups: _PointColorGroups) -> None:
    """Render each color's world points as discs via the uniform shader."""
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


def _draw_callback(obj: bpy.types.Object, mode: OverlayMode) -> None:
    """Internal handler body. Reads sidecar + mesh + draws colored discs."""
    entries = _read_provenance_entries(obj, mode)
    if entries is None:
        return
    matrix_world = obj.matrix_world
    color_groups: _PointColorGroups = {}
    for vert_idx, vert in enumerate(obj.data.vertices):
        entry = entries[vert_idx]
        provenance = entry.get("provenance") if isinstance(entry, dict) else None
        if not isinstance(provenance, str):
            continue
        color = _PROVENANCE_COLORS.get(provenance)
        if color is None:
            continue
        world_pos = matrix_world @ vert.co
        color_groups.setdefault(color, []).append((world_pos.x, world_pos.y, world_pos.z))
    _draw_color_groups(color_groups)
