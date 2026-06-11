"""Full pre-export validation pass - walks the scene + atlas files."""

from __future__ import annotations

import math
from collections.abc import Iterator, Sequence
from pathlib import Path

from .._shared.action_fcurves import action_fcurves
from .._shared.cp_keys import (
    PROSCENIO_HFRAMES,
    PROSCENIO_REGION_MODE,
    PROSCENIO_TYPE,
    PROSCENIO_VFRAMES,
)
from .._shared.material_images import iter_material_node_images
from .._shared.pg_cp_fallback import read_field
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

# How close a sprite_frame quad's UV bounds must sit to the full 0-1 sheet
# before the hframes/vframes grid is considered correctly authored.
_UV_SHEET_TOLERANCE = 0.02

# Pose-bone transform channels that count as "keyed" for the IK bake gate.
_IK_TRANSFORM_PROPS = frozenset(
    {"location", "rotation_euler", "rotation_quaternion", "rotation_axis_angle", "scale"}
)


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
    issues.extend(_validate_ik_bake(picked_armature))

    for obj in scene_objects:
        if getattr(obj, "type", None) != "MESH":
            continue
        for active_issue in validate_active_element(obj):
            issues.append(active_issue)
        issues.extend(_validate_element_against_armature(obj, available_bones))
        issues.extend(_validate_mesh_flatness(obj))
        issues.extend(_validate_sprite_frame_uvs(obj))

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


def _validate_ik_bake(armature: object) -> list[Issue]:
    """Error for an animated-target IK chain whose member bones carry no keyframes.

    Animating only the IK target and never baking is a silent wrong export: the
    writer reads raw fcurves, finds none on the chain bones, and writes flat
    intermediate bones - a wrong ``.proscenio`` with no warning. The message
    names the chain tip and points at the Bake IK to Keyframes fix.
    """
    action = _armature_action(armature)
    if action is None:
        return []
    keyed_bones = _keyed_transform_bones(action)
    issues: list[Issue] = []
    pose = getattr(armature, "pose", None)
    for pose_bone in getattr(pose, "bones", ()):
        for constraint in getattr(pose_bone, "constraints", ()):
            if not _is_active_ik(constraint):
                continue
            if not _ik_target_animated(constraint, armature, keyed_bones):
                continue
            members = _ik_chain_members(pose_bone, int(getattr(constraint, "chain_count", 0) or 0))
            if any(name in keyed_bones for name in members):
                continue
            issues.append(
                Issue(
                    "error",
                    "IK chain is driven by an animated target but its bones carry no "
                    "keyframes - the exporter reads raw fcurves and writes flat bones. "
                    "Run Bake IK to Keyframes before export",
                    name_of(pose_bone),
                )
            )
    return issues


def _armature_action(obj: object) -> object | None:
    anim = getattr(obj, "animation_data", None)
    return getattr(anim, "action", None) if anim is not None else None


def _is_active_ik(constraint: object) -> bool:
    """True for an IK constraint that actually influences the pose."""
    if getattr(constraint, "type", None) != "IK":
        return False
    if bool(getattr(constraint, "mute", False)):
        return False
    return float(getattr(constraint, "influence", 1.0)) > 0.0


def _ik_target_animated(constraint: object, armature: object, keyed_bones: set[str]) -> bool:
    """True when the constraint's IK goal is driven by animation.

    Same-armature targets (the usual control bone) are animated when the
    subtarget bone is keyed; a separate target object counts when it carries any
    action fcurve.
    """
    target = getattr(constraint, "target", None)
    if target is None:
        return False
    if target is armature:
        subtarget = str(getattr(constraint, "subtarget", ""))
        return bool(subtarget) and subtarget in keyed_bones
    target_action = _armature_action(target)
    return target_action is not None and any(True for _ in action_fcurves(target_action))


def _ik_chain_members(pose_bone: object, chain_count: int) -> list[str]:
    """Bone names in the IK chain: the constrained bone plus its parents.

    ``chain_count`` counts bones from the constrained bone toward the root;
    0 means the whole parent chain.
    """
    names: list[str] = []
    current: object | None = pose_bone
    remaining = chain_count if chain_count > 0 else -1
    while current is not None and remaining != 0:
        names.append(str(getattr(current, "name", "")))
        current = getattr(current, "parent", None)
        if remaining > 0:
            remaining -= 1
    return names


