"""Bone-follow health checks: double-drive and a stale follow inverse.

Both conditions are silent-wrong-render classes (spec 080 D7/D8):

- **Double-drive**: an object carrying BOTH a real ``parent_type == "BONE"``
  parent AND a Proscenio Child Of follow gets the bone's influence twice -
  it flies off the character the moment the bone poses. The Proscenio bind
  operators never author this (bind drops the parent keep-world first), so
  it only arises from hand-authoring; Clear Bone Follow / Unbind fixes it
  keep-world.
- **Stale inverse**: the Child Of ``inverse_matrix`` is a snapshot that
  cancels the bone rest AT BIND TIME. Editing the bone rest in Edit Mode -
  or moving the rig object - leaves it cancelling the old rest, so the
  follower sits offset at rest with no error anywhere; Godot (which derives
  the cancel from the live rest) then disagrees with the Blender viewport.
  Re-running Bind recomputes the inverse.

Staleness is detected without inverting anything: the stored inverse times
the current rest world matrix must be the identity. Pure attribute walks +
inline 4x4 products, so the checks run under plain pytest with list-of-list
matrix fakes and against live mathutils matrices identically.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from ..._shared.bone_follow_resolve import (
    ELEMENT_FOLLOW_CONSTRAINT,
    SLOT_FOLLOW_CONSTRAINT,
    bone_parent_name,
    follow_subtarget,
)
from .._shared import name_of
from ..issue import Issue

# Anything indexable as ``m[i][j]`` yielding floats - a mathutils Matrix and a
# list-of-lists test fake both satisfy it, and it carries no explicit Any (the
# addon's mypy profile bans that) nor an ineffectual ``...`` Protocol body.
_Matrix4 = Sequence[Sequence[float]]

_FOLLOW_NAMES = (SLOT_FOLLOW_CONSTRAINT, ELEMENT_FOLLOW_CONSTRAINT)
_IDENTITY_TOLERANCE = 1e-4


def validate_bone_follow(scene_objects: list[object]) -> list[Issue]:
    """Warnings for double-driven followers and stale follow inverses."""
    issues: list[Issue] = []
    for obj in scene_objects:
        follow = _proscenio_follow(obj)
        if follow is None:
            continue
        obj_name = name_of(obj)
        parent_bone = bone_parent_name(obj)
        if parent_bone:
            issues.append(
                Issue(
                    "warning",
                    (
                        f"'{obj_name}' is double-driven: bone parent "
                        f"'{parent_bone}' AND the Proscenio follow constraint "
                        "both apply the bone - Clear Bone Follow (or Unbind) "
                        "keeps the position and drops both"
                    ),
                    obj_name,
                )
            )
        issues.extend(_check_stale_inverse(follow, obj_name))
    return issues


def _proscenio_follow(obj: object) -> object | None:
    """The live Proscenio Child Of follow on ``obj`` (either kind), or None."""
    for constraint_name in _FOLLOW_NAMES:
        if not follow_subtarget(obj, constraint_name):
            continue
        for con in getattr(obj, "constraints", ()):
            if getattr(con, "name", "") == constraint_name:
                return cast("object", con)
    return None


def _check_stale_inverse(con: object, obj_name: str) -> list[Issue]:
    """Warning when the stored inverse no longer cancels the current rest."""
    subtarget = str(getattr(con, "subtarget", ""))
    armature = getattr(con, "target", None)
    if armature is None or not subtarget:
        return []
    bone = _data_bone(armature, subtarget)
    if bone is None:
        return [
            Issue(
                "warning",
                (
                    f"'{obj_name}' follows bone '{subtarget}' which no longer "
                    "exists on the rig - re-Bind to a live bone"
                ),
                obj_name,
            )
        ]
    arm_world = getattr(armature, "matrix_world", None)
    matrix_local = getattr(bone, "matrix_local", None)
    inverse = getattr(con, "inverse_matrix", None)
    if arm_world is None or matrix_local is None or inverse is None:
        return []
    rest_world = _matmul4(arm_world, matrix_local)
    if _is_identity(_matmul4(inverse, rest_world)):
        return []
    return [
        Issue(
            "warning",
            (
                f"'{obj_name}' has a stale follow of bone '{subtarget}': the "
                "rig's rest changed since the bind, so Blender and the Godot "
                "import disagree on its rest position - re-run Bind to Bone "
                "to recompute the follow"
            ),
            obj_name,
        )
    ]


def _data_bone(armature: object, bone_name: str) -> object | None:
    data = getattr(armature, "data", None)
    bones = getattr(data, "bones", None)
    if bones is None:
        return None
    getter = getattr(bones, "get", None)
    if callable(getter):
        return cast("object | None", getter(bone_name))
    for bone in bones:
        if getattr(bone, "name", "") == bone_name:
            return cast("object", bone)
    return None


def _matmul4(a: _Matrix4, b: _Matrix4) -> list[list[float]]:
    """Row-major 4x4 product over anything indexable as ``m[i][j]``."""
    return [
        [sum(float(a[i][k]) * float(b[k][j]) for k in range(4)) for j in range(4)] for i in range(4)
    ]


def _is_identity(m: list[list[float]]) -> bool:
    return all(
        abs(m[i][j] - (1.0 if i == j else 0.0)) <= _IDENTITY_TOLERANCE
        for i in range(4)
        for j in range(4)
    )
