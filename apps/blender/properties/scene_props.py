"""Scene-level Proscenio PropertyGroup.

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
    """Defaults for the Quick Armature modal."""

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
            "OFF, the legacy vocabulary applies: no-modifier = "
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
    """Defaults for the Skinning subpanel.

    Holds the knobs that the Automesh + Bind + Edit Weights
    operators read at invoke time. Stored on the scene so the
    settings persist across .blend reloads and surface in the
    panel for in-context tuning (matching the pattern for the Quick
    Armature defaults).
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
            "to the silhouette. Default 1 includes EVERY visible "
            "pixel (even faint anti-alias edges) - the safe choice "
            "for sprite skinning where losing pixels at the boundary "
            "is unacceptable. Raise to 127 to ignore anti-alias edges "
            "(matches COA Tools 2 convention but cuts AA pixels)."
        ),
        default=1,
        min=0,
        max=255,
    )
    automesh_margin_pixels: IntProperty(  # type: ignore[valid-type]
        name="Boundary margin (annulus)",
        description=(
            "Source-pixel margin that builds an ANNULUS topology "
            "(dilated outer ring + eroded inner ring + Constrained "
            "Delaunay between them). Zero (default) skips the annulus "
            "and produces a single-contour flat triangulation - the "
            "common case for 2D skinning (matches Spine / DragonBones). "
            "Set > 0 only when you want extra edge-loop density at the "
            "silhouette for fine border deformation control (cape, "
            "hair, ribbon)."
        ),
        default=0,
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
    automesh_interior_mode: EnumProperty(  # type: ignore[valid-type]
        name="Interior mode",
        description=(
            "How the mesh interior is filled. SIMPLE triangulates only the "
            "silhouette, holes, and your fold/cut/steiner verts (Spine-like "
            "sparse mesh; best for most flat 2D-skinning sprites). DENSE adds "
            "the uniform interior grid + bone-density fill (capes, hair, fine "
            "border control)."
        ),
        items=[
            (
                "SIMPLE",
                "Simple (sparse, Spine-like)",
                "Constrained Delaunay over silhouette + holes + your verts only; "
                "no automatic interior fill",
            ),
            (
                "DENSE",
                "Dense (uniform fill)",
                "Uniform interior grid + bone-density subdivision (current default)",
            ),
        ],
        default="SIMPLE",
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
    preserve_base_quad: BoolProperty(  # type: ignore[valid-type]
        name="Preserve base quad",
        description=(
            "Keep the 4 original quad corner vertices (in the "
            "proscenio_base_sprite vertex group) as loose verts after "
            "automesh runs. OFF (default) deletes them so the mesh "
            "is clean. ON preserves them so the user can manually "
            "stitch custom UV / weight work that lived on the quad "
            "(useful when the user has hand-tweaked the base before "
            "automesh and wants to merge the work afterwards)"
        ),
        default=False,
    )
    bind_init_mode: EnumProperty(  # type: ignore[valid-type]
        name="Bind mode",
        description=(
            "Algorithm used by Bind to Picker Armature. BONE_HEAT delegates "
            "to Blender's native Parent w/ Auto Weights (recommended for "
            "sprites with bones co-planar with the picture plane). PROXIMITY "
            "/ ENVELOPE / SINGLE_NEAREST / EMPTY are Proscenio fallbacks for "
            "edge cases (off-sprite armatures, manual paint baseline)."
        ),
        items=[
            (
                "BONE_HEAT",
                "Bone Heat (Blender native)",
                "Delegate to Blender's Parent w/ Auto Weights. Default; best for 2D pickers",
            ),
            (
                "PROXIMITY",
                "Proximity (1/d^p)",
                "Per-bone 1/distance^falloff_power normalized in XZ. Fallback when bone heat fails",
            ),
            (
                "ENVELOPE",
                "Envelope",
                "Weight 1.0 inside per-bone radius (read from bone Custom Property), "
                "0 outside, then per-vert normalized",
            ),
            (
                "SINGLE_NEAREST",
                "Single nearest",
                "Each vert gets weight 1.0 in its nearest bone, 0 in others",
            ),
            (
                "EMPTY",
                "Empty",
                "All-zero baseline for manual paint workflows",
            ),
        ],
        default="BONE_HEAT",
    )
    bind_falloff_power: FloatProperty(  # type: ignore[valid-type]
        name="Bind falloff power",
        description=(
            "Exponent for 1/dist^power per-vert weight (PROXIMITY mode only). "
            "Higher values = tighter local influence. 2.0 (inverse square) "
            "matches Spine / DragonBones convention."
        ),
        default=2.0,
        min=0.5,
        max=8.0,
    )
    bind_max_distance: FloatProperty(  # type: ignore[valid-type]
        name="Bind max distance",
        description=(
            "Bones beyond this distance contribute zero (PROXIMITY mode only). "
            "-1 = adaptive (1.5x armature deform-bone bbox extent)."
        ),
        default=-1.0,
    )
    preserve_on_regen: BoolProperty(  # type: ignore[valid-type]
        name="Preserve weights on regen",
        description=(
            "When ON (default), running Automesh from Sprite on an already-"
            "bound mesh snapshots the current weights, regenerates the mesh, "
            "then reprojects the weights onto the new topology via UV anchors. "
            "OFF lets automesh wipe weights (legacy behavior) - useful when "
            "the sprite changed enough that interpolation would produce "
            "nonsense."
        ),
        default=True,
    )
    show_provenance_overlay: BoolProperty(  # type: ignore[valid-type]
        name="Show provenance overlay",
        description=(
            "When ON, the Weight Paint viewport colors each vert by its "
            "weight source: cyan = reprojected (came from a regen), white "
            "= user paint, gray = auto seed (untouched bind output). The "
            "GPU draw handler ships later; this surface provides "
            "the data + toggle so the panel layout is stable."
        ),
        default=False,
    )
    authoring_inner_loop_count: IntProperty(  # type: ignore[valid-type]
        name="Inner loops",
        description=(
            "Concentric inner polylines computed via morphological erosion of "
            "the outer contour during interactive modal authoring. Higher count "
            "= more edge loops the CDT respects = more deformation control near "
            "the silhouette boundary. 0 disables inner loops"
        ),
        default=2,
        min=0,
        max=10,
    )
    authoring_inner_loop_spacing: FloatProperty(  # type: ignore[valid-type]
        name="Inner loop spacing",
        description=(
            "World-unit gap between adjacent inner loops in the authoring "
            "modal. Smaller = denser loops near the boundary; larger = single "
            "loop closer to mesh center"
        ),
        default=0.15,
        min=0.01,
        soft_max=1.0,
    )
    authoring_cut_margin: FloatProperty(  # type: ignore[valid-type]
        name="Cut margin",
        description=(
            "Width of the corridor gap carved by cut strokes, in world units. "
            "The stroke is offset +/- cut_margin/2 perpendicular to its tangent; "
            "the corridor between the two offset lines becomes a CDT hole, so the "
            "triangulation excludes it cleanly. Larger = wider gap between the cut "
            "sides. Clamped to a 0.01 minimum so the corridor never collapses."
        ),
        default=0.04,
        min=0.01,
        soft_max=0.2,
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
            "Substring filter applied to the Proscenio outliner (the outliner subpanel). "
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
