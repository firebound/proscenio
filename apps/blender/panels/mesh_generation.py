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
from ..core._shared.material_images import first_material_image
from ._helpers import (
    _active_armature,
    _is_mesh_element,
    _scene_skinning,
    draw_subpanel_header,
    draw_target_readout,
)


class PROSCENIO_PT_mesh_generation(bpy.types.Panel):
    """Mesh Generation - isolated Interior Mode + target readout; body in subpanels."""

    bl_label = "Mesh Generation"
    bl_idname = "PROSCENIO_PT_mesh_generation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 5
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "mesh_generation", "mesh_generation")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            layout.label(text="select a mesh to generate or edit", icon="INFO")
            return
        if not _is_mesh_element(context):
            # warn-not-hide: a sprite element is a mesh in Blender, but meshing
            # it would replace its single quad. Point at native bone-parenting.
            layout.label(text="mesh tools are mesh-only (this is a sprite)", icon="INFO")
            layout.label(text="to rig a sprite, parent it to a bone: Ctrl+P > Bone")
            return
        skinning_props = _scene_skinning(context)
        draw_target_readout(layout, _active_armature(context))
        if skinning_props is not None:
            # The trace params both entry points read (Automesh from Alpha + the
            # Interactive modal) live on the parent so neither subpanel hides
            # them; the alpha-only knobs stay in the Automesh from Alpha subpanel.
            layout.prop(skinning_props, "automesh_interior_mode")
            col = layout.column(align=True)
            col.prop(skinning_props, "automesh_contour_vertices")
            # Interior spacing is not dense-only: the interactive modal reads it
            # in SIMPLE mode too (free-draw resample + fold snap radius).
            col.prop(skinning_props, "automesh_interior_spacing")
            is_dense = skinning_props.automesh_interior_mode == "DENSE"
            dense_col = col.column(align=True)
            dense_col.active = is_dense
            dense_col.prop(skinning_props, "automesh_density_under_bones")
            sub = dense_col.column(align=True)
            sub.active = is_dense and bool(skinning_props.automesh_density_under_bones)
            sub.prop(skinning_props, "automesh_bone_radius")
            sub.prop(skinning_props, "automesh_bone_factor")


class PROSCENIO_PT_automesh_alpha(bpy.types.Panel):
    """Automesh from Alpha subpanel - the one-shot alpha-trace + its defaults."""

    bl_label = "Automesh from Alpha"
    bl_idname = "PROSCENIO_PT_automesh_alpha"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_mesh_generation"
    bl_order = 0
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _is_mesh_element(context)

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "automesh_alpha", "automesh_alpha")

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
        return _is_mesh_element(context)

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "automesh_interactive", "automesh_interactive")

    def draw(self, context: bpy.types.Context) -> None:
        _draw_automesh_interactive(self.layout, _scene_skinning(context), context.active_object)


class PROSCENIO_PT_manual_mesh(bpy.types.Panel):
    """Manual Mesh - the standalone Draw-with-vertices mode (spec 070).

    A TOP-LEVEL panel, separate from Mesh Generation: it is manual mesh
    AUTHORING, not automatic generation, and shares none of the automesh trace
    fields - keeping it apart avoids implying those fields affect it. Mutually
    exclusive with the Automesh modes (one per element). Like the other mesh
    panels it WARNS (not hides) on a sprite / non-mesh and carries the standard
    status badge + help button.
    """

    bl_label = "Manual Mesh"
    bl_idname = "PROSCENIO_PT_manual_mesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 6  # just after Mesh Generation (bl_order 5)
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "manual_mesh", "manual_mesh")

    def draw(self, context: bpy.types.Context) -> None:
        _draw_manual_mesh(self.layout, context)


class PROSCENIO_PT_debug_pipeline(bpy.types.Panel):
    """Debug Pipeline subpanel - the automesh debug stage enum + clear button."""

    bl_label = "Debug Pipeline"
    bl_idname = "PROSCENIO_PT_debug_pipeline"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_mesh_generation"
    bl_order = 3
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _is_mesh_element(context) and debug_mode_enabled(context)

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "debug_pipeline", "debug_pipeline")

    def draw(self, context: bpy.types.Context) -> None:
        _draw_debug_pipeline(self.layout, _scene_skinning(context))


def _draw_automesh_alpha(
    layout: bpy.types.UILayout,
    skinning_props: bpy.types.PropertyGroup | None,
) -> None:
    """Automesh-from-alpha-only defaults + the run button - drawn on the subpanel.

    The trace params shared with the Interactive modal (Interior Mode, contour
    vertices, interior spacing, the dense fields) live on the parent panel; only
    the alpha-trace-specific knobs are here.
    """
    if skinning_props is not None:
        col = layout.column(align=True)
        col.prop(skinning_props, "automesh_resolution")
        col.prop(skinning_props, "automesh_alpha_threshold")
        col.prop(skinning_props, "automesh_margin_pixels")
        col.separator()
        col.prop(skinning_props, "preserve_base_quad")
        # Regen reprojects weights when ON; surfaced here (not only in the
        # Snapshot subpanel) because this button is what triggers the regen.
        col.prop(skinning_props, "preserve_on_regen")
    layout.operator(
        "proscenio.automesh_from_alpha",
        text="Automesh from Alpha",
        icon="MOD_REMESH",
    )


def _automesh_running() -> bool:
    from ..operators.automesh._authoring_modal_guard import (  # type: ignore[import-not-found]
        is_running,
    )

    return is_running("automesh")


