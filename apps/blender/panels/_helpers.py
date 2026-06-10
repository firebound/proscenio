"""Cross-cutting panel helpers.

Shared across every panel module: the subpanel-header drawer (status
icon + help button), the mode-friendly predicate sets, and the idname
constants for the help / status operators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import bpy

from ..core._shared.feature_status import (  # type: ignore[import-not-found]
    FeatureStatus,
    badge_for,
    status_for,
)
from ..core._shared.props_access import (  # type: ignore[import-not-found]
    active_armature,
    scene_skinning,
)
from ..core.bpy_helpers.preview_icons import (  # type: ignore[import-not-found]
    blender_icon_id,
    godot_icon_id,
)

if TYPE_CHECKING:
    from ..core.validation.issue import Issue

_POSE_FRIENDLY_MODES = {"OBJECT", "POSE", "EDIT_ARMATURE"}
_HELP_OP_IDNAME = "proscenio.help"
_STATUS_OP_IDNAME = "proscenio.status_info"


def _scene_skinning(context: bpy.types.Context) -> bpy.types.PropertyGroup | None:
    """Return ``scene.proscenio.skinning`` defaults group, or None."""
    return scene_skinning(context)


def _active_armature(context: bpy.types.Context) -> bpy.types.Object | None:
    """Return the scene-picked Active Armature, or None."""
    return active_armature(context)


def _draw_status_button(layout: bpy.types.UILayout, feature_id: str) -> None:
    """Draw the status-badge button.

    Uses the custom Godot mark for the godot-ready band, the custom
    Blender mark for the blender-only band, and the built-in icon for
    every other band. The icon is wrapped in
    ``proscenio.status_info`` so hovering surfaces the band-specific
    tooltip (Blender does not honor custom tooltips on a plain
    ``layout.label``). A missing preview (headless / failed load) falls
    back to the band's built-in icon.
    """
    badge = badge_for(feature_id)
    status = status_for(feature_id)
    if status == FeatureStatus.GODOT_READY:
        icon_id = godot_icon_id()
    elif status == FeatureStatus.BLENDER_ONLY:
        icon_id = blender_icon_id()
    else:
        icon_id = 0
    if icon_id:
        op = layout.operator(_STATUS_OP_IDNAME, text="", icon_value=icon_id, emboss=False)
    else:
        op = layout.operator(_STATUS_OP_IDNAME, text="", icon=badge.icon, emboss=False)
    op.band = status.value


def draw_subpanel_header(
    layout: bpy.types.UILayout,
    feature_id: str,
    help_topic: str,
) -> None:
    """Append status icon + help button to a Proscenio subpanel foldout.

    Called from ``draw_header_preset`` (NOT ``draw_header``): Blender
    renders ``draw_header_preset`` content RIGHT of the auto-drawn
    ``bl_label``.
    """
    _draw_status_button(layout, feature_id)
    op = layout.operator(_HELP_OP_IDNAME, text="", icon="QUESTION", emboss=False)
    op.topic = help_topic


def draw_subbox_header(
    box: bpy.types.UILayout,
    title: str,
    title_icon: str,
    feature_id: str,
    help_topic: str,
) -> None:
    """Render a sub-box title row with status + help button on the right.

    Sub-boxes (``layout.box()``) don't have a header_preset slot, so the
    title + status badge + help icon are packed into a single row inside
    the box, giving each sub-box the same affordance as a top-level
    subpanel.
    """
    row = box.row(align=True)
    row.label(text=title, icon=title_icon)
    spacer = row.row()
    spacer.alignment = "RIGHT"
    _draw_status_button(spacer, feature_id)
    op = spacer.operator(_HELP_OP_IDNAME, text="", icon="QUESTION", emboss=False)
    op.topic = help_topic


def draw_picker_readout(layout: bpy.types.UILayout, picker: bpy.types.Object | None) -> None:
    """Draw the one-line "Picker: <armature>" readout row.

    ARMATURE_DATA icon then the picker name, or an INFO-marked
    "(none - set in Skeleton panel)" prompt when no armature is set.
    Shared by the Mesh Generation + Weight Paint panels so the picker
    affordance reads identically in both.
    """
    row = layout.row(align=True)
    row.label(text="", icon="ARMATURE_DATA")
    if picker is not None:
        row.label(text=f"Picker: {picker.name}")
    else:
        row.label(text="Picker: (none - set in Skeleton panel)", icon="INFO")


def draw_issue_row(layout: bpy.types.UILayout, issue: Issue) -> None:
    """Render one validation Issue as a panel row.

    ERROR / INFO icon plus an alert tint by severity. When the issue names
    an object the row is a clickable select-issue-object button
    (``[name] message``); otherwise a plain label. Shared by the
    Validation, Active Element and Active Slot panels so the issue row
    reads (and behaves) identically wherever findings surface - panels
    whose issues never set ``obj_name`` simply get the plain label.
    """
    row = layout.row(align=True)
    is_error = issue.severity == "error"
    row.alert = is_error
    icon = "ERROR" if is_error else "INFO"
    if issue.obj_name:
        op = row.operator(
            "proscenio.select_issue_object",
            text=f"[{issue.obj_name}] {issue.message}",
            icon=icon,
            emboss=False,
        )
        op.obj_name = issue.obj_name
    else:
        row.label(text=issue.message, icon=icon)
