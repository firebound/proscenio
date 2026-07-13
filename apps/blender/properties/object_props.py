"""Per-Object Proscenio PropertyGroup.

Holds every typed setting that lives on a mesh / Empty: element type,
frame metadata, texture region, slot flags, driver picker.

Storage has one home per field (spec 037):

- **Custom-Property-canonical** fields (``element_type``, ``hframes``,
  ``vframes``, ``frame``, ``centered``, the region fields, ``y_draw_order``,
  ``is_slot``, ``slot_default``, ``slot_bone``) store their value in the
  ``proscenio_*`` Custom Property (idprop) the headless writer reads. The
  PropertyGroup field is a typed ``get=``/``set=`` proxy over that idprop -
  it keeps the panel widget (labels, ranges, descriptions) but stores
  nothing itself. Animatable / driver-target fields (``frame``, the region
  fields) keyframe and drive on the idprop directly, because Blender cannot
  keyframe a field nested inside a PropertyGroup.
- **PropertyGroup-canonical** fields (``pixel_art``, ``material_isolated``,
  ``exclude_from_atlas``, the driver picker, ``is_outliner_favorite``) are
  pure GUI / operator state the headless writer never reads. They store in
  the PropertyGroup only - no idprop, no mirror.

The EnumProperty items tuples live here too - they are used by exactly
one PropertyGroup, so colocation keeps the Enum value <-> label mapping
next to the field that consumes it.
"""

from __future__ import annotations

import bpy
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

from ..core._shared import cp_keys  # type: ignore[import-not-found]
from ..core._shared.idprop_proxy import (  # type: ignore[import-not-found]
    enum_index_to_value,
    enum_value_to_index,
)
from ..core._shared.material_images import (  # type: ignore[import-not-found]
    set_object_texture_interpolation,
)
from ..core._shared.sprite_grid import clamp_frame_index  # type: ignore[import-not-found]
from ..core.armature.driver_expression import (  # type: ignore[import-not-found]
    DRIVER_SOURCE_AXIS_ITEMS,
)
from ..core.draw_order import y_location_from_draw_order  # type: ignore[import-not-found]
from ._dynamic_items import driver_bone_items, is_armature


def _pixel_art_update(self: ProscenioObjectProps, context: Context) -> None:
    """Flip every image-texture node on the active object to Closest / Linear.

    ``pixel_art`` is authoring-only viewport state: it sets the texture node's
    nearest-neighbor interpolation so pixel art stops bilinear-blurring under
    magnification. It is deliberately NOT stored on an idprop and NOT exported -
    it is PropertyGroup-canonical (pure GUI state). The Godot writer emits no
    ``texture_filter``, so the toggle changes nothing in the ``.proscenio``
    (regression-guarded by ``test_pixel_art_not_exported``).
    """
    obj = context.active_object
    if obj is not None:
        set_object_texture_interpolation(obj, "Closest" if self.pixel_art else "Linear")


# --- Custom-Property-backed proxy accessors --------------------------------
#
# Each CP-canonical field declares a ``get``/``set`` pair below. The getter
# reads the ``proscenio_*`` idprop off ``self.id_data`` (the Object this
# PropertyGroup is rooted on), the setter writes it. There is no recursion:
# the setter writes the idprop, never the proxy field itself, so Blender's
# ``set=``-suppresses-``update=`` rule is moot - the side effects (frame
# clamp, Y position) live in the setters explicitly.

ELEMENT_TYPE_ITEMS = (
    ("mesh", "Mesh", "Deformable cutout - Polygon2D vertices + UV (default)", 0),
    (
        "sprite",
        "Sprite",
        "Rigid quad - Sprite2D with hframes x vframes grid (1x1 = static)",
        1,
    ),
)
_ELEMENT_TYPE_VALUES = tuple(item[0] for item in ELEMENT_TYPE_ITEMS)

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
_REGION_MODE_VALUES = tuple(item[0] for item in REGION_MODE_ITEMS)

DRIVER_TARGET_ITEMS = (
    ("frame", "Frame index", "Sprite-frame cell - driven 0..hframes*vframes-1", 0),
    ("region_x", "Region X", "Texture region origin X (0..1)", 1),
    ("region_y", "Region Y", "Texture region origin Y (0..1)", 2),
    ("region_w", "Region W", "Texture region width (0..1)", 3),
    ("region_h", "Region H", "Texture region height (0..1)", 4),
)


def _get_element_type(self: ProscenioObjectProps) -> int:
    stored = str(_idprop_get(self, cp_keys.PROSCENIO_TYPE, "mesh"))
    return enum_value_to_index(stored, _ELEMENT_TYPE_VALUES)


def _set_element_type(self: ProscenioObjectProps, value: int) -> None:
    _idprop_set(self, cp_keys.PROSCENIO_TYPE, enum_index_to_value(value, _ELEMENT_TYPE_VALUES))


