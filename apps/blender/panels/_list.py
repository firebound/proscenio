"""Shared Proscenio UIList chrome: native name search + multi-select marker.

A plain mixin (:class:`ProscenioListMixin`) combined with ``bpy.types.UIList`` by
each registered list - not itself a bpy type, so registration is unaffected. It
carries the one ``filter_items`` the simple lists share (native ``filter_name``
search plus an overridable visibility hook, routed through
:func:`core.list_view.compute_list_filter`), so Bones and Actions gain search
without copying it. The lists that need extra per-row filtering or sorting
(Outliner, Slots) keep their own ``filter_items`` but call the same core function
with a closure that captures their per-call sets once. The per-row selection
marker - the radio dot the Outliner proved - is a free function so a multi-select
list draws it the same way.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import bpy

from ..core.list_view import compute_list_filter


class ProscenioListMixin:
    """``filter_items`` via the shared core, with name + visibility hooks.

    Subclasses override only the hooks they need: ``row_name`` (defaults to
    ``item.name``) and ``row_visible`` (defaults to always shown). Source
    (collection) order is kept - the right default for the hierarchy-ordered
    bone list; a list that needs sorting calls
    :func:`core.list_view.compute_list_filter` directly with a ``sort_key``.
    """

    if TYPE_CHECKING:
        # Provided by ``bpy.types.UIList`` at runtime: the mixin is always
        # combined with it. Declared under TYPE_CHECKING so the checker resolves
        # the filter API without adding runtime annotations Blender would scan.
        bitflag_filter_item: int
        filter_name: str

    def row_name(self, item: bpy.types.AnyType) -> str:
        return str(getattr(item, "name", ""))

    def row_visible(self, _context: bpy.types.Context, _item: bpy.types.AnyType) -> bool:
        return True

    def filter_items(
        self,
        context: bpy.types.Context,
        data: bpy.types.AnyType,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        rows = list(getattr(data, propname))
        return compute_list_filter(
            rows,
            bitflag=self.bitflag_filter_item,
            name_filter=self.filter_name or "",
            name_of=self.row_name,
            visible=lambda item: self.row_visible(context, item),
        )


def draw_select_marker(row: bpy.types.UILayout, *, selected: bool) -> None:
    """Draw the per-row multi-select dot (filled when ``selected``).

    The ``template_list`` active highlight marks only one row, so a list whose
    row maps to a real Blender selection needs this extra per-row cue for the
    selected-but-not-active rows.
    """
    row.label(text="", icon="RADIOBUT_ON" if selected else "RADIOBUT_OFF")
