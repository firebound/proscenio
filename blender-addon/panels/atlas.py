"""Atlas subpanel + packer box helpers."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import bpy

from ..operators.atlas_pack._paths import (  # type: ignore[import-not-found]
    scene_has_pre_pack_snapshot,
)
from ._helpers import draw_subpanel_header


class PROSCENIO_PT_atlas(bpy.types.Panel):
    """Read-only atlas filename discovered from materials."""

    bl_label = "Atlas"
    bl_idname = "PROSCENIO_PT_atlas"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, "atlas", "atlas")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        atlas_name = _discover_atlas_name()
        if atlas_name is None:
            layout.label(text="no atlas linked in materials", icon="INFO")
        else:
            layout.label(text=atlas_name, icon="IMAGE")
        _draw_packer_box(layout, context)


def _draw_packer_box(layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
    """Atlas packer controls (5.1.c.2): config + pack + apply."""
    scene_props = getattr(context.scene, "proscenio", None)
    if scene_props is None:
        return
    box = layout.box()
    box.label(text="Atlas packer", icon="TEXTURE")
    col = box.column(align=True)
    col.prop(scene_props, "pack_padding_px")
    col.prop(scene_props, "pack_max_size")
    col.prop(scene_props, "pack_pot")
    box.separator()
    box.operator("proscenio.pack_atlas", text="Pack Atlas", icon="MOD_ARRAY")
    if _packed_manifest_exists():
        box.operator("proscenio.apply_packed_atlas", text="Apply Packed Atlas", icon="FILE_REFRESH")
    else:
        sub = box.row()
        sub.enabled = False
        sub.label(text="run Pack Atlas first", icon="INFO")
    if scene_has_pre_pack_snapshot(context.scene):
        box.operator("proscenio.unpack_atlas", text="Unpack Atlas", icon="LOOP_BACK")


def _packed_manifest_exists() -> bool:
    """Check whether <blend>.atlas.json is sitting next to the active .blend."""
    blend = bpy.data.filepath
    if not blend:
        return False
    return (Path(blend).parent / f"{Path(blend).stem}.atlas.json").exists()


def _discover_atlas_name() -> str | None:
    for mat in bpy.data.materials:
        if not mat.use_nodes or mat.node_tree is None:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image is not None:
                fp = node.image.filepath
                return (
                    str(bpy.path.abspath(fp)).split("\\")[-1].split("/")[-1]
                    if fp
                    else (f"{node.image.name} (unsaved)")
                )
    return None


_classes: tuple[type, ...] = (PROSCENIO_PT_atlas,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
