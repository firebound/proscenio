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
        scene_props = getattr(context.scene, "proscenio", None)
        # Active-armature picker is always visible: in zero-armature
        # scenes it stays empty (Quick Armature will create QuickRig
        # and auto-populate it); otherwise the user picks the rig that
        # every Proscenio skeleton op targets, instead of relying on
        # whatever object Blender treats as active.
        if scene_props is not None:
            row = layout.row(align=True)
            row.label(text="", icon="ARMATURE_DATA")
            row.prop(scene_props, "active_armature", text="")
        if not armatures:
            row = layout.row()
            row.alert = True
            row.label(text="no Armature in scene", icon="ERROR")
            return
        target = (
            scene_props.active_armature
            if scene_props is not None and scene_props.active_armature is not None
            else armatures[0]
        )
        bones = getattr(target.data, "bones", [])
        layout.label(text=f"Armature '{target.name}' - {len(bones)} bone(s)")
        if len(armatures) > 1 and (
            scene_props is None or scene_props.active_armature is None
        ):
            row = layout.row()
            row.alert = True
            row.label(
                text=(
                    f"{len(armatures)} armatures - pick one above so every "
                    "Proscenio skeleton op targets the same rig"
                ),
                icon="ERROR",
            )
        if bones and scene_props is not None:
            layout.template_list(
                "PROSCENIO_UL_bones",
                "",
                target.data,
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
        _draw_quick_armature_defaults(layout, context)
        layout.operator("proscenio.create_slot", text="Create Slot", icon="LINK_BLEND")


def _draw_quick_armature_defaults(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
) -> None:
    """Inline sub-box exposing the SPEC 012 D15 Quick Armature defaults.

    Settings live on ``scene.proscenio.quick_armature`` so they ride
    with the .blend file and let one-off documents ship their own
    preferred prefix / snap / chord vocabulary without touching the
    user's global preferences.
    """
    scene_props = getattr(context.scene, "proscenio", None)
    if scene_props is None:
        return
    qa_props = getattr(scene_props, "quick_armature", None)
    if qa_props is None:
        return
    box = layout.box()
    box.label(text="Quick Armature defaults", icon="SETTINGS")
    box.prop(qa_props, "lock_to_front_ortho")
    box.prop(qa_props, "default_chain")
    box.prop(qa_props, "name_prefix")
    box.prop(qa_props, "snap_increment")


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
