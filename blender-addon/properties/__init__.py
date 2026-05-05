"""Proscenio property groups (SPEC 005).

These property groups expose typed widgets for the addon panel. Their
values round-trip with the legacy Custom Properties on the same data
block so users who authored a `.blend` before SPEC 005 see existing
values without manual re-entry, and power users can keep editing raw
Custom Properties if they prefer.

Contract:
- The PropertyGroup is the editor-side source of truth (typed, validated,
  surfaced in the panel).
- Each property has an `update` callback that mirrors the value to the
  Custom Property the writer reads (`proscenio_type`, etc.).
- On `register()`, every existing Custom Property is hydrated into the
  PropertyGroup so legacy data shows up in the new UI.
"""

from __future__ import annotations

import contextlib
from typing import Any

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import Object as _Object
from bpy.types import PropertyGroup, Scene

from ..core.hydrate import (  # type: ignore[import-not-found]
    OBJECT_PROPS as _OBJECT_PROPS,  # noqa: F401
)
from ..core.hydrate import (
    hydrate_object,
)

SPRITE_TYPE_ITEMS = (
    ("polygon", "Polygon", "Cutout-style sprite — Polygon2D vertices + UV (default)", 0),
    (
        "sprite_frame",
        "Sprite Frame",
        "Spritesheet sprite — Sprite2D with hframes x vframes grid",
        1,
    ),
)

REGION_MODE_ITEMS = (
    (
        "auto",
        "Auto",
        "Compute texture_region from the mesh's UV bounds at export time (default)",
        0,
    ),
    (
        "manual",
        "Manual",
        "Use the explicit region_x/y/w/h fields on this Object instead of UV bounds",
        1,
    ),
)


def _mirror_to_object(prop_name: str, obj: _Object, value: Any) -> None:
    """Write a PropertyGroup value back to the legacy Custom Property."""
    obj[prop_name] = value


def _on_sprite_type_update(self: ProscenioObjectProps, context: bpy.types.Context) -> None:
    obj = context.active_object
    if obj is not None:
        _mirror_to_object("proscenio_type", obj, self.sprite_type)


def _on_hframes_update(self: ProscenioObjectProps, context: bpy.types.Context) -> None:
    obj = context.active_object
    if obj is not None:
        _mirror_to_object("proscenio_hframes", obj, int(self.hframes))


def _on_vframes_update(self: ProscenioObjectProps, context: bpy.types.Context) -> None:
    obj = context.active_object
    if obj is not None:
        _mirror_to_object("proscenio_vframes", obj, int(self.vframes))


def _on_frame_update(self: ProscenioObjectProps, context: bpy.types.Context) -> None:
    obj = context.active_object
    if obj is not None:
        _mirror_to_object("proscenio_frame", obj, int(self.frame))


def _on_centered_update(self: ProscenioObjectProps, context: bpy.types.Context) -> None:
    obj = context.active_object
    if obj is not None:
        _mirror_to_object("proscenio_centered", obj, bool(self.centered))


class ProscenioObjectProps(PropertyGroup):
    """Per-Object Proscenio settings — one PropertyGroup per mesh."""

    sprite_type: EnumProperty(  # type: ignore[valid-type]
        name="Sprite type",
        description="Rendering path for this sprite — see SPEC 002",
        items=SPRITE_TYPE_ITEMS,
        default="polygon",
        update=_on_sprite_type_update,
    )
    hframes: IntProperty(  # type: ignore[valid-type]
        name="Horizontal frames",
        description="Spritesheet column count (sprite_frame only)",
        default=1,
        min=1,
        soft_max=64,
        update=_on_hframes_update,
    )
    vframes: IntProperty(  # type: ignore[valid-type]
        name="Vertical frames",
        description="Spritesheet row count (sprite_frame only)",
        default=1,
        min=1,
        soft_max=64,
        update=_on_vframes_update,
    )
    frame: IntProperty(  # type: ignore[valid-type]
        name="Initial frame",
        description="Frame index shown at rest pose (sprite_frame only). "
        "Animation tracks override at runtime.",
        default=0,
        min=0,
        update=_on_frame_update,
    )
    centered: BoolProperty(  # type: ignore[valid-type]
        name="Centered",
        description="Whether the Sprite2D's offset centers on its origin",
        default=True,
        update=_on_centered_update,
    )
    region_mode: EnumProperty(  # type: ignore[valid-type]
        name="Region mode",
        description=(
            "How `texture_region` is decided at export. "
            "Auto recomputes from UV bounds every export; "
            "Manual writes region_x/y/w/h verbatim."
        ),
        items=REGION_MODE_ITEMS,
        default="auto",
    )
    region_x: FloatProperty(  # type: ignore[valid-type]
        name="X",
        description="Region origin X (manual mode). Normalized [0,1] of atlas width.",
        default=0.0,
        min=0.0,
        max=1.0,
        precision=4,
    )
    region_y: FloatProperty(  # type: ignore[valid-type]
        name="Y",
        description="Region origin Y (manual mode). Normalized [0,1] of atlas height.",
        default=0.0,
        min=0.0,
        max=1.0,
        precision=4,
    )
    region_w: FloatProperty(  # type: ignore[valid-type]
        name="Width",
        description="Region width (manual mode). Normalized [0,1] of atlas width.",
        default=1.0,
        min=0.0,
        max=1.0,
        precision=4,
    )
    region_h: FloatProperty(  # type: ignore[valid-type]
        name="Height",
        description="Region height (manual mode). Normalized [0,1] of atlas height.",
        default=1.0,
        min=0.0,
        max=1.0,
        precision=4,
    )


