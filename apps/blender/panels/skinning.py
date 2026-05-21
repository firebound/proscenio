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
        _draw_bind_box(layout, skinning_props, picker)
        _draw_snapshot_box(layout, skinning_props, obj)
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


def _draw_bind_box(
    layout: bpy.types.UILayout,
    skinning_props: bpy.types.PropertyGroup | None,
    picker: bpy.types.Object | None,
) -> None:
    """Sub-box for the Bind to Picker Armature operator.

    Surfaces the Bind mode dropdown (BONE_HEAT default + 4 Proscenio
    fallbacks) and the run button. Button greys out when no picker
    armature is set in the Skeleton panel - the most common cause of
    bind failure, caught visually instead of via post-click ERROR.

    falloff_power + max_distance are not surfaced here; they reach
    the user via F3 redo after the operator runs, keeping the panel
    UI focused on the common case.
    """
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
        text="Restore Weight Snapshot",
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
