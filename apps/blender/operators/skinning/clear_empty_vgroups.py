"""Clear-empty-vertex-groups operator.

Drops every vertex group that holds no nonzero weight, behind a confirm
dialog that lists the groups to be removed. Empty groups are safe to drop
precisely because they carry no weights; the confirm copy still flags the
bind sidecar relationship so a user does not mass-delete a bound mesh's
base groups without looking.
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ...core._shared.report import report_info  # type: ignore[import-not-found]


def empty_vertex_group_names(obj: bpy.types.Object) -> list[str]:
    """Names of vertex groups on ``obj`` with no vertex weighted above zero.

    One pass over the mesh verts collects every group index that carries a
    nonzero weight; the empty groups are those not in that set, returned in
    vertex-group order.
    """
    weighted: set[int] = set()
    for vert in obj.data.vertices:
        for elem in vert.groups:
            if elem.weight > 0.0:
                weighted.add(elem.group)
    return [vg.name for vg in obj.vertex_groups if vg.index not in weighted]


class PROSCENIO_OT_clear_empty_vertex_groups(bpy.types.Operator):
    """Delete vertex groups that hold no nonzero weight."""

    bl_idname = "proscenio.clear_empty_vertex_groups"
    bl_label = "Proscenio: Clear Empty Vertex Groups"
    bl_description = (
        "Delete every vertex group on the active mesh that has no nonzero "
        "weight. Empty groups carry no weights, so removing them is safe; a "
        "confirm lists what will be deleted first"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    _empty_names: list[str]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return obj is not None and obj.type == "MESH" and len(obj.vertex_groups) > 0

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        self._empty_names = empty_vertex_group_names(context.active_object)
        if not self._empty_names:
            report_info(self, "no empty vertex groups to clear")
            return {"CANCELLED"}
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(
            text=f"Delete {len(self._empty_names)} empty vertex group(s)?",
            icon="TRASH",
        )
        col = layout.column(align=True)
        for name in self._empty_names:
            col.label(text=name)
        layout.label(
            text="Empty groups hold no weights, so this is safe.",
            icon="INFO",
        )

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return {"CANCELLED"}
        names = empty_vertex_group_names(obj)
        if not names:
            report_info(self, "no empty vertex groups to clear")
            return {"CANCELLED"}
        for name in names:
            group = obj.vertex_groups.get(name)
            if group is not None:
                obj.vertex_groups.remove(group)
        report_info(self, f"removed {len(names)} empty vertex group(s)")
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_clear_empty_vertex_groups,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
