"""Shared helpers for skinning bpy modules (the weight-paint productivity follow-up)."""

from __future__ import annotations

import bpy

from ..automesh.base_sprite import BASE_SPRITE_GROUP_NAME


def wipe_non_base_groups(obj: bpy.types.Object) -> int:
    """Remove every vertex group except the UV-anchor base sprite group.

    Returns the number of groups removed. Callers surface it when > 0
    so users notice manually-painted groups (e.g. ``extra_decoration``)
    that bind / apply_sidecar discards.
    """
    to_remove = [g for g in obj.vertex_groups if g.name != BASE_SPRITE_GROUP_NAME]
    for group in to_remove:
        obj.vertex_groups.remove(group)
    return len(to_remove)
