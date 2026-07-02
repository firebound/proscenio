"""Armature-resolution policy: which rig skeleton / skinning / export operations target.

Split out of ``props_access`` (which keeps the generic PropertyGroup None-guard
accessors); these five functions are the self-contained "which armature" policy
with their own consumers. Duck-typed and bpy-free at runtime - a ``SimpleNamespace``
``scene`` / ``context`` exercises the priority order without Blender; bpy is only
a type-hint import under ``TYPE_CHECKING``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from .props_access import scene_props

if TYPE_CHECKING:
    import bpy


def active_armature(context: bpy.types.Context) -> bpy.types.Object | None:
    """Return the Skeleton-panel picker armature, or None.

    Reads ``scene.proscenio.active_armature`` and returns it only when it is an
    ``ARMATURE`` object: an unset picker, an unregistered PropertyGroup, or a
    non-armature pointer all yield None. The single source of truth for "which
    armature do skeleton / skinning operations target".
    """
    props = scene_props(context)
    picker = getattr(props, "active_armature", None) if props is not None else None
    if picker is None or getattr(picker, "type", None) != "ARMATURE":
        return None
    return cast("bpy.types.Object", picker)


def resolve_target_armature(
    context: bpy.types.Context, obj: bpy.types.Object
) -> bpy.types.Object | None:
    """The armature ``obj`` should attach a bone of, or None.

    Priority: ``obj``'s own object-parent when it is an ARMATURE (the slot
    convention parents the Empty to the rig, and a sprite may share it), then
    the Skeleton picker, then the scene's export armature. The single
    resolution order both the slot bone-follow and the rigid sprite
    bone-attach route through, so the two never disagree on the rig.

    Duck-typed at runtime (``getattr`` only), so a ``SimpleNamespace`` ``obj``
    and ``context`` exercise the priority order without Blender.
    """
    parent = getattr(obj, "parent", None)
    if parent is not None and getattr(parent, "type", None) == "ARMATURE":
        return cast("bpy.types.Object", parent)
    picker = active_armature(context)
    if picker is not None:
        return picker
    scene = getattr(context, "scene", None)
    return resolve_export_armature(scene) if scene is not None else None


def resolve_export_armature(scene: object) -> bpy.types.Object | None:
    """Return the armature Proscenio exports for ``scene`` - picker first.

    Honours ``scene.proscenio.active_armature`` when it still points at a live
    ARMATURE present in this scene, otherwise the first ARMATURE in scene
    order. The writer and the export validator both route through this so they
    cannot disagree on the rig in a multi-armature scene.

    Duck-typed and bpy-free at runtime: ``scene`` may be a ``SimpleNamespace``
    in unit tests, and ``scene.proscenio`` is absent under ``--background``.
    """
    objects = list(getattr(scene, "objects", ()) or ())
    picked = _picked_scene_armature(scene, objects)
    if picked is not None:
        return picked
    first = next((o for o in objects if getattr(o, "type", None) == "ARMATURE"), None)
    return cast("bpy.types.Object | None", first)


def _picked_scene_armature(scene: object, objects: list[object]) -> bpy.types.Object | None:
    """The picker pointer when it is a live ARMATURE in ``objects``, else None.

    Guards a stale pointer: an armature unlinked from this scene (still in
    ``bpy.data``) or a freed datablock both fall through to the caller's
    scene-order fallback rather than exporting a rig the user cannot see.
    """
    props = getattr(scene, "proscenio", None)
    picked = getattr(props, "active_armature", None) if props is not None else None
    if picked is None:
        return None
    try:
        if getattr(picked, "type", None) != "ARMATURE":
            return None
        name = getattr(picked, "name", None)
    except ReferenceError:
        return None
    if not any(getattr(o, "name", None) == name for o in objects):
        return None
    return cast("bpy.types.Object", picked)


def describe_export_target(scene: object) -> tuple[str, bool] | None:
    """Name of the armature the writer will export, plus whether the picker chose it.

    Mirrors :func:`resolve_export_armature` but returns ``(name, picked)`` -
    ``picked`` is True when the Skeleton picker supplied the target, False when
    it fell back to the first armature in scene order. ``None`` when the scene
    has no armature at all. The Skeleton panel reads this to name the export
    target, so the picker-vs-fallback choice is visible before export.
    """
    objects = list(getattr(scene, "objects", ()) or ())
    picked = _picked_scene_armature(scene, objects)
    if picked is not None:
        return str(getattr(picked, "name", "")), True
    first = next((o for o in objects if getattr(o, "type", None) == "ARMATURE"), None)
    if first is None:
        return None
    return str(getattr(first, "name", "")), False
