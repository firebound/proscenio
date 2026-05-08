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
from ..core.mirror import (  # type: ignore[import-not-found]
    mirror_all_fields,
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

DRIVER_TARGET_ITEMS = (
    ("frame", "Frame index", "Sprite-frame cell — driven 0..hframes*vframes-1", 0),
    ("region_x", "Region X", "Texture region origin X (0..1)", 1),
    ("region_y", "Region Y", "Texture region origin Y (0..1)", 2),
    ("region_w", "Region W", "Texture region width (0..1)", 3),
    ("region_h", "Region H", "Texture region height (0..1)", 4),
)

DRIVER_SOURCE_AXIS_ITEMS = (
    ("ROT_Z", "Bone Rot Z", "Pose bone local rotation around Z (typical 2D plane)", 0),
    ("ROT_X", "Bone Rot X", "Pose bone local rotation around X", 1),
    ("ROT_Y", "Bone Rot Y", "Pose bone local rotation around Y", 2),
    ("LOC_X", "Bone Loc X", "Pose bone local translation X", 3),
    ("LOC_Y", "Bone Loc Y", "Pose bone local translation Y", 4),
    ("LOC_Z", "Bone Loc Z", "Pose bone local translation Z", 5),
)


def _is_armature(_self: object, obj: bpy.types.Object) -> bool:
    """PointerProperty poll: only allow ARMATURE objects in the picker."""
    return obj.type == "ARMATURE"


def _on_any_update(self: ProscenioObjectProps, context: bpy.types.Context) -> None:
    """Mirror every field on any panel edit.

    Bug fix (post-005.1.c.1): individual per-field callbacks left the CP
    set partial — defaults never fired their callback, so Reload Scripts
    restored only the field the user touched. Mirroring all 10 fields on
    every update keeps the CP snapshot complete after the first interaction.
    """
    obj = context.active_object
    if obj is not None:
        mirror_all_fields(self, obj)


class ProscenioObjectProps(PropertyGroup):
    """Per-Object Proscenio settings — one PropertyGroup per mesh."""

    sprite_type: EnumProperty(  # type: ignore[valid-type]
        name="Sprite type",
        description="Rendering path for this sprite — see SPEC 002",
        items=SPRITE_TYPE_ITEMS,
        default="polygon",
        update=_on_any_update,
    )
    hframes: IntProperty(  # type: ignore[valid-type]
        name="Horizontal frames",
        description="Spritesheet column count (sprite_frame only)",
        default=1,
        min=1,
        soft_max=64,
        update=_on_any_update,
    )
    vframes: IntProperty(  # type: ignore[valid-type]
        name="Vertical frames",
        description="Spritesheet row count (sprite_frame only)",
        default=1,
        min=1,
        soft_max=64,
        update=_on_any_update,
    )
    frame: IntProperty(  # type: ignore[valid-type]
        name="Initial frame",
        description="Frame index shown at rest pose (sprite_frame only). "
        "Animation tracks override at runtime.",
        default=0,
        min=0,
        update=_on_any_update,
    )
    centered: BoolProperty(  # type: ignore[valid-type]
        name="Centered",
        description="Whether the Sprite2D's offset centers on its origin",
        default=True,
        update=_on_any_update,
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
        update=_on_any_update,
    )
    region_x: FloatProperty(  # type: ignore[valid-type]
        name="X",
        description="Region origin X (manual mode). Normalized [0,1] of atlas width.",
        default=0.0,
        min=0.0,
        max=1.0,
        precision=4,
        update=_on_any_update,
    )
    region_y: FloatProperty(  # type: ignore[valid-type]
        name="Y",
        description="Region origin Y (manual mode). Normalized [0,1] of atlas height.",
        default=0.0,
        min=0.0,
        max=1.0,
        precision=4,
        update=_on_any_update,
    )
    region_w: FloatProperty(  # type: ignore[valid-type]
        name="Width",
        description="Region width (manual mode). Normalized [0,1] of atlas width.",
        default=1.0,
        min=0.0,
        max=1.0,
        precision=4,
        update=_on_any_update,
    )
    region_h: FloatProperty(  # type: ignore[valid-type]
        name="Height",
        description="Region height (manual mode). Normalized [0,1] of atlas height.",
        default=1.0,
        min=0.0,
        max=1.0,
        precision=4,
        update=_on_any_update,
    )
    material_isolated: BoolProperty(  # type: ignore[valid-type]
        name="Isolated material",
        description=(
            "When packing, keep this sprite's own material instead of linking "
            "it to the shared 'Proscenio.PackedAtlas' material. Useful for "
            "effect sprites that need their own shader (additive blend, custom "
            "fresnel, etc)."
        ),
        default=False,
        update=_on_any_update,
    )

    driver_target: EnumProperty(  # type: ignore[valid-type]
        name="Driver target",
        description="Sprite proscenio property the driver writes to",
        items=DRIVER_TARGET_ITEMS,
        default="region_x",
    )
    driver_source_armature: PointerProperty(  # type: ignore[valid-type]
        name="Driver armature",
        description="Armature whose pose bone supplies the driver value",
        type=_Object,
        poll=_is_armature,
    )
    driver_source_bone: StringProperty(  # type: ignore[valid-type]
        name="Driver bone",
        description="Pose bone whose transform feeds the driver",
        default="",
    )
    driver_source_axis: EnumProperty(  # type: ignore[valid-type]
        name="Driver axis",
        description="Pose bone transform channel feeding the driver",
        items=DRIVER_SOURCE_AXIS_ITEMS,
        default="ROT_Z",
    )
    driver_expression: StringProperty(  # type: ignore[valid-type]
        name="Driver expression",
        description=(
            "Driver expression. 'var' is the raw bone channel; "
            "edit in the Drivers Editor for scaling, offsets, branching."
        ),
        default="var",
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
    active_bone_index: IntProperty(  # type: ignore[valid-type]
        name="Active bone",
        description="Selected row in the Skeleton panel's bone list",
        default=0,
        min=0,
    )
    pack_padding_px: IntProperty(  # type: ignore[valid-type]
        name="Pack padding",
        description="Pixels of padding reserved around each sprite in the packed atlas",
        default=2,
        min=0,
        max=64,
    )
    pack_max_size: IntProperty(  # type: ignore[valid-type]
        name="Pack max size",
        description="Hard cap on the packed atlas dimensions (px). Pack fails above this.",
        default=4096,
        min=64,
        max=8192,
    )
    pack_pot: BoolProperty(  # type: ignore[valid-type]
        name="Power-of-two atlas",
        description="Round packed atlas dimensions up to a power of two (legacy GPU optimization)",
        default=False,
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


@bpy.app.handlers.persistent  # type: ignore[untyped-decorator]
def _on_blend_save_pre(_filepath: str) -> None:
    """Flush every PropertyGroup field to its Custom Property mirror before save.

    Bug fix (post-005.1.c.1): callbacks only fire on user interaction, so
    `.blend` files can be saved with a partial Custom Property snapshot if
    the user authored values via Python / drivers / handlers without going
    through the panel. The save handler walks every object with a Proscenio
    PropertyGroup and writes all 10 mirror fields, guaranteeing the saved
    `.blend` round-trips cleanly through Reload Scripts.
    """
    try:
        objects = list(bpy.data.objects)
    except AttributeError:
        return
    for obj in objects:
        props = getattr(obj, "proscenio", None)
        if props is None:
            continue
        mirror_all_fields(props, obj)


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
    if _on_blend_save_pre not in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(_on_blend_save_pre)
    # Defer hydration to the next tick. Two reasons:
    #   1. During initial Blender startup, bpy.data is _RestrictData here.
    #   2. Mid-session enable: PointerProperty wiring stabilizes only
    #      after register() returns. Setting PropertyGroup fields inline
    #      writes to a transient stub that drops before the data block is
    #      committed.
    bpy.app.timers.register(_deferred_hydrate, first_interval=0.0)


def unregister() -> None:
    if _on_blend_save_pre in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(_on_blend_save_pre)
    if _on_blend_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_blend_load)
    if hasattr(Scene, "proscenio"):
        del Scene.proscenio
    if hasattr(_Object, "proscenio"):
        del _Object.proscenio
    for cls in reversed(_classes):
        with contextlib.suppress(RuntimeError):
            bpy.utils.unregister_class(cls)
