"""Driver-shortcut box (SPEC 5.1.d.1).

Surfaces the bone-to-sprite driver picker on the Active Sprite panel:
target field, source armature, source bone, source axis, expression,
plus the operator that materializes the actual driver. Has its own
help/status badges via the SPEC 5.1.d.5 dispatch table.

Pulled out of ``panels/active_sprite.py`` by SPEC 009 wave 9.10.
"""

from __future__ import annotations

import bpy

from ..core.feature_status import (  # type: ignore[import-not-found]
    badge_for,
    status_for,
)
from ._helpers import _HELP_OP_IDNAME, _STATUS_OP_IDNAME


def draw_box(
    layout: bpy.types.UILayout,
    _context: bpy.types.Context,
    props: bpy.types.AnyType,
) -> None:
    """Render the driver-shortcut box."""
    box = layout.box()
    header = box.row(align=True)
    header.label(text="Drive from bone", icon="DRIVER")
    right = header.row()
    right.alignment = "RIGHT"
    badge = badge_for("drive_from_bone")
    status = status_for("drive_from_bone")
    op_status = right.operator(_STATUS_OP_IDNAME, text="", icon=badge.icon, emboss=False)
    op_status.band = status.value
    op = right.operator(_HELP_OP_IDNAME, text="", icon="QUESTION", emboss=False)
    op.topic = "drive_from_bone"
    box.prop(props, "driver_target", text="Target")
    box.prop(props, "driver_source_armature", text="Armature")
    box.prop(props, "driver_source_bone", text="Bone")
    box.prop(props, "driver_source_axis", text="Axis")
    box.prop(props, "driver_expression", text="Expression")
    row = box.row()
    armature = props.driver_source_armature
    has_bones = armature is not None and bool(getattr(armature.data, "bones", None))
    row.enabled = has_bones and bool(props.driver_source_bone)
    row.operator("proscenio.create_driver", text="Drive from Bone", icon="DRIVER")
