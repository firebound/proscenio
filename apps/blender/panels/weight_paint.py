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
from ..core.bpy_helpers.i18n import iface
from ..core.bpy_helpers.skinning import read_snapshots  # type: ignore[import-not-found]
from ..core.list_view import clamped_rows  # type: ignore[import-not-found]
from ..core.skinning.bone_modes import (  # type: ignore[import-not-found]
    overrides_apply_under_bind_mode,
    read_bone_modes,
)
from ..core.skinning.sidecar_schema import (  # type: ignore[import-not-found]
    count_entries_by_provenance,
)
from ._helpers import (
    _active_armature,
    _is_mesh_element,
    _scene_skinning,
    draw_subpanel_header,
    draw_target_readout,
)
from ._list import ProscenioListMixin

# bl_idname of the per-bone Soft/Hard/Clear operator, reached via its string
# id-name (the project convention for operator calls); named once so the three
# row.operator() call sites below do not repeat the literal.
_SET_BONE_MODE_OT = "proscenio.set_bone_mode"


class PROSCENIO_PT_weight_paint(bpy.types.Panel):
    """Weight Paint - mesh-only bind + weight authoring; body in subpanels."""

    bl_label = "Weight Paint"
    bl_idname = "PROSCENIO_PT_weight_paint"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 6
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "weight_paint", "weight_paint")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        if not _is_mesh_element(context):
            layout.label(
                text=iface("select a mesh element (Weight Paint is mesh-only)"), icon="INFO"
            )
            return
        draw_target_readout(layout, _active_armature(context))


class PROSCENIO_PT_bind(bpy.types.Panel):
    """Bind subpanel - bind the active mesh to the target armature."""

    bl_label = "Bind"
    bl_idname = "PROSCENIO_PT_bind"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_weight_paint"
    bl_order = 0
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _is_mesh_element(context)

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "bind", "bind")

    def draw(self, context: bpy.types.Context) -> None:
        _draw_bind(
            self.layout,
            context,
            _scene_skinning(context),
            _active_armature(context),
            context.active_object,
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

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "edit_weights", "edit_weights")

    def draw(self, context: bpy.types.Context) -> None:
        _draw_edit_weights(self.layout, context.active_object, _active_armature(context))
        _draw_weight_overlay_controls(self.layout, context)
        _draw_edit_weights_shortcuts(self.layout)


def _draw_edit_weights_shortcuts(layout: bpy.types.UILayout) -> None:
    """Collapsible mirror of the Edit Weights modal's status-bar cheatsheet while
    it runs (the shared interactive-tool pattern: ``layout.panel`` default-closed,
    gated on the operator's ``_statusbar_appended`` flag). Canonical sibling:
    ``_draw_manual_draw_cheatsheet`` in ``panels/mesh_generation.py``."""
    from ..operators.skinning._status_bar import (  # type: ignore[import-not-found]
        emit_edit_weights_chords,
    )
    from ..operators.skinning.edit_weights import (  # type: ignore[import-not-found]
        PROSCENIO_OT_edit_weights_modal as op,
    )

    if not op._statusbar_appended:
        return
    header, body = layout.panel("proscenio_edit_weights_shortcuts", default_closed=True)
    header.label(text=iface("Shortcuts"), icon="BRUSHES_ALL")
    if body is not None:
        emit_edit_weights_chords(body)


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

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "snapshot", "snapshot")

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

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "weight_transfer", "weight_transfer")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        skinning_props = _scene_skinning(context)
        if skinning_props is not None:
            layout.prop(skinning_props.bind, "weight_transfer_max_distance", text="Max Distance")
        op = layout.operator("proscenio.copy_weights_to_selected", icon="DUPLICATE")
        if skinning_props is not None:
            # Seed the operator from the panel so the click uses the field value;
            # F9 redo still exposes max_distance for a one-off tweak.
            op.max_distance = skinning_props.bind.weight_transfer_max_distance


