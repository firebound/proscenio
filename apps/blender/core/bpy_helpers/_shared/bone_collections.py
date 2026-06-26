"""Shared bone-collection resolution for the Rig UI / color operators.

One place resolves a bone collection by name on an armature and yields its
bones, so the collection operators - ``select_bone_collection`` and
``color_bone_collection`` - share one lookup and one missing-collection guard
rather than re-deriving it. Reads ``Armature.collections_all`` so a nested
(4.1+) collection is reachable by name, falling back to the flat ``collections``
on older data.
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
    """The bones in ``collection_name`` on ``armature``, nested ones included.

    An unknown collection (or one with no bones) yields ``[]`` so callers can
    treat "nothing to act on" uniformly. Prefers ``bones_recursive`` so a parent
    collection that holds bones only in its children (4.1+ nesting) still
    resolves them, falling back to the direct ``bones`` on older data. Returns
    the data ``Bone`` objects; callers that need pose bones index
    ``armature.pose.bones`` by name.
    """
    collection = resolve_collection(armature, collection_name)
    if collection is None:
        return []
    bones = getattr(collection, "bones_recursive", None)
    if bones is None:
        bones = getattr(collection, "bones", [])
    return list(bones)


def collection_theme_label(armature: bpy.types.Object, collection_name: str) -> str:
    """The theme-slot number every bone in ``collection_name`` shares, or ``""``.

    The collection swatch applies one palette to every bone, so when the bones
    still agree on a single ``THEME##`` slot we surface its number (``"1"`` ..
    ``"15"``) next to the color icon. A DEFAULT/CUSTOM slot, a mix of slots, or
    an empty collection yields ``""`` - nothing to show. Reads ``bone.color``,
    absent on a pre-4.0 datablock, in which case it is treated as DEFAULT.
    """
    bones = iter_collection_bones(armature, collection_name)
    if not bones:
        return ""
    palettes = {getattr(getattr(b, "color", None), "palette", "DEFAULT") for b in bones}
    if len(palettes) != 1:
        return ""
    palette = next(iter(palettes))
    if not palette.startswith("THEME"):
        return ""
    return palette[len("THEME") :].lstrip("0") or "0"
