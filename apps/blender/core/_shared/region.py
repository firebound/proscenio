"""Texture-region computation (the authoring panel.1.c.1).

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

from .pg_cp_fallback import read_field


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


def resolve_region(obj: object, uvs: list[list[float]]) -> list[float]:
    """Return the manual region override or fall back to UV bounds."""
    mode = str(
        read_field(obj, pg_field="region_mode", cp_key="proscenio_region_mode", default="auto")
    )
    if mode != "manual":
        return compute_region_from_uvs(uvs)
    return _manual_region_floats(obj)


def manual_region_or_none(obj: object) -> list[float] | None:
    """Return the manual region tuple, or ``None`` when in auto mode.

    Used by ``sprite`` where auto mode means "omit ``texture_region``
    entirely" (full atlas). Manual mode emits the four floats verbatim.
    """
    mode = str(
        read_field(obj, pg_field="region_mode", cp_key="proscenio_region_mode", default="auto")
    )
    if mode != "manual":
        return None
    return _manual_region_floats(obj)


def _manual_region_floats(obj: object) -> list[float]:
    rx = float(read_field(obj, pg_field="region_x", cp_key="proscenio_region_x", default=0.0))
    ry = float(read_field(obj, pg_field="region_y", cp_key="proscenio_region_y", default=0.0))
    rw = float(read_field(obj, pg_field="region_w", cp_key="proscenio_region_w", default=1.0))
    rh = float(read_field(obj, pg_field="region_h", cp_key="proscenio_region_h", default=1.0))
    return [round(rx, 6), round(ry, 6), round(rw, 6), round(rh, 6)]
