"""Driver-shortcut box (the Drive-from-Bone shortcut).

Surfaces the bone-to-element driver picker on the Active Element panel:
target field, source armature, source bone, source axis, expression,
plus the operator that materializes the actual driver. Has its own
help/status badges via the in-panel help system dispatch table.

Pulled out of ``panels/active_element.py`` by the code-modularity work.
"""

from __future__ import annotations

import bpy


def draw_box(
    layout: bpy.types.UILayout,
    props: bpy.types.AnyType,
) -> None:
    """Render the driver-shortcut fields inside the Drive from Bone subpanel."""
    layout.prop(props, "driver_target", text="Target")
    layout.prop(props, "driver_source_armature", text="Armature")
    layout.prop(props, "driver_source_bone", text="Bone")
    layout.prop(props, "driver_source_axis", text="Axis")
    layout.prop(props, "driver_expression", text="Expression")
    row = layout.row()
    armature = props.driver_source_armature
    has_bones = armature is not None and bool(getattr(armature.data, "bones", None))
    row.enabled = has_bones and bool(props.driver_source_bone)
    row.operator("proscenio.create_driver", text="Drive from Bone", icon="DRIVER")
