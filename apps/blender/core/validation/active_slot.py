"""Active-slot validation - cheap, runs every redraw."""

from __future__ import annotations

from collections.abc import Iterable

from .._shared.action_fcurves import action_fcurves, object_action_fcurves
from .._shared.cp_keys import PROSCENIO_SLOT_BONE, PROSCENIO_SLOT_DEFAULT
from .._shared.pg_cp_fallback import read_field
from ..slot.slot_emit import is_slot_empty
from ._shared import name_of
from .issue import Issue


def validate_active_slot(obj: object) -> list[Issue]:
    """Return per-active-Empty slot issues.

    Validates: (1) at least one child mesh, (2) ``slot_default`` resolves
    to an existing child, (3) child meshes share the Empty's
    ``parent_bone`` if any, (4) no slot child carries a
    ``bone_transform``-shaped fcurve, (5) no two attachments are keyed visible
    at the same frame within one animation (spec 079 R2).
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
    issues.extend(_check_slot_attachment_overlap(children, name))
    return issues


def _is_active_slot(obj: object) -> bool:
    return is_slot_empty(obj)


def _check_slot_default(obj: object, children: list[object], obj_name: str) -> list[Issue]:
    # Read the way the writer emits it (PG first, raw CP fallback) so a
    # proscenio_slot_default edited directly in the Custom Properties UI is
    # validated against the same value the export will carry.
    slot_default = str(read_field(obj, cp_key=PROSCENIO_SLOT_DEFAULT, default=""))
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


def slot_parent_bone(obj: object) -> str:
    """The bone ``obj`` follows, or "" when it follows none.

    Reads the ``slot_bone`` field first (the object-parent + Child Of
    convention), then a real ``parent_type == "BONE"`` parent - the same
    order the writer emits (``writer/slots.py``), so the Active Slot panel,
    the slot validators, and the export never disagree about the followed
    bone. A leftover ``parent_bone`` on an OBJECT-parented slot with no
    field is not a live follow.

    Shared by the validators and the panel so the "no parent bone" notion
    has a single definition.
    """
    slot_bone = str(read_field(obj, cp_key=PROSCENIO_SLOT_BONE, default=""))
    if slot_bone:
        return slot_bone
    if getattr(obj, "parent_type", "") != "BONE":
        return ""
    return str(getattr(obj, "parent_bone", ""))


def _check_slot_child_bones(obj: object, children: list[object], obj_name: str) -> list[Issue]:
    slot_bone = slot_parent_bone(obj)
    if not slot_bone:
        return []
    issues: list[Issue] = []
    for child in children:
        child_bone = slot_parent_bone(child)
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
    for fcurve in action_fcurves(action):
        path = str(getattr(fcurve, "data_path", ""))
        if path.startswith(("location", "rotation", "scale")):
            return True
    return False


# hide_render stores 0.0 (shown) / 1.0 (hidden); treat < 0.5 as visible, matching
# the writer's collapse (slot_animations._VISIBLE_THRESHOLD).
_VISIBLE_THRESHOLD = 0.5


def _check_slot_attachment_overlap(children: list[object], obj_name: str) -> list[Issue]:
    """Warn when 2+ attachments are keyed visible at one frame (spec 079 R2).

    The writer collapses 2+ simultaneously-visible attachments to the first in
    child order, so an overlap is an authoring smell, not a hard error: the
    exported swap silently drops the rest. This is the lazy + inline check that
    surfaces it. Attachments are grouped by the animation they are keyed in (their
    active action's name) so an overlap only fires within one animation, never
    across two unrelated clips.
    """
    by_animation: dict[str, dict[str, list[tuple[float, bool]]]] = {}
    for child in children:
        anim_name, keys = _visibility_timeline(child)
        if keys:
            by_animation.setdefault(anim_name, {})[name_of(child)] = keys

    issues: list[Issue] = []
    for anim_name, timelines in by_animation.items():
        if len(timelines) < 2:
            continue
        overlap = _first_overlap_frame(timelines)
        if overlap is None:
            continue
        frame, visible_names = overlap
        anim_label = f" in '{anim_name}'" if anim_name else ""
        issues.append(
            Issue(
                "warning",
                f"slot '{obj_name}': attachments {', '.join(visible_names)} are all "
                f"visible at frame {frame:.0f}{anim_label} - the export shows only "
                f"'{visible_names[0]}'; hide the rest",
                obj_name,
            )
        )
    return issues


def _visibility_timeline(obj: object) -> tuple[str, list[tuple[float, bool]]]:
    """The ``(animation-name, sorted (frame, visible) keys)`` for ``obj``.

    Reads ``obj``'s own ``hide_render`` keyframes scoped to its active action
    (``object_action_fcurves`` - its slot's channelbag on a 4.4+ slotted action,
    or its dedicated 4.2 action), so a mesh sharing a slotted action with its
    siblings reads only its own curve. Empty when ``obj`` keys no visibility.
    """
    anim = getattr(obj, "animation_data", None)
    action = getattr(anim, "action", None) if anim is not None else None
    anim_name = str(getattr(action, "name", "")) if action is not None else ""
    keys: list[tuple[float, bool]] = []
    for fcurve in object_action_fcurves(obj):
        if str(getattr(fcurve, "data_path", "")) != "hide_render":
            continue
        for kp in getattr(fcurve, "keyframe_points", ()) or ():
            co = getattr(kp, "co", None)
            if co is None:
                continue
            keys.append((float(co.x), float(co.y) < _VISIBLE_THRESHOLD))
    keys.sort(key=lambda pair: pair[0])
    return anim_name, keys


def _first_overlap_frame(
    timelines: dict[str, list[tuple[float, bool]]],
) -> tuple[float, list[str]] | None:
    """The earliest event frame where 2+ attachments hold visible, or ``None``.

    Evaluates each attachment's visibility with constant hold (the last key at or
    before the frame), matching the CONSTANT authoring interpolation and the
    writer's ``_visible_at``.
    """
    event_frames = sorted({frame for keys in timelines.values() for frame, _ in keys})
    for frame in event_frames:
        visible = [name for name, keys in timelines.items() if _visible_at(keys, frame)]
        if len(visible) >= 2:
            return frame, visible
    return None


def _visible_at(keys: list[tuple[float, bool]], frame: float) -> bool:
    """Constant-hold visibility at ``frame`` (the last key at or before it)."""
    visible = keys[0][1]
    for key_frame, key_visible in keys:
        if key_frame <= frame:
            visible = key_visible
        else:
            break
    return visible
