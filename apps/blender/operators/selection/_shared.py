"""Helpers shared across the selection operators."""

from __future__ import annotations

import bpy


def _sync_active_index(
    context: bpy.types.Context,
    prop_name: str,
    items: bpy.types.AnyType,
    target_name: str,
) -> None:
    """Update ``scene.proscenio.<prop_name>`` so the panel UIList highlight
    follows the row whose underlying datablock matches ``target_name``."""
    scene_props = getattr(context.scene, "proscenio", None)
    if scene_props is None or not hasattr(scene_props, prop_name):
        return
    for idx, candidate in enumerate(items):
        if candidate.name == target_name:
            setattr(scene_props, prop_name, idx)
            return
