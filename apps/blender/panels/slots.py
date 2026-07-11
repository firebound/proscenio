"""Slots panel - project slot list + Create Slot; Active Slot detail subpanel.

The parent lists every slot Empty in the scene (each row clickable to
select it) and hosts Create Slot, so the list never vanishes when the
active object is not a slot (the audit's disappearing-panel bug). The
Active Slot subpanel polls on the active object being a slot Empty and
carries the attachment detail + Add Selected Mesh. The subpanel's status
badge + help button land with the header-convention pass (a later phase);
the parent keeps the existing ``slot_system`` badge.
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core import validation  # type: ignore[import-not-found]
from ..core.bpy_helpers.i18n import iface
from ..core.bpy_helpers.slot import (  # type: ignore[import-not-found]
    bone_parent_collapses,
    slot_follow_shape,
)
from ..core.list_view import compute_list_filter  # type: ignore[import-not-found]
from ..core.slot.slot_emit import is_slot_empty  # type: ignore[import-not-found]
from ._helpers import draw_issue_row, draw_picture_plane_warning, draw_subpanel_header


def _is_slot(obj: bpy.types.Object) -> bool:
    """True when ``obj`` is an Empty flagged as a Proscenio slot."""
    return is_slot_empty(obj)


class PROSCENIO_UL_slots(bpy.types.UIList):
    """Native list of the scene's slot Empties - replaces the hand-rolled loop.

    Binds to ``bpy.data.objects`` (like the Outliner) and filters to slot
    Empties in the current view layer, so it gets native search + scroll. The
    active row is driven by ``scene.proscenio.active_slot_index``, written by
    ``proscenio.select_slot`` through the identity-based index helper.
    """

    bl_idname = "PROSCENIO_UL_slots"

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
        obj = item
        n_children = sum(1 for c in obj.children if c.type == "MESH")
        # Left-align the name (panel-UI convention - a bare operator centers);
        # child count on the right.
        split = layout.split(factor=0.75, align=True)
        name_row = split.row()
        name_row.alignment = "LEFT"
        op = name_row.operator(
            "proscenio.select_slot", text=obj.name, icon="LINK_BLEND", emboss=False
        )
        op.slot_name = obj.name
        count_row = split.row()
        count_row.alignment = "RIGHT"
        count_row.label(text=str(n_children), icon="OUTLINER_OB_MESH")

    def filter_items(
        self,
        context: bpy.types.Context,
        data: bpy.types.AnyType,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        """Keep only slot Empties in the view layer, name-filtered, sorted by name.

        Routes the search + flag/order computation through the shared
        :func:`compute_list_filter`; the slot-Empty + view-layer test is the
        per-row visibility closure.
        """
        objects = list(getattr(data, propname))
        view_layer_names = {o.name for o in context.view_layer.objects}
        return compute_list_filter(
            objects,
            bitflag=self.bitflag_filter_item,
            name_filter=self.filter_name or "",
            name_of=lambda obj: obj.name,
            visible=lambda obj: is_slot_empty(obj) and obj.name in view_layer_names,
            sort_key=lambda obj: obj.name.lower(),
        )


def _attachment_kind_for(mesh_obj: bpy.types.Object) -> str:
    """Read the kind ("mesh" / "sprite") of a slot attachment mesh."""
    props = getattr(mesh_obj, "proscenio", None)
    if props is None:
        return "mesh"
    return str(getattr(props, "element_type", "mesh"))


def _attachment_icon_for(kind: str) -> str:
    return "MESH_DATA" if kind == "mesh" else "IMAGE_DATA"


def _draw_follow_state(
    col: bpy.types.UILayout, empty: bpy.types.Object, bone: str, shape: str
) -> None:
    """Draw how the slot follows its bone, the parent line, and any warning.

    Both the constraint follow and a hand-authored bone parent are valid,
    exportable shapes; the bone-parent one only warns when its bone lies in the
    picture plane (where it collapses the attachment quads edge-on).
    """
    if shape == "constraint":
        col.label(text=f"follows bone '{bone}' (Proscenio constraint)", icon="CONSTRAINT")
    elif shape == "bone_parent":
        col.label(text=f"follows bone '{bone}' (bone parent)", icon="BONE_DATA")
    elif shape == "field_inert":
        col.label(text=f"bound to '{bone}' - not following yet", icon="BONE_DATA")
    else:
        col.label(text=iface("bone: (unparented)"), icon="BONE_DATA")

    parent = empty.parent
    if parent is not None:
        kind = "bone" if empty.parent_type == "BONE" else "object"
        col.label(text=f"parent: {parent.name} ({kind})", icon="OUTLINER_OB_EMPTY")

    if shape == "none":
        row = col.row()
        row.alert = True
        row.label(text=iface("no bone - attachments will not follow any bone"), icon="ERROR")
    elif shape == "field_inert":
        row = col.row()
        row.alert = True
        row.label(
            text=iface("slot_bone set but inert - Bind to Bone to follow in Blender"), icon="ERROR"
        )
    elif shape == "bone_parent" and bone_parent_collapses(empty):
        draw_picture_plane_warning(
            col,
            bone,
            [
                "bone-parenting collapses the quads edge-on",
                "Unbind, then Bind to Bone for a flat follow",
            ],
        )


def _draw_follow_button(col: bpy.types.UILayout, shape: str) -> None:
    """Bind when nothing live follows; Unbind when the slot already follows.

    The two-click flow (Unbind then Bind) keeps each shape explicit and never
    silently strips a hand-authored bone parent.
    """
    row = col.row(align=True)
    if shape in {"constraint", "bone_parent"}:
        row.operator("proscenio.unbind_slot_from_bone", text="Unbind from Bone", icon="X")
    else:  # none / field_inert - wire the live follow
        row.operator("proscenio.bind_slot_to_bone", text="Bind to Bone", icon="BONE_DATA")


class PROSCENIO_PT_slots(bpy.types.Panel):
    """Slots - the project slot list + Create Slot."""

    bl_label = "Slots"
    bl_idname = "PROSCENIO_PT_slots"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 3
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "slot_system", "slot_system")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene_props = getattr(context.scene, "proscenio", None)
        has_slots = any(_is_slot(o) for o in context.scene.objects)
        if not has_slots or scene_props is None:
            layout.label(text=iface("no slots yet - select meshes and Create Slot"), icon="INFO")
        else:
            layout.template_list(
                "PROSCENIO_UL_slots",
                "",
                bpy.data,
                "objects",
                scene_props,
                "active_slot_index",
                rows=5,
            )
        layout.separator()
        tip = layout.box().column(align=True)
        tip.scale_y = 0.8
        tip.label(text=iface("Pose Mode + active bone: slot anchored to the bone"), icon="INFO")
        tip.label(text=iface("Object Mode + meshes: slot wraps the selection"), icon="BLANK1")
        layout.operator("proscenio.create_slot", text="Create Slot", icon="ADD")


class PROSCENIO_PT_active_slot(bpy.types.Panel):
    """Active Slot subpanel - attachment detail + Add Selected Mesh.

    Polls on the active object being a slot Empty; the parent Slots panel
    stays visible regardless so the list + Create Slot never vanish.
    """

    bl_label = "Active Slot"
    bl_idname = "PROSCENIO_PT_active_slot"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_slots"
    bl_order = 0
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return obj is not None and _is_slot(obj)

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "active_slot", "active_slot")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        empty = context.active_object
        if empty is None:
            return
        props = empty.proscenio
        scene_props = getattr(context.scene, "proscenio", None)
        swap_anim = (
            str(getattr(scene_props, "slot_swap_target_animation", "")) if scene_props else ""
        )
        children = sorted(
            (c for c in empty.children if c.type == "MESH"),
            key=lambda c: c.name,
        )

        bone = validation.slot_parent_bone(empty)
        shape = slot_follow_shape(empty)
        col = layout.column()
        col.label(text=f"Slot '{empty.name}'", icon="LINK_BLEND")
        _draw_follow_state(col, empty, bone, shape)
        _draw_follow_button(col, shape)

        layout.separator()
        layout.label(text=f"Attachments ({len(children)}):", icon="OUTLINER_OB_MESH")
        # No inline empty-slot warning here: the validator already raises
        # "slot '<name>' has no MESH children" (with error severity), drawn by
        # the issue loop below, so an inline INFO line would just duplicate it.

        current_default = props.slot_default or (children[0].name if children else "")
        # Custom-draw column over the derived empty.children view (option 2 in
        # the spec - no synced CollectionProperty, so it cannot desync). A
        # template_list cannot bind here: empty.children is a computed sequence,
        # not a CollectionProperty. The box + scale_y caps how fast a long list
        # grows the panel; it is not a true native scrollbar (that is the gated
        # synced-collection upgrade in the spec).
        attach_col = layout.box().column(align=True)
        attach_col.scale_y = 0.9
        for child in children:
            row = attach_col.row(align=True)
            is_default = child.name == current_default
            icon = "SOLO_ON" if is_default else "SOLO_OFF"
            op = row.operator(
                "proscenio.set_slot_default",
                text="",
                icon=icon,
                emboss=is_default,
            )
            op.attachment_name = child.name
            row.label(text=child.name)
            kind = _attachment_kind_for(child)
            row.label(text=kind, icon=_attachment_icon_for(kind))
            # "Show only" keys this attachment shown + every sibling hidden at the
            # current frame (a slot swap), not an index into a list.
            key_op = row.operator(
                "proscenio.keyframe_slot_attachment",
                text="Show Only",
                icon="KEYFRAME_HLT",
            )
            key_op.attachment_name = child.name
            key_op.animation_name = swap_anim

        # Slot-swap authoring: the target animation the swap follows, plus the
        # keyable "(none)" state (every attachment hidden). Per-attachment
        # "Show only" buttons live in the rows above.
        swap_col = layout.column(align=True)
        swap_col.label(text="Keyframe swap (show only at current frame):", icon="KEYFRAME_HLT")
        if scene_props is not None:
            swap_col.prop_search(
                scene_props,
                "slot_swap_target_animation",
                bpy.data,
                "actions",
                text="Target anim",
            )
            if not swap_anim:
                hint = swap_col.row()
                hint.scale_y = 0.8
                hint.label(text="(empty: follows the active animation)", icon="BLANK1")
        none_op = swap_col.operator(
            "proscenio.keyframe_slot_attachment",
            text="(none) / Hide All",
            icon="HIDE_ON",
        )
        none_op.hide_all = True
        none_op.animation_name = swap_anim

        layout.separator()
        row = layout.row(align=True)
        # The picker (pick a mesh by name) breaks the single-selection
        # deadlock; Add Selected Mesh stays as the fast path when a mesh is
        # already selected.
        row.operator(
            "proscenio.attach_mesh_to_slot",
            text="Attach Mesh",
            icon="ADD",
        )
        row.operator(
            "proscenio.add_slot_attachment",
            text="Add Selected",
            icon="RESTRICT_SELECT_OFF",
        )

        for issue in validation.validate_active_slot(empty):
            draw_issue_row(layout, issue)


_classes: tuple[type, ...] = (
    PROSCENIO_UL_slots,
    PROSCENIO_PT_slots,
    PROSCENIO_PT_active_slot,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
