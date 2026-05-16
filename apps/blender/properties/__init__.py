"""Proscenio property groups (SPEC 005, repackaged in SPEC 009 wave 9.10).

These property groups expose typed widgets for the addon panel. Their
values round-trip with the legacy Custom Properties on the same data
block so users who authored a `.blend` before SPEC 005 see existing
values without manual re-entry, and power users can keep editing raw
Custom Properties if they prefer.

Contract:

- The PropertyGroup is the editor-side source of truth (typed,
  validated, surfaced in the panel).
- Each property has an ``update`` callback that mirrors the value to
  the Custom Property the writer reads (``proscenio_type``, etc).
- On ``register()``, every existing Custom Property is hydrated into
  the PropertyGroup so legacy data shows up in the new UI.

Submodules per concern (wave 9.10 split):

- ``object_props.py``     ``ProscenioObjectProps`` + EnumProperty items
                          tuples (sprite type, region mode, driver target,
                          driver source axis).
- ``scene_props.py``      ``ProscenioSceneProps`` - sticky export path,
                          atlas packer params, outliner state, validation
                          results collection.
- ``validation_issue.py`` ``ProscenioValidationIssue`` - one element of
                          the scene-level validation results collection.
- ``_handlers.py``        persistent ``bpy.app.handlers`` (load_post,
                          save_pre) + the deferred-hydrate timer job.
- ``_dynamic_items.py``   EnumProperty dynamic-items callbacks +
                          PointerProperty poll filters + the GC-pinning
                          items cache.

Registration order matters: ``ProscenioValidationIssue`` must register
before ``ProscenioSceneProps`` because the latter has a CollectionProperty
of the former.
"""

from __future__ import annotations

import contextlib

import bpy
from bpy.props import PointerProperty
from bpy.types import Object as _Object
from bpy.types import Scene

from ..core.hydrate import (  # type: ignore[import-not-found]
    OBJECT_PROPS as _OBJECT_PROPS,  # noqa: F401
)
from ._handlers import (
    deferred_hydrate,
    on_blend_load,
    on_blend_save_pre,
    on_depsgraph_update,
)
from .object_props import ProscenioObjectProps
from .scene_props import (
    ProscenioQuickArmatureProps,
    ProscenioSceneProps,
    ProscenioSkinningProps,
)
from .validation_issue import ProscenioValidationIssue

_classes: tuple[type, ...] = (
    ProscenioObjectProps,
    ProscenioValidationIssue,
    ProscenioQuickArmatureProps,
    ProscenioSkinningProps,
    ProscenioSceneProps,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)
    _Object.proscenio = PointerProperty(type=ProscenioObjectProps)
    Scene.proscenio = PointerProperty(type=ProscenioSceneProps)
    if on_blend_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(on_blend_load)
    if on_blend_save_pre not in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(on_blend_save_pre)
    if on_depsgraph_update not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update)
    # Defer hydration to the next tick. Two reasons:
    #   1. During initial Blender startup, bpy.data is _RestrictData here.
    #   2. Mid-session enable: PointerProperty wiring stabilizes only
    #      after register() returns. Setting PropertyGroup fields inline
    #      writes to a transient stub that drops before the data block
    #      is committed.
    # Guard against duplicate registration so reload-the-addon does not
    # pile up timers; a residual timer would fire after Scene.proscenio
    # has been deleted in unregister().
    if not bpy.app.timers.is_registered(deferred_hydrate):
        bpy.app.timers.register(deferred_hydrate, first_interval=0.0)


def unregister() -> None:
    # Pull the deferred hydrate timer first so a pending tick does not
    # fire against a half-torn-down PropertyGroup.
    if bpy.app.timers.is_registered(deferred_hydrate):
        bpy.app.timers.unregister(deferred_hydrate)
    if on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update)
    if on_blend_save_pre in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(on_blend_save_pre)
    if on_blend_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(on_blend_load)
    if hasattr(Scene, "proscenio"):
        del Scene.proscenio
    if hasattr(_Object, "proscenio"):
        del _Object.proscenio
    for cls in reversed(_classes):
        with contextlib.suppress(RuntimeError):
            bpy.utils.unregister_class(cls)
