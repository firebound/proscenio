"""Atlas pack operator - generates packed atlas PNG + manifest."""

from __future__ import annotations

from typing import ClassVar

import bpy

from ...core.props_access import scene_props  # type: ignore[import-not-found]
from ...core.report import report_error, report_info, report_warn  # type: ignore[import-not-found]
from ._paths import packed_atlas_paths


class PROSCENIO_OT_pack_atlas(bpy.types.Operator):
    """Generate a packed atlas PNG + manifest. Non-destructive - skips UV/material edits."""

    bl_idname = "proscenio.pack_atlas"
    bl_label = "Proscenio: Pack Atlas"
    bl_description = (
        "Walks every sprite mesh, collects its source image, packs them with "
        "MaxRects-BSSF, and writes <blend>.atlas.png + <blend>.atlas.json. "
        "Run Apply Packed Atlas afterwards to rewrite UVs and materials."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # Atlas pack reads source images and writes the manifest while every
        # sprite mesh is in Object Mode; running it from Edit Mode leaves the
        # active mesh's UV data behind BMesh and breaks the round-trip.
        return bool(bpy.data.filepath and context.mode == "OBJECT")

    def execute(self, context: bpy.types.Context) -> set[str]:
        from ...core import atlas_packer  # type: ignore[import-not-found]
        from ...core.bpy_helpers.atlas_collect import (  # type: ignore[import-not-found]
            collect_source_images,
        )
        from ...core.bpy_helpers.atlas_compose import (  # type: ignore[import-not-found]
            compose_atlas,
            write_manifest,
        )

        props = scene_props(context)
        if props is None:
            report_error(self, "scene props not registered")
            return {"CANCELLED"}

        sprite_meshes = [o for o in context.scene.objects if o.type == "MESH"]
        sources = collect_source_images(sprite_meshes)
        if not sources:
            report_warn(self, "no sprite meshes with source images found")
            return {"CANCELLED"}

        padding = int(props.pack_padding_px)
        items = [(src.obj_name, src.slice_px[2], src.slice_px[3]) for src in sources]
        packed = atlas_packer.pack(
            items,
            padding=padding,
            max_size=int(props.pack_max_size),
            power_of_two=bool(props.pack_pot),
        )
        if packed is None:
            report_error(
                self,
                f"pack failed - {len(items)} sprite(s) do not fit in "
                f"{props.pack_max_size}x{props.pack_max_size} px atlas.",
            )
            return {"CANCELLED"}

        atlas_png, manifest_json = packed_atlas_paths(bpy.data.filepath)
        atlas_png.parent.mkdir(parents=True, exist_ok=True)
        compose_atlas(sources, packed, atlas_png, padding=padding)
        write_manifest(packed, padding, sources, manifest_json)

        report_info(
            self,
            f"packed {len(packed.placements)} sprite(s) into "
            f"{packed.atlas_w}x{packed.atlas_h} px atlas -> {atlas_png.name}",
        )
        print(f"[Proscenio] packed atlas -> {atlas_png}")
        print(f"[Proscenio] manifest -> {manifest_json}")
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_pack_atlas,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
