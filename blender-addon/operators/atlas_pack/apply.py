"""Apply Packed Atlas operator -- rewrites UVs + materials per manifest."""

from __future__ import annotations

import json
from typing import Any, ClassVar

import bpy

from ...core.cp_keys import PROSCENIO_PRE_PACK  # type: ignore[import-not-found]
from ...core.report import report_error, report_info  # type: ignore[import-not-found]
from ._paths import (
    duplicate_active_uv_layer,
    first_texture_image_name,
    packed_atlas_paths,
    swap_image_in_materials,
)

_PACKED_ATLAS_MAT_NAME = "Proscenio.PackedAtlas"


class PROSCENIO_OT_apply_packed_atlas(bpy.types.Operator):
    """Rewrite UVs + materials so every sprite reads from the packed atlas."""

    bl_idname = "proscenio.apply_packed_atlas"
    bl_label = "Proscenio: Apply Packed Atlas"
    bl_description = (
        "Reads <blend>.atlas.json, rewrites every sprite's UVs to address the "
        "packed atlas, and (unless material_isolated is set on the object) "
        "links the sprite to the shared 'Proscenio.PackedAtlas' material. "
        "Undoable -- Ctrl+Z reverts."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not bpy.data.filepath:
            return False
        _, manifest = packed_atlas_paths(bpy.data.filepath)
        return manifest.exists()

    def execute(self, context: bpy.types.Context) -> set[str]:
        from ...core.bpy_helpers import atlas_io  # type: ignore[import-not-found]

        atlas_png, manifest_json = packed_atlas_paths(bpy.data.filepath)
        if not manifest_json.exists():
            report_error(self, f"manifest not found -- {manifest_json.name}")
            return {"CANCELLED"}

        atlas_w, atlas_h, _padding, placements = atlas_io.read_manifest(manifest_json)

        atlas_image = bpy.data.images.get(atlas_png.stem)
        if atlas_image is None:
            atlas_image = bpy.data.images.load(str(atlas_png), check_existing=True)

        shared_mat = self._ensure_shared_material(atlas_image)

        rewritten = 0
        skipped = 0
        for obj in context.scene.objects:
            if obj.type != "MESH" or obj.name not in placements:
                continue
            placement = placements[obj.name]
            self._snapshot_pre_pack(obj)
            if not self._apply_to_object(obj, placement, atlas_w, atlas_h):
                skipped += 1
                continue
            self._relink_material(obj, shared_mat, atlas_image)
            rewritten += 1

        msg = f"applied packed atlas to {rewritten} sprite(s)"
        if skipped:
            msg += f"; skipped {skipped} (no UV layer)"
        report_info(self, msg)
        print(f"[Proscenio] {msg}")
        return {"FINISHED"}

    def _snapshot_pre_pack(self, obj: bpy.types.Object) -> None:
        """Snapshot pre-apply state to a Custom Property + duplicated UV layer."""
        if PROSCENIO_PRE_PACK in obj:
            return
        snapshot: dict[str, Any] = {}
        materials = getattr(obj.data, "materials", None) or []
        if materials and materials[0] is not None:
            snapshot["material"] = materials[0].name
            snapshot["image"] = first_texture_image_name(materials[0])
        props = getattr(obj, "proscenio", None)
        if props is not None:
            snapshot["region_mode"] = str(props.region_mode)
            snapshot["region_x"] = float(props.region_x)
            snapshot["region_y"] = float(props.region_y)
            snapshot["region_w"] = float(props.region_w)
            snapshot["region_h"] = float(props.region_h)
        snapshot["uv_layer_snapshot"] = duplicate_active_uv_layer(obj)
        obj[PROSCENIO_PRE_PACK] = json.dumps(snapshot)

    def _apply_to_object(
        self,
        obj: bpy.types.Object,
        placement: object,
        atlas_w: int,
        atlas_h: int,
    ) -> bool:
        """Apply the packed atlas to a single sprite mesh."""
        props = getattr(obj, "proscenio", None)
        sprite_type = str(getattr(props, "sprite_type", "polygon")) if props else "polygon"
        rewrote = self._rewrite_uvs(obj, placement, atlas_w, atlas_h)
        if sprite_type == "sprite_frame" and props is not None:
            self._apply_sprite_frame(props, placement, atlas_w, atlas_h)
            return True
        return rewrote

    def _apply_sprite_frame(
        self,
        props: bpy.types.AnyType,
        placement: object,
        atlas_w: int,
        atlas_h: int,
    ) -> None:
        """Set region_mode=manual + region_x/y/w/h pointing at the slot."""
        slot = placement.slot  # type: ignore[attr-defined]
        props.region_mode = "manual"
        props.region_x = slot.x / atlas_w
        props.region_y = slot.y / atlas_h
        props.region_w = slot.w / atlas_w
        props.region_h = slot.h / atlas_h

    def _ensure_shared_material(self, atlas_image: bpy.types.Image) -> bpy.types.Material:
        """Create or refresh the shared 'Proscenio.PackedAtlas' material."""
        mat = bpy.data.materials.get(_PACKED_ATLAS_MAT_NAME)
        if mat is None:
            mat = bpy.data.materials.new(name=_PACKED_ATLAS_MAT_NAME)
        mat.use_nodes = True
        nt = mat.node_tree
        while nt.nodes:
            nt.nodes.remove(nt.nodes[0])
        out = nt.nodes.new(type="ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new(type="ShaderNodeBsdfPrincipled")
        tex = nt.nodes.new(type="ShaderNodeTexImage")
        tex.image = atlas_image
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        return mat

    def _rewrite_uvs(
        self,
        obj: bpy.types.Object,
        placement: object,
        atlas_w: int,
        atlas_h: int,
    ) -> bool:
        """Map polygon UVs from source-image space -> packed-atlas space."""
        mesh = obj.data
        uv_layer = mesh.uv_layers.active
        if uv_layer is None or len(uv_layer.data) == 0:
            return False
        slot = placement.slot  # type: ignore[attr-defined]
        slice_rect = placement.slice  # type: ignore[attr-defined]
        src_w = placement.source_w  # type: ignore[attr-defined]
        src_h = placement.source_h  # type: ignore[attr-defined]
        slot_y_bu = atlas_h - slot.y - slot.h
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                u, v = uv_layer.data[li].uv
                src_px_x = u * src_w
                src_px_y = v * src_h
                new_u = (slot.x + (src_px_x - slice_rect.x)) / atlas_w
                new_v = (slot_y_bu + (src_px_y - slice_rect.y)) / atlas_h
                uv_layer.data[li].uv = (new_u, new_v)
        return True

    def _relink_material(
        self,
        obj: bpy.types.Object,
        shared_mat: bpy.types.Material,
        atlas_image: bpy.types.Image,
    ) -> None:
        """Link sprite to shared material, or swap its image when isolated."""
        materials = getattr(obj.data, "materials", None)
        if materials is None:
            return
        props = getattr(obj, "proscenio", None)
        if bool(getattr(props, "material_isolated", False)):
            swap_image_in_materials(materials, atlas_image)
            return
        if materials:
            materials[0] = shared_mat
        else:
            materials.append(shared_mat)


_classes: tuple[type, ...] = (PROSCENIO_OT_apply_packed_atlas,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
