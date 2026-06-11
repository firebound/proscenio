"""Apply Packed Atlas operator - rewrites UVs + materials per manifest."""

from __future__ import annotations

import json
from typing import Any, ClassVar

import bpy

from ...core._shared.cp_keys import (  # type: ignore[import-not-found]
    PROSCENIO_ATLAS_ORIGIN_MARKER,
    PROSCENIO_PRE_PACK,
)
from ...core._shared.report import (  # type: ignore[import-not-found]
    report_error,
    report_info,
    report_warn,
)
from ...core.uv_bounds import remap_uv_into_slot  # type: ignore[import-not-found]
from ._paths import (
    duplicate_active_uv_layer,
    first_texture_image_name,
    packed_atlas_paths,
    pre_pack_snapshot_for,
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
        "Undoable - Ctrl+Z reverts."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not bpy.data.filepath:
            return False
        # uv_layer.data is empty under BMesh in Edit Mode; Object Mode only.
        if context.mode != "OBJECT":
            return False
        _, manifest = packed_atlas_paths(bpy.data.filepath)
        return manifest.exists()

    def execute(self, context: bpy.types.Context) -> set[str]:
        from ...core.bpy_helpers.atlas.atlas_manifest import (  # type: ignore[import-not-found]
            read_manifest,
        )

        atlas_png, manifest_json = packed_atlas_paths(bpy.data.filepath)
        if not manifest_json.exists():
            report_error(self, f"manifest not found - {manifest_json.name}")
            return {"CANCELLED"}

        atlas_w, atlas_h, _padding, placements = read_manifest(manifest_json)

        atlas_image = bpy.data.images.get(atlas_png.stem)
        if atlas_image is None:
            atlas_image = bpy.data.images.load(str(atlas_png), check_existing=True)

        shared_mat = self._ensure_shared_material(atlas_image)

        rewritten = 0
        skipped = 0
        skipped_drift = 0
        for obj in context.scene.objects:
            if obj.type != "MESH" or obj.name not in placements:
                continue
            placement = placements[obj.name]
            if not self._snapshot_pre_pack(obj):
                skipped_drift += 1
                continue
            if not self._apply_to_object(obj, placement, atlas_w, atlas_h):
                skipped += 1
                continue
            self._relink_material(obj, shared_mat, atlas_image)
            rewritten += 1

        msg = f"applied packed atlas to {rewritten} sprite(s)"
        if skipped:
            msg += f"; skipped {skipped} (no UV layer)"
        if skipped_drift:
            msg += f"; skipped {skipped_drift} (stale pre-pack snapshot)"
        report_info(self, msg)
        print(f"[Proscenio] {msg}")
        return {"FINISHED"}

    def _snapshot_pre_pack(self, obj: bpy.types.Object) -> bool:
        """Snapshot pre-apply state to a Custom Property + duplicated UV layer.

        When a snapshot already exists, restore the pre_pack layer into the
        active layer first so every Apply starts from the original
        source-image UVs (re-rewriting atlas-space UVs shrinks the slot).

        Returns True when re-rewriting is safe; False when the snapshot is
        unrecoverable (renamed pre_pack layer, mismatched length) and the
        caller should skip this sprite.
        """
        if PROSCENIO_PRE_PACK in obj:
            return self._restore_active_uvs_from_pre_pack(obj)
        snapshot: dict[str, Any] = {}
        materials = getattr(obj.data, "materials", None) or []
        if materials and materials[0] is not None:
            snapshot["material"] = materials[0].name
            snapshot["image"] = first_texture_image_name(materials[0])
            # Stamp the origin marker so Unpack can rescue this material if it
            # is renamed before the by-name restore runs.
            materials[0][PROSCENIO_ATLAS_ORIGIN_MARKER] = materials[0].name
        props = getattr(obj, "proscenio", None)
        if props is not None:
            snapshot["region_mode"] = str(props.region_mode)
            snapshot["region_x"] = float(props.region_x)
            snapshot["region_y"] = float(props.region_y)
            snapshot["region_w"] = float(props.region_w)
            snapshot["region_h"] = float(props.region_h)
        snapshot["uv_layer_snapshot"] = duplicate_active_uv_layer(obj)
        obj[PROSCENIO_PRE_PACK] = json.dumps(snapshot)
        return True

    def _restore_active_uvs_from_pre_pack(self, obj: bpy.types.Object) -> bool:
        """Copy the pre_pack snapshot layer's UVs into the active layer.

        Resolves the snapshot layer by the name stored in the CP, not from
        the live active layer name (which the user may have renamed).
        Returns False when the snapshot is unrecoverable so the caller can
        skip the sprite instead of double-packing.
        """
        uv_layers = getattr(obj.data, "uv_layers", None)
        if uv_layers is None:
            return False
        active = uv_layers.active
        if active is None:
            return False
        snapshot = pre_pack_snapshot_for(obj) or {}
        snap_name = str(snapshot.get("uv_layer_snapshot", ""))
        snap = uv_layers.get(snap_name) if snap_name else None
        if snap is None or len(snap.data) != len(active.data):
            report_warn(
                self,
                f"'{obj.name}': pre-pack UV snapshot missing or out of sync "
                f"(renamed layer?); skipping Apply to avoid cumulative drift",
            )
            return False
        for i, loop in enumerate(snap.data):
            active.data[i].uv = loop.uv
        return True

    def _apply_to_object(
        self,
        obj: bpy.types.Object,
        placement: object,
        atlas_w: int,
        atlas_h: int,
    ) -> bool:
        """Apply the packed atlas to a single sprite mesh."""
        props = getattr(obj, "proscenio", None)
        element_type = str(getattr(props, "element_type", "mesh")) if props else "mesh"
        rewrote = self._rewrite_uvs(obj, placement, atlas_w, atlas_h)
        if element_type == "sprite" and props is not None:
            self._apply_sprite(props, placement, atlas_w, atlas_h)
            return True
        return rewrote

    def _apply_sprite(
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
        # Packer emits top-down slot Y; remap_uv_into_slot wants it bottom-up.
        slot_px = (slot.x, atlas_h - slot.y - slot.h, slot.w, slot.h)
        slice_px = (slice_rect.x, slice_rect.y, slice_rect.w, slice_rect.h)
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                u, v = uv_layer.data[li].uv
                uv_layer.data[li].uv = remap_uv_into_slot(
                    u, v, slice_px, src_w, src_h, slot_px, atlas_w, atlas_h
                )
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
