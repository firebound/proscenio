"""Full pre-export validation pass - walks the scene + atlas files."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from pathlib import Path

from .._shared.material_images import iter_material_node_images
from .._shared.props_access import resolve_export_armature
from ..slot.slot_emit import is_slot_empty
from ._shared import abspath_or_none, armature_bone_names, name_of
from .active_element import validate_active_element
from .active_slot import validate_active_slot
from .issue import Issue


def validate_export(scene: object) -> list[Issue]:
    """Full pre-export pass. Walks the scene, hits the disk for the atlas.

    Returns every issue found; the caller decides whether to abort.
    Errors block export by convention; warnings inform but allow the
    operator to proceed.
    """
    issues: list[Issue] = []
    scene_objects = list(getattr(scene, "objects", ()))

    armatures = [o for o in scene_objects if getattr(o, "type", None) == "ARMATURE"]
    if not armatures:
        issues.append(Issue("error", "scene has no Armature - Proscenio export requires one"))
        return issues

    # Same picker-first resolver the writer uses, so validate and export
    # never disagree on which rig supplies the bones in a multi-armature scene.
    available_bones = armature_bone_names(resolve_export_armature(scene))

    for obj in scene_objects:
        if getattr(obj, "type", None) != "MESH":
            continue
        for active_issue in validate_active_element(obj):
            issues.append(active_issue)
        issues.extend(_validate_element_against_armature(obj, available_bones))

    issues.extend(_validate_slots(scene_objects))
    issues.extend(_validate_atlas_files(scene_objects))

    return issues


def _validate_slots(scene_objects: Sequence[object]) -> list[Issue]:
    """Walk slot Empties + cross-check name uniqueness."""
    seen: set[str] = set()
    issues: list[Issue] = []
    for obj in scene_objects:
        if not is_slot_empty(obj):
            continue
        name = name_of(obj)
        if name in seen:
            issues.append(Issue("error", f"duplicate slot name '{name}'", name))
        seen.add(name)
        issues.extend(validate_active_slot(obj))
    return issues


def _validate_element_against_armature(obj: object, bones: set[str]) -> list[Issue]:
    issues: list[Issue] = []

    parent_bone = getattr(obj, "parent_bone", "")
    has_parent_bone = bool(parent_bone) and parent_bone in bones
    vertex_groups = getattr(obj, "vertex_groups", ())
    matching_groups = [vg for vg in vertex_groups if str(vg.name) in bones]
    name = name_of(obj)

    # Slot attachments inherit their bone through the slot Empty, so the
    # missing-bone warning is a false positive on every slot scene.
    parented_to_slot = is_slot_empty(getattr(obj, "parent", None))

    if not has_parent_bone and not matching_groups and not parented_to_slot:
        issues.append(
            Issue(
                "warning",
                "element has no parent bone and no vertex groups matching armature bones - "
                "writer will fall back to empty bone field",
                name,
            )
        )

    if vertex_groups and not matching_groups:
        issues.append(
            Issue(
                "error",
                "element has vertex groups but none resolve to bones - "
                "writer will raise RuntimeError at export",
                name,
            )
        )

    return issues


def _validate_atlas_files(scene_objects: Sequence[object]) -> list[Issue]:
    """Check that every linked image used as an atlas resolves on disk."""
    issues: list[Issue] = []
    seen: set[str] = set()
    for obj in scene_objects:
        for fp_raw in _iter_object_atlas_filepaths(obj, seen):
            if not _atlas_path_resolves(fp_raw):
                issues.append(_atlas_missing_issue(obj, fp_raw))
    return issues


def _iter_object_atlas_filepaths(obj: object, seen: set[str]) -> Iterator[str]:
    """Yield filepaths for unique TEX_IMAGE images on `obj`'s material slots."""
    for slot in getattr(obj, "material_slots", ()):
        for image in iter_material_node_images(getattr(slot, "material", None)):
            fp_raw = str(getattr(image, "filepath", "") or "")
            if fp_raw and fp_raw not in seen:
                seen.add(fp_raw)
                yield fp_raw


def _atlas_path_resolves(fp_raw: str) -> bool:
    resolved = abspath_or_none(fp_raw)
    return resolved is not None and Path(resolved).exists()


def _atlas_missing_issue(obj: object, fp_raw: str) -> Issue:
    return Issue(
        "warning",
        f"atlas image {fp_raw!r} not found on disk - Godot will warn at import",
        name_of(obj),
    )
