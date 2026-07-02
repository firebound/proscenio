"""Cross-cutting panel helpers.

Shared across every panel module: the subpanel-header drawer (status
icon + help button), the mode-friendly predicate sets, and the idname
constants for the help / status operators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import bpy

from ..core._shared.armature_resolve import (  # type: ignore[import-not-found]
    active_armature,
)
from ..core._shared.feature_status import (  # type: ignore[import-not-found]
    FeatureStatus,
    badge_for,
    status_for,
)
from ..core._shared.props_access import (  # type: ignore[import-not-found]
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

# Below this N-panel width the header is too cramped to fit the status + help
# icons without overlapping the (already truncating) title, so they are
# dropped - mirroring how a narrow Blender header sheds its right-side
# affordances and keeps just the clipping label. Freeing this space also lets
# a custom draw_header title (Skeleton) truncate instead of being squeezed to
# nothing. Tune against a real N-panel if it hides too early / too late.
_HEADER_ICONS_MIN_WIDTH = 200


def _scene_skinning(context: bpy.types.Context) -> bpy.types.PropertyGroup | None:
    """Return ``scene.proscenio.skinning`` defaults group, or None."""
    return scene_skinning(context)


def _active_armature(context: bpy.types.Context) -> bpy.types.Object | None:
    """Return the scene-picked Active Armature, or None."""
    return active_armature(context)


def _active_mesh_props(context: bpy.types.Context) -> bpy.types.AnyType | None:
    """Return the active MESH object's Proscenio props, or None."""
    obj = context.active_object
    if obj is None or obj.type != "MESH":
        return None
    return getattr(obj, "proscenio", None)


def _is_mesh_element(context: bpy.types.Context) -> bool:
    """True when the active object is a MESH whose element_type is "mesh".

    A sprite element is also a Blender MESH, but a mesh tool would replace its
    single quad, so the Mesh Generation + Weight Paint gates exclude sprites.
    Shared by those panels and the Element panel's Active Mesh subpanel so the
    "is this a mesh element" test has one definition.
    """
    props = _active_mesh_props(context)
    return props is not None and props.element_type == "mesh"


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
    context: bpy.types.Context,
    feature_id: str,
    help_topic: str,
) -> None:
    """Append status icon + help button to a Proscenio subpanel foldout.

    Called from ``draw_header_preset`` (NOT ``draw_header``): Blender
    renders ``draw_header_preset`` content RIGHT of the auto-drawn
    ``bl_label``. Skipped when the N-panel is narrower than
    ``_HEADER_ICONS_MIN_WIDTH`` so the icons do not overlap the title.
    The panel-callback ``context`` is used for the width read (not global
    ``bpy.context``, which can resolve to a different region in a
    multi-editor layout).
    """
    region = getattr(context, "region", None)
    if region is not None and region.width < _HEADER_ICONS_MIN_WIDTH:
        return
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


def draw_help_button(layout: bpy.types.UILayout, help_topic: str) -> None:
    """Draw a standalone help ``?`` button bound to a help topic.

    For a single operator row that needs its own help affordance when
    there is no subpanel or sub-box header to host it (e.g. the Save Pose
    to Library row, whose subpanel header explains Pose Mode, not the
    pose-library asset flow).
    """
    op = layout.operator(_HELP_OP_IDNAME, text="", icon="QUESTION", emboss=False)
    op.topic = help_topic


def draw_target_readout(
    layout: bpy.types.UILayout,
    target: bpy.types.Object | None,
    *,
    source: str = "Skeleton",
) -> None:
    """Draw the one-line "Target: <source> <name>" readout row.

    For a panel that acts on a selection owned by *another* panel (the
    armature picked in the Skeleton panel). The readout names both what
    the panel targets and where that target is chosen, so the dependency
    is explicit. ARMATURE_DATA icon then "Target: Skeleton <name>", or an
    INFO-marked empty prompt when nothing is picked. Shared by Mesh
    Generation, Weight Paint, and Animation so the affordance reads
    identically across the panels that depend on the picked rig.
    """
    row = layout.row(align=True)
    row.label(text="", icon="ARMATURE_DATA")
    if target is not None:
        row.label(text=f"Target: {source} {target.name}")
    else:
        row.label(text=f"Target: {source} (none - pick a rig there)", icon="INFO")


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


def draw_picture_plane_warning(col: bpy.types.UILayout, bone: str, hint_lines: list[str]) -> None:
    """Alert box: ``bone`` lies in the camera picture plane, plus caller hints.

    The shared box body for the two picture-plane warnings (the slot
    bone-parent collapse and the sprite bone-parent rotation). Each caller keeps
    its own guard condition and passes its own follow-up ``hint_lines``.
    """
    box = col.box().column(align=True)
    box.alert = True
    box.label(text=f"bone '{bone}' lies in the picture plane", icon="ERROR")
    for line in hint_lines:
        box.label(text=line, icon="BLANK1")
