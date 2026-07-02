"""Bone-selection operators: Skeleton-list bone rows + per-bone toggles + collection select."""

from __future__ import annotations

from typing import Any, ClassVar

import bpy
from bpy.props import BoolProperty, StringProperty

from ...core._shared.report import report_warn  # type: ignore[import-not-found]
from ...core.bpy_helpers._shared.bone_collections import (  # type: ignore[import-not-found]
    iter_collection_bones,
)
from ...core.bpy_helpers._shared.bone_select import (  # type: ignore[import-not-found]
    bone_select_add,
    bone_select_only,
    bone_select_toggle,
)
from ...core.bpy_helpers._shared.select import select_only  # type: ignore[import-not-found]
from ._shared import _sync_active_index


class PROSCENIO_OT_select_bone_by_name(bpy.types.Operator):
    """Select + activate a bone from the Skeleton panel UIList.

    A plain click replaces the bone selection; Shift-click extends it and
    Ctrl-click toggles the clicked bone, mirroring the Outliner row modifiers.
    Bone selection is real only in POSE / EDIT modes; in Object mode the click
    just moves the active bone. ``invoke`` reads the event to set ``extend`` /
    ``toggle``; calling ``execute`` directly with the flags drives the same
    paths headlessly.
    """

    bl_idname = "proscenio.select_bone_by_name"
    bl_label = "Proscenio: Select Bone"
    bl_description = (
        "Selects the bone for this Skeleton-panel row in the viewport. Shift "
        "extends the selection, Ctrl toggles the bone"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        name="Armature",
        default="",
    )
    bone_name: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        default="",
    )
    extend: BoolProperty(  # type: ignore[valid-type]
        name="Extend",
        description="Add to the bone selection instead of replacing it (Shift)",
        default=False,
    )
    toggle: BoolProperty(  # type: ignore[valid-type]
        name="Toggle",
        description="Toggle this bone's selection (Ctrl)",
        default=False,
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        self.extend = event.shift
        self.toggle = event.ctrl
        return self.execute(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            report_warn(self, f"armature '{self.armature_name}' not found")
            return {"CANCELLED"}
        bones = getattr(armature.data, "bones", None)
        if bones is None or self.bone_name not in bones:
            report_warn(self, f"bone '{self.bone_name}' not in '{armature.name}'")
            return {"CANCELLED"}
        # Make the armature the active object so bone-level ops act on it; this
        # touches object selection only, not the per-bone selection set below.
        select_only(context, armature)
        mode = context.mode
        if self.toggle:
            bone_select_toggle(armature, self.bone_name, mode)
        elif self.extend:
            bone_select_add(armature, self.bone_name, mode)
        else:
            bone_select_only(armature, self.bone_name, mode)
        _sync_active_index(context, "active_bone_index", bones, self.bone_name)
        return {"FINISHED"}


def _request_armature(op: bpy.types.Operator, armature_name: str) -> bpy.types.Object | None:
    """Resolve a row-click operator's target armature, reporting + ``None`` on miss."""
    armature = bpy.data.objects.get(armature_name)
    if armature is None or armature.type != "ARMATURE":
        report_warn(op, f"armature '{armature_name}' not found", always=True)
        return None
    return armature


def _request_bone(
    op: bpy.types.Operator, armature_name: str, bone_name: str
) -> bpy.types.Bone | None:
    """Resolve a row-click operator's target bone, reporting + ``None`` on miss."""
    armature = _request_armature(op, armature_name)
    if armature is None:
        return None
    bone = getattr(armature.data, "bones", {}).get(bone_name)
    if bone is None:
        report_warn(op, f"bone '{bone_name}' not in '{armature.name}'", always=True)
        return None
    return bone


def _request_bone_props(
    op: bpy.types.Operator, armature_name: str, bone_name: str
) -> tuple[bpy.types.Bone, Any] | tuple[None, None]:
    """Resolve the target bone and its ``proscenio`` PropertyGroup, or report + ``None``."""
    bone = _request_bone(op, armature_name, bone_name)
    if bone is None:
        return None, None
    props = getattr(bone, "proscenio", None)
    if props is None:
        report_warn(op, "PropertyGroup not registered on this bone", always=True)
        return None, None
    return bone, props


class _BoneRowRequest:
    """Shared ``armature_name`` / ``bone_name`` request fields + flags for the
    Skeleton-list per-bone toggle operators. Blender collects property annotations
    across the MRO, so the concrete operators inherit these without redeclaring."""

    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        name="Armature",
        default="",
    )
    bone_name: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        default="",
    )


