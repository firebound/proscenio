"""Bone picture-plane orientation: the shared into-screen direction test.

bpy-bound (reads ``matrix_world`` off the armature and a pose bone's
``head`` / ``tail``), but the only mathutils use is the vector arithmetic the
bone matrices already return, so no top-level mathutils import is needed - the
module stays off the package bpy-free contract the same way :mod:`geometry`
does.

The XZ picture-plane convention: the camera looks down -Y, so a bone pointing
into the screen (world +/-Y) keeps a bone-parented attachment facing front,
while an in-plane bone (+X / +Z, e.g. a spine bone drawn up the figure) rotates
it out of the camera plane. Both the slot bone-follow collapse check and the
rigid sprite picture-plane warning are the same world-direction test against the
same cosine threshold; this is the single definition they share so they cannot
drift apart. The into-screen bone convention and its 0.7 threshold are recorded
in the architecture decision log.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy

# A bone whose world direction lies within this much of the picture plane (XZ)
# tilts a bone-parented child out of the camera plane. abs(dir.y) below this
# cosine threshold (~45 degrees off the -Y view axis) is the collapse/rotate
# risk band; at or above it the bone points far enough into the screen to stay
# flat.
_INTO_SCREEN_MIN_Y = 0.7


def bone_in_picture_plane(armature: bpy.types.Object, bone_name: str) -> bool:
    """True when ``bone_name``'s world direction lies in the picture plane.

    A bone pointing into the screen (world +/-Y) keeps a rigid bone-parented
    child facing front; an in-plane bone (+X / +Z) tilts it off the camera
    plane (collapsing a slot's attachment quads edge-on, rotating a rigid
    sprite out of view). Unknown, missing, or zero-length bones read False.
    """
    pose_bone = armature.pose.bones.get(bone_name)
    if pose_bone is None:
        return False
    world = armature.matrix_world
    direction = (world @ pose_bone.tail) - (world @ pose_bone.head)
    if direction.length < 1e-9:  # degenerate (zero-length) bone
        return False
    direction.normalize()
    return abs(direction.y) < _INTO_SCREEN_MIN_Y
