"""Weight Paint panel - mesh-only bind + weight authoring subpanels.

Split out of Mesh Generation. The parent polls on the active element
being a mesh (weight painting does not apply to sprite elements) and
surfaces the picker readout; the work lives in accordion subpanels: Bind,
Edit Weights, Snapshot, Sidecar IO, Weight Transfer. The panel renders
on any selection and shows a mesh-only hint when the active element is
not a mesh; every header carries a status badge + help button.
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core._shared.cp_keys import PROSCENIO_WEIGHT_SIDECAR  # type: ignore[import-not-found]
from ._helpers import (
    _active_armature,
    _scene_skinning,
    draw_picker_readout,
    draw_subpanel_header,
)


def _is_mesh_element(context: bpy.types.Context) -> bool:
    """True when the active object is a MESH whose element_type is "mesh"."""
    obj = context.active_object
    if obj is None or obj.type != "MESH":
        return False
    props = getattr(obj, "proscenio", None)
    return props is not None and props.element_type == "mesh"


class PROSCENIO_PT_weight_paint(bpy.types.Panel):
    """Weight Paint - mesh-only bind + weight authoring; body in subpanels."""

    bl_label = "Weight Paint"
    bl_idname = "PROSCENIO_PT_weight_paint"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 6
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "weight_paint", "weight_paint")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        if not _is_mesh_element(context):
            layout.label(text="select a mesh element (Weight Paint is mesh-only)", icon="INFO")
            return
        draw_picker_readout(layout, _active_armature(context))


class PROSCENIO_PT_bind(bpy.types.Panel):
    """Bind subpanel - bind the active mesh to the picker armature."""

    bl_label = "Bind"
    bl_idname = "PROSCENIO_PT_bind"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_weight_paint"
    bl_order = 0

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _is_mesh_element(context)

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "bind", "bind")

    def draw(self, context: bpy.types.Context) -> None:
        _draw_bind(
            self.layout, _scene_skinning(context), _active_armature(context), context.active_object
        )


class PROSCENIO_PT_edit_weights(bpy.types.Panel):
    """Edit Weights subpanel - the modal weight-paint entry + brush presets."""

    bl_label = "Edit Weights"
    bl_idname = "PROSCENIO_PT_edit_weights"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_weight_paint"
    bl_order = 1
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _is_mesh_element(context)

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "edit_weights", "edit_weights")

    def draw(self, context: bpy.types.Context) -> None:
        _draw_edit_weights(self.layout, context.active_object, _active_armature(context))


class PROSCENIO_PT_snapshot(bpy.types.Panel):
    """Snapshot subpanel - sidecar toggles + provenance counts + restore."""

    bl_label = "Snapshot"
    bl_idname = "PROSCENIO_PT_snapshot"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_weight_paint"
    bl_order = 2
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _is_mesh_element(context)

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "snapshot", "snapshot")

    def draw(self, context: bpy.types.Context) -> None:
        _draw_snapshot(self.layout, _scene_skinning(context), context.active_object)


class PROSCENIO_PT_sidecar_io(bpy.types.Panel):
    """Sidecar IO subpanel - export / import the weight sidecar JSON."""

    bl_label = "Sidecar IO"
    bl_idname = "PROSCENIO_PT_sidecar_io"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_weight_paint"
    bl_order = 3
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _is_mesh_element(context)

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "sidecar_io", "sidecar_io")

    def draw(self, context: bpy.types.Context) -> None:
        _draw_sidecar_io(self.layout, context.active_object)


class PROSCENIO_PT_weight_transfer(bpy.types.Panel):
    """Weight Transfer subpanel - copy weights from the active mesh to selected."""

    bl_label = "Weight Transfer"
    bl_idname = "PROSCENIO_PT_weight_transfer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_weight_paint"
    bl_order = 4
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _is_mesh_element(context)

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "weight_transfer", "weight_transfer")

    def draw(self, _context: bpy.types.Context) -> None:
        self.layout.operator("proscenio.copy_weights_to_selected", icon="DUPLICATE")


def _draw_bind(
    layout: bpy.types.UILayout,
    skinning_props: bpy.types.PropertyGroup | None,
    picker: bpy.types.Object | None,
    obj: bpy.types.Object | None,
) -> None:
    """Bind to Picker Armature + per-bone Soft/Hard overrides - on the subpanel layout.

    Run button greys out when no picker armature is set in the Skeleton
    panel - the most common cause of bind failure, caught visually instead
    of via post-click ERROR. Per-bone override rows appear below once a
    picker is present; ``depress`` marks the active override, a missing
    entry means the bone uses the operator-level default (bind_init_mode).
    """
    from ..core.skinning.bone_modes import read_bone_modes  # type: ignore[import-not-found]

    if skinning_props is not None:
        layout.prop(skinning_props, "bind_init_mode", text="Mode")
    row = layout.row()
    row.enabled = picker is not None
    row.operator(
        "proscenio.bind_mesh_to_armature",
        text="Bind to Picker Armature",
        icon="MOD_ARMATURE",
    )

    if picker is None or obj is None or obj.type != "MESH":
        return

    modes = read_bone_modes(obj)
    bones = picker.data.bones if picker.data is not None else []
    if not bones:
        return

    override_box = layout.box()
    override_box.label(text="Per-bone Soft/Hard overrides:")
    for bone in bones:
        current = modes.get(bone.name, "")
        bone_row = override_box.row(align=True)
        bone_row.label(text=bone.name)
        op_soft = bone_row.operator(
            "proscenio.set_bone_mode",
            text="Soft",
            depress=(current == "SOFT"),
        )
        op_soft.bone_name = bone.name
        op_soft.mode = "SOFT"
        op_hard = bone_row.operator(
            "proscenio.set_bone_mode",
            text="Hard",
            depress=(current == "HARD"),
        )
        op_hard.bone_name = bone.name
        op_hard.mode = "HARD"


def _draw_edit_weights(
    layout: bpy.types.UILayout,
    obj: bpy.types.Object | None,
    picker: bpy.types.Object | None,
) -> None:
    """Edit Weights modal entry + brush curve presets - on the subpanel layout.

    Button enabled only when (a) picker armature set, (b) mesh has a
    populated sidecar (binds preceded edit). Active vertex group label
    hints which bone the modal will start painting.
    """
    from ..core.skinning.brush_curve_presets import (  # type: ignore[import-not-found]
        PRESET_LABELS,
        PRESETS,
    )

    active_label = _active_group_label(obj)
    layout.label(text=f"Active group: {active_label}")
    row = layout.row()
    row.enabled = _edit_weights_button_enabled(obj, picker)
    row.operator(
        "proscenio.edit_weights",
        text="Edit Weights",
        icon="BRUSHES_ALL",
    )
    if obj is None or obj.type != "MESH":
        return
    if obj.get(PROSCENIO_WEIGHT_SIDECAR) is None:
        layout.label(text="bind first to enable", icon="INFO")

    layout.label(text="Brush curve preset:")
    row = layout.row(align=True)
    for preset_name in PRESETS:
        op = row.operator("proscenio.set_brush_preset", text=PRESET_LABELS[preset_name])
        op.preset_name = preset_name


def _active_group_label(obj: bpy.types.Object | None) -> str:
    if obj is None or obj.type != "MESH":
        return "(no mesh)"
    if len(obj.vertex_groups) == 0:
        return "(none)"
    active = obj.vertex_groups.active
    return active.name if active else "(none)"


def _edit_weights_button_enabled(
    obj: bpy.types.Object | None, picker: bpy.types.Object | None
) -> bool:
    if obj is None or obj.type != "MESH":
        return False
    if picker is None:
        return False
    if len(obj.vertex_groups) == 0:
        return False
    return obj.get(PROSCENIO_WEIGHT_SIDECAR) is not None


def _draw_snapshot(
    layout: bpy.types.UILayout,
    skinning_props: bpy.types.PropertyGroup | None,
    obj: bpy.types.Object | None,
) -> None:
    """Sidecar toggles + provenance counts pill + Restore button - on the subpanel layout.

    Counts are recomputed live from the JSON payload stored on the active
    mesh (single source of truth on the active mesh).
    """
    if skinning_props is not None:
        layout.prop(skinning_props, "preserve_on_regen")
        layout.prop(skinning_props, "show_provenance_overlay")
    counts = _sidecar_counts(obj)
    if counts is None:
        layout.label(text="no sidecar (run Bind first)", icon="INFO")
    else:
        layout.label(
            text=(
                f"{counts['user_paint']} paint / "
                f"{counts['auto_seed']} seed / "
                f"{counts['reprojected']} reprojected"
            )
        )
    row = layout.row()
    row.enabled = counts is not None
    row.operator(
        "proscenio.restore_weight_snapshot",
        text="Reset to Last Saved Weights",
        icon="LOOP_BACK",
    )


def _sidecar_counts(obj: bpy.types.Object | None) -> dict[str, int] | None:
    """Parse the sidecar JSON + count entries by provenance. None = no sidecar."""
    if obj is None or obj.type != "MESH":
        return None
    payload = obj.get(PROSCENIO_WEIGHT_SIDECAR)
    if payload is None:
        return None
    try:
        import json

        data = json.loads(payload)
    except (ValueError, TypeError):
        return None
    counts = {"user_paint": 0, "auto_seed": 0, "reprojected": 0}
    for entry in data.get("entries", []) or []:
        provenance = entry.get("provenance") if isinstance(entry, dict) else None
        if provenance in counts:
            counts[provenance] += 1
    return counts


def _draw_sidecar_io(
    layout: bpy.types.UILayout,
    obj: bpy.types.Object | None,
) -> None:
    """Export + Import file-dialog buttons for the sidecar JSON - on the subpanel layout."""
    row = layout.row(align=True)
    row.operator("proscenio.export_sidecar", text="Export", icon="EXPORT")
    row.operator("proscenio.import_sidecar", text="Import", icon="IMPORT")
    if obj is not None and obj.type == "MESH" and obj.get(PROSCENIO_WEIGHT_SIDECAR) is None:
        layout.label(text="no sidecar yet (run Bind first)", icon="INFO")


_classes: tuple[type, ...] = (
    PROSCENIO_PT_weight_paint,
    PROSCENIO_PT_bind,
    PROSCENIO_PT_edit_weights,
    PROSCENIO_PT_snapshot,
    PROSCENIO_PT_sidecar_io,
    PROSCENIO_PT_weight_transfer,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
