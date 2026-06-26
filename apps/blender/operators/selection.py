"""Selection operators: validation issue, outliner row, favorites, bone rows.

Covers the issue / outliner / action row clicks and favorite toggles, plus the
Skeleton-list bone-row affordances: the connectivity info tooltip, the Relative
Parenting toggle, the per-bone favorite, and the Rig UI collection-select.
"""

from __future__ import annotations

import contextlib
from typing import ClassVar

import bpy
from bpy.props import BoolProperty, StringProperty

from ..core._shared.props_access import object_props  # type: ignore[import-not-found]
from ..core._shared.report import report_warn  # type: ignore[import-not-found]
from ..core.armature.skeleton_target import (  # type: ignore[import-not-found]
    resolve_skeleton_target,
)
from ..core.bpy_helpers._shared.bone_collections import (  # type: ignore[import-not-found]
    iter_collection_bones,
)
from ..core.bpy_helpers._shared.bone_select import (  # type: ignore[import-not-found]
    bone_select_add,
    bone_select_only,
    bone_select_toggle,
)
from ..core.bpy_helpers._shared.select import (  # type: ignore[import-not-found]
    select_add,
    select_named_or_warn,
    select_only,
    select_toggle,
)


class PROSCENIO_OT_select_issue_object(bpy.types.Operator):
    """Select the object referenced by a validation issue and make it active."""

    bl_idname = "proscenio.select_issue_object"
    bl_label = "Proscenio: Select Issue Object"
    bl_description = "Selects and activates the object that the issue refers to"
    bl_options: ClassVar[set[str]] = {"REGISTER"}

    obj_name: StringProperty(  # type: ignore[valid-type]
        name="Object name",
        default="",
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not self.obj_name:
            report_warn(self, "issue has no object name")
            return {"CANCELLED"}
        # Guard at the operator boundary (not inside shared select_only): an
        # object not linked into the active view layer cannot be selected, and
        # select_set would raise. Same guard the outliner select path uses;
        # keeping it here leaves select_only's contract intact for the other
        # callers (a blanket suppress there would silently no-op them).
        if context.view_layer.objects.get(self.obj_name) is None:
            report_warn(self, f"'{self.obj_name}' is not in the current view layer")
            return {"CANCELLED"}
        obj = bpy.data.objects.get(self.obj_name)
        if obj is None:
            report_warn(self, f"object '{self.obj_name}' not found")
            return {"CANCELLED"}
        # Reveal then frame: clicking an issue is meant to surface the offending
        # object, and a hidden object cannot be selected.
        obj.hide_set(False)
        obj.hide_viewport = False
        select_only(context, obj)
        _frame_selected(context)
        return {"FINISHED"}


class PROSCENIO_OT_select_outliner_object(bpy.types.Operator):
    """Select + activate the object clicked in the Proscenio outliner.

    A plain click replaces the selection (Blender's single-click default);
    Shift-click extends it and Ctrl-click toggles the clicked row, mirroring
    the viewport / native-Outliner modifiers. ``invoke`` reads the click
    event to set ``extend`` / ``toggle``; calling ``execute`` directly with
    the flags drives the same paths headlessly.
    """

    bl_idname = "proscenio.select_outliner_object"
    bl_label = "Proscenio: Select Outliner Object"
    bl_description = (
        "Selects the object for this outliner row. Shift extends the "
        "selection, Ctrl toggles the row"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER"}

    obj_name: StringProperty(  # type: ignore[valid-type]
        name="Object name",
        default="",
    )
    extend: BoolProperty(  # type: ignore[valid-type]
        name="Extend",
        description="Add to the current selection instead of replacing it (Shift)",
        default=False,
    )
    toggle: BoolProperty(  # type: ignore[valid-type]
        name="Toggle",
        description="Toggle this row's selection (Ctrl)",
        default=False,
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        self.extend = event.shift
        self.toggle = event.ctrl
        return self.execute(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not self.obj_name:
            return {"CANCELLED"}
        # The list is sourced from bpy.data.objects, which keeps blocks left
        # behind by a delete/undo. Such a row points at an object not linked
        # into the view layer; select_set(True) on it raises. Skip-and-warn
        # at this boundary keeps the shared select_only contract intact for
        # the slot/camera/bone callers (a blanket suppress there would make
        # an object that genuinely cannot be selected no-op silently).
        if context.view_layer.objects.get(self.obj_name) is None:
            report_warn(self, f"'{self.obj_name}' is not in the current view layer")
            return {"CANCELLED"}
        obj = bpy.data.objects.get(self.obj_name)
        if obj is None:
            report_warn(self, f"object '{self.obj_name}' not found")
            return {"CANCELLED"}
        if self.toggle:
            select_toggle(context, obj)
        elif self.extend:
            select_add(context, obj)
        elif select_named_or_warn(self, context, self.obj_name) is None:
            return {"CANCELLED"}
        _sync_active_index(context, "active_outliner_index", bpy.data.objects, self.obj_name)
        return {"FINISHED"}


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


class PROSCENIO_OT_set_active_action(bpy.types.Operator):
    """Assign an action to the Skeleton-picked armature from the Animation panel."""

    bl_idname = "proscenio.set_active_action"
    bl_label = "Proscenio: Set Active Action"
    bl_description = (
        "Assigns this Animation-panel row's action to the armature picked in "
        "the Skeleton panel so the timeline plays it"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    action_name: StringProperty(  # type: ignore[valid-type]
        name="Action",
        default="",
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        action = bpy.data.actions.get(self.action_name)
        if action is None:
            report_warn(self, f"action '{self.action_name}' not found", always=True)
            return {"CANCELLED"}
        # The Skeleton picker is the single source of truth, same as every
        # other skeleton op. Do not scan the scene for an armature - that
        # silently targeted the wrong rig when more than one existed.
        armature = resolve_skeleton_target(context)
        if armature is None:
            report_warn(self, "no armature picked - pick one in the Skeleton panel", always=True)
            return {"CANCELLED"}
        # The picked armature can be deleted between pick and click; touching a
        # freed datablock raises ReferenceError. Guard and ask for a re-pick.
        try:
            if armature.animation_data is None:
                armature.animation_data_create()
            armature.animation_data.action = action
        except ReferenceError:
            report_warn(self, "picked armature no longer exists - pick one again", always=True)
            return {"CANCELLED"}
        _sync_active_index(context, "active_action_index", bpy.data.actions, self.action_name)
        return {"FINISHED"}


def _frame_selected(context: bpy.types.Context) -> None:
    """Frame the current selection in the first VIEW_3D area (best effort).

    ``view3d.view_selected`` needs a VIEW_3D WINDOW-region context, but the
    issue click runs in the N-panel UI region, so override to the area's
    WINDOW region. A headless run (or a layout with no VIEW_3D) simply skips
    framing; a RuntimeError from the override is suppressed for the same reason.
    """
    screen = getattr(context, "screen", None)
    if screen is None:
        return
    for area in screen.areas:
        if area.type != "VIEW_3D":
            continue
        region = next((r for r in area.regions if r.type == "WINDOW"), None)
        if region is None:
            continue
        with contextlib.suppress(RuntimeError), context.temp_override(area=area, region=region):
            bpy.ops.view3d.view_selected()
        return


def _sync_active_index(
    context: bpy.types.Context,
    prop_name: str,
    items: bpy.types.AnyType,
    target_name: str,
) -> None:
    """Update ``scene.proscenio.<prop_name>`` so the panel UIList highlight
    follows the row whose underlying datablock matches ``target_name``."""
    scene_props = getattr(context.scene, "proscenio", None)
    if scene_props is None or not hasattr(scene_props, prop_name):
        return
    for idx, candidate in enumerate(items):
        if candidate.name == target_name:
            setattr(scene_props, prop_name, idx)
            return


class PROSCENIO_OT_toggle_outliner_favorite(bpy.types.Operator):
    """Flip the outliner favorite flag on a target object."""

    bl_idname = "proscenio.toggle_outliner_favorite"
    bl_label = "Proscenio: Toggle Outliner Favorite"
    bl_description = (
        "Pin / unpin this object in the Proscenio outliner. "
        "Pinned objects survive the 'Favorites only' filter."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    obj_name: StringProperty(  # type: ignore[valid-type]
        name="Object name",
        default="",
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        if not self.obj_name:
            return {"CANCELLED"}
        obj = bpy.data.objects.get(self.obj_name)
        if obj is None:
            return {"CANCELLED"}
        props = object_props(obj)
        if props is None:
            report_warn(self, "PropertyGroup not registered on this object")
            return {"CANCELLED"}
        props.is_outliner_favorite = not bool(props.is_outliner_favorite)
        return {"FINISHED"}


#: Hover-tooltip copy for the bone-row connectivity icons. Keyed by the flag the
#: panel resolves from the bone, surfaced through the no-op info operator (a
#: ``layout.label`` icon carries no tooltip, so the icon is a click-less operator
#: button whose dynamic ``description`` is the explanation).
_BONE_FLAG_TOOLTIPS = {
    "connected": "Connected to parent - the bone head is locked to the parent's tail",
    "disconnected": (
        "Has a parent but its head moves freely (disconnected parenting). "
        "Connect / disconnect in Edit mode (it snaps the head to the parent tail)"
    ),
}


class PROSCENIO_OT_bone_flag_info(bpy.types.Operator):
    """No-op info button: carries the connectivity tooltip, performs no action.

    A ``layout.label`` icon renders no tooltip, so the bone row draws the
    connected / disconnected glyph as this click-less operator whose dynamic
    ``description`` is the per-flag explanation. Connect / disconnect itself is
    an Edit-mode geometry edit (it snaps the head onto the parent tail), so the
    panel only explains it, it does not toggle it.
    """

    bl_idname = "proscenio.bone_flag_info"
    bl_label = "Proscenio: Bone Connectivity"
    bl_options: ClassVar[set[str]] = {"INTERNAL"}

    flag: StringProperty(  # type: ignore[valid-type]
        name="Flag",
        default="",
    )

    @classmethod
    def description(
        cls, _context: bpy.types.Context, properties: bpy.types.OperatorProperties
    ) -> str:
        return _BONE_FLAG_TOOLTIPS.get(getattr(properties, "flag", ""), "")

    def execute(self, _context: bpy.types.Context) -> set[str]:
        return {"CANCELLED"}


class PROSCENIO_OT_toggle_bone_relative_parent(bpy.types.Operator):
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
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        name="Armature",
        default="",
    )
    bone_name: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        default="",
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            report_warn(self, f"armature '{self.armature_name}' not found")
            return {"CANCELLED"}
        bone = getattr(armature.data, "bones", {}).get(self.bone_name)
        if bone is None:
            report_warn(self, f"bone '{self.bone_name}' not in '{armature.name}'")
            return {"CANCELLED"}
        bone.use_relative_parent = not bool(bone.use_relative_parent)
        return {"FINISHED"}


class PROSCENIO_OT_toggle_bone_favorite(bpy.types.Operator):
    """Flip the Skeleton-list favorite flag on a bone (mirrors the outliner toggle)."""

    bl_idname = "proscenio.toggle_bone_favorite"
    bl_label = "Proscenio: Toggle Bone Favorite"
    bl_description = (
        "Pin / unpin this bone in the Skeleton list. Pinned bones survive the 'Favorites' filter"
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

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            report_warn(self, f"armature '{self.armature_name}' not found")
            return {"CANCELLED"}
        bone = getattr(armature.data, "bones", {}).get(self.bone_name)
        if bone is None:
            report_warn(self, f"bone '{self.bone_name}' not in '{armature.name}'")
            return {"CANCELLED"}
        props = getattr(bone, "proscenio", None)
        if props is None:
            report_warn(self, "PropertyGroup not registered on this bone")
            return {"CANCELLED"}
        props.is_favorite = not bool(props.is_favorite)
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
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            report_warn(self, f"armature '{self.armature_name}' not found")
            return {"CANCELLED"}
        bones = iter_collection_bones(armature, self.collection_name)
        if not bones:
            report_warn(self, f"collection '{self.collection_name}' has no bones")
            return {"CANCELLED"}
        # Make the armature the active object so bone ops act on it (object
        # selection only - the per-bone selection is set below).
        select_only(context, armature)
        mode = context.mode
        bone_select_only(armature, bones[0].name, mode)
        for bone in bones[1:]:
            bone_select_add(armature, bone.name, mode)
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_select_issue_object,
    PROSCENIO_OT_select_outliner_object,
    PROSCENIO_OT_select_bone_by_name,
    PROSCENIO_OT_set_active_action,
    PROSCENIO_OT_toggle_outliner_favorite,
    PROSCENIO_OT_bone_flag_info,
    PROSCENIO_OT_toggle_bone_relative_parent,
    PROSCENIO_OT_toggle_bone_favorite,
    PROSCENIO_OT_select_bone_collection,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
