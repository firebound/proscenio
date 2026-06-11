"""Weight Paint panel - mesh-only bind + weight authoring subpanels.

The parent polls on the active element being a mesh (weight painting does
not apply to sprite elements) and surfaces the picker readout; the work
lives in accordion subpanels: Bind, Edit Weights, Snapshot (which also holds
the snapshot file export / import), Weight Transfer. The panel renders on any
selection and shows a mesh-only hint when the active element is not a mesh.
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
        _draw_weight_overlay_controls(self.layout, context)


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

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        skinning_props = _scene_skinning(context)
        if skinning_props is not None:
            layout.prop(skinning_props, "weight_transfer_max_distance", text="Max Distance")
        op = layout.operator("proscenio.copy_weights_to_selected", icon="DUPLICATE")
        if skinning_props is not None:
            # Seed the operator from the panel so the click uses the field value;
            # F9 redo still exposes max_distance for a one-off tweak.
            op.max_distance = skinning_props.weight_transfer_max_distance


def _draw_bind(
    layout: bpy.types.UILayout,
    skinning_props: bpy.types.PropertyGroup | None,
    picker: bpy.types.Object | None,
    obj: bpy.types.Object | None,
) -> None:
    """Bind mode + target armature + per-bone overrides, then the Bind button.

    The Bind button is drawn last so the panel reads Mode, overrides, then
    the action that consumes them; it is disabled when no picker armature is
    set. The overrides box only draws its per-bone rows under the planar
    modes - Bone Heat returns before the override pass in ``apply_bind``, so
    under it the box shows a hint instead of inert toggles.
    """
    bind_mode = "BONE_HEAT"
    if skinning_props is not None:
        layout.prop(skinning_props, "bind_init_mode", text="Mode")
        bind_mode = skinning_props.bind_init_mode
    layout.label(
        text=f"Target: {picker.name}" if picker is not None else "Target: (no picker armature)",
        icon="ARMATURE_DATA",
    )

    if picker is not None and obj is not None and obj.type == "MESH":
        _draw_bone_overrides(layout, obj, picker, bind_mode)

    row = layout.row()
    row.enabled = picker is not None
    row.operator(
        "proscenio.bind_mesh_to_armature",
        text="Bind to Picker Armature",
        icon="MOD_ARMATURE",
    )


def _draw_bone_overrides(
    layout: bpy.types.UILayout,
    obj: bpy.types.Object,
    picker: bpy.types.Object,
    bind_mode: str,
) -> None:
    """Per-bone Soft / Hard / Clear rows, or a hint when the mode ignores them.

    A missing entry means the bone uses the operator-level default
    (bind_init_mode); the per-row clear button drops an override back to it.
    """
    from ..core.skinning.bone_modes import (  # type: ignore[import-not-found]
        overrides_apply_under_bind_mode,
        read_bone_modes,
    )

    bones = picker.data.bones if picker.data is not None else []
    if not bones:
        return
    override_box = layout.box()
    override_box.label(text="Per-bone Soft/Hard overrides:")
    if not overrides_apply_under_bind_mode(bind_mode):
        override_box.label(
            text="applies only to the planar modes - Bone Heat ignores these",
            icon="INFO",
        )
        return
    modes = read_bone_modes(obj)
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
        clear_sub = bone_row.row(align=True)
        clear_sub.enabled = current != ""
        op_clear = clear_sub.operator("proscenio.set_bone_mode", text="", icon="X")
        op_clear.bone_name = bone.name
        op_clear.mode = "CLEAR"


def _draw_edit_weights(
    layout: bpy.types.UILayout,
    obj: bpy.types.Object | None,
    picker: bpy.types.Object | None,
) -> None:
    """Edit Weights modal entry + brush curve presets.

    Button enabled only when (a) picker armature set, (b) mesh has a
    populated sidecar (bind must precede edit).
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


def _draw_weight_overlay_controls(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
) -> None:
    """Native viewport overlay levers so the texture shows through while painting.

    Surfaces Blender's own weight-paint opacity + Zero Weights display rather
    than building a custom overlay (the flat-mesh display ask). Opacity 0 does
    not fully hide the overlay - upstream Blender issue 145603.
    """
    box = layout.box()
    box.label(text="Viewport display:")
    overlay = getattr(context.space_data, "overlay", None)
    if overlay is not None:
        box.prop(overlay, "weight_paint_mode_opacity", text="Weight Opacity")
    tool_settings = context.tool_settings
    if tool_settings is not None:
        box.prop(tool_settings, "vertex_group_user", text="Zero Weights")
    box.label(text="opacity 0 is not fully invisible (Blender 145603)", icon="INFO")


def _draw_snapshot(
    layout: bpy.types.UILayout,
    skinning_props: bpy.types.PropertyGroup | None,
    obj: bpy.types.Object | None,
) -> None:
    """Snapshot toggles + provenance counts pill + Restore + file IO.

    Counts are recomputed live from the JSON payload stored on the active mesh.
    The Export / Import buttons (folded in from the former Sidecar IO subpanel)
    write the snapshot to a file or load one back; Import also pushes it onto
    the live weights when the mesh topology still matches.
    """
    if skinning_props is not None:
        layout.prop(skinning_props, "preserve_on_regen")
        layout.prop(skinning_props, "show_provenance_overlay")
    counts = _sidecar_counts(obj)
    if counts is None:
        layout.label(text="no snapshot (run Bind first)", icon="INFO")
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
    layout.separator()
    io_row = layout.row(align=True)
    io_row.operator("proscenio.export_sidecar", text="Export Snapshot", icon="EXPORT")
    io_row.operator("proscenio.import_sidecar", text="Import Snapshot", icon="IMPORT")


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


_classes: tuple[type, ...] = (
    PROSCENIO_PT_weight_paint,
    PROSCENIO_PT_bind,
    PROSCENIO_PT_edit_weights,
    PROSCENIO_PT_snapshot,
    PROSCENIO_PT_weight_transfer,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
