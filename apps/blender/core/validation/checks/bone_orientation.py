"""Bone rest-orientation check: warn for bones tilted out of the world XZ plane."""

from __future__ import annotations

import math

from .._shared import name_of
from ..issue import Issue

# Orientation guard: the exporter assumes the 2D rig lives in the world XZ
# plane and drops the depth (Y) axis. A bone whose rest direction tilts out of
# that plane exports silently wrong; this warn-only check surfaces that.
_PLANE_TOLERANCE = 0.1  # sin of the off-plane angle (~5.7 degrees)


def validate_bone_orientation(armature: object) -> list[Issue]:
    """Warn for rest bones whose direction tilts out of the world XZ plane."""
    data = getattr(armature, "data", None)
    # head_local / tail_local are armature-space; the exporter projects them
    # through the armature object's matrix_world (compute_bone_world_godot), so
    # match that here or a rotated / scaled armature object would make this check
    # disagree with the export. matrix_world is absent on the bpy-free test fakes
    # (which author rigs at identity), so those fall back to the local coords.
    matrix_world = getattr(armature, "matrix_world", None)
    issues: list[Issue] = []
    for bone in getattr(data, "bones", ()):
        head = getattr(bone, "head_local", None)
        tail = getattr(bone, "tail_local", None)
        if head is None or tail is None:
            continue
        if matrix_world is not None:
            head = matrix_world @ head
            tail = matrix_world @ tail
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
