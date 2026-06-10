"""Active-slot validation - cheap, runs every redraw."""

from __future__ import annotations

from collections.abc import Iterable

from ..slot.slot_emit import is_slot_empty
from ._shared import name_of
from .issue import Issue


def validate_active_slot(obj: object) -> list[Issue]:
    """Return per-active-Empty slot issues.

    Validates: (1) at least one child mesh, (2) ``slot_default`` resolves
    to an existing child, (3) child meshes share the Empty's
    ``parent_bone`` if any, (4) no slot child carries a
    ``bone_transform``-shaped fcurve.
    """
    if not _is_active_slot(obj):
        return []
    children_attr: Iterable[object] = getattr(obj, "children", ())
    children = [c for c in children_attr if getattr(c, "type", None) == "MESH"]
    name = name_of(obj)
    if not children:
        return [Issue("error", f"slot '{name}' has no MESH children", name)]

    issues: list[Issue] = []
    issues.extend(_check_slot_default(obj, children, name))
    issues.extend(_check_slot_child_bones(obj, children, name))
    issues.extend(_check_slot_child_transform_keys(children))
    return issues


def _is_active_slot(obj: object) -> bool:
    return is_slot_empty(obj)


def _check_slot_default(obj: object, children: list[object], obj_name: str) -> list[Issue]:
    props = getattr(obj, "proscenio", None)
    slot_default = str(getattr(props, "slot_default", "")) if props is not None else ""
    if not slot_default:
        return []
    child_names = {name_of(c) for c in children}
    if slot_default in child_names:
        return []
    return [
        Issue(
            "error",
            f"slot default '{slot_default}' is not a child of '{obj_name}'",
            obj_name,
        )
    ]


def _slot_bone_of(obj: object) -> str:
    if getattr(obj, "parent_type", "") != "BONE":
        return ""
    return str(getattr(obj, "parent_bone", ""))


def _check_slot_child_bones(obj: object, children: list[object], obj_name: str) -> list[Issue]:
    slot_bone = _slot_bone_of(obj)
    if not slot_bone:
        return []
    issues: list[Issue] = []
    for child in children:
        child_bone = _slot_bone_of(child)
        if child_bone and child_bone != slot_bone:
            child_name = name_of(child)
            issues.append(
                Issue(
                    "warning",
                    f"attachment '{child_name}' parent bone '{child_bone}' "
                    f"differs from slot bone '{slot_bone}'",
                    child_name,
                )
            )
    _ = obj_name  # accept for symmetry with _check_slot_default
    return issues


def _check_slot_child_transform_keys(children: list[object]) -> list[Issue]:
    issues: list[Issue] = []
    for child in children:
        if _has_bone_transform_keys(child):
            child_name = name_of(child)
            issues.append(
                Issue(
                    "warning",
                    f"slot child '{child_name}' carries bone-transform keyframes; "
                    f"visibility is the only thing the slot animates",
                    child_name,
                )
            )
    return issues


def _has_bone_transform_keys(obj: object) -> bool:
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
