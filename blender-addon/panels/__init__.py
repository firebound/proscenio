"""Blender UI panels (SPEC 005).

The sidebar is anchored by `PROSCENIO_PT_main`. Every other panel is a
child via `bl_parent_id`, which gives us collapsible subsections users
can fold individually. Subpanels poll on the active selection (or scene
state) so empty subpanels do not clutter the sidebar.
"""

from typing import ClassVar

import bpy

from ..core import validation  # type: ignore[import-not-found]


class PROSCENIO_PT_main(bpy.types.Panel):
    """Sidebar root — version banner; child panels do the work."""

    bl_label = "Proscenio"
    bl_idname = "PROSCENIO_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(text="Pipeline v0.1.0", icon="INFO")


_OBJECT_FRIENDLY_MODES = {"OBJECT", "EDIT_MESH", "PAINT_WEIGHT", "PAINT_VERTEX"}
_POSE_FRIENDLY_MODES = {"OBJECT", "POSE", "EDIT_ARMATURE"}


def _draw_region_box(
    layout: bpy.types.UILayout,
    props: bpy.types.AnyType,
    *,
    sprite_type: str,
) -> None:
    """Render the texture_region authoring box (5.1.c.1).

    Auto mode shows a static "computed at export" hint; manual mode unlocks
    the four region floats + the Snap-to-UV-bounds operator. For sprite_frame,
    auto mode means the writer omits texture_region entirely (full atlas).
    """
    box = layout.box()
    box.label(text="Texture region", icon="UV_DATA")
    box.prop(props, "region_mode", text="")
    if props.region_mode == "manual":
        row = box.row(align=True)
        row.prop(props, "region_x")
        row.prop(props, "region_y")
        row = box.row(align=True)
        row.prop(props, "region_w")
        row.prop(props, "region_h")
        if sprite_type == "polygon":
            box.operator("proscenio.snap_region_to_uv", icon="UV")
    else:
        hint = (
            "computed from UV bounds at export"
            if sprite_type == "polygon"
            else "omitted at export — full atlas used"
        )
        box.label(text=hint, icon="INFO")


