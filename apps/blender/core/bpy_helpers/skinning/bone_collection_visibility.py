"""Bone Collections visibility snapshot/restore (the paint work, T4).

Blender 4.0+ exposes `armature.data.collections` with per-collection
`is_visible`. Blender 3.x has no Bone Collections; we fall back to
per-bone `hide` flag.

The module accepts duck-typed inputs so tests use SimpleNamespace
mocks rather than booting bpy. No bpy import at module level.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BoneCollectionSnapshot:
    """Captured visibility state. visible_names + bone_hide_states are mutually exclusive."""

    visible_names: list[str] = field(default_factory=list)
    bone_hide_states: dict[str, bool] = field(default_factory=dict)


def snapshot(armature: Any) -> BoneCollectionSnapshot:
    """Detect 4.0+ vs 3.x API; capture current visibility."""
    collections = getattr(armature.data, "collections", None)
    if collections is not None:
        visible = [c.name for c in collections if getattr(c, "is_visible", False)]
        return BoneCollectionSnapshot(visible_names=visible, bone_hide_states={})
    bones = getattr(armature.data, "bones", [])
    hide_states = {b.name: bool(getattr(b, "hide", False)) for b in bones}
    return BoneCollectionSnapshot(visible_names=[], bone_hide_states=hide_states)


def restore(armature: Any, snap: BoneCollectionSnapshot) -> None:
    """Reapply visibility. Detects API generation from the snapshot shape."""
    collections = getattr(armature.data, "collections", None)
    if collections is not None and snap.visible_names is not None:
        wanted = set(snap.visible_names)
        for collection in collections:
            collection.is_visible = collection.name in wanted
        return
    bones = getattr(armature.data, "bones", [])
    for bone in bones:
        if bone.name in snap.bone_hide_states:
            bone.hide = snap.bone_hide_states[bone.name]
