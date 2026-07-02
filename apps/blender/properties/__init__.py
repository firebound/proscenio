"""Proscenio property groups.

These property groups expose typed widgets for the addon panel. The
per-Object fields that the writer reads store their value in a single
home - the ``proscenio_*`` Custom Property - and surface in the panel
through a ``get=``/``set=`` proxy over that idprop (see ``object_props``).

Contract:

- The CP-canonical fields read and write the Custom Property the writer
  reads; the PropertyGroup proxy is the typed editor widget over it.
- The PG-canonical fields (pixel art, atlas flags, the driver picker,
  outliner favorite) store in the PropertyGroup only - pure GUI state.
- There is no mirror and no hydrate: one field, one storage home, so
  nothing is copied at load or save time.

Submodules per concern:

- ``object_props.py``     ``ProscenioObjectProps`` + EnumProperty items
                          tuples (sprite type, region mode, driver target,
                          driver source axis) + the idprop get/set proxies.
- ``bone_props.py``       ``ProscenioBoneProps`` - per-bone GUI state
                          (Skeleton-list favorite), registered on
                          ``bpy.types.Bone``.
- ``scene_props.py``      ``ProscenioSceneProps`` - sticky export path,
                          atlas packer params, outliner state, validation
                          results collection.
- ``validation_issue.py`` ``ProscenioValidationIssue`` - one element of
                          the scene-level validation results collection.
- ``_handlers.py``        persistent ``bpy.app.handlers`` (load_post
                          armature auto-fill, depsgraph hygiene).
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
from bpy.types import Bone as _Bone
from bpy.types import Object as _Object
from bpy.types import Scene

from ._handlers import (
    on_blend_load,
    on_depsgraph_update,
)
from .bone_props import ProscenioBoneProps
from .object_props import ProscenioObjectProps
from .scene_props import (
    ProscenioAuthoringProps,
    ProscenioAutomeshProps,
    ProscenioBindProps,
    ProscenioDebugProps,
    ProscenioQuickArmatureProps,
    ProscenioSceneProps,
    ProscenioSkinningProps,
)
from .validation_issue import ProscenioValidationIssue

_classes: tuple[type, ...] = (
    ProscenioObjectProps,
    ProscenioBoneProps,
    ProscenioValidationIssue,
    ProscenioQuickArmatureProps,
    # The nested skinning groups must register BEFORE ProscenioSkinningProps,
    # whose PointerProperty fields reference them.
    ProscenioAutomeshProps,
    ProscenioBindProps,
    ProscenioAuthoringProps,
    ProscenioDebugProps,
    ProscenioSkinningProps,
    ProscenioSceneProps,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)
    _Object.proscenio = PointerProperty(type=ProscenioObjectProps)
    _Bone.proscenio = PointerProperty(type=ProscenioBoneProps)
    Scene.proscenio = PointerProperty(type=ProscenioSceneProps)
    if on_blend_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(on_blend_load)
    if on_depsgraph_update not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update)


def unregister() -> None:
    if on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update)
    if on_blend_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(on_blend_load)
    if hasattr(Scene, "proscenio"):
        del Scene.proscenio
    if hasattr(_Bone, "proscenio"):
        del _Bone.proscenio
    if hasattr(_Object, "proscenio"):
        del _Object.proscenio
    for cls in reversed(_classes):
        with contextlib.suppress(RuntimeError):
            bpy.utils.unregister_class(cls)
