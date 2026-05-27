"""Copy vertex weights from active mesh to selected targets (SPEC 013 O7)."""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import FloatProperty

from ..core.skinning.weight_transfer import transfer_weights_by_nearest


class PROSCENIO_OT_copy_weights_to_selected(bpy.types.Operator):
    bl_idname = "proscenio.copy_weights_to_selected"
    bl_label = "Copy Weights to Selected"
    bl_description = (
        "Copy vertex weights from the active mesh to all other selected meshes "
        "by nearest-vertex world position"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    max_distance: FloatProperty(
        name="Max Distance",
        description="Target verts beyond this distance from any source vert get no weights",
        default=0.5,
        min=0.0,
        soft_max=5.0,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        active = context.active_object
        if active is None or active.type != "MESH":
            return False
        targets = [o for o in context.selected_objects if o.type == "MESH" and o != active]
        return len(targets) >= 1

    def execute(self, context: bpy.types.Context) -> set[str]:
        source = context.active_object
        targets = [o for o in context.selected_objects if o.type == "MESH" and o != source]
        source_positions = [tuple(source.matrix_world @ v.co) for v in source.data.vertices]
        source_weights: list[dict[str, float]] = []
        for vert in source.data.vertices:
            wd: dict[str, float] = {}
            for vg in source.vertex_groups:
                try:
                    w = vg.weight(vert.index)
                    if w > 1e-6:
                        wd[vg.name] = w
                except RuntimeError:
                    continue
            source_weights.append(wd)
        total_verts_copied = 0
        for target in targets:
            target_positions = [tuple(target.matrix_world @ v.co) for v in target.data.vertices]
            transferred = transfer_weights_by_nearest(
                source_positions, source_weights, target_positions, self.max_distance
            )
            for vi, wd in enumerate(transferred):
                if not wd:
                    continue
                for bone_name, w in wd.items():
                    if bone_name not in target.vertex_groups:
                        target.vertex_groups.new(name=bone_name)
                    target.vertex_groups[bone_name].add([vi], w, "REPLACE")
                total_verts_copied += 1
        self.report(
            {"INFO"},
            f"Copied weights to {total_verts_copied} vert(s) across {len(targets)} mesh(es)",
        )
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_copy_weights_to_selected,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
