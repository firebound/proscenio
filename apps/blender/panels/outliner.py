"""Outliner subpanel + UIList + category-rank helper."""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core.outliner_view import category_rank, row_visible
from ._helpers import draw_subpanel_header


class PROSCENIO_UL_sprite_outliner(bpy.types.UIList):
    """Sprite-centric outliner - slots, attachments, sprite meshes, armatures."""

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
        rank = category_rank(obj)
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
        # A bare operator button stretches across the row and centers its
        # text. Split the row and draw the label in a LEFT-aligned sub-row so
        # names hug the left edge (spec 036 left-align-names); the favorite
        # star keeps the right edge in the split remainder. (Owned by spec
        # 036, landed here since this PR already restructures these rows.)
        row = layout.row(align=True)
        # Multi-select marker: the template_list active highlight marks only
        # one row, so selected-but-not-active rows need their own cue. Read
        # the real object selection (Shift/Ctrl-click drive it through
        # proscenio.select_outliner_object). filter_items already drops
        # out-of-view-layer rows, so select_get() is safe to call here.
        sel_icon = "RADIOBUT_ON" if obj.select_get() else "RADIOBUT_OFF"
        row.label(text="", icon=sel_icon)
        split = row.split(factor=0.92, align=True)
        name_row = split.row()
        name_row.alignment = "LEFT"
        op = name_row.operator(
            "proscenio.select_outliner_object",
            text=label,
            icon=row_icon,
            emboss=False,
        )
        op.obj_name = obj.name
        fav_row = split.row()
        fav_row.alignment = "RIGHT"
        fav = fav_row.operator(
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
        """Hide non-Proscenio + out-of-view-layer objects, apply text + favorites
        filter, sort by category."""
        objects = list(getattr(data, propname))
        scene_props = getattr(context.scene, "proscenio", None)
        # One search field: Blender's native "Filter by Name" (self.filter_name).
        # The Proscenio drawer was removed in spec 043, so there is no second
        # source to reconcile here.
        flt_text = (self.filter_name or "").lower()
        favorites_only = bool(
            scene_props is not None and getattr(scene_props, "outliner_show_favorites", False)
        )
        # Names linked into the current view layer. The list is sourced from
        # bpy.data.objects, which keeps a deleted/undone object's datablock for
        # the rest of the session; a row whose object left the view layer must
        # drop out (it is no longer in the scene).
        view_layer_names = {o.name for o in context.view_layer.objects}
        n = len(objects)
        flt_flags = [0] * n
        ranks: list[int] = [0] * n
        for i, obj in enumerate(objects):
            rank = category_rank(obj)
            ranks[i] = rank
            obj_props = getattr(obj, "proscenio", None)
            is_fav = bool(
                obj_props is not None and getattr(obj_props, "is_outliner_favorite", False)
            )
            if row_visible(
                obj,
                in_view_layer=obj.name in view_layer_names,
                rank=rank,
                is_favorite=is_fav,
                favorites_only=favorites_only,
                filter_text=flt_text,
            ):
                flt_flags[i] = self.bitflag_filter_item
        order = sorted(range(n), key=lambda i: (ranks[i], objects[i].name.lower()))
        flt_neworder = [0] * n
        for new_i, orig_i in enumerate(order):
            flt_neworder[orig_i] = new_i
        return flt_flags, flt_neworder


class PROSCENIO_PT_outliner(bpy.types.Panel):
    """Sprite-centric outliner - replaces Blender's outliner for big rigs."""

    bl_label = "Outliner"
    bl_idname = "PROSCENIO_PT_outliner"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 1
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "outliner", "outliner")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene_props = getattr(context.scene, "proscenio", None)
        if scene_props is None:
            layout.label(text="Proscenio scene props not registered", icon="ERROR")
            return
        # Search is Blender's native "Filter by Name" (the UIList's expand
        # arrows); spec 043 dropped the redundant Proscenio search drawer.
        # Only the favorites-only toggle stays in the panel header row.
        row = layout.row(align=True)
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
