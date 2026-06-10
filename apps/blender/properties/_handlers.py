"""Hydration handlers + deferred-hydrate timer.

Isolates the persistent ``bpy.app.handlers`` integration so the main
properties module reads as a clean PG declaration list. Three jobs:

- ``hydrate_existing_objects``: walk every object in the current
  ``bpy.data`` and copy its legacy Custom Properties into the
  PropertyGroup.
- ``on_blend_load`` / ``on_blend_save_pre``: persistent handlers wired
  into Blender's load_post / save_pre lists.
- ``deferred_hydrate``: zero-interval ``bpy.app.timers`` job scheduled
  inside ``register()`` so PointerProperty wiring is fully established
  before we touch it.
"""

from __future__ import annotations

import bpy

from ..core._shared.hydrate import hydrate_object  # type: ignore[import-not-found]
from ..core.bpy_helpers._shared.redraw import tag_redraw_areas  # type: ignore[import-not-found]
from ..core.mirror import mirror_all_fields  # type: ignore[import-not-found]


def hydrate_existing_objects() -> None:
    """Walk every object in the current ``bpy.data`` and hydrate.

    During Blender's initial startup, ``bpy.data`` is wrapped in
    ``_RestrictData`` and accessing ``.objects`` raises
    ``AttributeError``. The function bails out silently in that case;
    the ``load_post`` handler retries once the current `.blend`
    finishes loading.
    """
    try:
        objects = list(bpy.data.objects)
    except AttributeError:
        return
    for obj in objects:
        hydrate_object(obj)


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
    """Re-hydrate every time a `.blend` finishes loading."""
    hydrate_existing_objects()
    auto_populate_active_armature()


@bpy.app.handlers.persistent  # type: ignore[untyped-decorator]
def on_depsgraph_update(scene: bpy.types.Scene, _depsgraph: bpy.types.Depsgraph) -> None:
    """Keep ``scene.proscenio.active_armature`` in sync with reality.

    Blender nulls the PointerProperty when the referenced Object is
    deleted, but not when the user only unlinks it from the scene (or
    renames via Outliner): the pointer then dangles, resolving to an
    Object no longer in this scene. The handler clears that case.

    Wrapped in a broad ``Exception`` guard because depsgraph callbacks
    fire inside Blender's draw / event loop, where a bubbling Python
    exception can leave the C side mid-state and crash the next draw.
    """
    try:
        proscenio = getattr(scene, "proscenio", None)
        if proscenio is None:
            return
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
    except Exception:  # depsgraph hook safety - swallow to protect draw cycle
        # No logging: the operator INFO bar is not reachable from a
        # depsgraph callback, so there is nowhere to surface it.
        pass


def _tag_view3d_areas_redraw() -> None:
    tag_redraw_areas(getattr(bpy.context, "window_manager", None), {"VIEW_3D"})


@bpy.app.handlers.persistent  # type: ignore[untyped-decorator]
def on_blend_save_pre(_filepath: str) -> None:
    """Flush every PropertyGroup field to its CP mirror before save."""
    try:
        objects = list(bpy.data.objects)
    except AttributeError:
        return
    for obj in objects:
        props = getattr(obj, "proscenio", None)
        if props is None:
            continue
        mirror_all_fields(props, obj)


def deferred_hydrate() -> None:
    """Run hydration one tick after register().

    Blender's PointerProperty wiring is not fully established the
    moment register() returns - assigning to the PropertyGroup inside
    register sometimes writes to a stub that is dropped before the
    data block is materialized. A zero-interval timer schedules the
    hydration for after the addon-enable cycle completes, when the
    property data is real and persistent.
    """
    hydrate_existing_objects()
    auto_populate_active_armature()