def _draw_weight_paint_brush(layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
    """Mirror Blender's weight-paint brush controls inline (5.1.b)."""
    box = layout.box()
    box.label(text="Weight paint", icon="BRUSH_DATA")
    tool_settings = context.tool_settings
    wp = getattr(tool_settings, "weight_paint", None)
    brush = getattr(wp, "brush", None) if wp is not None else None
    if brush is None:
        box.label(text="no active brush", icon="INFO")
        return
    ups = tool_settings.unified_paint_settings
    box.prop(ups, "use_unified_size", text="Unified size")
    box.prop(ups if ups.use_unified_size else brush, "size", slider=True)
    box.prop(ups, "use_unified_strength", text="Unified strength")
    box.prop(ups if ups.use_unified_strength else brush, "strength", slider=True)
    box.prop(ups if ups.use_unified_weight else brush, "weight", slider=True)
    box.prop(brush, "use_auto_normalize", text="Auto-normalize")


class PROSCENIO_PT_active_sprite(bpy.types.Panel):
    """Per-sprite settings — sprite type dropdown + sprite_frame metadata."""

    bl_label = "Active Sprite"
    bl_idname = "PROSCENIO_PT_active_sprite"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return False
        return context.mode in _OBJECT_FRIENDLY_MODES

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        obj = context.active_object
        if obj is None:
            return

        props = getattr(obj, "proscenio", None)
        if props is None:
            layout.label(text="proscenio property group not registered", icon="ERROR")
            return

        layout.prop(props, "sprite_type")

        if props.sprite_type == "sprite_frame":
            box = layout.box()
            box.label(text="Sprite frame", icon="IMAGE_DATA")
            box.prop(props, "hframes")
            box.prop(props, "vframes")
            box.prop(props, "frame")
            box.prop(props, "centered")
            _draw_region_box(layout, props, sprite_type="sprite_frame")
        elif context.mode == "PAINT_WEIGHT":
            _draw_weight_paint_brush(layout, context)
        else:
            mesh = obj.data
            vg_count = len(getattr(obj, "vertex_groups", []) or [])
            poly_count = len(getattr(mesh, "polygons", []) or [])
            box = layout.box()
            box.label(text="Polygon", icon="MESH_DATA")
            box.label(text=f"{poly_count} polygon(s), {vg_count} vertex group(s)")
            box.operator("proscenio.reproject_sprite_uv", icon="UV")
            _draw_region_box(layout, props, sprite_type="polygon")

        for issue in validation.validate_active_sprite(obj):
            row = layout.row()
            icon = "ERROR" if issue.severity == "error" else "INFO"
            row.alert = issue.severity == "error"
            row.label(text=issue.message, icon=icon)


class PROSCENIO_PT_skeleton(bpy.types.Panel):
    """Skeleton summary — bone count + presence checks."""

    bl_label = "Skeleton"
    bl_idname = "PROSCENIO_PT_skeleton"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.mode in _POSE_FRIENDLY_MODES

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        armatures = [o for o in context.scene.objects if o.type == "ARMATURE"]
        if not armatures:
            row = layout.row()
            row.alert = True
            row.label(text="no Armature in scene", icon="ERROR")
            return
        first = armatures[0]
        bones = getattr(first.data, "bones", [])
        layout.label(text=f"Armature '{first.name}' — {len(bones)} bone(s)")
        if len(armatures) > 1:
            row = layout.row()
            row.alert = True
            row.label(
                text=f"{len(armatures)} armatures — writer uses the first only",
                icon="ERROR",
            )
        # Pose-mode-only helpers (5.1.a + 5.1.b).
        if context.mode == "POSE":
            layout.separator()
            layout.operator("proscenio.bake_current_pose", icon="KEY_HLT")
            layout.operator("proscenio.toggle_ik_chain", icon="CON_KINEMATIC")


class PROSCENIO_UL_actions(bpy.types.UIList):
    """List view for ``bpy.data.actions`` — Animation subpanel uses this."""

    bl_idname = "PROSCENIO_UL_actions"

    def draw_item(
        self,
        _context: bpy.types.Context,
        layout: bpy.types.UILayout,
        _data: bpy.types.AnyType,
        item: bpy.types.AnyType,
        _icon: int,
        _active_data: bpy.types.AnyType,
        _active_propname: str,
    ) -> None:
        start, end = item.frame_range
        row = layout.row(align=True)
        row.label(text=item.name, icon="ACTION")
        row.label(text=f"[{start:.0f}-{end:.0f}]")


class PROSCENIO_PT_animation(bpy.types.Panel):
    """Read-only summary of the actions the writer would emit."""

    bl_label = "Animation"
    bl_idname = "PROSCENIO_PT_animation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        actions = bpy.data.actions
        if not actions:
            layout.label(text="no actions to export", icon="INFO")
            return
        layout.template_list(
            "PROSCENIO_UL_actions",
            "",
            bpy.data,
            "actions",
            context.scene.proscenio,
            "active_action_index",
            rows=min(max(len(actions), 2), 6),
        )
        layout.label(text=f"{len(actions)} action(s) total", icon="INFO")


class PROSCENIO_PT_atlas(bpy.types.Panel):
    """Read-only atlas filename discovered from materials."""

    bl_label = "Atlas"
    bl_idname = "PROSCENIO_PT_atlas"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        atlas_name = _discover_atlas_name()
        if atlas_name is None:
            layout.label(text="no atlas linked in materials", icon="INFO")
            return
        layout.label(text=atlas_name, icon="IMAGE")


def _discover_atlas_name() -> str | None:
    for mat in bpy.data.materials:
        if not mat.use_nodes or mat.node_tree is None:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image is not None:
                fp = node.image.filepath
                return (
                    str(bpy.path.abspath(fp)).split("\\")[-1].split("/")[-1]
                    if fp
                    else (f"{node.image.name} (unsaved)")
                )
    return None


class PROSCENIO_PT_validation(bpy.types.Panel):
    """Lazy validation results — populated by the Validate operator."""

    bl_label = "Validation"
    bl_idname = "PROSCENIO_PT_validation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene_props = getattr(context.scene, "proscenio", None)
        if scene_props is None:
            layout.label(text="proscenio scene props not registered", icon="ERROR")
            return

        if not scene_props.validation_ran:
            layout.label(text="run Validate to see issues", icon="INFO")
            return

        issues = list(scene_props.validation_results)
        if not issues:
            layout.label(text="no issues — ready to export", icon="CHECKMARK")
            return

        for issue in issues:
            row = layout.row(align=True)
            row.alert = issue.severity == "error"
            icon = "ERROR" if issue.severity == "error" else "INFO"
            if issue.obj_name:
                op = row.operator(
                    "proscenio.select_issue_object",
                    text=f"[{issue.obj_name}] {issue.message}",
                    icon=icon,
                    emboss=False,
                )
                op.obj_name = issue.obj_name
            else:
                row.label(text=issue.message, icon=icon)


class PROSCENIO_PT_export(bpy.types.Panel):
    """Export panel — sticky path, ppu, validate, export, re-export."""

    bl_label = "Export"
    bl_idname = "PROSCENIO_PT_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene_props = getattr(context.scene, "proscenio", None)
        if scene_props is None:
            layout.label(text="proscenio scene props not registered", icon="ERROR")
            return

        layout.prop(scene_props, "last_export_path")
        layout.prop(scene_props, "pixels_per_unit")
        layout.operator("proscenio.create_ortho_camera", icon="OUTLINER_OB_CAMERA")
        layout.separator()
        col = layout.column(align=True)
        col.operator("proscenio.validate_export", icon="CHECKMARK")
        col.operator("proscenio.export_godot", icon="EXPORT")
        if scene_props.last_export_path:
            col.operator("proscenio.reexport_godot", icon="FILE_REFRESH")


class PROSCENIO_PT_help(bpy.types.Panel):
    """Shortcut cheat-sheet — every Proscenio operator with its idname."""

    bl_label = "Help"
    bl_idname = "PROSCENIO_PT_help"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(text="Operators (use F3 to search):", icon="QUESTION")
        for idname, label in _OPERATOR_REFERENCE:
            row = layout.row(align=True)
            row.label(text=label)
            row.label(text=idname)


_OPERATOR_REFERENCE: tuple[tuple[str, str], ...] = (
    ("proscenio.validate_export", "Validate"),
    ("proscenio.export_godot", "Export Proscenio (.proscenio)"),
    ("proscenio.reexport_godot", "Re-export"),
    ("proscenio.create_ortho_camera", "Preview Camera"),
    ("proscenio.bake_current_pose", "Bake Current Pose"),
    ("proscenio.toggle_ik_chain", "Toggle IK"),
    ("proscenio.reproject_sprite_uv", "Reproject UV"),
    ("proscenio.snap_region_to_uv", "Snap region to UV bounds"),
    ("proscenio.select_issue_object", "Select Issue Object"),
    ("proscenio.smoke_test", "Smoke test (Hello Proscenio)"),
)


class PROSCENIO_PT_diagnostics(bpy.types.Panel):
    """Smoke test + future addon-health buttons."""

    bl_label = "Diagnostics"
    bl_idname = "PROSCENIO_PT_diagnostics"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.operator("proscenio.smoke_test", icon="PLAY")


_classes: tuple[type, ...] = (
    PROSCENIO_UL_actions,
    PROSCENIO_PT_main,
    PROSCENIO_PT_active_sprite,
    PROSCENIO_PT_skeleton,
    PROSCENIO_PT_animation,
    PROSCENIO_PT_atlas,
    PROSCENIO_PT_validation,
    PROSCENIO_PT_export,
    PROSCENIO_PT_help,
    PROSCENIO_PT_diagnostics,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
