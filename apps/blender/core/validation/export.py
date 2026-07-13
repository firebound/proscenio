"""Full pre-export validation pass - orchestrates the per-family checks."""

from __future__ import annotations

from .._shared.armature_resolve import resolve_export_armature
from .._shared.cp_keys import DEFAULT_Y_LOCATION_SPACING
from ._shared import armature_bone_names
from .active_element import validate_active_element
from .checks.atlas_files import validate_atlas_files
from .checks.bone_follow import validate_bone_follow
from .checks.bone_orientation import validate_bone_orientation
from .checks.driver_rotation import validate_driver_rotation_modes
from .checks.element_armature import validate_element_against_armature
from .checks.ik_bake import validate_ik_bake
from .checks.mesh_flatness import validate_mesh_flatness
from .checks.slots import validate_slots
from .checks.sprite_frame_uvs import validate_sprite_frame_uvs
from .checks.sprite_orientation import validate_sprite_orientation
from .issue import Issue


def validate_export(
    scene: object,
    *,
    layer_spacing: float = DEFAULT_Y_LOCATION_SPACING,
) -> list[Issue]:
    """Full pre-export pass. Walks the scene, hits the disk for the atlas.

    Returns every issue found; the caller decides whether to abort.
    Errors block export by convention; warnings inform but allow the
    operator to proceed. ``layer_spacing`` is threaded to the per-element
    pass for the Y Location (Draw Order) divergence check; the operator
    passes ``addon_prefs.y_location_spacing(context)``.
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
    issues.extend(validate_bone_orientation(picked_armature))
    issues.extend(validate_ik_bake(picked_armature))

    for obj in scene_objects:
        if getattr(obj, "type", None) != "MESH":
            continue
        for active_issue in validate_active_element(obj, layer_spacing=layer_spacing):
            issues.append(active_issue)
        issues.extend(validate_element_against_armature(obj, available_bones))
        issues.extend(validate_mesh_flatness(obj))
        issues.extend(validate_sprite_frame_uvs(obj))
        issues.extend(validate_sprite_orientation(obj))

    issues.extend(validate_driver_rotation_modes(scene_objects))
    issues.extend(validate_bone_follow(scene_objects))
    issues.extend(validate_slots(scene_objects))
    issues.extend(validate_atlas_files(scene_objects))

    return issues
