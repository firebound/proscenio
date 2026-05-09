"""Hydration handlers + deferred-hydrate timer (SPEC 009 wave 9.7).

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

from ..core.hydrate import hydrate_object  # type: ignore[import-not-found]
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


@bpy.app.handlers.persistent  # type: ignore[untyped-decorator]
def on_blend_load(_filepath: str) -> None:
    """Re-hydrate every time a `.blend` finishes loading."""
    hydrate_existing_objects()


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
    moment register() returns -- assigning to the PropertyGroup inside
    register sometimes writes to a stub that is dropped before the
    data block is materialized. A zero-interval timer schedules the
    hydration for after the addon-enable cycle completes, when the
    property data is real and persistent.
    """
    hydrate_existing_objects()
