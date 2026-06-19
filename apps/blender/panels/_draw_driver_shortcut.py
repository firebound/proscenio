"""Driver-shortcut box (the Drive-from-Bone shortcut).

Surfaces the bone-to-element driver picker on the Active Element panel:
target field, source armature, source bone, source axis, the two-range
linear map (input bone-channel range to output target-value range) with a
raw-expression Advanced fallback, a live readout of the driven target value,
plus the operator that materializes the actual driver. Has its own
help/status badges via the in-panel help system dispatch table.
"""

from __future__ import annotations

import bpy

from ..core.bpy_helpers.armature.driver_list import (  # type: ignore[import-not-found]
    proscenio_driver_rows,
)


def draw_box(
    layout: bpy.types.UILayout,
    sprite: bpy.types.Object,
) -> None:
    """Render the driver-shortcut fields + the existing-driver list."""
    props = sprite.proscenio
    layout.prop(props, "driver_target", text="Target")
    layout.prop(props, "driver_source_armature", text="Armature")
    layout.prop(props, "driver_source_bone", text="Bone")
    layout.prop(props, "driver_source_axis", text="Axis")

    if props.driver_advanced:
        layout.prop(props, "driver_expression", text="Expression")
    else:
        in_row = layout.row(align=True)
        in_row.prop(props, "driver_in_min", text="In Min")
        in_row.prop(props, "driver_in_max", text="In Max")
        out_row = layout.row(align=True)
        out_row.prop(props, "driver_out_min", text="Out Min")
        out_row.prop(props, "driver_out_max", text="Out Max")
    layout.prop(props, "driver_advanced", text="Advanced expression")

    _draw_value_readout(layout, props)

    row = layout.row()
    armature = props.driver_source_armature
    has_bones = armature is not None and bool(getattr(armature.data, "bones", None))
    row.enabled = has_bones and bool(props.driver_source_bone)
    row.operator("proscenio.create_driver", text="Drive from Bone", icon="DRIVER")

    _draw_driver_list(layout, sprite)


def _draw_driver_list(layout: bpy.types.UILayout, sprite: bpy.types.Object) -> None:
    """List the element's existing proscenio bone drivers, each with a remove X.

    The create path only ever replaces the one driver per source bone; this is
    the management surface that view-and-removes them. Hidden when the element
    has none so the subpanel stays compact until a driver exists.
    """
    rows = proscenio_driver_rows(sprite)
    if not rows:
        return
    layout.separator()
    layout.label(text=f"Drivers ({len(rows)}):", icon="DRIVER")
    col = layout.box().column(align=True)
    for driver_row in rows:
        item = col.row(align=True)
        source = f"<- {driver_row.bone}" if driver_row.bone else "(no bone)"
        item.label(text=f"{driver_row.label}  {source}")
        remove = item.operator("proscenio.remove_driver", text="", icon="X", emboss=False)
        remove.data_path = driver_row.data_path


def _draw_value_readout(layout: bpy.types.UILayout, props: bpy.types.AnyType) -> None:
    """Show the live driven value of the selected target property.

    The driver writes into ``proscenio.<target>``, so the target field holds the
    current driven result once the depsgraph evaluates - reading it back here is
    the inline readout (no Inspect popup). Integer targets (frame) print whole;
    region channels print to three decimals.
    """
    target_field = str(props.driver_target)
    current = getattr(props, target_field, None)
    if current is None:
        return
    text = f"Value: {current}" if isinstance(current, int) else f"Value: {current:.3f}"
    layout.label(text=text)
