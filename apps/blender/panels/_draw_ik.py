"""IK helper cluster for the Skeleton Pose Mode subpanel.

The active-chain constraint lookup plus the curated IK controls (toggle,
constraint props, in-plane lock). Kept out of ``skeleton.py`` so the panel
module reads as panel definitions; ``skeleton`` re-exports ``_active_ik_constraint``
so ``test_ik_authoring_ergonomics`` still imports it from there.
"""

from __future__ import annotations

import bpy

from ..core.bpy_helpers.i18n import iface

# Constraint that marks a Proscenio-owned IK chain; the name is the single
# source the panel reads (a renamed .IK control suffix must not change the cue).
_IK_CONSTRAINT_NAME = "Proscenio IK"


def _active_ik_constraint(context: bpy.types.Context) -> bpy.types.Constraint | None:
    """The active pose bone's ``Proscenio IK`` constraint, or None."""
    bone = getattr(context, "active_pose_bone", None)
    if bone is None:
        return None
    return bone.constraints.get(_IK_CONSTRAINT_NAME)


def _draw_ik_toggle(layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
    """Draw the create / remove IK button with an honest, state-resolved label.

    One operator (``proscenio.toggle_ik_chain``) does both create and destroy;
    the label reads "Add IK Chain" when the active bone has no Proscenio IK and
    "Remove IK Chain" when it does, so the button names the action it performs.
    """
    has_chain = _active_ik_constraint(context) is not None
    text = "Remove IK Chain" if has_chain else "Add IK Chain"
    icon = "X" if has_chain else "CON_KINEMATIC"
    layout.operator("proscenio.toggle_ik_chain", text=text, icon=icon)


def _draw_ik_constraint_props(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    constraint: bpy.types.Constraint,
) -> None:
    """Draw the curated IK constraint controls for the active chain.

    The trio the IK flow needs - chain length, keyframable influence (the
    IK/FK-blend seed, with an explicit insert-key button), pole target - plus an
    opt-in "lock chain in-plane" toggle that gives the otherwise-hidden
    ``lock_ik_*`` flags a visible owner. Deliberately not the full native
    KinematicConstraint UI (no stretch / iterations / weight): the export bakes
    the chain, so those are native-UI territory.
    """
    box = layout.box()
    box.label(text=iface("Proscenio IK"), icon="CON_KINEMATIC")
    box.prop(constraint, "chain_count", text="Chain length")

    influence_row = box.row(align=True)
    influence_row.prop(constraint, "influence", text="Influence", slider=True)
    # Explicit insert-key affordance for the IK/FK-blend seed (the prop already
    # honors keying; this is the one-click button on the chain's tip bone).
    influence_row.operator("proscenio.key_ik_influence", text="", icon="KEYFRAME_HLT")

    box.prop(constraint, "pole_target", text="Pole target")
    if constraint.pole_target is not None and constraint.pole_target.type == "ARMATURE":
        box.prop_search(
            constraint,
            "pole_subtarget",
            constraint.pole_target.data,
            "bones",
            text="Pole bone",
        )

    _draw_ik_inplane_lock(box, context, constraint)


def _draw_ik_inplane_lock(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    constraint: bpy.types.Constraint,
) -> None:
    """Opt-in "lock chain in-plane" toggle for the active chain's tip bone.

    Locks the chain's out-of-plane rotation DOFs on the constrained bone so the
    solve stays in the 2D picture plane. Off by default and clearly labelled,
    because loose ``lock_ik_*`` flags are hidden bone state that otherwise read
    as "the bone will not rotate" with no explanation.
    """
    bone = getattr(context, "active_pose_bone", None)
    if bone is None or constraint.name != _IK_CONSTRAINT_NAME:
        return
    locked = bool(bone.lock_ik_x and bone.lock_ik_z)
    op = layout.operator(
        "proscenio.toggle_ik_inplane_lock",
        text="Unlock chain in-plane" if locked else "Lock chain in-plane",
        icon="LOCKED" if locked else "UNLOCKED",
    )
    op.bone_name = bone.name
