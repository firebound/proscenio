"""Proscenio validation surface (SPEC 005).

Two entry points map to the panel's two validation paths:

- :func:`validate_active_sprite` — cheap structural checks for inline
  feedback; called on every panel redraw, must stay O(1) on the active
  object.
- :func:`validate_export` — full lazy pass triggered by the Validate
  button or the Export operator; allowed to walk every scene object,
  check vertex groups against bones, hit the disk for atlas files.

Both return :class:`list[Issue]`. The panel layer renders icons + text
from each issue; export blocks when any issue carries severity ``error``.

Validation here is *structural and semantic* — JSON Schema validation
runs in CI and the test runner, not in the live Blender session.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Severity = Literal["error", "warning"]


@dataclass(frozen=True, slots=True)
class Issue:
    """A single validation finding.

    ``obj_name`` is optional and lets a future "select offending object"
    UX click straight to the source.
    """

    severity: Severity
    message: str
    obj_name: str | None = None


# --------------------------------------------------------------------------- #
# Inline / cheap checks
# --------------------------------------------------------------------------- #


def validate_active_sprite(obj: Any) -> list[Issue]:
    """Return per-active-object issues. Cheap — runs every panel redraw.

    ``obj`` is a ``bpy.types.Object``; typed loosely to keep the
    validation module testable without importing ``bpy``.
    """
    if obj is None or getattr(obj, "type", None) != "MESH":
        return []

    issues: list[Issue] = []
    sprite_type = _read_sprite_type(obj)

    if sprite_type == "sprite_frame":
        issues.extend(_validate_sprite_frame_fields(obj))
    elif sprite_type == "polygon":
        issues.extend(_validate_polygon_mesh(obj))
    else:
        issues.append(
            Issue(
                "error",
                f"unknown sprite type {sprite_type!r} (expected 'polygon' or 'sprite_frame')",
                obj.name,
            )
        )

    return issues


def _read_sprite_type(obj: Any) -> str:
    props = getattr(obj, "proscenio", None)
    if props is not None and hasattr(props, "sprite_type"):
        return str(props.sprite_type)
    return str(obj.get("proscenio_type", "polygon")) if hasattr(obj, "get") else "polygon"


def _read_int(obj: Any, prop_name: str, custom_key: str, default: int) -> int:
    props = getattr(obj, "proscenio", None)
    if props is not None and hasattr(props, prop_name):
        return int(getattr(props, prop_name))
    if hasattr(obj, "get") and custom_key in obj:
        return int(obj[custom_key])
    return default


def _validate_sprite_frame_fields(obj: Any) -> list[Issue]:
    issues: list[Issue] = []
    hframes = _read_int(obj, "hframes", "proscenio_hframes", 0)
    vframes = _read_int(obj, "vframes", "proscenio_vframes", 0)
    if hframes < 1:
        issues.append(Issue("error", "sprite_frame needs hframes >= 1", obj.name))
    if vframes < 1:
        issues.append(Issue("error", "sprite_frame needs vframes >= 1", obj.name))
    return issues


def _validate_polygon_mesh(obj: Any) -> list[Issue]:
    mesh = getattr(obj, "data", None)
    polygons = getattr(mesh, "polygons", None) if mesh is not None else None
    if not polygons:
        return [Issue("warning", "polygon sprite mesh has no polygons", obj.name)]
    return []


# --------------------------------------------------------------------------- #
# Lazy / export-time checks
# --------------------------------------------------------------------------- #


def validate_active_slot(obj: Any) -> list[Issue]:
    """Return per-active-Empty slot issues (SPEC 004 D9 + D10).

    Cheap -- runs on every panel redraw. ``obj`` is the active Empty
    flagged with ``proscenio.is_slot``. Validates: (1) at least one
    child mesh, (2) ``slot_default`` resolves to an existing child,
    (3) child meshes share the Empty's ``parent_bone`` if any,
    (4) no slot child carries a ``bone_transform``-shaped fcurve
    (warning -- visibility toggling makes bone keys silent unless the
    child is the visible attachment at that frame).
    """
    if not _is_active_slot(obj):
        return []
    children = [c for c in getattr(obj, "children", ()) if getattr(c, "type", None) == "MESH"]
    if not children:
        return [Issue("error", f"slot '{obj.name}' has no MESH children", obj.name)]

    issues: list[Issue] = []
    issues.extend(_check_slot_default(obj, children))
    issues.extend(_check_slot_child_bones(obj, children))
    issues.extend(_check_slot_child_transform_keys(children))
    return issues


def _is_active_slot(obj: Any) -> bool:
    if obj is None or getattr(obj, "type", None) != "EMPTY":
        return False
    props = getattr(obj, "proscenio", None)
    return props is not None and bool(getattr(props, "is_slot", False))


def _check_slot_default(obj: Any, children: list[Any]) -> list[Issue]:
    slot_default = str(getattr(obj.proscenio, "slot_default", ""))
    if not slot_default:
        return []
    child_names = {c.name for c in children}
    if slot_default in child_names:
        return []
    return [
        Issue(
            "error",
            f"slot default '{slot_default}' is not a child of '{obj.name}'",
            obj.name,
        )
    ]


def _slot_bone_of(obj: Any) -> str:
    if getattr(obj, "parent_type", "") != "BONE":
        return ""
    return str(getattr(obj, "parent_bone", ""))


def _check_slot_child_bones(obj: Any, children: list[Any]) -> list[Issue]:
    slot_bone = _slot_bone_of(obj)
    if not slot_bone:
        return []
    issues: list[Issue] = []
    for child in children:
        child_bone = _slot_bone_of(child)
        if child_bone and child_bone != slot_bone:
            issues.append(
                Issue(
                    "warning",
                    f"attachment '{child.name}' parent bone '{child_bone}' "
                    f"differs from slot bone '{slot_bone}'",
                    child.name,
                )
            )
    return issues


def _check_slot_child_transform_keys(children: list[Any]) -> list[Issue]:
    issues: list[Issue] = []
    for child in children:
        if _has_bone_transform_keys(child):
            issues.append(
                Issue(
                    "warning",
                    f"slot child '{child.name}' carries bone-transform keyframes; "
                    f"visibility is the only thing the slot animates",
                    child.name,
                )
            )
    return issues


def _has_bone_transform_keys(obj: Any) -> bool:
    """True when ``obj`` has any fcurve targeting location/rotation/scale."""
    anim = getattr(obj, "animation_data", None)
    action = getattr(anim, "action", None) if anim is not None else None
    if action is None:
        return False
    fcurves = getattr(action, "fcurves", None)
    if fcurves is None:
        return False
    for fcurve in fcurves:
        path = str(getattr(fcurve, "data_path", ""))
        if path.startswith(("location", "rotation", "scale")):
            return True
    return False


def validate_export(scene: Any) -> list[Issue]:
    """Full pre-export pass. Walks the scene, hits the disk for the atlas.

    Returns every issue found; the caller decides whether to abort. Errors
    block export by convention; warnings inform but allow the operator to
    proceed.
    """
    issues: list[Issue] = []
    scene_objects = list(getattr(scene, "objects", ()))

    armatures = [o for o in scene_objects if getattr(o, "type", None) == "ARMATURE"]
    if not armatures:
        issues.append(Issue("error", "scene has no Armature — Proscenio export requires one"))
        return issues

    available_bones = _armature_bone_names(armatures[0])

    for obj in scene_objects:
        if getattr(obj, "type", None) != "MESH":
            continue
        for active_issue in validate_active_sprite(obj):
            issues.append(active_issue)
        issues.extend(_validate_sprite_against_armature(obj, available_bones))

    issues.extend(_validate_slots(scene_objects))

    issues.extend(_validate_atlas_files(scene_objects))

    return issues


def _validate_slots(scene_objects: list[Any]) -> list[Issue]:
    """Walk slot Empties + cross-check name uniqueness (D9)."""
    seen: set[str] = set()
    issues: list[Issue] = []
    for obj in scene_objects:
        if getattr(obj, "type", None) != "EMPTY":
            continue
        props = getattr(obj, "proscenio", None)
        if props is None or not bool(getattr(props, "is_slot", False)):
            continue
        if obj.name in seen:
            issues.append(Issue("error", f"duplicate slot name '{obj.name}'", obj.name))
        seen.add(obj.name)
        issues.extend(validate_active_slot(obj))
    return issues


def _armature_bone_names(armature_obj: Any) -> set[str]:
    armature = getattr(armature_obj, "data", None)
    bones = getattr(armature, "bones", None) if armature is not None else None
    if bones is None:
        return set()
    return {str(b.name) for b in bones}


def _validate_sprite_against_armature(obj: Any, bones: set[str]) -> list[Issue]:
    issues: list[Issue] = []

    parent_bone = getattr(obj, "parent_bone", "")
    has_parent_bone = bool(parent_bone) and parent_bone in bones
    vertex_groups = getattr(obj, "vertex_groups", ())
    matching_groups = [vg for vg in vertex_groups if str(vg.name) in bones]

    if not has_parent_bone and not matching_groups:
        issues.append(
            Issue(
                "warning",
                "sprite has no parent bone and no vertex groups matching armature bones — "
                "writer will fall back to empty bone field",
                obj.name,
            )
        )

    if vertex_groups and not matching_groups:
        issues.append(
            Issue(
                "error",
                "sprite has vertex groups but none resolve to bones — "
                "writer will raise RuntimeError at export",
                obj.name,
            )
        )

    return issues


def _validate_atlas_files(scene_objects: list[Any]) -> list[Issue]:
    """Check that every linked image used as an atlas resolves on disk."""
    issues: list[Issue] = []
    seen: set[str] = set()
    for obj in scene_objects:
        for image, fp_raw in _iter_object_atlas_images(obj, seen):
            if not _atlas_path_resolves(fp_raw):
                issues.append(_atlas_missing_issue(obj, fp_raw))
            del image  # silence "unused" — kept available for future checks
    return issues


def _iter_object_atlas_images(obj: Any, seen: set[str]) -> Iterator[tuple[Any, str]]:
    """Yield (image, filepath) tuples for unique TEX_IMAGE nodes on `obj`."""
    for slot in getattr(obj, "material_slots", ()):
        material = getattr(slot, "material", None)
        if material is None or not getattr(material, "use_nodes", False):
            continue
        tree = getattr(material, "node_tree", None)
        if tree is None:
            continue
        for node in tree.nodes:
            image, fp_raw = _texture_image_filepath(node)
            if fp_raw and fp_raw not in seen:
                seen.add(fp_raw)
                yield image, fp_raw


def _texture_image_filepath(node: Any) -> tuple[Any, str]:
    """Return (image, raw_filepath) for a TEX_IMAGE node, or (None, '')."""
    if getattr(node, "type", "") != "TEX_IMAGE":
        return None, ""
    image = getattr(node, "image", None)
    if image is None:
        return None, ""
    return image, str(getattr(image, "filepath", "") or "")


def _atlas_path_resolves(fp_raw: str) -> bool:
    resolved = _abspath_or_none(fp_raw)
    return resolved is not None and Path(resolved).exists()


def _atlas_missing_issue(obj: Any, fp_raw: str) -> Issue:
    return Issue(
        "warning",
        f"atlas image {fp_raw!r} not found on disk — Godot will warn at import",
        getattr(obj, "name", None),
    )


def _abspath_or_none(filepath: str) -> str | None:
    try:
        import bpy
    except ImportError:
        return filepath if not filepath.startswith("//") else None
    return str(bpy.path.abspath(filepath))