def _draw_bind(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
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
        layout.prop(skinning_props.bind, "init_mode", text="Mode")
        bind_mode = skinning_props.bind.init_mode
        # max_distance / falloff_power feed only the Proximity bind; the other
        # modes ignore both, so drawing them elsewhere would be inert UI. The
        # data path (operator props, invoke seeding, apply) is already wired -
        # this is layout-only.
        if bind_mode == "PROXIMITY":
            layout.prop(skinning_props.bind, "max_distance", text="Max Distance")
            layout.prop(skinning_props.bind, "falloff_power", text="Falloff Power")
    # No own "Target:" line - the Weight Paint parent panel already shows the
    # "Target: Skeleton <name>" readout above this subpanel.

    if picker is not None and obj is not None and obj.type == "MESH":
        _draw_bone_overrides(layout, context, picker, bind_mode)

    row = layout.row()
    row.enabled = picker is not None
    row.operator(
        "proscenio.bind_mesh_to_armature",
        text="Bind to Target Armature",
        icon="MOD_ARMATURE",
    )


class PROSCENIO_UL_bone_overrides(ProscenioListMixin, bpy.types.UIList):
    """Per-bone Soft / Hard / Clear override rows with native scroll + search.

    Bound to the target armature's bones; Soft / Hard set the active mesh's
    per-bone bind mode and the X clears it back to the operator default. The
    shared mixin gives it the native name filter and source (hierarchy) order;
    ``template_list`` caps the height so a many-bone rig scrolls instead of
    pushing the Bind button off-screen.
    """

    bl_idname = "PROSCENIO_UL_bone_overrides"

    def draw_item(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
        _data: bpy.types.AnyType,
        item: bpy.types.AnyType,
        _icon: int,
        _active_data: bpy.types.AnyType,
        _active_propname: str,
    ) -> None:
        obj = context.active_object
        current = read_bone_modes(obj).get(item.name, "") if obj is not None else ""
        row = layout.row(align=True)
        row.label(text=item.name)
        op_soft = row.operator(_SET_BONE_MODE_OT, text="Soft", depress=(current == "SOFT"))
        op_soft.bone_name = item.name
        op_soft.mode = "SOFT"
        op_hard = row.operator(_SET_BONE_MODE_OT, text="Hard", depress=(current == "HARD"))
        op_hard.bone_name = item.name
        op_hard.mode = "HARD"
        clear_sub = row.row(align=True)
        clear_sub.enabled = current != ""
        op_clear = clear_sub.operator(_SET_BONE_MODE_OT, text="", icon="X")
        op_clear.bone_name = item.name
        op_clear.mode = "CLEAR"


def _draw_bone_overrides(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    picker: bpy.types.Object,
    bind_mode: str,
) -> None:
    """Draw the per-bone Soft/Hard override list, or a hint when the mode ignores it.

    A missing entry means the bone uses the operator-level default
    (bind_init_mode); the per-row clear button drops an override back to it. The
    list is a native ``template_list`` so a many-bone rig scrolls inside a capped
    box instead of growing the panel unbounded.
    """
    bones = picker.data.bones if picker.data is not None else []
    if not bones:
        return
    override_box = layout.box()
    override_box.label(text=iface("Per-bone Soft/Hard overrides:"))
    if not overrides_apply_under_bind_mode(bind_mode):
        override_box.label(
            text=iface("applies only to the planar modes - Bone Heat ignores these"),
            icon="INFO",
        )
        return
    scene_props = getattr(context.scene, "proscenio", None)
    if scene_props is None:
        return
    override_box.template_list(
        "PROSCENIO_UL_bone_overrides",
        "",
        picker.data,
        "bones",
        scene_props,
        "active_bone_index",
        rows=clamped_rows(len(bones), minimum=3, maximum=6),
    )


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
    if obj is not None and obj.mode == "WEIGHT_PAINT":
        # In the mode: the button exits. Setting Object mode is enough - the
        # Edit Weights modal's own mode-watch timer then runs _finish, so the
        # teardown stays on a single code path.
        op = row.operator("object.mode_set", text="Exit Painting Mode", icon="CHECKMARK")
        op.mode = "OBJECT"
    else:
        row.enabled = _edit_weights_button_enabled(obj, picker)
        row.operator(
            "proscenio.edit_weights",
            text="Edit Weights",
            icon="BRUSHES_ALL",
        )
    if obj is None or obj.type != "MESH":
        return
    if obj.get(PROSCENIO_WEIGHT_SIDECAR) is None:
        layout.label(text=iface("bind first to enable"), icon="INFO")

    layout.label(text=iface("Brush curve preset:"))
    row = layout.row(align=True)
    for preset_name in PRESETS:
        op = row.operator("proscenio.set_brush_preset", text=PRESET_LABELS[preset_name])
        op.preset_name = preset_name

    # Maintenance: drop vertex groups left empty by re-binds or edits. The
    # operator polls for a mesh with groups, so it disables itself otherwise.
    layout.separator()
    layout.operator(
        "proscenio.clear_empty_vertex_groups",
        text="Clear Empty Vertex Groups",
        icon="TRASH",
    )


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
    box.label(text=iface("Viewport display:"))
    overlay = getattr(context.space_data, "overlay", None)
    if overlay is not None:
        box.prop(overlay, "weight_paint_mode_opacity", text="Weight Opacity")
    tool_settings = context.tool_settings
    if tool_settings is not None:
        box.prop(tool_settings, "vertex_group_user", text="Zero Weights")
    box.label(text=iface("opacity 0 is not fully invisible (Blender 145603)"), icon="INFO")


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
        layout.prop(skinning_props.automesh, "preserve_on_regen")
        # The provenance overlay toggle lived here but registered no draw handler
        # outside the Edit Weights modal (which forces the overlay on for its
        # session and restores the prior value on exit), so it was dead UI.
    counts = _sidecar_counts(obj)
    if counts is None:
        layout.label(text=iface("no snapshot (run Bind first)"), icon="INFO")
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
    _draw_named_snapshots(layout, obj)
    layout.separator()
    io_row = layout.row(align=True)
    io_row.operator("proscenio.export_sidecar", text="Export Snapshot", icon="EXPORT")
    io_row.operator("proscenio.import_sidecar", text="Import Snapshot", icon="IMPORT")


def _draw_named_snapshots(layout: bpy.types.UILayout, obj: bpy.types.Object | None) -> None:
    """Named save points: a Save button + one restore row per snapshot.

    Manual save points (pinned icon) are unbounded; the rolling auto-snapshots
    (recover icon) are the last few the Edit Weights modal captured per session.
    """
    layout.separator()
    has_sidecar = obj is not None and obj.get(PROSCENIO_WEIGHT_SIDECAR) is not None
    save_row = layout.row(align=True)
    save_row.enabled = has_sidecar
    save_row.operator("proscenio.save_weight_snapshot", text="Save Snapshot", icon="ADD")
    snapshots = read_snapshots(obj) if obj is not None else []
    if not snapshots:
        return
    box = layout.box().column(align=True)
    for snapshot in snapshots:
        snap_row = box.row(align=True)
        icon = "PINNED" if snapshot.kind == "manual" else "RECOVER_LAST"
        snap_row.label(text=snapshot.name, icon=icon)
        restore = snap_row.operator("proscenio.restore_named_snapshot", text="", icon="LOOP_BACK")
        restore.snapshot_name = snapshot.name


def _sidecar_counts(obj: bpy.types.Object | None) -> dict[str, int] | None:
    """Count the object's sidecar entries by provenance. None = no sidecar."""
    if obj is None or obj.type != "MESH":
        return None
    return count_entries_by_provenance(obj.get(PROSCENIO_WEIGHT_SIDECAR))


_classes: tuple[type, ...] = (
    PROSCENIO_UL_bone_overrides,
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
