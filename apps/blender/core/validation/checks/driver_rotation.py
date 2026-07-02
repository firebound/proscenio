"""Driver rotation-mode check: warn when a driving bone is not in XYZ Euler mode."""

from __future__ import annotations

from collections.abc import Iterator, Sequence

from ...armature.driver_targets import is_proscenio_driver_path
from .._shared import name_of
from ..issue import Issue

# A Drive-from-Bone driver reads the source bone rotation as XYZ Euler (the
# create operator sets the driver variable's rotation_mode to XYZ). A bone left
# in Quaternion (or a non-XYZ Euler order) feeds the driver a value that does
# not track the keyed rotation 1:1, so the animation reads wrong with no error.
# Warn-only - Convert rotation to Euler is the one-click fix.
_DRIVER_ROTATION_MODE = "XYZ"


def validate_driver_rotation_modes(scene_objects: Sequence[object]) -> list[Issue]:
    """Warn when a bone driving a sprite is not in the XYZ Euler mode its driver assumes."""
    issues: list[Issue] = []
    for obj in scene_objects:
        if getattr(obj, "type", None) != "MESH":
            continue
        for armature, bone_name in _unique_driver_rotation_sources(obj):
            mode = _pose_bone_rotation_mode(armature, bone_name)
            if mode is not None and mode != _DRIVER_ROTATION_MODE:
                issues.append(
                    Issue(
                        "warning",
                        f"bone '{bone_name}' drives this sprite's rotation but is in "
                        f"{mode} mode, not XYZ Euler - the driver reads XYZ, so the "
                        "animation will not track. Run Convert rotation to Euler",
                        name_of(obj),
                    )
                )
    return issues


def _unique_driver_rotation_sources(obj: object) -> Iterator[tuple[object, str]]:
    """Yield the unique ``(armature, bone_name)`` ROT_* sources of obj's proscenio drivers."""
    seen: set[tuple[str, str]] = set()
    for fcurve in _proscenio_driver_fcurves(obj):
        for armature, bone_name in _driver_rotation_sources(getattr(fcurve, "driver", None)):
            key = (name_of(armature), bone_name)
            if key in seen:
                continue
            seen.add(key)
            yield armature, bone_name


def _proscenio_driver_fcurves(obj: object) -> Iterator[object]:
    """Yield the object's driver fcurves whose data_path is a proscenio idprop."""
    anim = getattr(obj, "animation_data", None)
    for fcurve in getattr(anim, "drivers", ()):
        if is_proscenio_driver_path(str(getattr(fcurve, "data_path", ""))):
            yield fcurve


def _driver_rotation_sources(driver: object) -> Iterator[tuple[object, str]]:
    """Yield ``(armature_obj, bone_name)`` for each ROT_* bone channel the driver reads."""
    for var in getattr(driver, "variables", ()):
        for target in getattr(var, "targets", ()):
            target_id = getattr(target, "id", None)
            bone_name = str(getattr(target, "bone_target", ""))
            transform_type = str(getattr(target, "transform_type", ""))
            if (
                transform_type.startswith("ROT_")
                and bone_name
                and getattr(target_id, "type", None) == "ARMATURE"
            ):
                yield target_id, bone_name


def _pose_bone_rotation_mode(armature: object, bone_name: str) -> str | None:
    """The pose bone's ``rotation_mode``, or ``None`` when the bone is not found."""
    pose = getattr(armature, "pose", None)
    for pose_bone in getattr(pose, "bones", ()):
        if str(getattr(pose_bone, "name", "")) == bone_name:
            return str(getattr(pose_bone, "rotation_mode", ""))
    return None
