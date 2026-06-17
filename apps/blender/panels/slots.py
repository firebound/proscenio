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
from ..core.bpy_helpers.slot import (  # type: ignore[import-not-found]
    bone_parent_collapses,
    slot_follow_shape,
)
from ..core.slot.slot_emit import is_slot_empty  # type: ignore[import-not-found]
from ._helpers import draw_issue_row, draw_subpanel_header


def _is_slot(obj: bpy.types.Object) -> bool:
    """True when ``obj`` is an Empty flagged as a Proscenio slot."""
    return is_slot_empty(obj)


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
        col.label(text="bone: (unparented)", icon="BONE_DATA")

    parent = empty.parent
    if parent is not None:
        kind = "bone" if empty.parent_type == "BONE" else "object"
        col.label(text=f"parent: {parent.name} ({kind})", icon="OUTLINER_OB_EMPTY")

    if shape == "none":
        row = col.row()
        row.alert = True
        row.label(text="no bone - attachments will not follow any bone", icon="ERROR")
    elif shape == "field_inert":
        row = col.row()
        row.alert = True
        row.label(text="slot_bone set but inert - Bind to Bone to follow in Blender", icon="ERROR")
    elif shape == "bone_parent" and bone_parent_collapses(empty):
        box = col.box().column(align=True)
        box.alert = True
        box.label(text=f"bone '{bone}' lies in the picture plane", icon="ERROR")
        box.label(text="bone-parenting collapses the quads edge-on", icon="BLANK1")
        box.label(text="Unbind, then Bind to Bone for a flat follow", icon="BLANK1")


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
        active = context.active_object
        slots = sorted((o for o in context.scene.objects if _is_slot(o)), key=lambda o: o.name)
        if not slots:
            layout.label(text="no slots yet - select meshes and Create Slot", icon="INFO")
        else:
            col = layout.column(align=True)
            for slot in slots:
                row = col.row(align=True)
                op = row.operator(
                    "proscenio.select_slot",
                    text=slot.name,
                    icon="LINK_BLEND",
                    depress=slot is active,
                )
                op.slot_name = slot.name
                n_children = sum(1 for c in slot.children if c.type == "MESH")
                row.label(text=str(n_children), icon="OUTLINER_OB_MESH")
        layout.separator()
        tip = layout.box().column(align=True)
        tip.scale_y = 0.8
        tip.label(text="Pose Mode + active bone: slot anchored to the bone", icon="INFO")
        tip.label(text="Object Mode + meshes: slot wraps the selection", icon="BLANK1")
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
        if not children:
            row = layout.row()
            row.alert = True
            row.label(text="empty slot - add child meshes", icon="INFO")

        current_default = props.slot_default or (children[0].name if children else "")
        for child in children:
            row = layout.row(align=True)
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
            key_op = row.operator(
                "proscenio.keyframe_slot_attachment",
                text="",
                icon="KEYFRAME_HLT",
            )
            key_op.attachment_name = child.name

        layout.separator()
        row = layout.row()
        row.operator(
            "proscenio.add_slot_attachment",
            text="Add Selected Mesh",
            icon="ADD",
        )

        for issue in validation.validate_active_slot(empty):
            draw_issue_row(layout, issue)


_classes: tuple[type, ...] = (
    PROSCENIO_PT_slots,
    PROSCENIO_PT_active_slot,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
