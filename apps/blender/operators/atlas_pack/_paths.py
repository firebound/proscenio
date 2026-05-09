"""Shared atlas-pack filesystem + snapshot helpers (SPEC 009 wave 9.2)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import bpy

from ...core.cp_keys import PROSCENIO_PRE_PACK  # type: ignore[import-not-found]


def first_texture_image_name(mat: bpy.types.Material) -> str:
    """Return the name of the first image-textured node on ``mat`` (or '')."""
    if not mat.use_nodes or mat.node_tree is None:
        return ""
    for node in mat.node_tree.nodes:
        if node.type == "TEX_IMAGE" and node.image is not None:
            return str(node.image.name)
    return ""


def duplicate_active_uv_layer(obj: bpy.types.Object) -> str:
    """Duplicate the active UV layer to ``<name>.pre_pack`` for later restore.

    No-op when the snapshot already exists. Returns the snapshot layer
    name or an empty string when there was no active UV layer.
    """
    mesh = obj.data
    uv_layers = getattr(mesh, "uv_layers", None)
    if uv_layers is None:
        return ""
    active = uv_layers.active
    if active is None or len(active.data) == 0:
        return ""
    snap_name = f"{active.name}.pre_pack"
    if snap_name in uv_layers:
        return snap_name
    snap = uv_layers.new(name=snap_name, do_init=False)
    if snap is None:
        return ""
    for i, loop in enumerate(active.data):
        snap.data[i].uv = loop.uv
    uv_layers.active = active
    return str(snap.name)


def pre_pack_snapshot_for(obj: bpy.types.Object) -> dict[str, Any] | None:
    """Read the pre-pack snapshot stored as a Custom Property, or ``None``."""
    raw = obj.get(PROSCENIO_PRE_PACK)
    if not raw:
        return None
    try:
        data = json.loads(str(raw))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def scene_has_pre_pack_snapshot(scene: bpy.types.Scene) -> bool:
    """True when at least one mesh in ``scene`` carries a pre-pack snapshot."""
    return any(PROSCENIO_PRE_PACK in obj for obj in scene.objects if obj.type == "MESH")


def packed_atlas_paths(blend_path: str) -> tuple[Path, Path]:
    """Return ``(atlas_png_path, manifest_json_path)`` next to the .blend."""
    blend = Path(blend_path) if blend_path else Path("untitled.blend")
    stem = blend.stem if blend.stem else "atlas_packed"
    folder = blend.parent if blend_path else Path(bpy.path.abspath("//"))
    return folder / f"{stem}.atlas.png", folder / f"{stem}.atlas.json"


def swap_image_in_materials(materials: bpy.types.AnyType, atlas_image: bpy.types.Image) -> None:
    """For every image-textured node across ``materials``, swap to ``atlas_image``."""
    for mat in materials:
        if mat is None or not mat.use_nodes or mat.node_tree is None:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE":
                node.image = atlas_image
