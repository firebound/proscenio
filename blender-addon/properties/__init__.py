"""Proscenio property groups (SPEC 005, repackaged in SPEC 009 wave 9.7).

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

Submodules per concern:

- ``_handlers.py``       persistent ``bpy.app.handlers`` (load_post,
                         save_pre) + the deferred-hydrate timer job.
- ``_dynamic_items.py``  EnumProperty dynamic-items callbacks +
                         PointerProperty poll filters + the GC-pinning
                         items cache.

The PropertyGroup classes live here because their order of definition
+ their cross-references to ``_dynamic_items`` callbacks is tightest
when colocated.
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
from ._dynamic_items import driver_bone_items, is_armature, on_any_update
from ._handlers import deferred_hydrate, on_blend_load, on_blend_save_pre

SPRITE_TYPE_ITEMS = (
    ("polygon", "Polygon", "Cutout-style sprite -- Polygon2D vertices + UV (default)", 0),
    (
        "sprite_frame",
        "Sprite Frame",
        "Spritesheet sprite -- Sprite2D with hframes x vframes grid",
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
    ("frame", "Frame index", "Sprite-frame cell -- driven 0..hframes*vframes-1", 0),
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


class ProscenioObjectProps(PropertyGroup):
    """Per-Object Proscenio settings -- one PropertyGroup per mesh."""

    sprite_type: EnumProperty(  # type: ignore[valid-type]
        name="Sprite type",
        description="Rendering path for this sprite -- see SPEC 002",
        items=SPRITE_TYPE_ITEMS,
        default="polygon",
        update=on_any_update,
    )
    hframes: IntProperty(  # type: ignore[valid-type]
        name="Horizontal frames",
        description="Spritesheet column count (sprite_frame only)",
        default=1,
        min=1,
        soft_max=64,
        update=on_any_update,
    )
    vframes: IntProperty(  # type: ignore[valid-type]
        name="Vertical frames",
        description="Spritesheet row count (sprite_frame only)",
        default=1,
        min=1,
        soft_max=64,
        update=on_any_update,
    )
    frame: IntProperty(  # type: ignore[valid-type]
        name="Initial frame",
        description=(
            "Frame index shown at rest pose (sprite_frame only). "
            "Animation tracks override at runtime."
        ),
        default=0,
        min=0,
        update=on_any_update,
    )
    centered: BoolProperty(  # type: ignore[valid-type]
        name="Centered",
        description="Whether the Sprite2D's offset centers on its origin",
        default=True,
        update=on_any_update,
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
        update=on_any_update,
    )
    region_x: FloatProperty(  # type: ignore[valid-type]
        name="X",
        description="Region origin X (manual mode). Normalized [0,1] of atlas width.",
        default=0.0,
        min=0.0,
        max=1.0,
        precision=4,
        update=on_any_update,
    )
    region_y: FloatProperty(  # type: ignore[valid-type]
        name="Y",
        description="Region origin Y (manual mode). Normalized [0,1] of atlas height.",
        default=0.0,
        min=0.0,
        max=1.0,
        precision=4,
        update=on_any_update,
    )
    region_w: FloatProperty(  # type: ignore[valid-type]
        name="Width",
        description="Region width (manual mode). Normalized [0,1] of atlas width.",
        default=1.0,
        min=0.0,
        max=1.0,
        precision=4,
        update=on_any_update,
    )
    region_h: FloatProperty(  # type: ignore[valid-type]
        name="Height",
        description="Region height (manual mode). Normalized [0,1] of atlas height.",
        default=1.0,
        min=0.0,
        max=1.0,
        precision=4,
        update=on_any_update,
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
        update=on_any_update,
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
        poll=is_armature,
    )
    driver_source_bone: EnumProperty(  # type: ignore[valid-type]
        name="Driver bone",
        description="Pose bone whose transform feeds the driver",
        items=driver_bone_items,
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

    is_outliner_favorite: BoolProperty(  # type: ignore[valid-type]
        name="Outliner favorite",
        description=(
            "Pin this object to the top of the Proscenio outliner (5.1.d.4). "
            "Toggle 'Show favorites only' on the panel to hide everything else."
        ),
        default=False,
    )

    is_slot: BoolProperty(  # type: ignore[valid-type]
        name="Is slot anchor",
        description=(
            "When True on an Empty object, marks it as the parent of a slot -- "
            "child meshes become attachments, the writer emits a slots[] entry, "
            "and the Godot importer wires a Node2D parent + visible-toggled children."
        ),
        default=False,
    )
    slot_default: StringProperty(  # type: ignore[valid-type]
        name="Slot default",
        description=(
            "Name of the attachment shown by default when the scene loads. "
            "Empty string defers to the first child mesh by sorted name."
        ),
        default="",
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
    """Scene-level Proscenio settings -- sticky export path, default ppu."""

    last_export_path: StringProperty(  # type: ignore[valid-type]
        name="Last export path",
        description=(
            "Sticky destination for one-click re-export. "
            "Saved with the .blend so the document carries its export target."
        ),
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
        description=(
            "Round packed atlas dimensions up to a power of two (legacy GPU optimization)"
        ),
        default=False,
    )
    outliner_filter: StringProperty(  # type: ignore[valid-type]
        name="Outliner filter",
        description=(
            "Substring filter applied to the Proscenio outliner (5.1.d.4). "
            "Empty string shows every Proscenio-relevant object."
        ),
        default="",
    )
    outliner_show_favorites: BoolProperty(  # type: ignore[valid-type]
        name="Favorites only",
        description=(
            "When True, the outliner hides every object except those flagged "
            "via proscenio.is_outliner_favorite."
        ),
        default=False,
    )
    active_outliner_index: IntProperty(  # type: ignore[valid-type]
        name="Active outliner row",
        description="Selected row in the Proscenio outliner UIList",
        default=0,
        min=0,
    )


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
    if on_blend_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(on_blend_load)
    if on_blend_save_pre not in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(on_blend_save_pre)
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
