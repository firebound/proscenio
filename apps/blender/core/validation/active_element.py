"""Active-element validation: cheap structural checks for inline panel feedback."""

from __future__ import annotations

from ._shared import name_of, read_element_type, read_int
from .issue import Issue


def validate_active_element(obj: object) -> list[Issue]:
    """Return per-active-object issues. Cheap - runs every panel redraw.

    ``obj`` is a ``bpy.types.Object``; typed loosely to keep the
    validation module testable without importing ``bpy``.
    """
    if obj is None or getattr(obj, "type", None) != "MESH":
        return []

    issues: list[Issue] = []
    element_type = read_element_type(obj)
    name = name_of(obj)

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
    issues.extend(_validate_sprite_is_quad(obj, name))
    return issues


def _validate_sprite_is_quad(obj: object, name: str) -> list[Issue]:
    """Warn when a sprite element's mesh is no longer a single quad.

    A sprite exports as a Godot Sprite2D carved from its single base quad
    (4 verts, 1 face). A mesh tool run on the sprite by mistake (automesh
    replaces the quad with a dense cutout) leaves geometry the writer cannot
    map back to a sprite. Skips when the mesh data is unavailable - nothing to
    judge.
    """
    mesh = getattr(obj, "data", None)
    vertices = getattr(mesh, "vertices", None) if mesh is not None else None
    polygons = getattr(mesh, "polygons", None) if mesh is not None else None
    if vertices is None or polygons is None:
        return []
    vert_count = len(vertices)
    face_count = len(polygons)
    if vert_count == 4 and face_count == 1:
        return []
    return [
        Issue(
            "warning",
            f"sprite element mesh is {vert_count} verts / {face_count} face(s), not a "
            "single quad - a mesh tool likely ran on this sprite; to attach a sprite to "
            "a bone, parent it with Ctrl+P > Bone instead of meshing it",
            name,
        )
    ]


def _validate_mesh(obj: object, name: str) -> list[Issue]:
    mesh = getattr(obj, "data", None)
    polygons = getattr(mesh, "polygons", None) if mesh is not None else None
    if not polygons:
        return [Issue("warning", "mesh element has no polygons", name)]
    return []
