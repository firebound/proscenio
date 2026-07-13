"""Element bone-attach resolution: the armature a rigid element binds against.

bpy-bound per the bpy_helpers contract. Since spec 080 the attach AUTHORING
lives in the shared bone-follow core (``.._shared.bone_follow`` - constraint-
first bind / unbind / convert); this module keeps the element-facing armature
resolution and re-exports the picture-plane helper. The raw keep-transform
bone parent remains a supported power-user authoring shape, but it is
hand-authored (Ctrl+P > Bone) - the addon no longer writes it.
"""

from __future__ import annotations

import bpy

from ..._shared.armature_resolve import resolve_target_armature
from .._shared.bone_orientation import bone_in_picture_plane

__all__ = [
    "bone_in_picture_plane",
    "resolve_sprite_armature",
]


def resolve_sprite_armature(
    context: bpy.types.Context, obj: bpy.types.Object
) -> bpy.types.Object | None:
    """The armature a rigid element should bind to, or None.

    The element-facing name for the shared :func:`resolve_target_armature`:
    parent-if-ARMATURE, then the Skeleton picker, then the scene's export
    armature - the same resolution order the slot bone-follow uses, so the two
    never disagree on the rig.
    """
    return resolve_target_armature(context, obj)
