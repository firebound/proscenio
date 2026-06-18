"""Skeleton panel + bone UIList + accordion subpanels.

The Skeleton panel hosts the isolated project-wide Active Armature
selector and the armature-presence messaging. The body splits into
subpanels: Armature (the bone hierarchy), Pose Mode (pose-only
authoring ops), and Quick Armature (the modal rig draw + its defaults).
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core._shared.props_access import describe_export_target
from ._helpers import _POSE_FRIENDLY_MODES, draw_help_button, draw_subpanel_header


def _explicit_target(context: bpy.types.Context) -> bpy.types.Object | None:
    """Return the scene's picked Active Armature object, or None."""
    scene_props = getattr(context.scene, "proscenio", None)
    return scene_props.active_armature if scene_props is not None else None


# Below this N-panel width the Skeleton header drops the picked-armature name
# and keeps just "Skeleton" (a custom draw_header label cannot truncate, so the
# name is dropped wholesale rather than left to vanish mid-word). GUI-tunable.
_SKELETON_HEADER_NAME_MIN_WIDTH = 220


class PROSCENIO_UL_bones(bpy.types.UIList):
    """List view for ``Armature.bones`` - the Armature subpanel uses this."""

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
        depth = 0
        parent = item.parent
        while parent is not None:
            depth += 1
            parent = parent.parent
        # A bare operator button stretches and centers its text, which hid the
        # depth indent. Split the row and draw the name in a LEFT-aligned
        # sub-row so it hugs the left edge (same fix as the Outliner); the
        # connectivity flags take the right side.
        split = row.split(factor=0.7, align=True)
        name_row = split.row()
        name_row.alignment = "LEFT"
        op = name_row.operator(
            "proscenio.select_bone_by_name",
            text=("  " * depth) + item.name,
            icon="BONE_DATA",
            emboss=False,
        )
        op.armature_name = armature_obj.name if armature_obj is not None else ""
        op.bone_name = item.name
        flags = []
        if getattr(item, "use_connect", False):
            flags.append("connected")
        elif item.parent is not None:
            # A child bone not connected to its parent. Disconnected parenting
            # is a legitimate, common topology, not a mistake - but it was
            # silent before, so flag it for parity with "connected".
            flags.append("disconnected")
        if getattr(item, "use_relative_parent", False):
            flags.append("relative")
        flag_row = split.row()
        flag_row.alignment = "RIGHT"
        flag_row.label(text=", ".join(flags))


class PROSCENIO_PT_skeleton(bpy.types.Panel):
    """Skeleton - the project-wide armature selector + presence checks."""

    # The full "Skeleton: <name>" title is drawn in draw_header (bl_label
    # blank) because Blender renders draw_header LEFT of bl_label here, so the
    # whole title must live in one place to read in order. A custom draw_header
    # label has no native truncation, so instead of letting "Skeleton: <name>"
    # vanish when narrow, draw_header drops the <name> below a width threshold
    # and keeps the short "Skeleton" - which survives narrow widths fine.
    bl_label = ""
    bl_idname = "PROSCENIO_PT_skeleton"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 4
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.mode in _POSE_FRIENDLY_MODES

    def draw_header(self, context: bpy.types.Context) -> None:
        target = _explicit_target(context)
        try:
            name = target.name if target is not None else None
        except ReferenceError:
            name = None
        region = getattr(context, "region", None)
        width = getattr(region, "width", 9999)
        # Keep "Skeleton: <name>" while there is room; drop the name (the base
        # "Skeleton" stays) once the panel is too narrow to fit it.
        if name and width >= _SKELETON_HEADER_NAME_MIN_WIDTH:
            self.layout.label(text=f"Skeleton: {name}")
        else:
            self.layout.label(text="Skeleton")

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "skeleton", "skeleton")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene_props = getattr(context.scene, "proscenio", None)
        armatures = [o for o in context.scene.objects if o.type == "ARMATURE"]
        # Writes during ``draw`` are forbidden by Blender, so the initial
        # fill happens in the load_post / deferred_hydrate handlers; here the
        # picker is surfaced read-only (clearing it falls back to QuickRig).
        if scene_props is not None:
            row = layout.row(align=True)
            row.label(text="", icon="ARMATURE_DATA")
            row.prop(scene_props, "active_armature", text="")
        described = describe_export_target(context.scene)
        if described is not None:
            name, picked = described
            source = "picked" if picked else "first in scene - no rig picked"
            layout.label(text=f"Exports: {name} ({source})", icon="EXPORT")
        explicit_target = _explicit_target(context)
        if not armatures:
            row = layout.row()
            row.label(text="no Armature in scene - use Quick Armature below", icon="INFO")
        elif explicit_target is None:
            box = layout.box()
            box.label(
                text="no rig picked - skeleton ops will create a new Proscenio.QuickRig",
                icon="INFO",
            )
            box.label(text="Use existing instead:")
            buttons = box.column(align=True)
            for arm in armatures:
                op = buttons.operator(
                    "proscenio.set_active_armature",
                    text=arm.name,
                    icon="ARMATURE_DATA",
                )
                op.armature_name = arm.name


