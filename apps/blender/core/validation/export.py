"""Full pre-export validation pass - walks the scene + atlas files."""

from __future__ import annotations

import math
from collections.abc import Iterator, Sequence
from pathlib import Path

from .._shared.material_images import iter_material_node_images
from .._shared.props_access import resolve_export_armature
from ..slot.slot_emit import is_slot_empty
from ._shared import abspath_or_none, armature_bone_names, name_of
from .active_element import validate_active_element
from .active_slot import validate_active_slot
from .issue import Issue

# Orientation guards: the exporter assumes the 2D rig lives in the world XZ
# plane and drops the depth (Y) axis. A bone whose rest direction tilts out of
# that plane, or a mesh carrying depth on the dropped axis, exports silently
# wrong; these warn-only checks surface that before a broken scene ships.
_PLANE_TOLERANCE = 0.1  # sin of the off-plane angle (~5.7 degrees)
_FLATNESS_TOLERANCE = 0.1  # mesh depth as a fraction of its in-plane size


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
    picked_armature = resolve_export_armature(scene)
    available_bones = armature_bone_names(picked_armature)
    issues.extend(_validate_bone_orientation(picked_armature))

    for obj in scene_objects:
        if getattr(obj, "type", None) != "MESH":
            continue
        for active_issue in validate_active_element(obj):
            issues.append(active_issue)
        issues.extend(_validate_element_against_armature(obj, available_bones))
        issues.extend(_validate_mesh_flatness(obj))

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


def _validate_bone_orientation(armature: object) -> list[Issue]:
    """Warn for rest bones whose direction tilts out of the world XZ plane."""
    data = getattr(armature, "data", None)
    issues: list[Issue] = []
    for bone in getattr(data, "bones", ()):
        head = getattr(bone, "head_local", None)
        tail = getattr(bone, "tail_local", None)
        if head is None or tail is None:
            continue
        if _direction_off_plane(head, tail):
            issues.append(
                Issue(
                    "warning",
                    "bone rest direction tilts out of the XZ plane - the exporter "
                    "projects bone angles onto XZ and will misread this bone",
                    name_of(bone),
                )
            )
    return issues


def _direction_off_plane(head: object, tail: object) -> bool:
    """True when the head->tail direction carries a significant depth (Y) component."""
    dx = float(getattr(tail, "x", 0.0)) - float(getattr(head, "x", 0.0))
    dy = float(getattr(tail, "y", 0.0)) - float(getattr(head, "y", 0.0))
    dz = float(getattr(tail, "z", 0.0)) - float(getattr(head, "z", 0.0))
    total = math.sqrt(dx * dx + dy * dy + dz * dz)
    if total < 1e-6:
        return False  # zero-length bone has no direction to judge
    return abs(dy) / total > _PLANE_TOLERANCE


def _validate_mesh_flatness(obj: object) -> list[Issue]:
    """Warn for meshes that are not planar - 3D geometry the exporter flattens.

    Frame-independent: a cutout sits in one plane, so its thinnest extent is
    near zero whatever plane it lies in. Comparing the smallest axis spread to
    the largest catches a genuinely 3D mesh without assuming which axis is the
    depth (the writer drops world Y, but a quad may be authored in local XY or
    XZ, so a fixed-axis test would false-warn one of them).
    """
    mesh = getattr(obj, "data", None)
    coords = [v.co for v in getattr(mesh, "vertices", ()) if getattr(v, "co", None) is not None]
    if len(coords) < 2:
        return []
    spreads = sorted(
        max(float(getattr(c, axis)) for c in coords) - min(float(getattr(c, axis)) for c in coords)
        for axis in ("x", "y", "z")
    )
    extent, thickness = spreads[2], spreads[0]
    if extent < 1e-6:
        return []  # degenerate (point) mesh, nothing to flatten
    if thickness > _FLATNESS_TOLERANCE * extent:
        return [
            Issue(
                "warning",
                "element is not flat - it has thickness on every axis, so the "
                "exporter's flatten-to-plane will lose geometry",
                name_of(obj),
            )
        ]
    return []


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
