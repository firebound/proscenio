"""Mesh Generation panel + automesh accordion subpanels.

Was the Skinning panel. The parent hosts the isolated Interior Mode
selector + the picker readout; the automesh entry points split into
accordion subpanels: Automesh from Alpha (the one-shot alpha-trace),
Automesh Interactive (the modal authoring entry), and Debug Pipeline
(the stage enum + clear button).

Weight painting (Bind / Edit Weights / Snapshot / Weight Transfer) lives
in the dedicated mesh-only ``weight_paint`` panel. The
status badge + help button on each automesh subpanel header land with the
header-convention pass (a later phase); the parent keeps the existing
``skinning`` badge until the feature-id rename in that same phase.
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..addon_prefs import debug_mode_enabled
from ..core._shared.props_access import element_type_of  # type: ignore[import-not-found]
from ._helpers import (
    _active_armature,
    _scene_skinning,
    draw_picker_readout,
    draw_subpanel_header,
)


def _active_is_mesh_element(context: bpy.types.Context) -> bool:
    """True when the active object is a MESH whose element_type is "mesh".

    A sprite element is also a Blender MESH, but running a mesh tool on it
    replaces its single quad - so the mesh-generation gate matches the
    weight_paint panel and excludes sprites. Mirrors weight_paint._is_mesh_element.
    """
    obj = context.active_object
    if obj is None or obj.type != "MESH":
        return False
    return element_type_of(obj) == "mesh"


class PROSCENIO_PT_mesh_generation(bpy.types.Panel):
    """Mesh Generation - isolated Interior Mode + picker readout; body in subpanels."""

    bl_label = "Mesh Generation"
    bl_idname = "PROSCENIO_PT_mesh_generation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 5
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "mesh_generation", "mesh_generation")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            layout.label(text="select a mesh to generate or edit", icon="INFO")
            return
        if not _active_is_mesh_element(context):
            # warn-not-hide: a sprite element is a mesh in Blender, but meshing
            # it would replace its single quad. Point at native bone-parenting.
            layout.label(text="mesh tools are mesh-only (this is a sprite)", icon="INFO")
            layout.label(text="to rig a sprite, parent it to a bone: Ctrl+P > Bone")
            return
        skinning_props = _scene_skinning(context)
        draw_picker_readout(layout, _active_armature(context))
        if skinning_props is not None:
            layout.prop(skinning_props, "automesh_interior_mode")


class PROSCENIO_PT_automesh_alpha(bpy.types.Panel):
    """Automesh from Alpha subpanel - the one-shot alpha-trace + its defaults."""

    bl_label = "Automesh from Alpha"
    bl_idname = "PROSCENIO_PT_automesh_alpha"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_mesh_generation"
    bl_order = 0

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_is_mesh_element(context)

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "automesh_alpha", "automesh_alpha")

    def draw(self, context: bpy.types.Context) -> None:
        _draw_automesh_alpha(self.layout, _scene_skinning(context))


class PROSCENIO_PT_automesh_interactive(bpy.types.Panel):
    """Automesh Interactive subpanel - the multi-stage modal authoring entry."""

    bl_label = "Automesh Interactive"
    bl_idname = "PROSCENIO_PT_automesh_interactive"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_mesh_generation"
    bl_order = 1
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_is_mesh_element(context)

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "automesh_interactive", "automesh_interactive")

    def draw(self, context: bpy.types.Context) -> None:
        _draw_automesh_interactive(self.layout, _scene_skinning(context), context.active_object)


class PROSCENIO_PT_debug_pipeline(bpy.types.Panel):
    """Debug Pipeline subpanel - the automesh debug stage enum + clear button."""

    bl_label = "Debug Pipeline"
    bl_idname = "PROSCENIO_PT_debug_pipeline"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_mesh_generation"
    bl_order = 2
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_is_mesh_element(context) and debug_mode_enabled(context)

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "debug_pipeline", "debug_pipeline")

    def draw(self, context: bpy.types.Context) -> None:
        _draw_debug_pipeline(self.layout, _scene_skinning(context))


def _draw_automesh_alpha(
    layout: bpy.types.UILayout,
    skinning_props: bpy.types.PropertyGroup | None,
) -> None:
    """Automesh-from-alpha defaults + the run button - drawn on the subpanel layout.

    Interior Mode lives on the parent panel; the dense-only fields here
    read it back for their ``active`` state.
    """
    if skinning_props is not None:
        col = layout.column(align=True)
        col.prop(skinning_props, "automesh_resolution")
        col.prop(skinning_props, "automesh_alpha_threshold")
        col.prop(skinning_props, "automesh_margin_pixels")
        col.prop(skinning_props, "automesh_contour_vertices")
        # Interior spacing is not dense-only: the interactive modal reads it in
        # SIMPLE mode too (free-draw resample + fold snap radius), so it stays
        # in the always-active column rather than greyed behind DENSE.
        col.prop(skinning_props, "automesh_interior_spacing")
        col.separator()
        col.prop(skinning_props, "preserve_base_quad")
        # Regen reprojects weights when ON; surfaced here (not only in the
        # Snapshot subpanel) because this button is what triggers the regen.
        col.prop(skinning_props, "preserve_on_regen")
        col.separator()
        is_dense = skinning_props.automesh_interior_mode == "DENSE"
        dense_col = col.column(align=True)
        dense_col.active = is_dense
        dense_col.prop(skinning_props, "automesh_density_under_bones")
        sub = dense_col.column(align=True)
        sub.active = is_dense and bool(skinning_props.automesh_density_under_bones)
        sub.prop(skinning_props, "automesh_bone_radius")
        sub.prop(skinning_props, "automesh_bone_factor")
    layout.operator(
        "proscenio.automesh_from_alpha",
        text="Automesh from Alpha",
        icon="MOD_REMESH",
    )


def _draw_automesh_interactive(
    layout: bpy.types.UILayout,
    skinning_props: bpy.types.PropertyGroup | None,
    obj: bpy.types.Object | None,
) -> None:
    """Interactive modal automesh authoring entry - drawn on the subpanel layout.

    Button greys out when active obj is not MESH or has no image texture
    (modal validates these at invoke; the panel mirror is a UX cue).
    """
    layout.label(text="Interactive trace and edit")
    if skinning_props is not None:
        row = layout.row(align=True)
        row.prop(skinning_props, "authoring_inner_loop_count", text="Loops")
        row.prop(skinning_props, "authoring_inner_loop_spacing", text="Spacing")
        row = layout.row()
        row.prop(skinning_props, "authoring_cut_margin", text="Cut margin")
        # APPLY regenerates the mesh + reprojects weights when ON; mirror the
        # toggle here so the regen trigger and its weight-preserve control sit
        # together.
        layout.prop(skinning_props, "preserve_on_regen")
    row = layout.row()
    row.enabled = _authoring_button_enabled(obj)
    row.operator(
        "proscenio.automesh_authoring",
        text="Author Mesh (interactive)",
        icon="MOD_REMESH",
    )
    if obj is None or obj.type != "MESH":
        layout.label(text="select a mesh first", icon="INFO")


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


def _draw_debug_pipeline(
    layout: bpy.types.UILayout,
    skinning_props: bpy.types.PropertyGroup | None,
) -> None:
    """Automesh debug stage enum + clear button - drawn on the subpanel layout.

    Stage selection survives to the operator via ProscenioSkinningProps
    so the user can pick a stage from the panel and click the main
    Automesh button (which reads the PG at invoke time). The Clear
    button below is a separate operator that nukes every debug
    companion for the active sprite.
    """
    if skinning_props is None:
        return
    layout.prop(skinning_props, "debug_stage", text="")
    layout.operator(
        "proscenio.clear_automesh_debug",
        text="Clear Debug Companions",
        icon="TRASH",
    )


_classes: tuple[type, ...] = (
    PROSCENIO_PT_mesh_generation,
    PROSCENIO_PT_automesh_alpha,
    PROSCENIO_PT_automesh_interactive,
    PROSCENIO_PT_debug_pipeline,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
