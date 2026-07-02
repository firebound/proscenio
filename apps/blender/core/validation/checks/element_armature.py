"""Element-vs-armature check: parent-bone / vertex-group resolution warnings."""

from __future__ import annotations

from ...slot.slot_emit import is_slot_empty
from .._shared import name_of
from ..issue import Issue


def validate_element_against_armature(obj: object, bones: set[str]) -> list[Issue]:
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