class PROSCENIO_PT_armature(bpy.types.Panel):
    """Active Armature subpanel - the bone hierarchy of the picked armature."""

    bl_label = "Active Armature"
    bl_idname = "PROSCENIO_PT_armature"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_skeleton"
    bl_order = 0

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        target = _explicit_target(context)
        return target is not None and bool(getattr(target.data, "bones", None))

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "armature", "armature")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        target = _explicit_target(context)
        scene_props = getattr(context.scene, "proscenio", None)
        if target is None or scene_props is None:
            return
        bones = getattr(target.data, "bones", [])
        # The armature name now rides the Skeleton header; the body just
        # carries the bone count.
        layout.label(text=f"{len(bones)} bone(s)")
        layout.template_list(
            "PROSCENIO_UL_bones",
            "",
            target.data,
            "bones",
            scene_props,
            "active_bone_index",
            rows=min(max(len(bones), 3), 8),
        )


class PROSCENIO_PT_pose_mode(bpy.types.Panel):
    """Pose Mode subpanel - pose-only authoring shortcuts."""

    bl_label = "Pose Mode"
    bl_idname = "PROSCENIO_PT_pose_mode"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_skeleton"
    bl_order = 1

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "pose_mode", "pose_mode")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        if context.mode != "POSE":
            layout.label(text="enter Pose mode to bake / save poses", icon="INFO")
            return
        layout.operator("proscenio.bake_current_pose", text="Bake Current Pose", icon="KEY_HLT")
        layout.operator("proscenio.toggle_ik_chain", text="Toggle IK", icon="CON_KINEMATIC")
        layout.operator("proscenio.bake_ik_chain", text="Bake IK to Keyframes", icon="KEYFRAME_HLT")
        # The subpanel header explains Pose Mode; the pose-library asset flow
        # (writable-library precheck, where the asset lands) has its own topic,
        # so the row carries its own ? - the orphan the #96 restructure left.
        pose_row = layout.row(align=True)
        pose_row.operator(
            "proscenio.save_pose_asset",
            text="Save Pose to Library",
            icon="ASSET_MANAGER",
        )
        draw_help_button(pose_row, "pose_library")


class PROSCENIO_PT_quick_armature(bpy.types.Panel):
    """Quick Armature subpanel - the modal rig draw + its defaults.

    Always reachable, even with no armature in the scene, so the
    operator that creates a rig is never gated behind one already
    existing.
    """

    bl_label = "Quick Armature"
    bl_idname = "PROSCENIO_PT_quick_armature"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_skeleton"
    bl_order = 2
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "quick_armature", "quick_armature")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.operator("proscenio.quick_armature", text="Quick Armature", icon="GREASEPENCIL")
        scene_props = getattr(context.scene, "proscenio", None)
        qa_props = getattr(scene_props, "quick_armature", None) if scene_props is not None else None
        if qa_props is None:
            return
        layout.prop(qa_props, "lock_to_front_ortho")
        layout.prop(qa_props, "default_chain")
        layout.prop(qa_props, "name_prefix")
        layout.prop(qa_props, "snap_increment")


_classes: tuple[type, ...] = (
    PROSCENIO_UL_bones,
    PROSCENIO_PT_skeleton,
    PROSCENIO_PT_armature,
    PROSCENIO_PT_pose_mode,
    PROSCENIO_PT_quick_armature,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
