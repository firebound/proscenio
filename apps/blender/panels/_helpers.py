"""Cross-cutting panel helpers.

Shared across every panel module: the subpanel-header drawer (status
icon + help button), the mode-friendly predicate sets, and the idname
constants for the help / status operators.
"""

from __future__ import annotations

import bpy

from ..core._shared.feature_status import badge_for, status_for  # type: ignore[import-not-found]

_POSE_FRIENDLY_MODES = {"OBJECT", "POSE", "EDIT_ARMATURE"}
_HELP_OP_IDNAME = "proscenio.help"
_STATUS_OP_IDNAME = "proscenio.status_info"


def _scene_skinning(context: bpy.types.Context) -> bpy.types.PropertyGroup | None:
    """Return ``scene.proscenio.skinning`` defaults group, or None."""
    scene_props = getattr(context.scene, "proscenio", None)
    return getattr(scene_props, "skinning", None) if scene_props is not None else None


def _active_armature(context: bpy.types.Context) -> bpy.types.Object | None:
    """Return the scene-picked Active Armature, or None."""
    scene_props = getattr(context.scene, "proscenio", None)
    return getattr(scene_props, "active_armature", None) if scene_props is not None else None


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


def draw_subbox_header(
    box: bpy.types.UILayout,
    title: str,
    title_icon: str,
    feature_id: str,
    help_topic: str,
) -> None:
    """Render a sub-box title row with status + help button on the right.

    Sub-boxes (``layout.box()``) don't have a header_preset slot, so the
    Proscenio status + help affordances had to be omitted - leaving help
    topics like ``sprite_frame_preview`` orphan in the UI even though
    they exist in ``core/help_topics.py``. This helper packs title +
    status badge + help icon into a single row inside the box, so each
    sub-box gets the same affordance as a top-level subpanel.
    """
    badge = badge_for(feature_id)
    status = status_for(feature_id)
    row = box.row(align=True)
    row.label(text=title, icon=title_icon)
    spacer = row.row()
    spacer.alignment = "RIGHT"
    op = spacer.operator(_STATUS_OP_IDNAME, text="", icon=badge.icon, emboss=False)
    op.band = status.value
    op = spacer.operator(_HELP_OP_IDNAME, text="", icon="QUESTION", emboss=False)
    op.topic = help_topic
