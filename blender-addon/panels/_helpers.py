"""Cross-cutting panel helpers (SPEC 009 wave 9.3).

Shared across every panel module: the subpanel-header drawer (status
icon + help button), the mode-friendly predicate sets, and the idname
constants for the help / status operators.
"""

from __future__ import annotations

import bpy

from ..core.feature_status import badge_for, status_for  # type: ignore[import-not-found]

_OBJECT_FRIENDLY_MODES = {"OBJECT", "EDIT_MESH", "PAINT_WEIGHT", "PAINT_VERTEX"}
_POSE_FRIENDLY_MODES = {"OBJECT", "POSE", "EDIT_ARMATURE"}
_HELP_OP_IDNAME = "proscenio.help"
_STATUS_OP_IDNAME = "proscenio.status_info"


def draw_subpanel_header(
    layout: bpy.types.UILayout,
    feature_id: str,
    help_topic: str,
) -> None:
    """Append status icon + help button to a Proscenio subpanel foldout.

    Called from ``draw_header_preset`` (NOT ``draw_header``): Blender
    renders ``draw_header_preset`` content RIGHT of the auto-drawn
    ``bl_label``. The status icon is wrapped in ``proscenio.status_info``
    so hovering surfaces the band-specific tooltip (Blender does not
    honor custom tooltips on plain ``layout.label``).
    """
    badge = badge_for(feature_id)
    status = status_for(feature_id)
    op = layout.operator(_STATUS_OP_IDNAME, text="", icon=badge.icon, emboss=False)
    op.band = status.value
    op = layout.operator(_HELP_OP_IDNAME, text="", icon="QUESTION", emboss=False)
    op.topic = help_topic