def _manual_draw_running() -> bool:
    from ..operators.automesh._authoring_modal_guard import (  # type: ignore[import-not-found]
        is_running,
    )

    return is_running("manual_draw")


def _draw_automesh_cheatsheet(layout: bpy.types.UILayout) -> None:
    """Collapsible mirror of the Automesh modal's status-bar cheatsheet while it
    runs (Quick Armature pattern: ``layout.panel`` default-closed, full chords)."""
    from ..operators.automesh._status_bar import (  # type: ignore[import-not-found]
        emit_authoring_chord_layout,
    )
    from ..operators.automesh.automesh_authoring import (  # type: ignore[import-not-found]
        PROSCENIO_OT_automesh_authoring as op,
    )

    state = op.authoring_state()
    if not state.active:
        return
    header, body = layout.panel("proscenio_automesh_shortcuts", default_closed=True)
    header.label(text="Shortcuts", icon="MOD_REMESH")
    if body is not None:
        emit_authoring_chord_layout(body, state.label, state.stage, state.tool)


def _draw_manual_draw_cheatsheet(layout: bpy.types.UILayout) -> None:
    """Collapsible mirror of the Manual Draw modal's cheatsheet while it runs."""
    from ..operators.automesh.draw_mesh_vertices import (  # type: ignore[import-not-found]
        PROSCENIO_OT_draw_mesh_vertices as op,
    )
    from ..operators.automesh.draw_mesh_vertices import (  # type: ignore[import-not-found]
        emit_manual_draw_chords,
    )

    if not _manual_draw_running():
        return
    header, body = layout.panel("proscenio_manual_draw_shortcuts", default_closed=True)
    header.label(text=f"Shortcuts - {op._current_tool}", icon="GREASEPENCIL")
    if body is not None:
        emit_manual_draw_chords(body, op._current_tool)


def _draw_automesh_interactive(
    layout: bpy.types.UILayout,
    skinning_props: bpy.types.PropertyGroup | None,
    obj: bpy.types.Object | None,
) -> None:
    """Interactive modal automesh authoring entry. The button TOGGLES: it starts
    the modal, and re-invokes as an Exit while it runs (Quick Armature pattern);
    the trace fields stay editable mid-flight (the modal polls them live)."""
    running = _automesh_running()
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
    if running:
        _draw_automesh_step_nav(layout)
    row = layout.row()
    # Stay enabled while running so the Exit click lands; otherwise gate on a
    # MESH + image texture.
    row.enabled = running or _authoring_button_enabled(obj)
    row.operator(
        "proscenio.automesh_authoring",
        text="Exit Author Mesh" if running else "Author Mesh (interactive)",
        icon="X" if running else "MOD_REMESH",
        depress=running,
    )
    _draw_automesh_cheatsheet(layout)


def _draw_automesh_step_nav(layout: bpy.types.UILayout) -> None:
    """Stage nav for the running modal: the current step label + Back / Next
    buttons that drive the modal from the panel (spec 070), above the Exit row."""
    from ..operators.automesh.automesh_authoring import (  # type: ignore[import-not-found]
        PROSCENIO_OT_automesh_authoring as op,
    )

    layout.label(text=op.authoring_state().label, icon="MOD_REMESH")
    row = layout.row(align=True)
    back = row.operator("proscenio.automesh_step", text="Back", icon="TRIA_LEFT")
    back.direction = "RETREAT"
    nxt = row.operator("proscenio.automesh_step", text="Next", icon="TRIA_RIGHT")
    nxt.direction = "ADVANCE"


def _draw_manual_mesh(layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
    """Manual Mesh panel body (spec 070) - the standalone Draw-with-vertices mode.

    WARNS (not hides) on a non-mesh / sprite, mirroring Mesh Generation. Toggles
    like the automesh entry (start / Exit); the button greys out without a MESH +
    image texture and stays live while running so the Exit click lands.
    """
    obj = context.active_object
    if obj is None or obj.type != "MESH":
        layout.label(text="select a mesh to author", icon="INFO")
        return
    if not _is_mesh_element(context):
        # warn-not-hide: a sprite element is a Blender mesh, but drawing a mesh
        # would replace its single quad. Point at native bone-parenting.
        layout.label(text="mesh tools are mesh-only (this is a sprite)", icon="INFO")
        layout.label(text="to rig a sprite, parent it to a bone: Ctrl+P > Bone")
        return
    running = _manual_draw_running()
    layout.label(text="Build the mesh by clicking vertices")
    skinning_props = _scene_skinning(context)
    if skinning_props is not None:
        # Spec 070 C1: Manual Mesh has its own interior-mode toggle (independent
        # of the automesh fields); DENSE reveals the shared interior spacing knob.
        layout.prop(skinning_props, "manual_interior_mode")
        if skinning_props.manual_interior_mode == "DENSE":
            layout.prop(skinning_props, "automesh_interior_spacing")
    row = layout.row()
    row.enabled = running or _authoring_button_enabled(obj)
    row.operator(
        "proscenio.draw_mesh_vertices",
        text="Exit Draw with vertices" if running else "Draw with vertices",
        icon="X" if running else "GREASEPENCIL",
        depress=running,
    )
    _draw_manual_draw_cheatsheet(layout)


def _authoring_button_enabled(obj: bpy.types.Object | None) -> bool:
    if obj is None or obj.type != "MESH":
        return False
    return first_material_image(obj) is not None


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
    PROSCENIO_PT_manual_mesh,
    PROSCENIO_PT_debug_pipeline,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