def _keyed_transform_bones(action: object) -> set[str]:
    """Pose-bone names that carry a transform fcurve in the action."""
    keyed: set[str] = set()
    for fcurve in action_fcurves(action):
        bone, prop = _split_pose_bone_path(str(getattr(fcurve, "data_path", "")))
        if bone is not None and prop in _IK_TRANSFORM_PROPS:
            keyed.add(bone)
    return keyed


def _split_pose_bone_path(data_path: str) -> tuple[str | None, str | None]:
    """Parse ``pose.bones["name"].prop`` into ``(name, prop)``; ``(None, None)``
    for any other path."""
    prefix = 'pose.bones["'
    if not data_path.startswith(prefix):
        return None, None
    end = data_path.find('"]', len(prefix))
    if end == -1:
        return None, None
    bone = data_path[len(prefix) : end]
    rest = data_path[end + 2 :].lstrip(".")
    prop = rest.split(".")[-1].split("[")[0] if rest else ""
    return bone, prop


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


def _validate_sprite_frame_uvs(obj: object) -> list[Issue]:
    """Warn when a sheet-sliced sprite's quad UVs do not span the full 0-1 sheet.

    An ``auto`` region-mode sprite with a multi-frame grid (hframes * vframes > 1)
    derives its texture_region from the quad's UV bounds, which Godot then slices
    into the grid. UVs hand-shrunk to a sub-rect silently garble that grid
    relative to the full-sheet preview. Manual-region sprites address an explicit
    rect, so the full-sheet expectation does not apply to them.
    """
    if not _is_sheet_sliced_sprite(obj):
        return []
    bounds = _uv_bounds(obj)
    if bounds is None:
        return []
    u_min, u_max, v_min, v_max = bounds
    if _uv_spans_sheet(u_min, u_max, v_min, v_max):
        return []
    return [
        Issue(
            "warning",
            f"sprite UVs span [{u_min:.2f}, {u_max:.2f}] x [{v_min:.2f}, {v_max:.2f}], not "
            f"the full 0-1 sheet - the hframes/vframes grid will be garbled in Godot",
            name_of(obj),
        )
    ]


def _is_sheet_sliced_sprite(obj: object) -> bool:
    """True for a multi-frame sprite whose region comes from UV bounds (auto)."""
    element_type = str(
        read_field(obj, pg_field="element_type", cp_key=PROSCENIO_TYPE, default="mesh")
    )
    if element_type != "sprite":
        return False
    region_mode = str(
        read_field(obj, pg_field="region_mode", cp_key=PROSCENIO_REGION_MODE, default="auto")
    )
    if region_mode == "manual":
        return False
    hframes = int(read_field(obj, pg_field="hframes", cp_key=PROSCENIO_HFRAMES, default=1))
    vframes = int(read_field(obj, pg_field="vframes", cp_key=PROSCENIO_VFRAMES, default=1))
    return hframes * vframes > 1


def _uv_bounds(obj: object) -> tuple[float, float, float, float] | None:
    """Min/max (u, v) over the active UV layer, or None when there is none."""
    mesh = getattr(obj, "data", None)
    uv_layers = getattr(mesh, "uv_layers", None)
    active = getattr(uv_layers, "active", None)
    data = getattr(active, "data", None)
    if not data:
        return None
    us = [float(loop.uv[0]) for loop in data]
    vs = [float(loop.uv[1]) for loop in data]
    if not us:
        return None
    return min(us), max(us), min(vs), max(vs)


def _uv_spans_sheet(u_min: float, u_max: float, v_min: float, v_max: float) -> bool:
    return (
        u_min <= _UV_SHEET_TOLERANCE
        and v_min <= _UV_SHEET_TOLERANCE
        and u_max >= 1.0 - _UV_SHEET_TOLERANCE
        and v_max >= 1.0 - _UV_SHEET_TOLERANCE
    )


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