class PROSCENIO_OT_toggle_bone_relative_parent(_BoneRowRequest, bpy.types.Operator):
    """Flip a bone's Relative Parenting flag from the Skeleton list.

    ``Bone.use_relative_parent`` is a pose-inheritance flag (the child follows
    the parent's local transform), writable directly on the data bone in Pose /
    Object mode with no geometric side effect - unlike connect / disconnect,
    which is an Edit-mode topology edit. So this one is a real one-click toggle.
    """

    bl_idname = "proscenio.toggle_bone_relative_parent"
    bl_label = "Proscenio: Toggle Relative Parenting"
    bl_description = (
        "Toggle Relative Parenting on this bone - the child follows the parent's "
        "local transform instead of its rest offset. A pose flag, not a geometry edit"
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        bone = _request_bone(self, self.armature_name, self.bone_name)
        if bone is None:
            return {"CANCELLED"}
        bone.use_relative_parent = not bool(bone.use_relative_parent)
        return {"FINISHED"}


class PROSCENIO_OT_toggle_bone_favorite(_BoneRowRequest, bpy.types.Operator):
    """Flip the Skeleton-list favorite flag on a bone (mirrors the outliner toggle)."""

    bl_idname = "proscenio.toggle_bone_favorite"
    bl_label = "Proscenio: Toggle Bone Favorite"
    bl_description = (
        "Pin / unpin this bone in the Skeleton list. Pinned bones survive the 'Favorites' filter"
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        _bone, props = _request_bone_props(self, self.armature_name, self.bone_name)
        if props is None:
            return {"CANCELLED"}
        props.is_favorite = not bool(props.is_favorite)
        return {"FINISHED"}


class PROSCENIO_OT_toggle_bone_export(_BoneRowRequest, bpy.types.Operator):
    """Flip the per-bone ``exclude_from_export`` flag from the Skeleton list.

    The rigger's authorship over what reaches Godot: a deform bone that is a
    rig helper (a tweak handle that should not ship as a Bone2D) can be pinned
    off the export here. Non-deform bones are already dropped by the export gate,
    so the toggle refuses them rather than storing hidden state.
    """

    bl_idname = "proscenio.toggle_bone_export"
    bl_label = "Proscenio: Toggle Bone Export"
    bl_description = (
        "Include / exclude this bone from the Godot export. Exclude a rig helper "
        "that only makes sense in Blender so it does not ship as a dead Bone2D"
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        bone, props = _request_bone_props(self, self.armature_name, self.bone_name)
        if props is None:
            return {"CANCELLED"}
        # A non-deform bone is already dropped by the export gate (bone_is_exported
        # ignores exclude_from_export when use_deform is off), so toggling it would
        # store hidden state that the row's "won't export" icon does not reflect -
        # and would silently bite if the bone later becomes a deform bone. Refuse.
        if not bool(getattr(bone, "use_deform", False)):
            report_warn(
                self,
                f"bone '{self.bone_name}' does not deform, so it is already out of the export",
                always=True,
            )
            return {"CANCELLED"}
        props.exclude_from_export = not bool(props.exclude_from_export)
        return {"FINISHED"}


class PROSCENIO_OT_select_bone_collection(bpy.types.Operator):
    """Select every bone in a bone collection from the Rig UI subpanel.

    Replace semantics: the click selects exactly the collection's bones (the
    first via ``bone_select_only``, which clears the prior selection, then the
    rest added). Bone selection is real only in POSE / EDIT modes; in Object
    mode the active bone still moves so the list highlight tracks the click.
    """

    bl_idname = "proscenio.select_bone_collection"
    bl_label = "Proscenio: Select Bone Collection"
    bl_description = "Selects every bone assigned to this bone collection in the viewport"
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        name="Armature",
        default="",
    )
    collection_name: StringProperty(  # type: ignore[valid-type]
        name="Bone collection",
        default="",
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        armature = _request_armature(self, self.armature_name)
        if armature is None:
            return {"CANCELLED"}
        bones = iter_collection_bones(armature, self.collection_name)
        if not bones:
            report_warn(self, f"collection '{self.collection_name}' has no bones", always=True)
            return {"CANCELLED"}
        # Make the armature the active object so bone ops act on it (object
        # selection only - the per-bone selection is set below).
        select_only(context, armature)
        mode = context.mode
        bone_select_only(armature, bones[0].name, mode)
        for bone in bones[1:]:
            bone_select_add(armature, bone.name, mode)
        return {"FINISHED"}
