"""Active-element validation: cheap structural checks for inline panel feedback."""

from __future__ import annotations

from ._shared import read_element_type, read_int
from .issue import Issue


def _name_of(obj: object) -> str:
    return str(getattr(obj, "name", ""))


def validate_active_element(obj: object) -> list[Issue]:
    """Return per-active-object issues. Cheap - runs every panel redraw.

    ``obj`` is a ``bpy.types.Object``; typed loosely to keep the
    validation module testable without importing ``bpy``.
    """
    if obj is None or getattr(obj, "type", None) != "MESH":
        return []

    issues: list[Issue] = []
    element_type = read_element_type(obj)
    name = _name_of(obj)

    if element_type == "sprite":
        issues.extend(_validate_sprite_fields(obj, name))
    elif element_type == "mesh":
        issues.extend(_validate_mesh(obj, name))
    else:
        issues.append(
            Issue(
                "error",
                f"unknown element type {element_type!r} (expected 'mesh' or 'sprite')",
                name,
            )
        )

    return issues


def _validate_sprite_fields(obj: object, name: str) -> list[Issue]:
    issues: list[Issue] = []
    hframes = read_int(obj, "hframes", "proscenio_hframes", 0)
    vframes = read_int(obj, "vframes", "proscenio_vframes", 0)
    if hframes < 1:
        issues.append(Issue("error", "sprite needs hframes >= 1", name))
    if vframes < 1:
        issues.append(Issue("error", "sprite needs vframes >= 1", name))
    return issues


def _validate_mesh(obj: object, name: str) -> list[Issue]:
    mesh = getattr(obj, "data", None)
    polygons = getattr(mesh, "polygons", None) if mesh is not None else None
    if not polygons:
        return [Issue("warning", "mesh element has no polygons", name)]
    return []