class ProscenioValidationIssue(PropertyGroup):
    """A single validation finding stored on the scene for the panel to render."""

    severity: StringProperty(  # type: ignore[valid-type]
        name="Severity",
        default="warning",
        description="One of 'error' or 'warning'",
    )
    message: StringProperty(  # type: ignore[valid-type]
        name="Message",
        default="",
    )
    obj_name: StringProperty(  # type: ignore[valid-type]
        name="Object",
        default="",
        description="Name of the offending object (empty if scene-wide)",
    )


class ProscenioSceneProps(PropertyGroup):
    """Scene-level Proscenio settings — sticky export path, default ppu."""

    last_export_path: StringProperty(  # type: ignore[valid-type]
        name="Last export path",
        description="Sticky destination for one-click re-export. "
        "Saved with the .blend so the document carries its export target.",
        subtype="FILE_PATH",
        default="",
    )
    pixels_per_unit: FloatProperty(  # type: ignore[valid-type]
        name="Pixels per unit",
        description="Conversion ratio between Blender units and Godot pixels",
        default=100.0,
        min=0.0001,
    )
    validation_results: CollectionProperty(  # type: ignore[valid-type]
        type=ProscenioValidationIssue,
    )
    validation_ran: BoolProperty(  # type: ignore[valid-type]
        name="Validation ran",
        default=False,
        description="True after the user has run Validate at least once this session",
    )
    active_action_index: IntProperty(  # type: ignore[valid-type]
        name="Active action",
        description="Selected row in the Animation panel's action list",
        default=0,
        min=0,
    )


def _hydrate_existing_objects() -> None:
    """Walk every object in the current ``bpy.data`` and hydrate.

    During Blender's initial startup, ``bpy.data`` is wrapped in
    ``_RestrictData`` and accessing ``.objects`` raises
    ``AttributeError``. The function bails out silently in that case;
    the ``load_post`` handler retries once the current `.blend` finishes
    loading.
    """
    try:
        objects = list(bpy.data.objects)
    except AttributeError:
        return
    for obj in objects:
        hydrate_object(obj)


@bpy.app.handlers.persistent  # type: ignore[untyped-decorator]
def _on_blend_load(_filepath: str) -> None:
    """Re-hydrate every time a `.blend` finishes loading.

    Persists across Blender's internal reloads so the handler does not
    drop off when the user opens a different file.
    """
    _hydrate_existing_objects()


def _deferred_hydrate() -> None:
    """Run hydration one tick after register().

    Blender's PointerProperty wiring is not fully established the moment
    register() returns — assigning to the PropertyGroup inside register
    sometimes writes to a stub that is dropped before the data block is
    materialized. A zero-interval timer schedules the hydration for
    after the addon-enable cycle completes, when the property data is
    real and persistent.
    """
    _hydrate_existing_objects()


_classes: tuple[type, ...] = (
    ProscenioObjectProps,
    ProscenioValidationIssue,
    ProscenioSceneProps,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)
    _Object.proscenio = PointerProperty(type=ProscenioObjectProps)
    Scene.proscenio = PointerProperty(type=ProscenioSceneProps)
    if _on_blend_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_blend_load)
    # Defer hydration to the next tick. Two reasons:
    #   1. During initial Blender startup, bpy.data is _RestrictData here.
    #   2. Mid-session enable: PointerProperty wiring stabilizes only
    #      after register() returns. Setting PropertyGroup fields inline
    #      writes to a transient stub that drops before the data block is
    #      committed.
    bpy.app.timers.register(_deferred_hydrate, first_interval=0.0)


def unregister() -> None:
    if _on_blend_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_blend_load)
    if hasattr(Scene, "proscenio"):
        del Scene.proscenio
    if hasattr(_Object, "proscenio"):
        del _Object.proscenio
    for cls in reversed(_classes):
        with contextlib.suppress(RuntimeError):
            bpy.utils.unregister_class(cls)
