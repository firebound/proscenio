"""Active-sprite validation: cheap structural checks for inline panel feedback."""

from __future__ import annotations

from ._shared import read_int, read_sprite_type
from .issue import Issue


def _name_of(obj: object) -> str:
    return str(getattr(obj, "name", ""))


def validate_active_sprite(obj: object) -> list[Issue]:
    """Return per-active-object issues. Cheap - runs every panel redraw.

    ``obj`` is a ``bpy.types.Object``; typed loosely to keep the
    validation module testable without importing ``bpy``.
    """
    if obj is None or getattr(obj, "type", None) != "MESH":
        return []

    issues: list[Issue] = []
    sprite_type = read_sprite_type(obj)
    name = _name_of(obj)

    if sprite_type == "sprite_frame":
        issues.extend(_validate_sprite_frame_fields(obj, name))
    elif sprite_type == "polygon":
        issues.extend(_validate_polygon_mesh(obj, name))
    else:
        issues.append(
            Issue(
                "error",
                f"unknown sprite type {sprite_type!r} (expected 'polygon' or 'sprite_frame')",
                name,
            )
        )

    return issues


def _validate_sprite_frame_fields(obj: object, name: str) -> list[Issue]:
    issues: list[Issue] = []
    hframes = read_int(obj, "hframes", "proscenio_hframes", 0)
    vframes = read_int(obj, "vframes", "proscenio_vframes", 0)
    if hframes < 1:
        issues.append(Issue("error", "sprite_frame needs hframes >= 1", name))
    if vframes < 1:
        issues.append(Issue("error", "sprite_frame needs vframes >= 1", name))
    return issues


def _validate_polygon_mesh(obj: object, name: str) -> list[Issue]:
    mesh = getattr(obj, "data", None)
    polygons = getattr(mesh, "polygons", None) if mesh is not None else None
    if not polygons:
        return [Issue("warning", "polygon sprite mesh has no polygons", name)]
    return []
