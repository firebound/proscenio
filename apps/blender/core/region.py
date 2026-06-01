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

from typing import Protocol, TypeVar, cast, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class _CPLookup(Protocol):
    """Anything that exposes ``__contains__`` + ``__getitem__`` (the legacy
    Custom Property dict-style access). Both ``bpy.types.Object`` and the
    pytest ``SimpleNamespace`` mocks satisfy it."""

    def __contains__(self, key: object) -> bool: ...
    def __getitem__(self, key: str) -> object: ...


def _read_field(obj: object, field: str, custom_key: str, default: T) -> T:
    """PropertyGroup-first read with Custom Property fallback (the authoring panel).

    Same trust-the-CP-callsite contract as ``core.pg_cp_fallback.read_field``:
    the caller declares ``default``'s type, and the CP path is cast back to
    it. A writer that stores the wrong type under a Custom Property is a
    bug at the writer site, not a defensive check here.
    """
    props = getattr(obj, "proscenio", None)
    if props is not None and hasattr(props, field):
        return cast(T, getattr(props, field))
    if isinstance(obj, _CPLookup) and custom_key in obj:
        return cast(T, obj[custom_key])
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


def resolve_region(obj: object, uvs: list[list[float]]) -> list[float]:
    """Return the manual region override or fall back to UV bounds."""
    mode = str(_read_field(obj, "region_mode", "proscenio_region_mode", "auto"))
    if mode != "manual":
        return compute_region_from_uvs(uvs)
    return _manual_region_floats(obj)


def manual_region_or_none(obj: object) -> list[float] | None:
    """Return the manual region tuple, or ``None`` when in auto mode.

    Used by ``sprite_frame`` where auto mode means "omit ``texture_region``
    entirely" (full atlas). Manual mode emits the four floats verbatim.
    """
    mode = str(_read_field(obj, "region_mode", "proscenio_region_mode", "auto"))
    if mode != "manual":
        return None
    return _manual_region_floats(obj)


def _manual_region_floats(obj: object) -> list[float]:
    rx = float(_read_field(obj, "region_x", "proscenio_region_x", 0.0))
    ry = float(_read_field(obj, "region_y", "proscenio_region_y", 0.0))
    rw = float(_read_field(obj, "region_w", "proscenio_region_w", 1.0))
    rh = float(_read_field(obj, "region_h", "proscenio_region_h", 1.0))
    return [round(rx, 6), round(ry, 6), round(rw, 6), round(rh, 6)]
