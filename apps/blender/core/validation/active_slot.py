"""Active-slot validation (SPEC 004 D9 + D10) - cheap, runs every redraw."""

from __future__ import annotations

from typing import Any

from .issue import Issue


def validate_active_slot(obj: Any) -> list[Issue]:
    """Return per-active-Empty slot issues.

    Validates: (1) at least one child mesh, (2) ``slot_default`` resolves
    to an existing child, (3) child meshes share the Empty's
    ``parent_bone`` if any, (4) no slot child carries a
    ``bone_transform``-shaped fcurve (warning - visibility toggling
    makes bone keys silent unless the child is the visible attachment
    at that frame).
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
