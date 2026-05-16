"""Scene-level Proscenio PropertyGroup (SPEC 009 wave 9.10).

Holds per-scene settings that ride along with the .blend: sticky
export path, default pixels-per-unit, validation result rows, atlas
packer parameters, outliner state.
"""

from __future__ import annotations

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
from bpy.types import PropertyGroup

from .validation_issue import ProscenioValidationIssue


def _is_armature(_self: PropertyGroup, obj: _Object) -> bool:
    """PointerProperty poll: only Armature objects qualify as targets."""
    return bool(obj.type == "ARMATURE")


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


class ProscenioSkinningProps(PropertyGroup):
    """SPEC 013 Wave 13.1 defaults for the Skinning subpanel.

    Holds the knobs that the Automesh + Bind + Edit Weights
    operators read at invoke time. Stored on the scene so the
    settings persist across .blend reloads and surface in the
    panel for in-context tuning (matching the SPEC 012 D15
    pattern for Quick Armature defaults).
    """

    automesh_resolution: FloatProperty(  # type: ignore[valid-type]
        name="Mesh resolution",
        description=(
            "Image downscale factor for the alpha contour walker. "
            "1.0 = full image, 0.25 = quarter-pixel (default - safe "
            "for typical HD sprites). Lower values produce more "
            "vertices but cost quadratically more time."
        ),
        default=0.25,
        min=0.01,
        max=1.0,
    )
    automesh_alpha_threshold: IntProperty(  # type: ignore[valid-type]
        name="Alpha threshold",
        description=(
            "Pixels with alpha strictly above this value contribute "
            "to the silhouette. 127 matches COA Tools 2 default."
        ),
        default=127,
        min=0,
        max=255,
    )
    automesh_margin_pixels: IntProperty(  # type: ignore[valid-type]
        name="Boundary margin",
        description=(
            "Dilate (outer) / erode (inner) the contour by this many "
            "pixels. Controls annulus thickness - higher values give "
            "thicker silhouette ring of edge loops. Zero falls back "
            "to a single-contour flat triangulation."
        ),
        default=5,
        min=0,
        max=100,
    )
    automesh_contour_vertices: IntProperty(  # type: ignore[valid-type]
        name="Contour vertices",
        description=(
            "Target vertex count for the outer contour after Laplacian "
            "smoothing + arc-length resampling. Inner contour uses "
            "half this count. Higher = smoother silhouette + more "
            "deformation control + more triangles."
        ),
        default=64,
        min=8,
        max=512,
    )
    automesh_interior_spacing: FloatProperty(  # type: ignore[valid-type]
        name="Interior spacing",
        description=(
            "World-unit spacing for the interior Steiner-point grid "
            "fed into bmesh.ops.triangle_fill. Lower = denser interior "
            "= more triangles that can deform under bone influence. "
            "Tune against the sprite's world-unit scale (pixels per unit "
            "in the scene props)."
        ),
        default=0.1,
        min=0.001,
        soft_max=2.0,
    )
    automesh_density_under_bones: BoolProperty(  # type: ignore[valid-type]
        name="Density follows bones",
        description=(
            "When ON and the picker armature has deform bones, add "
            "extra interior triangles near each bone segment so the "
            "mesh has more density where deformation actually happens. "
            "OFF falls back to uniform interior density."
        ),
        default=True,
    )
    automesh_bone_radius: FloatProperty(  # type: ignore[valid-type]
        name="Bone influence radius",
        description=(
            "World-unit radius around each bone segment within which "
            "the density-under-bones subdivision applies."
        ),
        default=0.5,
        min=0.01,
        soft_max=5.0,
    )
    automesh_bone_factor: IntProperty(  # type: ignore[valid-type]
        name="Bone density factor",
        description=(
            "Multiplier for interior point density near bones. "
            "1 = same as uniform, 2 = double, 4 = quadruple. Diminishing "
            "returns above 4."
        ),
        default=2,
        min=1,
        max=8,
    )
    debug_stage: EnumProperty(  # type: ignore[valid-type]
        name="Debug stage",
        description=(
            "Stop the automesh pipeline at the named stage + emit a "
            "wireframe companion object into the Proscenio.Debug "
            "collection so the user can inspect intermediate output. "
            "Off / Final run the full pipeline normally; non-final "
            "stages skip the bmesh write into the active sprite"
        ),
        items=[
            ("off", "Off", "Run the full pipeline, no debug companions"),
            (
                "raw_contours",
                "1 - Raw contours",
                "Stop after Moore Neighbour tracing + world conversion; "
                "shows pixel-stair contours before any smoothing",
            ),
            (
                "smoothed",
                "2 - Smoothed",
                "Stop after Laplacian smoothing of the raw contours",
            ),
            (
                "resampled",
                "3 - Resampled",
                "Stop after arc-length resampling; these are the actual verts that enter the bmesh",
            ),
            (
                "interior_points",
                "4 - Interior points",
                "Stop after generating Steiner interior points (uniform grid + bone-aware density)",
            ),
            (
                "bridges",
                "5 - Bridges",
                "Stop after computing radial bridge offset; shows the "
                "outer + inner verts + planned bridge edges (no fill)",
            ),
            (
                "fill_no_interior",
                "6 - Triangle fill (no interior)",
                "Stop after bmesh.ops.triangle_fill; mesh shows the "
                "strip annulus before interior Steiner points are inserted",
            ),
            (
                "final",
                "Final",
                "Run the full pipeline AND clear any prior debug companions for the sprite",
            ),
        ],
        default="off",
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
    skinning: PointerProperty(  # type: ignore[valid-type]
        type=ProscenioSkinningProps,
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
