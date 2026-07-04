"""Attach-to-Bone body draw (Element subpanel).

Renders the rigid sprite-to-bone attach block: the current bone-parent state,
the Parent / Clear button, and the picture-plane warning. This is the non-slot
path - a sprite pinned to a single bone with no swap. Mirrors the slot panel's
follow-state block but for the active sprite object itself.
"""

from __future__ import annotations

import bpy

from ..core.bpy_helpers.i18n import iface
from ..core.bpy_helpers.sprite import (  # type: ignore[import-not-found]
    bone_in_picture_plane,
    current_bone_parent,
    resolve_sprite_armature,
)
from ._helpers import draw_picture_plane_warning


def _candidate_bone(context: bpy.types.Context, armature: bpy.types.Object) -> str:
    """The bone to prefill the Parent button with: the active pose bone, else "".

    Only an active pose bone of the resolved armature qualifies; anything else
    leaves the button generic and routes the choice through the picker dialog.
    """
    active_bone = getattr(context, "active_pose_bone", None)
    if active_bone is None:
        return ""
    name = str(active_bone.name)
    return name if name in armature.data.bones else ""


def draw_body(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    obj: bpy.types.Object,
) -> None:
    """Attach-to-Bone body block - drawn inside the Attach to Bone subpanel."""
    col = layout.column()
    bone = current_bone_parent(obj)
    armature = resolve_sprite_armature(context, obj)

    if bone:
        col.label(text=f"parented to bone '{bone}'", icon="BONE_DATA")
        parent = obj.parent
        if parent is not None:
            col.label(text=f"parent: {parent.name} (bone)", icon="OUTLINER_OB_ARMATURE")
        col.operator("proscenio.clear_sprite_bone_parent", text="Clear Bone Parent", icon="X")
        if armature is not None and bone_in_picture_plane(armature, bone):
            draw_picture_plane_warning(
                col,
                bone,
                [
                    "the sprite rotates out of the camera plane",
                    "use a slot instead for a flat follow",
                ],
            )
        return

    if armature is None:
        col.label(text=iface("no rig - pick an armature in Skeleton"), icon="INFO")
        return

    candidate = _candidate_bone(context, armature)
    text = f"Parent To Bone ({candidate})" if candidate else "Parent To Bone"
    op = col.operator("proscenio.parent_sprite_to_bone", text=text, icon="BONE_DATA")
    op.bone_name = candidate
    col.label(text=iface("rigid follow of one bone - no slot, no swap"), icon="INFO")
