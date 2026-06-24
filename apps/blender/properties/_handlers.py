"""Persistent ``bpy.app.handlers`` integration for the per-Object props.

Isolates the handlers so the main properties module reads as a clean PG
declaration list. Two jobs survive the storage split (spec 037):

- ``on_blend_load``: a ``load_post`` handler that auto-fills the active
  armature pointer when a freshly opened `.blend` is unambiguous.
- ``on_depsgraph_update``: per-tick scene hygiene (armature pointer +
  Outliner / Slots / Skeleton highlight follow).

There is no hydrate handler and no save-pre mirror flush any more: each
per-Object field has one storage home (its ``proscenio_*`` Custom
Property), edited through a ``get=``/``set=`` PropertyGroup proxy, so
nothing needs copying between a PropertyGroup and a Custom Property at
load or save time.
"""

from __future__ import annotations

import bpy

from ..core.bpy_helpers._shared.redraw import tag_redraw_areas  # type: ignore[import-not-found]
from ..core.outliner_view import (  # type: ignore[import-not-found]
    is_outliner_relevant,
    source_index_for_name,
)
from ..core.slot.slot_emit import is_slot_empty  # type: ignore[import-not-found]


def auto_populate_active_armature() -> None:
    """Pre-fill ``scene.proscenio.active_armature`` when unambiguous.

    When a `.blend` opens with exactly one armature in the scene and the
    Proscenio pointer still empty, set it, so the Skeleton picker visibly
    reflects the rig that skeleton operations will target.
    """
    try:
        scenes = list(bpy.data.scenes)
    except AttributeError:
        return
    for scene in scenes:
        proscenio = getattr(scene, "proscenio", None)
        if proscenio is None or proscenio.active_armature is not None:
            continue
        armatures = [obj for obj in scene.objects if obj.type == "ARMATURE"]
        if len(armatures) == 1:
            proscenio.active_armature = armatures[0]


@bpy.app.handlers.persistent  # type: ignore[untyped-decorator]
def on_blend_load(_filepath: str) -> None:
    """Auto-fill the active armature every time a `.blend` finishes loading."""
    auto_populate_active_armature()


@bpy.app.handlers.persistent  # type: ignore[untyped-decorator]
def on_depsgraph_update(scene: bpy.types.Scene, _depsgraph: bpy.types.Depsgraph) -> None:
    """Per-tick scene hygiene: armature pointer + Outliner highlight follow.

    Wrapped in a broad ``Exception`` guard because depsgraph callbacks
    fire inside Blender's draw / event loop, where a bubbling Python
    exception can leave the C side mid-state and crash the next draw.
    Both jobs are cheap guarded comparisons that early-out unless
    something actually changed; this callback fires on every transform
    and frame change, so it must never do real work on the common path.
    """
    try:
        proscenio = getattr(scene, "proscenio", None)
        if proscenio is None:
            return
        _clear_dangling_active_armature(scene, proscenio)
        sync_outliner_to_active_object(scene)
        sync_slots_to_active_object(scene)
        sync_bone_index_to_active_bone(scene)
    except Exception:  # depsgraph hook safety - swallow to protect draw cycle
        # No logging: the operator INFO bar is not reachable from a
        # depsgraph callback, so there is nowhere to surface it.
        pass


def _clear_dangling_active_armature(scene: bpy.types.Scene, proscenio: bpy.types.AnyType) -> None:
    """Null ``active_armature`` when it dangles outside the scene.

    Blender nulls the PointerProperty when the referenced Object is
    deleted, but not when the user only unlinks it from the scene (or
    renames via Outliner): the pointer then dangles, resolving to an
    Object no longer in this scene. This clears that case.
    """
    pointer = proscenio.active_armature
    if pointer is None:
        return
    try:
        if pointer.name in scene.objects and pointer.type == "ARMATURE":
            return
    except ReferenceError:
        # Pointer references a freed datablock. Treat as stale.
        pass
    proscenio.active_armature = None
    _tag_view3d_areas_redraw()


def sync_outliner_to_active_object(scene: bpy.types.Scene) -> None:
    """Move the Outliner highlight to follow the viewport's active object.

    Closes the selection loop the Outliner click already drives the other
    way: selecting an object in the 3D viewport points
    ``active_outliner_index`` at that object's source-collection row.
    Early-outs keep the depsgraph callback cheap - it does nothing unless
    the active object is a Proscenio-relevant row whose index differs from
    what the panel already shows. A non-Proscenio active object (camera,
    light) leaves the highlight untouched rather than pointing it at a
    hidden row.
    """
    proscenio = getattr(scene, "proscenio", None)
    if proscenio is None or not hasattr(proscenio, "active_outliner_index"):
        return
    view_layer = getattr(bpy.context, "view_layer", None)
    active = getattr(getattr(view_layer, "objects", None), "active", None)
    if active is None or not is_outliner_relevant(active):
        return
    idx = source_index_for_name(bpy.data.objects, active.name)
    if idx is None or proscenio.active_outliner_index == idx:
        return
    proscenio.active_outliner_index = idx
    _tag_view3d_areas_redraw()


def sync_slots_to_active_object(scene: bpy.types.Scene) -> None:
    """Move the Slots highlight to follow the active object when it is a slot.

    The Slots list and the Outliner both bind ``bpy.data.objects`` but with
    separate active-index props, so without this the Slots row stays lit on the
    previously clicked slot when the active object changes elsewhere (the
    cross-list-deselect bug). A non-slot active object leaves the highlight
    untouched. Cheap early-outs keep the per-tick depsgraph callback light.
    """
    proscenio = getattr(scene, "proscenio", None)
    if proscenio is None or not hasattr(proscenio, "active_slot_index"):
        return
    view_layer = getattr(bpy.context, "view_layer", None)
    active = getattr(getattr(view_layer, "objects", None), "active", None)
    if active is None or not is_slot_empty(active):
        return
    idx = source_index_for_name(bpy.data.objects, active.name)
    if idx is None or proscenio.active_slot_index == idx:
        return
    proscenio.active_slot_index = idx
    _tag_view3d_areas_redraw()


def sync_bone_index_to_active_bone(scene: bpy.types.Scene) -> None:
    """Move the Skeleton bone highlight to follow the picked armature's active bone.

    Closes the same loop for bones: selecting a bone in the viewport points the
    Skeleton list at it. Targets the picked Active Armature (the rig the list
    shows). The fast-path guard reads the bone already under the highlight, so
    the O(bones) index scan only runs when the active bone actually changed -
    this callback fires on every transform.
    """
    proscenio = getattr(scene, "proscenio", None)
    if proscenio is None or not hasattr(proscenio, "active_bone_index"):
        return
    armature = getattr(proscenio, "active_armature", None)
    bones = getattr(getattr(armature, "data", None), "bones", None)
    active_bone = getattr(bones, "active", None) if bones is not None else None
    if active_bone is None:
        return
    current = proscenio.active_bone_index
    if 0 <= current < len(bones) and bones[current].name == active_bone.name:
        return
    idx = source_index_for_name(bones, active_bone.name)
    if idx is None or proscenio.active_bone_index == idx:
        return
    proscenio.active_bone_index = idx
    _tag_view3d_areas_redraw()


def _tag_view3d_areas_redraw() -> None:
    tag_redraw_areas(getattr(bpy.context, "window_manager", None), {"VIEW_3D"})
