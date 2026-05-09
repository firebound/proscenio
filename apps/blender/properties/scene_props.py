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
    StringProperty,
)
from bpy.types import PropertyGroup

from .validation_issue import ProscenioValidationIssue


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
