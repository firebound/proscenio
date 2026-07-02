"""Object-selection operators: validation issue, outliner row, outliner favorite."""

from __future__ import annotations

import contextlib
from typing import ClassVar

import bpy
from bpy.props import BoolProperty, StringProperty

from ...core._shared.props_access import object_props  # type: ignore[import-not-found]
from ...core._shared.report import report_warn  # type: ignore[import-not-found]
from ...core.bpy_helpers._shared.select import (  # type: ignore[import-not-found]
    select_add,
    select_named_or_warn,
    select_only,
    select_toggle,
)
from ._shared import _sync_active_index


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
