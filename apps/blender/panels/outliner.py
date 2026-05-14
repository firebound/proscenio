"""Outliner subpanel + UIList + category-rank helper (5.1.d.4)."""

from __future__ import annotations

from typing import ClassVar

import bpy

from ._helpers import draw_subpanel_header

_OUTLINER_RANK_HIDDEN = 9


def _outliner_category_rank(obj: bpy.types.Object) -> int:
    """Rank the object for the outliner's sort-by-category pass.

    0 = slot Empty (top of the list, drives a slot).
    1 = slot attachment mesh (rendered indented under its slot).
    2 = sprite mesh (Proscenio polygon / sprite_frame, parented to bone or floating).
    3 = armature.
    9 = irrelevant for Proscenio (cameras, lights, etc.) - hidden by ``filter_items``.
    """
    obj_props = getattr(obj, "proscenio", None)
    if obj.type == "EMPTY" and obj_props is not None and bool(getattr(obj_props, "is_slot", False)):
        return 0
    if obj.type == "ARMATURE":
        return 3
    if obj.type == "MESH":
        parent = obj.parent
        parent_props = getattr(parent, "proscenio", None) if parent is not None else None
        if (
            parent is not None
            and parent.type == "EMPTY"
            and parent_props is not None
            and bool(getattr(parent_props, "is_slot", False))
        ):
            return 1
        return 2
    return _OUTLINER_RANK_HIDDEN


class PROSCENIO_UL_sprite_outliner(bpy.types.UIList):
    """Sprite-centric outliner - slots, attachments, sprite meshes, armatures (5.1.d.4)."""

    bl_idname = "PROSCENIO_UL_sprite_outliner"

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
        obj_props = getattr(obj, "proscenio", None)
        is_fav = bool(obj_props is not None and getattr(obj_props, "is_outliner_favorite", False))
        rank = _outliner_category_rank(obj)
        if rank == 0:
            row_icon = "LINK_BLEND"
            label = f"[slot] {obj.name}"
        elif rank == 1:
            row_icon = "OBJECT_DATAMODE"
            label = f"  -> {obj.name}"
        elif rank == 2:
            row_icon = "MESH_DATA"
            parent_bone = obj.parent_bone if obj.parent and obj.parent_type == "BONE" else ""
            label = f"{obj.name}{' @ ' + parent_bone if parent_bone else ''}"
        elif rank == 3:
            row_icon = "ARMATURE_DATA"
            label = f"[arm] {obj.name}"
        else:
            row_icon = "OBJECT_DATA"
            label = obj.name
        row = layout.row(align=True)
        op = row.operator(
            "proscenio.select_outliner_object",
            text=label,
            icon=row_icon,
            emboss=False,
        )
        op.obj_name = obj.name
        fav = row.operator(
            "proscenio.toggle_outliner_favorite",
            text="",
            icon="SOLO_ON" if is_fav else "SOLO_OFF",
            emboss=False,
        )
        fav.obj_name = obj.name

    def filter_items(
        self,
        context: bpy.types.Context,
        data: bpy.types.AnyType,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        """Hide non-Proscenio objects, apply text + favorites filter, sort by category."""
        objects = list(getattr(data, propname))
        scene_props = getattr(context.scene, "proscenio", None)
        proscenio_text = (getattr(scene_props, "outliner_filter", "") or "").lower()
        # Blender renders a built-in "Filter by Name" field at the bottom of
        # every UIList. Our filter_items previously read only scene_props
        # and ignored self.filter_name, so the native field looked broken.
        # Prefer the Proscenio search bar (top, with VIEWZOOM icon) when
        # both are non-empty; otherwise fall through to whichever is set.
        native_text = (self.filter_name or "").lower()
        flt_text = proscenio_text or native_text
        favorites_only = bool(
            scene_props is not None and getattr(scene_props, "outliner_show_favorites", False)
        )
        n = len(objects)
        flt_flags = [0] * n
        ranks: list[int] = [0] * n
        for i, obj in enumerate(objects):
            rank = _outliner_category_rank(obj)
            ranks[i] = rank
            if rank == _OUTLINER_RANK_HIDDEN:
                continue
            obj_props = getattr(obj, "proscenio", None)
            is_fav = bool(
                obj_props is not None and getattr(obj_props, "is_outliner_favorite", False)
            )
            if favorites_only and not is_fav:
                continue
            if flt_text and flt_text not in obj.name.lower():
                continue
            flt_flags[i] = self.bitflag_filter_item
        order = sorted(range(n), key=lambda i: (ranks[i], objects[i].name.lower()))
        flt_neworder = [0] * n
        for new_i, orig_i in enumerate(order):
            flt_neworder[orig_i] = new_i
        return flt_flags, flt_neworder


class PROSCENIO_PT_outliner(bpy.types.Panel):
    """Sprite-centric outliner - replaces Blender's outliner for big rigs (5.1.d.4)."""

    bl_label = "Outliner"
    bl_idname = "PROSCENIO_PT_outliner"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "outliner", "outliner")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene_props = getattr(context.scene, "proscenio", None)
        if scene_props is None:
            layout.label(text="Proscenio scene props not registered", icon="ERROR")
            return
        row = layout.row(align=True)
        row.prop(scene_props, "outliner_filter", text="", icon="VIEWZOOM")
        row.prop(scene_props, "outliner_show_favorites", text="", icon="SOLO_ON")
        layout.template_list(
            "PROSCENIO_UL_sprite_outliner",
            "",
            bpy.data,
            "objects",
            scene_props,
            "active_outliner_index",
            rows=8,
        )


_classes: tuple[type, ...] = (
    PROSCENIO_UL_sprite_outliner,
    PROSCENIO_PT_outliner,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
