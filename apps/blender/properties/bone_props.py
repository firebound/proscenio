"""Per-bone Proscenio PropertyGroup.

Registered as ``bpy.types.Bone.proscenio``, mirroring ``Object.proscenio``. Per-
bone state stored on the PropertyGroup (no Custom-Property mirror): the Skeleton
list's per-bone favorite (the bone analogue of the Object outliner favorite) and
the ``exclude_from_export`` rig-helper flag the Godot export reads. Persists in
the .blend on the data bone, so it is per-armature and shared across every user
of the armature - the same scope as the bone's edit-mode color.
"""

from __future__ import annotations

from bpy.props import BoolProperty
from bpy.types import PropertyGroup


class ProscenioBoneProps(PropertyGroup):
    """Proscenio per-bone GUI state (``bpy.types.Bone.proscenio``)."""

    is_favorite: BoolProperty(  # type: ignore[valid-type]
        name="Skeleton favorite",
        description=(
            "Pin this bone in the Skeleton panel's bone list. Toggle 'Favorites' "
            "on the Active Armature subpanel to hide every other bone; favorites "
            "keep their hierarchy order, they do not move to the top."
        ),
        default=False,
    )
    exclude_from_export: BoolProperty(  # type: ignore[valid-type]
        name="Exclude from export",
        description=(
            "Keep this bone out of the Godot export - a rig helper that only "
            "makes sense in Blender (a Drive-from-Bone source, a tweak handle). "
            "Non-deform control bones (IK goals, poles) are already dropped; this "
            "pins off a bone that still deforms. The Drive-from-Bone shortcut sets "
            "it automatically on the source bone."
        ),
        default=False,
    )
