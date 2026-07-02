"""IK-bake check: error for an animated-target IK chain whose bones carry no keyframes."""

from __future__ import annotations

from ..._shared.action_fcurves import action_fcurves
from .._shared import name_of
from ..issue import Issue

# Pose-bone transform channels that count as "keyed" for the IK bake gate.
_IK_TRANSFORM_PROPS = frozenset(
    {"location", "rotation_euler", "rotation_quaternion", "rotation_axis_angle", "scale"}
)


def validate_ik_bake(armature: object) -> list[Issue]:
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
