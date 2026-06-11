"""Per-Object Proscenio PropertyGroup.

Holds every typed setting that lives on a mesh / Empty: element type,
frame metadata, texture region, slot flags, driver picker.

The EnumProperty items tuples live here too - they are used by exactly
one PropertyGroup, so colocation keeps the Enum value <-> label mapping
next to the field that consumes it.
"""

from __future__ import annotations

from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import Object as _Object
from bpy.types import PropertyGroup

from ._dynamic_items import driver_bone_items, is_armature, on_any_update

ELEMENT_TYPE_ITEMS = (
    ("mesh", "Mesh", "Deformable cutout - Polygon2D vertices + UV (default)", 0),
    (
        "sprite",
        "Sprite",
        "Rigid quad - Sprite2D with hframes x vframes grid (1x1 = static)",
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
    ("frame", "Frame index", "Sprite-frame cell - driven 0..hframes*vframes-1", 0),
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
    """Per-Object Proscenio settings - one PropertyGroup per mesh."""

    element_type: EnumProperty(  # type: ignore[valid-type]
        name="Element type",
        description="Rendering path - Mesh maps to Polygon2D, Sprite maps to Sprite2D",
        items=ELEMENT_TYPE_ITEMS,
        default="mesh",
        update=on_any_update,
    )
    hframes: IntProperty(  # type: ignore[valid-type]
        name="Horizontal frames",
        description="Spritesheet column count (sprite only)",
        default=1,
        min=1,
        soft_max=64,
        update=on_any_update,
    )
    vframes: IntProperty(  # type: ignore[valid-type]
        name="Vertical frames",
        description="Spritesheet row count (sprite only)",
        default=1,
        min=1,
        soft_max=64,
        update=on_any_update,
    )
    frame: IntProperty(  # type: ignore[valid-type]
        name="Initial frame",
        description=(
            "Frame index shown at rest pose (sprite only). Animation tracks override at runtime."
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
    exclude_from_atlas: BoolProperty(  # type: ignore[valid-type]
        name="Exclude from atlas",
        description=(
            "Keep this sprite out of Pack Atlas entirely: it is not packed, "
            "its UVs and material are left untouched, and it ships its own "
            "texture. Use it to keep large or rarely-shared sprites out of the "
            "shared atlas."
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
        default="ROT_Y",
    )
    driver_in_min: FloatProperty(  # type: ignore[valid-type]
        name="Input min",
        description=(
            "Bone-channel value mapped to the output minimum. The default spans "
            "negative rotation so a bone swung back no longer clamps to zero - the "
            "first-contact failure the raw 'var' default produced."
        ),
        default=-1.5708,  # -pi/2 rad (about -90 deg)
        precision=4,
    )
    driver_in_max: FloatProperty(  # type: ignore[valid-type]
        name="Input max",
        description="Bone-channel value mapped to the output maximum.",
        default=1.5708,  # +pi/2 rad (about +90 deg)
        precision=4,
    )
    driver_out_min: FloatProperty(  # type: ignore[valid-type]
        name="Output min",
        description="Target-property value when the bone sits at the input minimum.",
        default=0.0,
        precision=4,
    )
    driver_out_max: FloatProperty(  # type: ignore[valid-type]
        name="Output max",
        description="Target-property value when the bone sits at the input maximum.",
        default=1.0,
        precision=4,
    )
    driver_advanced: BoolProperty(  # type: ignore[valid-type]
        name="Advanced expression",
        description=(
            "Drive from the hand-written expression below instead of the two "
            "ranges. 'var' is the raw bone channel; edit for scaling, offsets, "
            "or branching the two-range map cannot express."
        ),
        default=False,
    )
    driver_expression: StringProperty(  # type: ignore[valid-type]
        name="Driver expression",
        description=(
            "Driver expression (Advanced). 'var' is the raw bone channel. "
            "Built from the two ranges unless Advanced is on; edit in the "
            "Drivers Editor for anything the linear map cannot express."
        ),
        default="var",
    )

    is_outliner_favorite: BoolProperty(  # type: ignore[valid-type]
        name="Outliner favorite",
        description=(
            "Pin this object to the top of the Proscenio outliner (the outliner subpanel). "
            "Toggle 'Show favorites only' on the panel to hide everything else."
        ),
        default=False,
        update=on_any_update,
    )

    is_slot: BoolProperty(  # type: ignore[valid-type]
        name="Is slot anchor",
        description=(
            "When True on an Empty object, marks it as the parent of a slot - "
            "child meshes become attachments, the writer emits a slots[] entry, "
            "and the Godot importer wires a Node2D parent + visible-toggled children."
        ),
        default=False,
        update=on_any_update,
    )
    slot_default: StringProperty(  # type: ignore[valid-type]
        name="Slot default",
        description=(
            "Name of the attachment shown by default when the scene loads. "
            "Empty string defers to the first child mesh by sorted name."
        ),
        default="",
        update=on_any_update,
    )
