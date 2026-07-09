"""Action-assignment operator: set the Skeleton-picked armature's active action."""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import StringProperty

from ...core._shared.action_kind import (  # type: ignore[import-not-found]
    is_visibility_only_action,
)
from ...core._shared.report import report_warn  # type: ignore[import-not-found]
from ...core.armature.skeleton_target import (  # type: ignore[import-not-found]
    resolve_skeleton_target,
)
from ._shared import _sync_active_index


class PROSCENIO_OT_set_active_action(bpy.types.Operator):
    """Assign an action to the Skeleton-picked armature from the Animation panel."""

    bl_idname = "proscenio.set_active_action"
    bl_label = "Proscenio: Set Active Action"
    bl_description = (
        "Assigns this Animation-panel row's action to the armature picked in "
        "the Skeleton panel so the timeline plays it"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    action_name: StringProperty(  # type: ignore[valid-type]
        name="Action",
        default="",
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        action = bpy.data.actions.get(self.action_name)
        if action is None:
            report_warn(self, f"action '{self.action_name}' not found", always=True)
            return {"CANCELLED"}
        # A slot swap authored as direct visibility keyframes creates its own
        # visibility-only action (hide_render / hide_viewport). Grafting it onto
        # the armature would play empty on the rig and hide the real rig action
        # of the same name behind it; refuse and point the artist at the swap
        # authoring instead (spec 079 D2).
        if is_visibility_only_action(action):
            report_warn(
                self,
                f"action '{action.name}' animates attachment visibility, not the rig - "
                "author it from the Active Slot panel, not the Animation list",
                always=True,
            )
            return {"CANCELLED"}
        # The Skeleton picker is the single source of truth, same as every
        # other skeleton op. Do not scan the scene for an armature - that
        # silently targeted the wrong rig when more than one existed.
        armature = resolve_skeleton_target(context)
        if armature is None:
            report_warn(self, "no armature picked - pick one in the Skeleton panel", always=True)
            return {"CANCELLED"}
        # The picked armature can be deleted between pick and click; touching a
        # freed datablock raises ReferenceError. Guard and ask for a re-pick.
        try:
            if armature.animation_data is None:
                armature.animation_data_create()
            armature.animation_data.action = action
        except ReferenceError:
            report_warn(self, "picked armature no longer exists - pick one again", always=True)
            return {"CANCELLED"}
        _sync_active_index(context, "active_action_index", bpy.data.actions, self.action_name)
        return {"FINISHED"}
