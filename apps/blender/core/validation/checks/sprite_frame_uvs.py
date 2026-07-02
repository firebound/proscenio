"""Sprite-frame UV check: warn when a sheet-sliced sprite's UVs miss the full sheet."""

from __future__ import annotations

from ..._shared.cp_keys import (
    PROSCENIO_HFRAMES,
    PROSCENIO_REGION_MODE,
    PROSCENIO_TYPE,
    PROSCENIO_VFRAMES,
)
from ..._shared.pg_cp_fallback import read_field
from .._shared import name_of
from ..issue import Issue

# How close a sprite_frame quad's UV bounds must sit to the full 0-1 sheet
# before the hframes/vframes grid is considered correctly authored.
_UV_SHEET_TOLERANCE = 0.02


def validate_sprite_frame_uvs(obj: object) -> list[Issue]:
    """Warn when a sheet-sliced sprite's quad UVs do not span the full 0-1 sheet.

    An ``auto`` region-mode sprite with a multi-frame grid (hframes * vframes > 1)
    derives its texture_region from the quad's UV bounds, which Godot then slices
    into the grid. UVs hand-shrunk to a sub-rect silently garble that grid
    relative to the full-sheet preview. Manual-region sprites address an explicit
    rect, so the full-sheet expectation does not apply to them.
    """
    if not _is_sheet_sliced_sprite(obj):
        return []
    bounds = _uv_bounds(obj)
    if bounds is None:
        return []
    u_min, u_max, v_min, v_max = bounds
    if _uv_spans_sheet(u_min, u_max, v_min, v_max):
        return []
    return [
        Issue(
            "warning",
            f"sprite UVs span [{u_min:.2f}, {u_max:.2f}] x [{v_min:.2f}, {v_max:.2f}], not "
            f"the full 0-1 sheet - the hframes/vframes grid will be garbled in Godot",
            name_of(obj),
        )
    ]


def _is_sheet_sliced_sprite(obj: object) -> bool:
    """True for a multi-frame sprite whose region comes from UV bounds (auto)."""
    element_type = str(read_field(obj, cp_key=PROSCENIO_TYPE, default="mesh"))
    if element_type != "sprite":
        return False
    region_mode = str(read_field(obj, cp_key=PROSCENIO_REGION_MODE, default="auto"))
    if region_mode == "manual":
        return False
    hframes = int(read_field(obj, cp_key=PROSCENIO_HFRAMES, default=1))
    vframes = int(read_field(obj, cp_key=PROSCENIO_VFRAMES, default=1))
    return hframes * vframes > 1


def _uv_bounds(obj: object) -> tuple[float, float, float, float] | None:
    """Min/max (u, v) over the active UV layer, or None when there is none."""
    mesh = getattr(obj, "data", None)
    uv_layers = getattr(mesh, "uv_layers", None)
    active = getattr(uv_layers, "active", None)
    data = getattr(active, "data", None)
    if not data:
        return None
    us = [float(loop.uv[0]) for loop in data]
    vs = [float(loop.uv[1]) for loop in data]
    if not us:
        return None
    return min(us), max(us), min(vs), max(vs)


def _uv_spans_sheet(u_min: float, u_max: float, v_min: float, v_max: float) -> bool:
    return (
        u_min <= _UV_SHEET_TOLERANCE
        and v_min <= _UV_SHEET_TOLERANCE
        and u_max >= 1.0 - _UV_SHEET_TOLERANCE
        and v_max >= 1.0 - _UV_SHEET_TOLERANCE
    )
