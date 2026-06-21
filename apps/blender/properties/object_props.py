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
from bpy.types import Context, PropertyGroup
from bpy.types import Object as _Object

from ..core._shared.material_images import (  # type: ignore[import-not-found]
    set_object_texture_interpolation,
)
from ..core._shared.sprite_grid import clamp_frame_index  # type: ignore[import-not-found]
from ..core.armature.driver_expression import (  # type: ignore[import-not-found]
    DRIVER_SOURCE_AXIS_ITEMS,
)
from ..core.mirror import mirror_all_fields  # type: ignore[import-not-found]
from ._dynamic_items import driver_bone_items, is_armature, on_any_update


def _clamp_frame_and_update(self: ProscenioObjectProps, context: Context) -> None:
    """Clamp ``frame`` into the sprite grid, then run the shared mirror update.

    Written through ``self["frame"]`` (the idprop) so it does not re-enter this
    callback. Wired onto ``frame``, ``hframes``, and ``vframes`` so shrinking
    the grid pulls a now-out-of-range initial frame back in - the static
    ``max=`` cannot express a bound that depends on two other fields.
    """
    clamped = clamp_frame_index(self.frame, self.hframes, self.vframes)
    if clamped != int(self.frame):
        self["frame"] = clamped
    on_any_update(self, context)


def _pixel_art_update(self: ProscenioObjectProps, context: Context) -> None:
    """Flip every image-texture node on the active object to Closest / Linear.

    ``pixel_art`` is authoring-only viewport state: it sets the texture node's
    nearest-neighbor interpolation so pixel art stops bilinear-blurring under
    magnification. It is deliberately NOT mirrored to a Custom Property and
    NOT exported - it does not call the shared mirror, and it has no entry in
    ``mirror.OBJECT_MIRROR_MAP`` / ``hydrate.OBJECT_PROPS``. The Godot writer
    emits no ``texture_filter``, so the toggle changes nothing in the
    ``.proscenio`` (regression-guarded by ``test_pixel_art_not_exported``).
    """
    obj = context.active_object
    if obj is not None:
        set_object_texture_interpolation(obj, "Closest" if self.pixel_art else "Linear")


def _y_draw_order_update(self: ProscenioObjectProps, context: Context) -> None:
    """Position the owning object in Y from its draw-order layer, then mirror.

    ``y_draw_order`` is the authoritative draw order: a stored integer that
    doubles as the object's Y position (``order * spacing``) so stacked planes
    separate in the viewport and never z-fight. The writer reads the integer
    directly, so the spacing only spreads planes in Blender - it never changes
    the exported order. The spacing comes from the addon preference (imported
    lazily to avoid an import cycle at registration).

    Resolves the object through ``self.id_data`` (the ID this PropertyGroup is
    rooted on), not the active object, so editing the field from a non-active
    Outliner row moves and mirrors the correct object. Mirrors inline for the
    same reason - the shared ``on_any_update`` keys off the active object.
    """
    obj = self.id_data
    if obj is None:
        return
    from ..addon_prefs import y_location_spacing

    obj.location.y = self.y_draw_order * y_location_spacing(context)
    mirror_all_fields(self, obj)


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
        update=_clamp_frame_and_update,
    )
    vframes: IntProperty(  # type: ignore[valid-type]
        name="Vertical frames",
        description="Spritesheet row count (sprite only)",
        default=1,
        min=1,
        soft_max=64,
        update=_clamp_frame_and_update,
    )
    frame: IntProperty(  # type: ignore[valid-type]
        name="Frame",
        description=(
            "Frame index shown at rest pose (sprite only). Animation tracks override at runtime."
        ),
        default=0,
        min=0,
        update=_clamp_frame_and_update,
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
    y_draw_order: IntProperty(  # type: ignore[valid-type]
        name="Y Location (Draw Order)",
        description=(
            "Draw order of this element as a whole-number layer. In Blender it "
            "sets the object's Y position (this number times the Y Location "
            "spacing in the addon preferences) so stacked planes separate and "
            "do not z-fight; in Godot it sets the Sprite / Polygon draw order "
            "(z_index). Higher pushes the element further back, lower (incl. "
            "negative) pulls it forward. Reorder by editing this number, not by "
            "dragging the object in Y - a manual Y drag is flagged in validation."
        ),
        default=0,
        update=_y_draw_order_update,
    )
    pixel_art: BoolProperty(  # type: ignore[valid-type]
        name="Pixel art",
        description=(
            "Show this element's texture with crisp nearest-neighbor sampling "
            "(Closest interpolation) instead of Blender's bilinear blur "
            "(Linear). Authoring-only viewport state - it sets the interpolation "
            "on every image-texture node of this object's materials and is not "
            "exported. Off by default; the importer leaves new art on Linear."
        ),
        default=False,
        update=_pixel_art_update,
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
            "Flag this object as a favorite in the Proscenio outliner (the outliner subpanel). "
            "Toggle 'Show favorites only' on the panel to hide everything else; "
            "favorites keep their normal category order, they do not move to the top."
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
    slot_bone: StringProperty(  # type: ignore[valid-type]
        name="Slot bone",
        description=(
            "Bone this slot follows. The Godot importer parents the slot Node2D "
            "under that Bone2D so the attachments track the bone (e.g. a weapon "
            "following an arm). Bind to Bone sets this and adds a Child Of "
            "constraint that keeps the flat attachment quads in the picture "
            "plane for any bone orientation. Hand bone-parenting the Empty "
            "(Ctrl+P > Bone) also sets the followed bone and exports, but only "
            "for bones pointing into the screen - an in-plane bone tilts the "
            "quads edge-on. Empty string anchors the slot at the skeleton root."
        ),
        default="",
        update=on_any_update,
    )
