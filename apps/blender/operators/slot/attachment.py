"""Slot attachment operators: add attachment, set default, keyframe visibility."""

from __future__ import annotations

import json
from typing import ClassVar

import bpy
from bpy.props import BoolProperty, StringProperty

from ...core._shared.action_fcurves import (  # type: ignore[import-not-found]
    action_fcurves,
    object_action_fcurves,
)
from ...core._shared.report import report_info, report_warn  # type: ignore[import-not-found]
from ...core.bpy_helpers._shared._bpy_compat import (  # type: ignore[import-not-found]
    iter_keyframe_points,
)
from ...core.bpy_helpers._shared.parenting import (  # type: ignore[import-not-found]
    parent_keep_world,
)

# Legacy Custom Property + fcurve data path the visibility model replaced. Named
# here only so the one-shot migration operator can read an in-flight authored
# blend; the live authoring + export paths no longer touch them.
_LEGACY_SLOT_INDEX = "proscenio_slot_index"
_LEGACY_SLOT_INDEX_PATH = '["proscenio_slot_index"]'
_LEGACY_ATTACHMENT_ORDER = "proscenio_slot_attachment_order"

# Fallback animation name when a swap is keyed with no rig animation to follow.
_DEFAULT_SWAP_ANIMATION = "Swap"


def _slot_armature(empty: bpy.types.Object) -> bpy.types.Object | None:
    """The armature a slot Empty rides, via its object-parent or its Child Of."""
    parent = getattr(empty, "parent", None)
    if parent is not None and getattr(parent, "type", None) == "ARMATURE":
        return parent
    for con in empty.constraints:
        target = getattr(con, "target", None)
        if target is not None and getattr(target, "type", None) == "ARMATURE":
            return target
    return None


def _active_action(obj: bpy.types.Object | None) -> bpy.types.Action | None:
    anim = getattr(obj, "animation_data", None) if obj is not None else None
    return getattr(anim, "action", None) if anim is not None else None


def _resolve_target_action(
    empty: bpy.types.Object,
    siblings: list[bpy.types.Object],
    override: str,
) -> bpy.types.Action:
    """The action datablock the visibility keys land in (spec 079 D3).

    Resolution, in order: an explicit ``override`` animation name; else the
    rig's active action (so the swap co-locates in that animation and merges
    into it by name on export); else an action a sibling already keyed (repeat
    keys extend one datablock); else a fresh default-named swap action.
    """
    if override:
        return bpy.data.actions.get(override) or bpy.data.actions.new(override)
    rig_action = _active_action(_slot_armature(empty))
    if rig_action is not None:
        return rig_action
    for mesh in siblings:
        sibling_action = _active_action(mesh)
        if sibling_action is not None:
            return sibling_action
    return bpy.data.actions.get(_DEFAULT_SWAP_ANIMATION) or bpy.data.actions.new(
        _DEFAULT_SWAP_ANIMATION
    )


def _key_visibility(
    mesh: bpy.types.Object,
    action: bpy.types.Action,
    *,
    visible: bool,
    frame: int,
) -> None:
    """Bind ``mesh`` to ``action`` and hard-cut-key its visibility at ``frame``.

    Keys ``hide_viewport`` (viewport preview) and ``hide_render`` (the export
    truth the writer reads) in lockstep, then forces CONSTANT interpolation so
    the swap is a hard cut, never a tween. On Blender 4.4+ the mesh binds its
    own slot in the shared action; on 4.2 the caller passes a per-mesh action.
    """
    mesh.animation_data_create()
    if mesh.animation_data.action is not action:
        mesh.animation_data.action = action
    mesh.hide_viewport = not visible
    mesh.hide_render = not visible
    mesh.keyframe_insert(data_path="hide_viewport", frame=frame)
    mesh.keyframe_insert(data_path="hide_render", frame=frame)
    for fcurve in object_action_fcurves(mesh):
        if fcurve.data_path not in ("hide_render", "hide_viewport"):
            continue
        for keyframe in iter_keyframe_points(fcurve):
            keyframe.interpolation = "CONSTANT"
        fcurve.update()


class PROSCENIO_OT_add_slot_attachment(bpy.types.Operator):
    """Re-parent the active mesh into the active slot Empty."""

    bl_idname = "proscenio.add_slot_attachment"
    bl_label = "Proscenio: Add Slot Attachment"
    bl_description = "Re-parent the selected mesh as a child of the active slot Empty"
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        empty = context.active_object
        if empty is None or empty.type != "EMPTY":
            return False
        props = getattr(empty, "proscenio", None)
        if props is None or not bool(getattr(props, "is_slot", False)):
            return False
        return any(obj.type == "MESH" and obj is not empty for obj in context.selected_objects)

    def execute(self, context: bpy.types.Context) -> set[str]:
        empty = context.active_object
        meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if not meshes:
            report_warn(self, "no MESH objects selected")
            return {"CANCELLED"}
        for mesh in meshes:
            parent_keep_world(mesh, empty)
        report_info(self, f"added {len(meshes)} attachment(s) to slot '{empty.name}'")
        return {"FINISHED"}


