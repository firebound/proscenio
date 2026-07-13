"""Attach-to-Bone body draw (Element subpanel).

Renders the rigid element-to-bone follow block: the current follow state
(constraint / raw bone parent / none), the Bind / Convert / Clear buttons.
This is the non-slot path - an element pinned to a single bone with no swap.
Mirrors the slot panel's follow-state block but for the active element
itself. Constraint-first (spec 080): Bind authors the Child Of follow; a raw
bone parent still exports and offers a one-click Convert.
"""

from __future__ import annotations

import bpy

from ..core._shared.bone_follow_resolve import (  # type: ignore[import-not-found]
    ELEMENT_FOLLOW_CONSTRAINT,
    follow_subtarget,
)
from ..core.bpy_helpers._shared.bone_follow import follow_shape  # type: ignore[import-not-found]
from ..core.bpy_helpers.i18n import iface
from ..core.bpy_helpers.sprite import (  # type: ignore[import-not-found]
    resolve_sprite_armature,
)


def _candidate_bone(context: bpy.types.Context, armature: bpy.types.Object) -> str:
    """The bone to prefill the Bind button with: the active pose bone, else "".

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
    shape = follow_shape(obj, ELEMENT_FOLLOW_CONSTRAINT)
    armature = resolve_sprite_armature(context, obj)

    if shape == "constraint":
        bone = follow_subtarget(obj, ELEMENT_FOLLOW_CONSTRAINT)
        col.label(text=f"follows bone '{bone}' (Proscenio constraint)", icon="CONSTRAINT")
        col.operator("proscenio.clear_sprite_bone_parent", text="Clear Bone Follow", icon="X")
        return

    if shape == "bone_parent":
        bone = str(obj.parent_bone)
        col.label(text=f"follows bone '{bone}' (raw bone parent)", icon="BONE_DATA")
        parent = obj.parent
        if parent is not None:
            col.label(text=f"parent: {parent.name} (bone)", icon="OUTLINER_OB_ARMATURE")
        col.operator(
            "proscenio.convert_element_follow",
            text="Convert to Constraint",
            icon="CONSTRAINT",
        )
        col.operator("proscenio.clear_sprite_bone_parent", text="Clear Bone Follow", icon="X")
        return

    if armature is None:
        col.label(text=iface("no rig - pick an armature in Skeleton"), icon="INFO")
        return

    candidate = _candidate_bone(context, armature)
    text = f"Bind to Bone ({candidate})" if candidate else "Bind to Bone"
    op = col.operator("proscenio.parent_sprite_to_bone", text=text, icon="BONE_DATA")
    op.bone_name = candidate
    col.label(text=iface("rigid follow of one bone - no slot, no swap"), icon="INFO")
