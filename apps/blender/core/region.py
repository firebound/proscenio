"""Texture-region computation (SPEC 005.1.c.1).

Pulled out of the writer so the override resolution can be tested without
a Blender session. The two entry points cover both modes:

- :func:`compute_region_from_uvs` - auto mode. Min/max bounds across the
  Godot-space UV list (``[u, v]`` with v already flipped).
- :func:`resolve_region` - picks between the auto path and the manual
  ``Object.proscenio.region_*`` override based on ``region_mode``.

``obj`` is duck-typed: anything that exposes ``getattr(obj, "proscenio")``
plus ``__contains__`` / ``__getitem__`` for the legacy Custom Property
fallback. Real Blender ``bpy.types.Object`` satisfies it; tests pass a
:class:`types.SimpleNamespace`-flavored mock with the same shape.
"""

from __future__ import annotations

from typing import Any


def _read_field(obj: Any, field: str, custom_key: str, default: Any) -> Any:
    """PropertyGroup-first read with Custom Property fallback (SPEC 005)."""
    props = getattr(obj, "proscenio", None)
    if props is not None and hasattr(props, field):
        return getattr(props, field)
    if hasattr(obj, "__contains__") and custom_key in obj:
        return obj[custom_key]
    return default


def compute_region_from_uvs(uvs: list[list[float]]) -> list[float]:
    """Min/max bounds of the UV list rounded to 6 decimal places."""
    if not uvs:
        return [0.0, 0.0, 0.0, 0.0]
    xs = [u[0] for u in uvs]
    ys = [u[1] for u in uvs]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    return [
        round(x_min, 6),
        round(y_min, 6),
        round(x_max - x_min, 6),
        round(y_max - y_min, 6),
    ]


def resolve_region(obj: Any, uvs: list[list[float]]) -> list[float]:
    """Return the manual region override or fall back to UV bounds."""
    mode = str(_read_field(obj, "region_mode", "proscenio_region_mode", "auto"))
    if mode != "manual":
        return compute_region_from_uvs(uvs)
    rx = float(_read_field(obj, "region_x", "proscenio_region_x", 0.0))
    ry = float(_read_field(obj, "region_y", "proscenio_region_y", 0.0))
    rw = float(_read_field(obj, "region_w", "proscenio_region_w", 1.0))
    rh = float(_read_field(obj, "region_h", "proscenio_region_h", 1.0))
    return [round(rx, 6), round(ry, 6), round(rw, 6), round(rh, 6)]


def manual_region_or_none(obj: Any) -> list[float] | None:
    """Return the manual region tuple, or ``None`` when in auto mode.

    Used by ``sprite_frame`` where auto mode means "omit ``texture_region``
    entirely" (full atlas). Manual mode emits the four floats verbatim.
    """
    mode = str(_read_field(obj, "region_mode", "proscenio_region_mode", "auto"))
    if mode != "manual":
        return None
    rx = float(_read_field(obj, "region_x", "proscenio_region_x", 0.0))
    ry = float(_read_field(obj, "region_y", "proscenio_region_y", 0.0))
    rw = float(_read_field(obj, "region_w", "proscenio_region_w", 1.0))
    rh = float(_read_field(obj, "region_h", "proscenio_region_h", 1.0))
    return [round(rx, 6), round(ry, 6), round(rw, 6), round(rh, 6)]
