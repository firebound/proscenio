"""Unpack Atlas operator -- restore original UVs + materials from snapshot."""

from __future__ import annotations

import contextlib
from typing import Any, ClassVar

import bpy

from ...core.cp_keys import PROSCENIO_PRE_PACK  # type: ignore[import-not-found]
from ...core.report import report_info  # type: ignore[import-not-found]
from ._paths import pre_pack_snapshot_for, scene_has_pre_pack_snapshot, swap_image_in_materials


class PROSCENIO_OT_unpack_atlas(bpy.types.Operator):
    """Revert a previous Apply Packed Atlas -- restore original UVs + materials."""

    bl_idname = "proscenio.unpack_atlas"
    bl_label = "Proscenio: Unpack Atlas"
    bl_description = (
        "Restores every sprite mesh to its pre-Apply state -- original UVs, "
        "original material, original region_mode. Reads a snapshot stored as "
        "a Custom Property + a duplicated UV layer (`<name>.pre_pack`). "
        "Survives .blend reload (Ctrl+Z does not)."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return scene_has_pre_pack_snapshot(context.scene)

    def execute(self, context: bpy.types.Context) -> set[str]:
        restored = 0
        for obj in context.scene.objects:
            if obj.type != "MESH":
                continue
            snapshot = pre_pack_snapshot_for(obj)
            if snapshot is None:
                continue
            self._restore_object(obj, snapshot)
            del obj[PROSCENIO_PRE_PACK]
            restored += 1
        msg = f"unpacked {restored} sprite(s) -- restored pre-Apply state"
        report_info(self, msg)
        print(f"[Proscenio] {msg}")
        return {"FINISHED"}

    def _restore_object(self, obj: bpy.types.Object, snapshot: dict[str, Any]) -> None:
        self._restore_uvs(obj, snapshot.get("uv_layer_snapshot", ""))
        self._restore_material(obj, snapshot)
        self._restore_region(obj, snapshot)

    def _restore_uvs(self, obj: bpy.types.Object, snap_name: str) -> None:
        if not snap_name:
            return
        uv_layers = getattr(obj.data, "uv_layers", None)
        if uv_layers is None:
            return
        snap = uv_layers.get(snap_name)
        if snap is None:
            return
        original_name = snap_name[: -len(".pre_pack")] if snap_name.endswith(".pre_pack") else ""
        target = uv_layers.get(original_name) or uv_layers.active
        if target is None:
            return
        for i, loop in enumerate(snap.data):
            target.data[i].uv = loop.uv
        uv_layers.remove(snap)

    def _restore_material(self, obj: bpy.types.Object, snapshot: dict[str, Any]) -> None:
        mat_name = str(snapshot.get("material", ""))
        materials = getattr(obj.data, "materials", None)
        if not mat_name or materials is None:
            return
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            return
        if materials:
            materials[0] = mat
        else:
            materials.append(mat)
        image_name = str(snapshot.get("image", ""))
        if image_name:
            image = bpy.data.images.get(image_name)
            if image is not None:
                swap_image_in_materials(materials, image)

    def _restore_region(self, obj: bpy.types.Object, snapshot: dict[str, Any]) -> None:
        props = getattr(obj, "proscenio", None)
        if props is None or "region_mode" not in snapshot:
            return
        props.region_mode = str(snapshot["region_mode"])
        with contextlib.suppress(TypeError, ValueError):
            props.region_x = float(snapshot.get("region_x", 0.0))
            props.region_y = float(snapshot.get("region_y", 0.0))
            props.region_w = float(snapshot.get("region_w", 1.0))
            props.region_h = float(snapshot.get("region_h", 1.0))


_classes: tuple[type, ...] = (PROSCENIO_OT_unpack_atlas,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
