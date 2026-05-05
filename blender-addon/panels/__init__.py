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
        return obj is not None and obj.type == "MESH"

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
        else:
            mesh = obj.data
            vg_count = len(getattr(obj, "vertex_groups", []) or [])
            poly_count = len(getattr(mesh, "polygons", []) or [])
            box = layout.box()
            box.label(text="Polygon", icon="MESH_DATA")
            box.label(text=f"{poly_count} polygon(s), {vg_count} vertex group(s)")

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
        actions = list(bpy.data.actions)
        if not actions:
            layout.label(text="no actions to export", icon="INFO")
            return
        for action in actions:
            row = layout.row()
            start, end = action.frame_range
            row.label(text=f"{action.name}  [{start:.0f}-{end:.0f}]", icon="ACTION")


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
                return str(bpy.path.abspath(fp)).split("\\")[-1].split("/")[-1] if fp else (
                    f"{node.image.name} (unsaved)"
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
            row = layout.row()
            row.alert = issue.severity == "error"
            icon = "ERROR" if issue.severity == "error" else "INFO"
            label = (
                f"[{issue.obj_name}] {issue.message}" if issue.obj_name else issue.message
            )
            row.label(text=label, icon=icon)


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
        layout.separator()
        col = layout.column(align=True)
        col.operator("proscenio.validate_export", icon="CHECKMARK")
        col.operator("proscenio.export_godot", icon="EXPORT")
        if scene_props.last_export_path:
            col.operator("proscenio.reexport_godot", icon="FILE_REFRESH")


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
    PROSCENIO_PT_main,
    PROSCENIO_PT_active_sprite,
    PROSCENIO_PT_skeleton,
    PROSCENIO_PT_animation,
    PROSCENIO_PT_atlas,
    PROSCENIO_PT_validation,
    PROSCENIO_PT_export,
    PROSCENIO_PT_diagnostics,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
