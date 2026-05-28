"""Copy vertex weights from active mesh to selected targets (SPEC 013 O7)."""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import FloatProperty

from ..core.skinning.weight_transfer import (  # type: ignore[import-not-found]
    transfer_weights_by_nearest,
)


class PROSCENIO_OT_copy_weights_to_selected(bpy.types.Operator):
    bl_idname = "proscenio.copy_weights_to_selected"
    bl_label = "Copy Weights to Selected"
    bl_description = (
        "Copy vertex weights from the active mesh to all other selected meshes "
        "by nearest-vertex world position"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    max_distance: FloatProperty(  # type: ignore[valid-type]
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
        source_positions, source_weights = _collect_source_data(source)
        total_verts_copied = sum(
            _apply_to_target(target, source_positions, source_weights, self.max_distance)
            for target in targets
        )
        self.report(
            {"INFO"},
            f"Copied weights to {total_verts_copied} vert(s) across {len(targets)} mesh(es)",
        )
        return {"FINISHED"}


def _read_vert_weights(vert: bpy.types.MeshVertex, obj: bpy.types.Object) -> dict[str, float]:
    """Return a name->weight dict for one vert across the obj's vertex_groups."""
    weights: dict[str, float] = {}
    for vg in obj.vertex_groups:
        try:
            w = vg.weight(vert.index)
        except RuntimeError:
            continue
        if w > 1e-6:
            weights[vg.name] = w
    return weights


def _collect_source_data(
    source: bpy.types.Object,
) -> tuple[list[tuple[float, float, float]], list[dict[str, float]]]:
    """Materialize source mesh world positions + per-vert weight dicts."""
    positions = [tuple(source.matrix_world @ v.co) for v in source.data.vertices]
    weights = [_read_vert_weights(v, source) for v in source.data.vertices]
    return positions, weights


def _apply_to_target(
    target: bpy.types.Object,
    source_positions: list[tuple[float, float, float]],
    source_weights: list[dict[str, float]],
    max_distance: float,
) -> int:
    """Transfer weights to one target mesh; return verts that received weights."""
    target_positions = [tuple(target.matrix_world @ v.co) for v in target.data.vertices]
    transferred = transfer_weights_by_nearest(
        source_positions, source_weights, target_positions, max_distance
    )
    applied = 0
    for vi, wd in enumerate(transferred):
        if not wd:
            continue
        for bone_name, w in wd.items():
            if bone_name not in target.vertex_groups:
                target.vertex_groups.new(name=bone_name)
            target.vertex_groups[bone_name].add([vi], w, "REPLACE")
        applied += 1
    return applied


_classes: tuple[type, ...] = (PROSCENIO_OT_copy_weights_to_selected,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
