"""Scene-level Proscenio PropertyGroup (SPEC 009 wave 9.10).

Holds per-scene settings that ride along with the .blend: sticky
export path, default pixels-per-unit, validation result rows, atlas
packer parameters, outliner state.
"""

from __future__ import annotations

from bpy.props import (
    BoolProperty,
    CollectionProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import Object as _Object
from bpy.types import PropertyGroup

from .validation_issue import ProscenioValidationIssue


def _is_armature(_self: PropertyGroup, obj: _Object) -> bool:
    """PointerProperty poll: only Armature objects qualify as targets."""
    return obj.type == "ARMATURE"


class ProscenioQuickArmatureProps(PropertyGroup):
    """SPEC 012 Wave 12.2 defaults for the Quick Armature modal."""

    lock_to_front_ortho: BoolProperty(  # type: ignore[valid-type]
        name="Lock to Front Orthographic",
        description=(
            "On invoke, snap the active 3D viewport to Front Orthographic so "
            "bones land on the Y=0 picture plane. Restores the prior view on "
            "exit when the user has not orbited mid-modal."
        ),
        default=True,
    )
    name_prefix: StringProperty(  # type: ignore[valid-type]
        name="Bone name prefix",
        description=(
            "Prefix for auto-named bones (e.g. 'def' produces 'def.000', "
            "'def.001'). Whitespace is stripped; empty falls back to 'qbone'."
        ),
        default="qbone",
    )
    default_chain: BoolProperty(  # type: ignore[valid-type]
        name="Default = chain connected",
        description=(
            "When ON (recommended), no-modifier drag chains the new bone to "
            "the last one (head snaps to parent's tail, matches Blender's E "
            "extrude reflex). Hold Shift to start a new root instead. When "
            "OFF, the legacy SPEC 012.1 vocabulary applies: no-modifier = "
            "unparented root, Shift = chain (no connect)."
        ),
        default=True,
    )
    snap_increment: FloatProperty(  # type: ignore[valid-type]
        name="Snap increment",
        description=(
            "World-unit grid step applied while Ctrl is held during drag. "
            "Set to 1.0 to align bones to whole world units (matches PPU=100 "
            "pixel-perfect cutout authoring)."
        ),
        default=1.0,
        min=0.001,
        soft_max=10.0,
    )


class ProscenioSceneProps(PropertyGroup):
    """Scene-level Proscenio settings - sticky export path, default ppu."""

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
    quick_armature: PointerProperty(  # type: ignore[valid-type]
        type=ProscenioQuickArmatureProps,
    )
    active_armature: PointerProperty(  # type: ignore[valid-type]
        name="Active armature",
        description=(
            "The armature every Proscenio skeleton operation targets - "
            "Quick Armature appends bones here, IK / pose helpers act on "
            "this rig, and the writer exports it. Set explicitly via the "
            "Skeleton subpanel to avoid surprises in scenes with more "
            "than one armature; if unset, the operators auto-detect a "
            "sensible target (active object > single scene armature > "
            "Proscenio.QuickRig fallback)."
        ),
        type=_Object,
        poll=_is_armature,
    )
