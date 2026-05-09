"""Full pre-export validation pass -- walks the scene + atlas files."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ._shared import abspath_or_none, armature_bone_names
from .active_slot import validate_active_slot
from .active_sprite import validate_active_sprite
from .issue import Issue


def validate_export(scene: Any) -> list[Issue]:
    """Full pre-export pass. Walks the scene, hits the disk for the atlas.

    Returns every issue found; the caller decides whether to abort.
    Errors block export by convention; warnings inform but allow the
    operator to proceed.
    """
    issues: list[Issue] = []
    scene_objects = list(getattr(scene, "objects", ()))

    armatures = [o for o in scene_objects if getattr(o, "type", None) == "ARMATURE"]
    if not armatures:
        issues.append(Issue("error", "scene has no Armature -- Proscenio export requires one"))
        return issues

    available_bones = armature_bone_names(armatures[0])

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
                "sprite has no parent bone and no vertex groups matching armature bones -- "
                "writer will fall back to empty bone field",
                obj.name,
            )
        )

    if vertex_groups and not matching_groups:
        issues.append(
            Issue(
                "error",
                "sprite has vertex groups but none resolve to bones -- "
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
            del image  # silence "unused" -- kept available for future checks
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
    resolved = abspath_or_none(fp_raw)
    return resolved is not None and Path(resolved).exists()


def _atlas_missing_issue(obj: Any, fp_raw: str) -> Issue:
    return Issue(
        "warning",
        f"atlas image {fp_raw!r} not found on disk -- Godot will warn at import",
        getattr(obj, "name", None),
    )