def _get_region_mode(self: ProscenioObjectProps) -> int:
    stored = str(_idprop_get(self, cp_keys.PROSCENIO_REGION_MODE, "auto"))
    return enum_value_to_index(stored, _REGION_MODE_VALUES)


def _set_region_mode(self: ProscenioObjectProps, value: int) -> None:
    _idprop_set(
        self, cp_keys.PROSCENIO_REGION_MODE, enum_index_to_value(value, _REGION_MODE_VALUES)
    )


def _get_hframes(self: ProscenioObjectProps) -> int:
    return max(1, int(_idprop_get(self, cp_keys.PROSCENIO_HFRAMES, 1)))


def _set_hframes(self: ProscenioObjectProps, value: int) -> None:
    _idprop_set(self, cp_keys.PROSCENIO_HFRAMES, max(1, int(value)))
    _reclamp_frame(self)


def _get_vframes(self: ProscenioObjectProps) -> int:
    return max(1, int(_idprop_get(self, cp_keys.PROSCENIO_VFRAMES, 1)))


def _set_vframes(self: ProscenioObjectProps, value: int) -> None:
    _idprop_set(self, cp_keys.PROSCENIO_VFRAMES, max(1, int(value)))
    _reclamp_frame(self)


def _get_frame(self: ProscenioObjectProps) -> int:
    return max(0, int(_idprop_get(self, cp_keys.PROSCENIO_FRAME, 0)))


def _set_frame(self: ProscenioObjectProps, value: int) -> None:
    clamped = clamp_frame_index(int(value), self.hframes, self.vframes)
    _idprop_set(self, cp_keys.PROSCENIO_FRAME, clamped)


def _reclamp_frame(self: ProscenioObjectProps) -> None:
    """Pull a now-out-of-range frame back into the grid after a grid resize.

    Shrinking ``hframes`` / ``vframes`` can leave ``frame`` past the last
    cell; re-clamp it so the writer never emits an index Godot rejects. The
    static ``max=`` cannot express a bound that depends on two other fields.
    """
    current = int(_idprop_get(self, cp_keys.PROSCENIO_FRAME, 0))
    clamped = clamp_frame_index(current, self.hframes, self.vframes)
    if clamped != current:
        _idprop_set(self, cp_keys.PROSCENIO_FRAME, clamped)


def _get_centered(self: ProscenioObjectProps) -> bool:
    return bool(_idprop_get(self, cp_keys.PROSCENIO_CENTERED, True))


def _set_centered(self: ProscenioObjectProps, value: bool) -> None:
    _idprop_set(self, cp_keys.PROSCENIO_CENTERED, bool(value))


def _region_float_get(self: ProscenioObjectProps, cp_key: str, default: float) -> float:
    return float(_idprop_get(self, cp_key, default))


def _region_float_set(self: ProscenioObjectProps, cp_key: str, value: float) -> None:
    _idprop_set(self, cp_key, min(1.0, max(0.0, float(value))))


def _get_region_x(self: ProscenioObjectProps) -> float:
    return _region_float_get(self, cp_keys.PROSCENIO_REGION_X, 0.0)


def _set_region_x(self: ProscenioObjectProps, value: float) -> None:
    _region_float_set(self, cp_keys.PROSCENIO_REGION_X, value)


def _get_region_y(self: ProscenioObjectProps) -> float:
    return _region_float_get(self, cp_keys.PROSCENIO_REGION_Y, 0.0)


def _set_region_y(self: ProscenioObjectProps, value: float) -> None:
    _region_float_set(self, cp_keys.PROSCENIO_REGION_Y, value)


def _get_region_w(self: ProscenioObjectProps) -> float:
    return _region_float_get(self, cp_keys.PROSCENIO_REGION_W, 1.0)


def _set_region_w(self: ProscenioObjectProps, value: float) -> None:
    _region_float_set(self, cp_keys.PROSCENIO_REGION_W, value)


def _get_region_h(self: ProscenioObjectProps) -> float:
    return _region_float_get(self, cp_keys.PROSCENIO_REGION_H, 1.0)


def _set_region_h(self: ProscenioObjectProps, value: float) -> None:
    _region_float_set(self, cp_keys.PROSCENIO_REGION_H, value)


def _get_y_draw_order(self: ProscenioObjectProps) -> int:
    return int(_idprop_get(self, cp_keys.PROSCENIO_Y_DRAW_ORDER, 0))


def _set_y_draw_order(self: ProscenioObjectProps, value: int) -> None:
    """Store the draw-order layer and position the object in Y from it.

    The integer is the authoritative draw order (the writer negates it into
    ``z_index``); the Y position (``order * spacing``) only spreads stacked
    planes in the viewport so they do not z-fight, and never changes the
    export. The spacing comes from the addon preference. Resolves the object
    through ``self.id_data`` so editing from a non-active Outliner row moves
    the correct object. Reads ``bpy.context`` for the preference because a
    ``set=`` callback receives no context argument.
    """
    order = int(value)
    obj = self.id_data
    if obj is None:
        return
    obj[cp_keys.PROSCENIO_Y_DRAW_ORDER] = order
    from ..addon_prefs import y_location_spacing  # local import avoids a register cycle

    obj.location.y = y_location_from_draw_order(order, y_location_spacing(bpy.context))


