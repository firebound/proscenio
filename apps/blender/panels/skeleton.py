"""Skeleton subpanel + bone UIList."""

from __future__ import annotations

from typing import ClassVar

import bpy

from ._helpers import _POSE_FRIENDLY_MODES, draw_subpanel_header


class PROSCENIO_UL_bones(bpy.types.UIList):
    """List view for ``Armature.bones`` - Skeleton subpanel uses this."""

    bl_idname = "PROSCENIO_UL_bones"

    def draw_item(
        self,
        _context: bpy.types.Context,
        layout: bpy.types.UILayout,
        data: bpy.types.AnyType,
        item: bpy.types.AnyType,
        _icon: int,
        _active_data: bpy.types.AnyType,
        _active_propname: str,
    ) -> None:
        row = layout.row(align=True)
        # `data` is the armature data block. Walk back to its owning Object
        # so the operator can address it by name + sync pose-mode selection.
        armature_obj = next(
            (o for o in bpy.data.objects if o.type == "ARMATURE" and o.data is data),
            None,
        )
        op = row.operator(
            "proscenio.select_bone_by_name",
            text=item.name,
            icon="BONE_DATA",
            emboss=False,
        )
        op.armature_name = armature_obj.name if armature_obj is not None else ""
        op.bone_name = item.name
        parent_name = item.parent.name if item.parent is not None else "-"
        row.label(text=f"parent: {parent_name}")
        row.label(text=f"len {item.length:.2f}")


class PROSCENIO_PT_skeleton(bpy.types.Panel):
    """Skeleton summary - bone count + presence checks."""

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

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "skeleton", "skeleton")

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
        layout.label(text=f"Armature '{first.name}' - {len(bones)} bone(s)")
        if len(armatures) > 1:
            row = layout.row()
            row.alert = True
            row.label(
                text=f"{len(armatures)} armatures - writer uses the first only",
                icon="ERROR",
            )
        if bones:
            scene_props = getattr(context.scene, "proscenio", None)
            if scene_props is not None:
                layout.template_list(
                    "PROSCENIO_UL_bones",
                    "",
                    first.data,
                    "bones",
                    scene_props,
                    "active_bone_index",
                    rows=min(max(len(bones), 3), 8),
                )
        if context.mode == "POSE":
            layout.separator()
            layout.operator("proscenio.bake_current_pose", text="Bake Current Pose", icon="KEY_HLT")
            layout.operator("proscenio.toggle_ik_chain", text="Toggle IK", icon="CON_KINEMATIC")
            layout.operator(
                "proscenio.save_pose_asset",
                text="Save Pose to Library",
                icon="ASSET_MANAGER",
            )
        layout.separator()
        layout.operator("proscenio.quick_armature", text="Quick Armature", icon="GREASEPENCIL")
        layout.operator("proscenio.create_slot", text="Create Slot", icon="LINK_BLEND")


_classes: tuple[type, ...] = (
    PROSCENIO_UL_bones,
    PROSCENIO_PT_skeleton,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
