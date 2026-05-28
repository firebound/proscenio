"""Skinning subpanel (SPEC 013 Wave 13.1).

Parallel to ``PROSCENIO_PT_skeleton`` per D13. Surfaces the
Automesh + Bind + Edit Weights operators alongside the
``scene.proscenio.skinning`` defaults so the user can tune the
density / threshold / margin in context.

Wave 13.1 first cut ships only the Automesh sub-box. Bind +
Edit Weights buttons appear here in later Wave 13.1 commits;
they live behind ``# TODO(SPEC 013 follow-up)`` comments so
the layout shape is stable.
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ._helpers import draw_subpanel_header


class PROSCENIO_PT_skinning(bpy.types.Panel):
    """Skinning subpanel - automesh, bind, weight paint helpers."""

    bl_label = "Skinning"
    bl_idname = "PROSCENIO_PT_skinning"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return obj is not None and obj.type == "MESH"

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "skinning", "skinning")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene_props = getattr(context.scene, "proscenio", None)
        skinning_props = getattr(scene_props, "skinning", None) if scene_props is not None else None

        picker = getattr(scene_props, "active_armature", None) if scene_props is not None else None
        picker_row = layout.row(align=True)
        picker_row.label(text="", icon="ARMATURE_DATA")
        if picker is not None:
            picker_row.label(text=f"Picker: {picker.name}")
        else:
            picker_row.label(text="Picker: (none - set in Skeleton panel)", icon="INFO")

        obj = context.active_object
        _draw_automesh_box(layout, skinning_props)
        _draw_authoring_box(layout, skinning_props, obj)
        _draw_bind_box(layout, skinning_props, picker, obj)
        _draw_edit_weights_box(layout, obj, picker)
        _draw_weight_transfer_box(layout)
        _draw_snapshot_box(layout, skinning_props, obj)
        _draw_sidecar_io_box(layout, obj)
        _draw_debug_box(layout, skinning_props)


def _draw_automesh_box(
    layout: bpy.types.UILayout,
    skinning_props: bpy.types.PropertyGroup | None,
) -> None:
    """Sub-box surfacing the Automesh defaults + the run button."""
    box = layout.box()
    box.label(text="Automesh from sprite", icon="OUTLINER_OB_MESH")
    if skinning_props is not None:
        col = box.column(align=True)
        col.prop(skinning_props, "automesh_resolution")
        col.prop(skinning_props, "automesh_alpha_threshold")
        col.prop(skinning_props, "automesh_margin_pixels")
        col.prop(skinning_props, "automesh_contour_vertices")
        col.prop(skinning_props, "automesh_interior_spacing")
        col.separator()
        col.prop(skinning_props, "preserve_base_quad")
        col.separator()
        col.prop(skinning_props, "automesh_density_under_bones")
        sub = col.column(align=True)
        sub.active = bool(skinning_props.automesh_density_under_bones)
        sub.prop(skinning_props, "automesh_bone_radius")
        sub.prop(skinning_props, "automesh_bone_factor")
    box.operator(
        "proscenio.automesh_from_sprite",
        text="Automesh from Sprite",
        icon="MOD_REMESH",
    )


def _draw_authoring_box(
    layout: bpy.types.UILayout,
    skinning_props: bpy.types.PropertyGroup | None,
    obj: bpy.types.Object | None,
) -> None:
    """Sub-box surfacing the interactive modal automesh authoring entry.

    Button greys out when active obj is not MESH or has no image texture
    (modal validates these at invoke; the panel mirror is a UX cue).
    """
    box = layout.box()
    box.label(text="Automesh authoring", icon="MOD_REMESH")
    box.label(text="Multi-stage modal preview")
    if skinning_props is not None:
        row = box.row(align=True)
        row.prop(skinning_props, "authoring_inner_loop_count", text="Loops")
        row.prop(skinning_props, "authoring_inner_loop_spacing", text="Spacing")
        row = box.row()
        row.prop(skinning_props, "authoring_cut_margin", text="Cut margin")
    row = box.row()
    row.enabled = _authoring_button_enabled(obj)
    row.operator(
        "proscenio.automesh_authoring",
        text="Automesh (modal)",
        icon="MOD_REMESH",
    )
    if obj is None or obj.type != "MESH":
        box.label(text="select a mesh first", icon="INFO")


def _authoring_button_enabled(obj: bpy.types.Object | None) -> bool:
    if obj is None or obj.type != "MESH":
        return False
    if obj.data is None:
        return False
    return any(
        node.type == "TEX_IMAGE" and node.image is not None
        for material in obj.data.materials
        if material is not None and material.use_nodes and material.node_tree is not None
        for node in material.node_tree.nodes
    )


def _draw_bind_box(
    layout: bpy.types.UILayout,
    skinning_props: bpy.types.PropertyGroup | None,
    picker: bpy.types.Object | None,
    obj: bpy.types.Object | None = None,
) -> None:
    """Sub-box for the Bind to Picker Armature operator.

    Surfaces the Bind mode dropdown (BONE_HEAT default + 4 Proscenio
    fallbacks) and the run button. Button greys out when no picker
    armature is set in the Skeleton panel - the most common cause of
    bind failure, caught visually instead of via post-click ERROR.

    falloff_power + max_distance are not surfaced here; they reach
    the user via F3 redo after the operator runs, keeping the panel
    UI focused on the common case.

    Per-bone Soft/Hard override rows appear below the run button when
    a picker armature is present. Each bone gets a two-button toggle;
    depress=True marks the active override. Missing entry means the
    bone uses the operator-level default (bind_init_mode).
    """
    from ..core.skinning.bone_modes import read_bone_modes  # type: ignore[import-not-found]

    box = layout.box()
    box.label(text="Bind to picker", icon="LINK_BLEND")
    if skinning_props is not None:
        box.prop(skinning_props, "bind_init_mode", text="Mode")
    row = box.row()
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

    override_box = box.box()
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


def _draw_edit_weights_box(
    layout: bpy.types.UILayout,
    obj: bpy.types.Object | None,
    picker: bpy.types.Object | None,
) -> None:
    """Sub-box surfacing the Edit Weights modal entry button.

    Button enabled only when (a) picker armature set, (b) mesh has
    a populated sidecar (binds preceded edit). Active vertex group
    label hints which bone the modal will start painting.

    Brush curve presets (O4) appear below the entry button as a
    4-button aligned row so the artist can switch curve shape without
    opening the brush curve editor.
    """
    from ..core.skinning.brush_curve_presets import (  # type: ignore[import-not-found]
        PRESET_LABELS,
        PRESETS,
    )

    box = layout.box()
    box.label(text="Edit Weights", icon="BRUSHES_ALL")
    active_label = _active_group_label(obj)
    box.label(text=f"Active group: {active_label}")
    row = box.row()
    row.enabled = _edit_weights_button_enabled(obj, picker)
    row.operator(
        "proscenio.edit_weights",
        text="Edit Weights",
        icon="BRUSHES_ALL",
    )
    if obj is None or obj.type != "MESH":
        return
    if obj.get("proscenio_weight_sidecar") is None:
        box.label(text="bind first to enable", icon="INFO")

    box.label(text="Brush curve preset:")
    row = box.row(align=True)
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
    return obj.get("proscenio_weight_sidecar") is not None


def _draw_weight_transfer_box(layout: bpy.types.UILayout) -> None:
    """Sub-box surfacing the Copy Weights to Selected operator (SPEC 013 O7).

    Active mesh = source; other selected meshes = targets. Button
    enabled by operator poll (active MESH + at least one other selected MESH).
    """
    box = layout.box()
    box.label(text="Weight transfer:", icon="DUPLICATE")
    box.operator("proscenio.copy_weights_to_selected", icon="DUPLICATE")


def _draw_snapshot_box(
    layout: bpy.types.UILayout,
    skinning_props: bpy.types.PropertyGroup | None,
    obj: bpy.types.Object | None,
) -> None:
    """Sub-box surfacing the sidecar toggles + counts pill + Restore button.

    Counts are recomputed live from the JSON payload stored on the
    active mesh (single source of truth per T6 of sidecar-design).
    Toggle for show_provenance_overlay reserves UI for Wave 13.2-paint
    even though the GPU draw handler is not in scope this wave.
    """
    box = layout.box()
    box.label(text="Snapshot", icon="FILE_TICK")
    if skinning_props is not None:
        box.prop(skinning_props, "preserve_on_regen")
        box.prop(skinning_props, "show_provenance_overlay")
    counts = _sidecar_counts(obj)
    if counts is None:
        box.label(text="no sidecar (run Bind first)", icon="INFO")
    else:
        box.label(
            text=(
                f"{counts['user_paint']} paint / "
                f"{counts['auto_seed']} seed / "
                f"{counts['reprojected']} reprojected"
            )
        )
    row = box.row()
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
    payload = obj.get("proscenio_weight_sidecar")
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


def _draw_sidecar_io_box(
    layout: bpy.types.UILayout,
    obj: bpy.types.Object | None,
) -> None:
    """Sub-box with Export + Import file-dialog buttons for sidecar JSON."""
    box = layout.box()
    box.label(text="Sidecar IO", icon="FILE_TEXT")
    row = box.row(align=True)
    row.operator("proscenio.export_sidecar", text="Export", icon="EXPORT")
    row.operator("proscenio.import_sidecar", text="Import", icon="IMPORT")
    if obj is not None and obj.type == "MESH" and obj.get("proscenio_weight_sidecar") is None:
        box.label(text="no sidecar yet (run Bind first)", icon="INFO")


def _draw_debug_box(
    layout: bpy.types.UILayout,
    skinning_props: bpy.types.PropertyGroup | None,
) -> None:
    """Sub-box exposing the Automesh debug stage enum + clear button.

    Stage selection survives to the operator via ProscenioSkinningProps
    so the user can pick a stage from the panel and click the main
    Automesh button (which reads the PG at invoke time). The Clear
    button below is a separate operator that nukes every debug
    companion for the active sprite.
    """
    if skinning_props is None:
        return
    box = layout.box()
    box.label(text="Debug pipeline", icon="EXPERIMENTAL")
    box.prop(skinning_props, "debug_stage", text="")
    box.operator(
        "proscenio.clear_automesh_debug",
        text="Clear Debug Companions",
        icon="TRASH",
    )


_classes: tuple[type, ...] = (PROSCENIO_PT_skinning,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