def _get_is_slot(self: ProscenioObjectProps) -> bool:
    return bool(_idprop_get(self, cp_keys.PROSCENIO_IS_SLOT, False))


def _set_is_slot(self: ProscenioObjectProps, value: bool) -> None:
    _idprop_set(self, cp_keys.PROSCENIO_IS_SLOT, bool(value))


def _get_slot_default(self: ProscenioObjectProps) -> str:
    return str(_idprop_get(self, cp_keys.PROSCENIO_SLOT_DEFAULT, ""))


def _set_slot_default(self: ProscenioObjectProps, value: str) -> None:
    _idprop_set(self, cp_keys.PROSCENIO_SLOT_DEFAULT, str(value))


def _idprop_get(self: ProscenioObjectProps, key: str, default: object) -> object:
    obj = self.id_data
    if obj is None:
        return default
    return obj.get(key, default)


def _idprop_set(self: ProscenioObjectProps, key: str, value: object) -> None:
    obj = self.id_data
    if obj is not None:
        obj[key] = value


class ProscenioObjectProps(PropertyGroup):
    """Per-Object Proscenio settings - one PropertyGroup per mesh."""

    element_type: EnumProperty(  # type: ignore[valid-type]
        name="Element type",
        description="Rendering path - Mesh maps to Polygon2D, Sprite maps to Sprite2D",
        items=ELEMENT_TYPE_ITEMS,
        default="mesh",
        get=_get_element_type,
        set=_set_element_type,
    )
    hframes: IntProperty(  # type: ignore[valid-type]
        name="Horizontal frames",
        description="Spritesheet column count (sprite only)",
        default=1,
        min=1,
        soft_max=64,
        get=_get_hframes,
        set=_set_hframes,
    )
    vframes: IntProperty(  # type: ignore[valid-type]
        name="Vertical frames",
        description="Spritesheet row count (sprite only)",
        default=1,
        min=1,
        soft_max=64,
        get=_get_vframes,
        set=_set_vframes,
    )
    frame: IntProperty(  # type: ignore[valid-type]
        name="Frame",
        description=(
            "Frame index shown at rest pose (sprite only). Animation tracks override at runtime."
        ),
        default=0,
        min=0,
        get=_get_frame,
        set=_set_frame,
    )
    centered: BoolProperty(  # type: ignore[valid-type]
        name="Centered",
        description="Whether the Sprite2D's offset centers on its origin",
        default=True,
        get=_get_centered,
        set=_set_centered,
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
        get=_get_region_mode,
        set=_set_region_mode,
    )
    region_x: FloatProperty(  # type: ignore[valid-type]
        name="X",
        description="Region origin X (manual mode). Normalized [0,1] of atlas width.",
        default=0.0,
        min=0.0,
        max=1.0,
        precision=4,
        get=_get_region_x,
        set=_set_region_x,
    )
    region_y: FloatProperty(  # type: ignore[valid-type]
        name="Y",
        description="Region origin Y (manual mode). Normalized [0,1] of atlas height.",
        default=0.0,
        min=0.0,
        max=1.0,
        precision=4,
        get=_get_region_y,
        set=_set_region_y,
    )
    region_w: FloatProperty(  # type: ignore[valid-type]
        name="Width",
        description="Region width (manual mode). Normalized [0,1] of atlas width.",
        default=1.0,
        min=0.0,
        max=1.0,
        precision=4,
        get=_get_region_w,
        set=_set_region_w,
    )
    region_h: FloatProperty(  # type: ignore[valid-type]
        name="Height",
        description="Region height (manual mode). Normalized [0,1] of atlas height.",
        default=1.0,
        min=0.0,
        max=1.0,
        precision=4,
        get=_get_region_h,
        set=_set_region_h,
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
        get=_get_y_draw_order,
        set=_set_y_draw_order,
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
    )

    is_slot: BoolProperty(  # type: ignore[valid-type]
        name="Is slot anchor",
        description=(
            "When True on an Empty object, marks it as the parent of a slot - "
            "child meshes become attachments, the writer emits a slots[] entry, "
            "and the Godot importer wires a Node2D parent + visible-toggled children."
        ),
        default=False,
        get=_get_is_slot,
        set=_set_is_slot,
    )
    slot_default: StringProperty(  # type: ignore[valid-type]
        name="Slot default",
        description=(
            "Name of the attachment shown by default when the scene loads. "
            "Empty string defers to the first child mesh by sorted name."
        ),
        default="",
        get=_get_slot_default,
        set=_set_slot_default,
    )
    # `slot_bone` retired (spec 080 D5): the Proscenio Child Of constraint is
    # the binding's single source of truth - the writer and the panel read its
    # subtarget directly, with the legacy `proscenio_slot_bone` idprop kept as
    # a read-fallback for pre-080 files only.
