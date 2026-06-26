"""Shared bone-collection resolution for the Rig UI / color / shape operators.

One place resolves a bone collection by name on an armature and yields its
bones, so the three collection operators - ``select_bone_collection``,
``color_bone_collection``, ``assign_bone_shape`` (collection scope) - share one
lookup and one missing-collection guard rather than re-deriving it. Reads
``Armature.collections_all`` so a nested (4.1+) collection is reachable by name,
falling back to the flat ``collections`` on older data.
"""

from __future__ import annotations

import bpy


def resolve_collection(
    armature: bpy.types.Object, collection_name: str
) -> bpy.types.BoneCollection | None:
    """The named bone collection on ``armature``'s data, or None.

    Looks in ``collections_all`` (every collection including nested ones) first,
    then the top-level ``collections``; either may be absent on a malformed or
    pre-4.0 datablock, in which case the lookup is a clean None.
    """
    data = getattr(armature, "data", None)
    if data is None:
        return None
    for attr in ("collections_all", "collections"):
        collections = getattr(data, attr, None)
        getter = getattr(collections, "get", None)
        if callable(getter):
            found = getter(collection_name)
            if found is not None:
                return found
    return None


def iter_collection_bones(armature: bpy.types.Object, collection_name: str) -> list[bpy.types.Bone]:
    """The bones assigned to ``collection_name`` on ``armature``, or an empty list.

    An unknown collection (or one with no bones) yields ``[]`` so callers can
    treat "nothing to act on" uniformly. Returns the data ``Bone`` objects;
    callers that need pose bones index ``armature.pose.bones`` by name.
    """
    collection = resolve_collection(armature, collection_name)
    if collection is None:
        return []
    return list(getattr(collection, "bones", []))