class PROSCENIO_OT_attach_mesh_to_slot(bpy.types.Operator):
    """Pick a mesh by name and re-parent it into the active slot.

    The picker breaks the single-selection deadlock: you cannot have the
    slot active AND a target mesh selected at the same time, so
    ``add_slot_attachment`` (which re-parents the selection) has no path
    when the slot is what you just clicked. This dialog chooses the target
    by name instead, leaving the active object alone.
    """

    bl_idname = "proscenio.attach_mesh_to_slot"
    bl_label = "Proscenio: Attach Mesh to Slot"
    bl_description = (
        "Pick a mesh by name and attach it to the active slot, without having to select it first"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    mesh_name: StringProperty(  # type: ignore[valid-type]
        name="Mesh",
        description="Mesh to attach to the active slot",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        empty = context.active_object
        if empty is None or empty.type != "EMPTY":
            return False
        props = getattr(empty, "proscenio", None)
        return props is not None and bool(getattr(props, "is_slot", False))

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: bpy.types.Context) -> None:
        # prop_search over the scene's objects; execute validates the pick is
        # a mesh. (There is no mesh-only collection to search directly.)
        self.layout.prop_search(self, "mesh_name", context.scene, "objects", text="Mesh")

    def execute(self, context: bpy.types.Context) -> set[str]:
        empty = context.active_object
        if empty is None or empty.type != "EMPTY":
            return {"CANCELLED"}
        mesh = bpy.data.objects.get(self.mesh_name)
        if mesh is None or mesh.type != "MESH":
            report_warn(self, f"'{self.mesh_name}' is not a mesh")
            return {"CANCELLED"}
        parent_keep_world(mesh, empty)
        report_info(self, f"attached '{mesh.name}' to slot '{empty.name}'")
        return {"FINISHED"}


class PROSCENIO_OT_set_slot_default(bpy.types.Operator):
    """Mark the named attachment as the slot's default."""

    bl_idname = "proscenio.set_slot_default"
    bl_label = "Proscenio: Set Slot Default"
    bl_description = "Make this attachment the slot's default visible child at scene load"
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    attachment_name: StringProperty(  # type: ignore[valid-type]
        name="Attachment name",
        description="Name of the mesh child to flag as default",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        empty = context.active_object
        if empty is None or empty.type != "EMPTY":
            return False
        props = getattr(empty, "proscenio", None)
        return props is not None and bool(getattr(props, "is_slot", False))

    def execute(self, context: bpy.types.Context) -> set[str]:
        empty = context.active_object
        props = empty.proscenio
        children_names = {child.name for child in empty.children if child.type == "MESH"}
        if self.attachment_name not in children_names:
            report_warn(
                self,
                f"'{self.attachment_name}' is not a child of slot '{empty.name}'",
            )
            return {"CANCELLED"}
        props.slot_default = self.attachment_name
        report_info(self, f"slot '{empty.name}' default = '{self.attachment_name}'")
        return {"FINISHED"}


class PROSCENIO_OT_keyframe_slot_attachment(bpy.types.Operator):
    """Show only the chosen attachment at the current frame (a slot swap).

    Keys every sibling attachment's visibility in lockstep - the chosen one
    shown, the rest hidden (or all hidden for the ``(none)`` state) - with hard
    cuts, on the animation the swap follows. The writer collapses these per-mesh
    visibility keys back into one exclusive ``slot_attachment`` track.
    """

    bl_idname = "proscenio.keyframe_slot_attachment"
    bl_label = "Proscenio: Keyframe Slot Attachment"
    bl_description = (
        "Show only the chosen attachment from the current frame (hard cut) - the "
        "slot swap the exporter projects into a Godot slot_attachment track"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    attachment_name: StringProperty(  # type: ignore[valid-type]
        name="Attachment name",
        description="Name of the mesh child to show from this frame",
        default="",
    )
    hide_all: BoolProperty(  # type: ignore[valid-type]
        name="Hide all",
        description="Key the (none) state - every attachment hidden at this frame",
        default=False,
    )
    animation_name: StringProperty(  # type: ignore[valid-type]
        name="Animation",
        description="Override the animation the swap follows (defaults to the rig's active one)",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        empty = context.active_object
        if empty is None or empty.type != "EMPTY":
            return False
        props = getattr(empty, "proscenio", None)
        return props is not None and bool(getattr(props, "is_slot", False))

    def execute(self, context: bpy.types.Context) -> set[str]:
        empty = context.active_object
        siblings = [child for child in empty.children if child.type == "MESH"]
        frame = context.scene.frame_current
        if not self.hide_all and self.attachment_name not in {m.name for m in siblings}:
            report_warn(
                self,
                f"'{self.attachment_name}' is not an attachment of slot '{empty.name}'",
            )
            return {"CANCELLED"}
        action = _resolve_target_action(empty, siblings, self.animation_name)
        for mesh in siblings:
            visible = (not self.hide_all) and mesh.name == self.attachment_name
            _key_visibility(mesh, action, visible=visible, frame=frame)
        shown = "(none)" if self.hide_all else self.attachment_name
        report_info(self, f"keyed '{shown}' on slot '{empty.name}' at frame {frame}")
        return {"FINISHED"}


class PROSCENIO_OT_convert_slot_index_to_visibility(bpy.types.Operator):
    """Migrate a legacy ``proscenio_slot_index`` track to visibility keyframes.

    One-shot converter for a blend authored before spec 079: reads the active
    slot Empty's index fcurve and re-authors each keyed index as a show-only
    visibility keyframe on its attachments, so an in-flight authored swap carries
    over without hand re-authoring. Clears the legacy index track + idprops so a
    second run is a no-op.
    """

    bl_idname = "proscenio.convert_slot_index_to_visibility"
    bl_label = "Proscenio: Convert Slot Index to Visibility"
    bl_description = (
        "Convert this slot's legacy proscenio_slot_index keyframes into "
        "attachment visibility keyframes (spec 079 migration)"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        empty = context.active_object
        if empty is None or empty.type != "EMPTY":
            return False
        props = getattr(empty, "proscenio", None)
        return props is not None and bool(getattr(props, "is_slot", False))

    def execute(self, context: bpy.types.Context) -> set[str]:
        empty = context.active_object
        index_action = _active_action(empty)
        if index_action is None:
            report_warn(self, f"slot '{empty.name}' has no animation to convert")
            return {"CANCELLED"}
        index_keys = _read_legacy_index_keys(index_action)
        if not index_keys:
            report_warn(self, f"slot '{empty.name}' has no proscenio_slot_index keyframes")
            return {"CANCELLED"}
        order = _legacy_attachment_order(empty)
        siblings = [child for child in empty.children if child.type == "MESH"]
        # Co-locate the migrated swap in the rig's active animation (merge by
        # name), preserving the legacy index-action name when there is no rig.
        target = _resolve_target_action(empty, siblings, override="")
        if target is index_action:
            target = bpy.data.actions.get(_DEFAULT_SWAP_ANIMATION) or bpy.data.actions.new(
                _DEFAULT_SWAP_ANIMATION
            )
        for frame, idx in index_keys:
            chosen = order[idx] if 0 <= idx < len(order) else None
            for mesh in siblings:
                _key_visibility(mesh, target, visible=mesh.name == chosen, frame=frame)
        _clear_legacy_index(empty)
        report_info(
            self,
            f"converted {len(index_keys)} slot-index key(s) on '{empty.name}' to visibility",
        )
        return {"FINISHED"}


def _read_legacy_index_keys(action: bpy.types.Action) -> list[tuple[int, int]]:
    """Sorted ``(frame, index)`` from a legacy ``proscenio_slot_index`` fcurve."""
    keys: list[tuple[int, int]] = []
    for fcurve in action_fcurves(action):
        if fcurve.data_path != _LEGACY_SLOT_INDEX_PATH:
            continue
        for kp in iter_keyframe_points(fcurve):
            keys.append((round(kp.co.x), round(kp.co.y)))
    keys.sort()
    return keys


def _legacy_attachment_order(empty: bpy.types.Object) -> list[str]:
    """The name order a legacy index resolved against: snapshot idprop or children."""
    raw = empty.get(_LEGACY_ATTACHMENT_ORDER)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except (ValueError, TypeError):
            parsed = None
        if isinstance(parsed, list) and all(isinstance(name, str) for name in parsed):
            return list(parsed)
    return [child.name for child in empty.children if child.type == "MESH"]


def _clear_legacy_index(empty: bpy.types.Object) -> None:
    """Drop the legacy index binding + idprops so a re-run is a no-op."""
    anim = getattr(empty, "animation_data", None)
    if anim is not None and _active_action(empty) is not None:
        anim.action = None
    for key in (_LEGACY_SLOT_INDEX, _LEGACY_ATTACHMENT_ORDER):
        if key in empty:
            del empty[key]


_classes: tuple[type, ...] = (
    PROSCENIO_OT_add_slot_attachment,
    PROSCENIO_OT_attach_mesh_to_slot,
    PROSCENIO_OT_set_slot_default,
    PROSCENIO_OT_keyframe_slot_attachment,
    PROSCENIO_OT_convert_slot_index_to_visibility,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
