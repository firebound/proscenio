"""Animation subpanel + actions UIList."""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core._shared.action_kind import (  # type: ignore[import-not-found]
    animation_representatives,
)
from ..core.bpy_helpers.i18n import iface
from ..core.list_view import compute_list_filter  # type: ignore[import-not-found]
from ._helpers import _active_armature, draw_subpanel_header, draw_target_readout
from ._list import ProscenioListMixin


class PROSCENIO_UL_actions(ProscenioListMixin, bpy.types.UIList):
    """List view for ``bpy.data.actions`` - Animation subpanel uses this.

    Single-select (a click assigns the active action); the shared mixin gives it
    native ``filter_name`` search. Rows are deduped to one per exported animation
    name (spec 079 D2), so a rig action and its per-mesh visibility action show
    as one animation.
    """

    bl_idname = "PROSCENIO_UL_actions"

    def filter_items(
        self,
        _context: bpy.types.Context,
        data: bpy.types.AnyType,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        """Show one row per exported animation name, honouring the search box.

        Overrides the mixin's plain name filter to also collapse same-named
        datablocks (rig + visibility) into a single representative row.
        """
        actions = list(getattr(data, propname))
        representative_ids = {id(actions[i]) for i in animation_representatives(actions)}
        return compute_list_filter(
            actions,
            bitflag=self.bitflag_filter_item,
            name_filter=self.filter_name or "",
            name_of=lambda action: str(getattr(action, "name", "")),
            visible=lambda action: id(action) in representative_ids,
        )

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
        start, end = item.frame_range
        row = layout.row(align=True)
        op = row.operator(
            "proscenio.set_active_action",
            text=item.name,
            icon="ACTION",
            emboss=False,
        )
        op.action_name = item.name
        row.label(text=f"[{start:.0f}-{end:.0f}]")


class PROSCENIO_PT_animation(bpy.types.Panel):
    """Read-only summary of the actions the writer would emit."""

    bl_label = "Animation"
    bl_idname = "PROSCENIO_PT_animation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 7
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "animation", "animation")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        # Clicking an action assigns it to the Skeleton-picked armature, so
        # declare that target first - same readout as Mesh Generation and
        # Weight Paint.
        draw_target_readout(layout, _active_armature(context))
        actions = bpy.data.actions
        if not actions:
            layout.label(text=iface("no actions to export"), icon="INFO")
            return
        # The list dedups same-named datablocks (rig + per-mesh visibility) into
        # one row per exported animation, so count the deduped names, not the raw
        # datablocks (spec 079 D2).
        n_animations = len({str(getattr(action, "name", "")) for action in actions})
        layout.template_list(
            "PROSCENIO_UL_actions",
            "",
            bpy.data,
            "actions",
            context.scene.proscenio,
            "active_action_index",
            rows=min(max(n_animations, 2), 6),
        )
        layout.label(text=f"{n_animations} animation(s) total", icon="INFO")


_classes: tuple[type, ...] = (
    PROSCENIO_UL_actions,
    PROSCENIO_PT_animation,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
