"""In-panel help-topic dispatch table for Proscenio.

Powers the ``?`` button surfaced next to every Proscenio subpanel.
Each topic carries a title + ordered sections of plain-text content
that the help operator renders inside a ``invoke_popup`` window. Pure
Python - no bpy imports - so the dispatch can be unit-tested + so
the panel module can read content without a draw-time import cycle.

Adding a new help topic:

1. Add a ``HelpTopic`` row to ``HELP_TOPICS`` keyed by a stable id.
2. Reference the id from the panel via ``_help_button(layout, topic)``.
3. Optionally cross-link to a planning doc or example under ``see_also``.

Content guidelines:

- Lead with "What it does" so the user gets the answer in 1 line.
- Follow with "How to use it" - click order, expected selection state.
- Close with "Where it fits" mapping the feature to the
  Photoshop -> Blender -> Godot pipeline.
- Optionally "Caveats" for known foot-guns.

Plain-text only. No Markdown - Blender's UILayout renders one line
per ``layout.label``. Bullet lists are emulated with leading ``- ``.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class HelpSection:
    heading: str
    body: tuple[str, ...]


@dataclass(frozen=True)
class HelpTopic:
    """One help entry surfaced via the ``?`` button.

    Sections render in order. ``see_also`` is rendered as a tail list
    of relative paths to a planning doc or example for users who want
    to dive deeper.
    """

    title: str
    summary: str  # one-liner shown at the top of the popup
    sections: tuple[HelpSection, ...]
    see_also: tuple[str, ...] = field(default_factory=tuple)
    doc_url: str = ""  # full URL to the online docs page; empty hides the button


_SECTION_WHAT = "What it does"
_SECTION_HOW = "How to use it"


def _section(heading: str, *lines: str) -> HelpSection:
    return HelpSection(heading=heading, body=tuple(lines))


HELP_TOPICS: dict[str, HelpTopic] = {
    "status_legend": HelpTopic(
        title="Status badges",
        summary="Quick legend for the icons next to every Proscenio panel header.",
        sections=(
            _section(
                "godot-ready (Godot mark)",
                "Exports to .proscenio + ships in the Godot importer. Edits to",
                "fields under this panel reach the runtime scene.",
            ),
            _section(
                "blender-only (TOOL_SETTINGS)",
                "Authoring shortcut. Lives entirely on the Blender side - the",
                ".proscenio export ignores these. Useful for posing, IK chains,",
                "preview cameras, driver shortcuts.",
            ),
            _section(
                "planned (EXPERIMENTAL)",
                "Designed but not yet implemented. The UI surface exists today",
                "as a placeholder so the future feature has a discoverable home.",
            ),
            _section(
                "out-of-scope (CANCEL)",
                "Intentionally not exported. Authored in Blender for the user's",
                "own workflow only - IK constraints, shape keys, anything Godot",
                "does not consume.",
            ),
            _section(
                "Per-feature status",
                "Hover the icon for the specific band of THIS feature. Click",
                "the icon to re-open this legend.",
            ),
        ),
        see_also=(),
    ),
    "pipeline_overview": HelpTopic(
        title="Proscenio pipeline overview",
        summary="Photoshop -> Blender -> Godot, one JSON contract between every step.",
        sections=(
            _section(
                "The pipeline",
                "1. Photoshop authors layered art (or skip + author meshes in Blender).",
                "2. UXP plugin writes a manifest - Blender importer stamps planes.",
                "3. Blender authors armature, weights, actions, regions.",
                "4. Proscenio writer emits .proscenio (JSON Schema v1).",
                "5. Godot EditorImportPlugin reads .proscenio -> .scn",
                "   (Skeleton2D + Polygon2D + AnimationPlayer).",
                "6. User wraps .scn in a Wrapper.tscn for scripts/extra nodes.",
            ),
            _section(
                "Why a JSON contract",
                "The .proscenio file is the single source of truth between the three sides.",
                "Photoshop never knows about Blender; Blender never knows about Godot.",
                "Schema bumps require a coordinated multi-component PR + format_version bump.",
            ),
            _section(
                "Status badges",
                "godot-ready  - exports to .proscenio + ships in the Godot importer.",
                "blender-only - editor authoring shortcut, never reaches the .proscenio.",
                "planned      - designed on paper, UI placeholder, not yet implemented.",
                "out-of-scope - intentionally not exported.",
            ),
        ),
        see_also=(),
    ),
    "active_element": HelpTopic(
        title="Active Element",
        summary="Per-element Proscenio settings - drives writer behavior + Godot node choice.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Surfaces every per-mesh field the writer reads when emitting an element",
                "entry into the .proscenio. Shown only when the active object is a MESH.",
            ),
            _section(
                "Element type",
                "Mesh   -> Polygon2D (cutout, deformable, weight paint).",
                "Sprite -> Sprite2D (spritesheet, hframes x vframes grid + frame index).",
                "Pick by use case - Mesh for deformable cutout, Sprite",
                "for grid-cycled animations.",
            ),
            _section(
                "Texture region",
                "Auto   - writer computes from the mesh UV bounds at export time.",
                "Manual - writer reads region_x/y/w/h verbatim. Use for atlas slicing.",
                "Snap to UV bounds populates the manual fields from the current UV.",
            ),
            _section(
                "Drive from bone",
                "Wires a Blender driver between the picked pose bone and a sprite",
                "proscenio.* property. Useful for iris-scrolling or threshold flags.",
                "For HARD texture swaps (forearm front/back), use the slot system",
                "instead.",
            ),
        ),
        see_also=(),
    ),
    "skeleton": HelpTopic(
        title="Skeleton",
        summary="Read-only summary of the armature the writer would export.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Lists every bone the writer will emit + flags multi-armature scenes.",
                "Pose-mode helpers (Bake Pose / Toggle IK) are blender-only conveniences",
                "and never affect the .proscenio output.",
            ),
            _section(
                "Bake Current Pose",
                "Inserts location/rotation/scale keyframes on every pose bone at the",
                "playhead. Shortcut to author rest-pose + key offsets in one click.",
            ),
            _section(
                "Toggle IK",
                "Adds (or removes) a 'Proscenio IK' constraint on the active pose bone",
                "so you can pose-test with IK while authoring. The constraint never",
                "reaches the .proscenio - IK in Godot is added post-import via",
                "Skeleton2DIK.",
            ),
        ),
        see_also=("specs/decisions.md",),
    ),
    "animation": HelpTopic(
        title="Animation",
        summary="List of actions the writer would emit as Godot AnimationLibrary entries.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Read-only summary of every Action in bpy.data.actions. The writer",
                "iterates them and emits a track per fcurve, mapping bone_transform",
                "and sprite_frame paths to Godot AnimationPlayer tracks.",
            ),
            _section(
                "Where they go",
                "All actions land in the imported scene's AnimationPlayer under the",
                "default ('') AnimationLibrary. The wrapper Wrapper.tscn can host its",
                "own second AnimationPlayer for game-side animations without colliding.",
            ),
        ),
        see_also=(),
    ),
    "atlas": HelpTopic(
        title="Atlas",
        summary="Pack source images into a shared atlas, rewrite UVs, restore via Unpack.",
        sections=(
            _section(
                "Pack Atlas",
                "Walks every sprite mesh, collects its source image, runs MaxRects-BSSF",
                "packing, writes <blend>.atlas.png + <blend>.atlas.json. Non-destructive",
                "-- UVs + materials are NOT touched yet.",
            ),
            _section(
                "Apply Packed Atlas",
                "Reads the manifest, snapshots pre-Apply state into a Custom Property",
                "(proscenio_pre_pack), then rewrites every sprite's UVs + material to",
                "address the packed atlas.",
            ),
            _section(
                "Unpack Atlas",
                "Reverts a previous Apply by reading the snapshot back. Survives",
                ".blend save/reload - Ctrl+Z does not. Use this when you need to",
                "edit a source image and re-pack from scratch.",
            ),
        ),
        see_also=(),
    ),
    "validation": HelpTopic(
        title="Validation",
        summary="Walks the scene, reports issues that would block export.",
        sections=(
            _section(
                "What it catches",
                "- Missing armature when sprites carry vertex groups.",
                "- Bone references that no longer exist on the armature.",
                "- Atlas image files missing from disk.",
                "- sprite meshes without hframes/vframes.",
            ),
            _section(
                _SECTION_HOW,
                "Click Validate; rows render below with click-to-select on the",
                "offending object. Errors block Export; warnings are informational.",
            ),
        ),
        see_also=(),
    ),
    "export": HelpTopic(
        title="Export",
        summary="Write the active scene to a .proscenio JSON file.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Runs the writer, validates against packages/models/schemas/proscenio.schema.json,",
                "writes the result. Sticky - the path is remembered next to the",
                ".blend so Re-export skips the file dialog.",
            ),
            _section(
                "Pixels per unit",
                "Conversion ratio between Blender world units and Godot pixels.",
                "Default 100 - 1 m in Blender = 100 px in Godot.",
            ),
            _section(
                "What lands in Godot",
                "The .proscenio is read by the EditorImportPlugin. A .scn is generated",
                "with Skeleton2D + Bone2D + Polygon2D/Sprite2D + AnimationPlayer - all",
                "native nodes, no GDExtension, no plugin runtime dependency.",
            ),
        ),
        see_also=(),
    ),
    "drive_from_bone": HelpTopic(
        title="Drive from Bone",
        summary="Wire a Blender driver between a pose bone and a sprite Proscenio property.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Adds a TRANSFORMS driver variable that feeds the picked bone channel",
                "into the chosen proscenio.* property. Re-running on the same",
                "(sprite, target) pair replaces the existing driver - no duplicates.",
            ),
            _section(
                _SECTION_HOW,
                "1. Select the sprite mesh as the active object.",
                "2. Pick an Armature in the box (any object, no need for selection).",
                "3. Pick a Bone from the dropdown (lists every bone of the armature).",
                "4. Pick the source axis (default ROT_Z = local 2D rotation).",
                "5. Click Drive from Bone. The driver lands in the Drivers Editor.",
            ),
            _section(
                "Caveats",
                "Driver expression defaults to 'var' (raw radians/units). FloatProperty",
                "fields like region_x are clamped [0,1] - bone rotation > 1 rad will",
                "saturate. Edit the expression in the Drivers Editor for scaling/offsets.",
            ),
            _section(
                "Hard swap vs gradual",
                "This shortcut is for GRADUAL parameter mapping (iris scroll, region",
                "nudge). For HARD texture swaps (forearm front/back), the slot system",
                "is the right primitive.",
            ),
        ),
        see_also=(),
    ),
    "quick_armature": HelpTopic(
        title="Quick Armature",
        summary="Click-drag in the viewport to draw bones without entering Edit Mode.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Modal viewport tool that creates or extends a 'Proscenio.QuickRig'",
                "armature one bone per click-drag. Each press records the bone head",
                "on the world Y=0 picture plane (Proscenio 2D-cutout convention);",
                "each release records the tail and lands the bone. Speeds up the",
                "rough-sketch phase before refining in Edit Mode.",
            ),
            _section(
                _SECTION_HOW,
                "1. Click 'Quick Armature' in the Skeleton subpanel.",
                "2. Click-drag in the 3D viewport: press = head, release = tail.",
                "3. Hold Shift on press to auto-parent the new bone to the previous",
                "   one in the chain (use_connect=False - head stays where you",
                "   clicked rather than snapping onto the parent's tail).",
                "4. Esc or right-click exits the modal session.",
            ),
            _section(
                "Caveats",
                "Bones are flat on the Y=0 plane (this is a 2D pipeline). Drags",
                "shorter than 1e-4 world units are skipped to avoid degenerate",
                "zero-length bones. The QuickRig armature is identical to any",
                "hand-built one - rename, parent meshes, weight-paint, or merge",
                "into your main rig as usual.",
            ),
        ),
        see_also=("specs/decisions.md",),
    ),
    "outliner": HelpTopic(
        title="Outliner",
        summary="Sprite-centric flat list of slots, sprite meshes, and armatures.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Filters every Blender object down to the ones Proscenio cares",
                "about, sorts them by category (slots first, then attachments,",
                "then sprite meshes, then armatures), and lets you click a row",
                "to make that object active. Replaces / supplements Blender's",
                "native outliner for big rigs (the doll fixture has 64 bones +",
                "22 sprite meshes + several slots - finding 'brow.L mesh' in",
                "the native outliner requires scroll + expand every time).",
            ),
            _section(
                _SECTION_HOW,
                "1. Type a substring into the filter input - live filter on object",
                "   names. Empty string shows everything Proscenio-relevant.",
                "2. Click a row -> object becomes active + selected (the active",
                "   sprite / skeleton subpanels populate accordingly).",
                "3. Click the SOLO icon next to a row -> pin it as a favorite.",
                "4. Toggle 'Favorites only' (the SOLO icon next to the filter",
                "   input) to hide everything except your favorites.",
            ),
            _section(
                "Layout",
                "Slots render with a [slot] prefix at the top. Their attachment",
                "meshes render right after, indented with a '↳'. Floating sprite",
                "meshes render unprefixed; armatures render with [arm] last.",
            ),
            _section(
                "Where it fits",
                "Pure authoring shortcut - edits to favorites or filter state",
                "live entirely on the Blender side. The .proscenio export is",
                "untouched.",
            ),
        ),
        see_also=(),
    ),
    "slot_system": HelpTopic(
        title="Slot system",
        summary="Empty Object + child meshes = one slot. Animation flips visibility per key.",
        sections=(
            _section(
                _SECTION_WHAT,
                "A slot presents one of N attachment meshes at a time. Use it for",
                "hard texture swaps - forearm front/back, sword/staff/empty, brow",
                "up/down, expression swap. Different from the driver shortcut,",
                "which is for gradual parameter mapping.",
            ),
            _section(
                _SECTION_HOW,
                "1. Pose-mode (or any mode): click 'Create Slot' in the Skeleton",
                "   panel. With meshes selected, they wrap into the new Empty as",
                "   attachments; without, an empty slot anchors at the active bone.",
                "2. Promote selected meshes into an existing slot via 'Add Selected",
                "   Mesh' in the Active Slot panel.",
                "3. Pick which attachment is visible at scene load (default) by",
                "   clicking the SOLO icon next to its row.",
                "4. Animate slot_attachment by keyframing the slot's attachment",
                "   value in the Action editor.",
            ),
            _section(
                "Mixing mesh + sprite attachments",
                "Slots are kind-agnostic. A single slot can hold mesh",
                "(weight-painted) AND sprite (texture-sliced) children",
                "freely - e.g. an eye slot with two mesh attachments",
                "(open / closed) plus one sprite attachment (4-cell glow",
                "cycle). The Photoshop import flow that produced each child",
                "(layer stack vs sprite group) does not matter.",
            ),
            _section(
                "What lands in Godot",
                "Each slot becomes a Node2D parent under the bone, with N sibling",
                "Polygon2D / Sprite2D children. Default attachment starts",
                "visible=true, others false. The slot_attachment animation track",
                "flips visibility per key with constant interpolation.",
            ),
        ),
        see_also=(),
    ),
    "sprite_frame_preview": HelpTopic(
        title="Sprite_frame preview material",
        summary="Slice the spritesheet live in Material Preview mode via shader nodes + drivers.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Inserts a SpriteFrameSlicer node group between the material's",
                "TexCoord and ImageTexture nodes. Drivers wire",
                "obj.proscenio.frame / hframes / vframes onto the slicer inputs",
                "so the visible cell tracks the panel + animation values.",
                "Without the slicer, Blender shows the full atlas on the quad.",
            ),
            _section(
                _SECTION_HOW,
                "1. Select a sprite mesh.",
                "2. Click 'Setup Preview' in the Active Element panel.",
                "3. Z-key cycles to Material Preview mode - the active cell",
                "   shows on the quad, updating live as 'frame' animates.",
                "4. 'Remove Preview' un-wires the slicer + drops the drivers,",
                "   restoring the full-atlas render.",
            ),
            _section(
                "Caveats",
                "- Solid / Workbench engines only honor diffuse_color - the",
                "  slicer is invisible there. The render_layers fixture script",
                "  uses Workbench so its output is unchanged.",
                "- Atlases with padding between cells are not yet supported;",
                "  the slicer assumes contiguous cells.",
                "- Re-runs of Setup Preview are idempotent: existing slicer",
                "  + drivers are refreshed without duplicating nodes.",
            ),
        ),
        see_also=(),
    ),
    "pose_library": HelpTopic(
        title="Save Pose to Library",
        summary="Bundle the current armature pose into a Blender Asset Browser entry.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Tiny shim over Blender's native poselib.create_pose_asset.",
                "Wraps the call with sensible defaults so authors get a one-click",
                "entry point in the Skeleton subpanel instead of digging through",
                "Window > Pose Library every time.",
            ),
            _section(
                _SECTION_HOW,
                "1. Enter Pose Mode on the active armature.",
                "2. Set the desired pose - rotate / translate / scale bones.",
                "3. Click 'Save Pose to Library' in the Skeleton panel.",
                "4. The pose lands in the Asset Browser as '<action>.<frame>'",
                "   (or '<armature>.<frame>' when no action is active).",
                "5. Open Window > Asset Browser to apply the saved pose later.",
            ),
            _section(
                "Where it fits",
                "Pose assets live entirely on the Blender side - they never",
                "reach the .proscenio export. Use them to library + reuse poses",
                "across animations, characters, or projects. Animation tracks",
                "still drive the runtime; pose assets are an authoring shortcut.",
            ),
            _section(
                "Caveats",
                "- Requires Blender 3.5+ (poselib operator availability).",
                "- The shim does not curate the Asset Browser layout - pose",
                "  assets land in the active asset library; configure that via",
                "  Edit > Preferences > File Paths > Asset Libraries.",
            ),
        ),
        see_also=(),
    ),
    "import_photoshop": HelpTopic(
        title="Import Photoshop Manifest",
        summary="Stamp planes + stub armature from a v1 PSD manifest.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Reads a manifest emitted by the Proscenio Photoshop UXP plugin,",
                "stamps one mesh per layer + composes spritesheet textures",
                "for sprite groups, parents everything to a stub root armature.",
            ),
            _section(
                _SECTION_HOW,
                "1. Run the Proscenio Exporter panel in Photoshop on a layered PSD.",
                "2. Click Import Photoshop Manifest, pick the resulting .json.",
                "3. Choose placement: landed (feet on Z=0) or centered (manifest center).",
                "4. Refine the stub armature + paint weights in Blender.",
            ),
            _section(
                "Idempotent re-import",
                "Meshes carry a proscenio_import_origin = 'psd:<layer>' tag. Re-running",
                "on the same manifest reuses existing meshes - user-set rotation,",
                "parenting, and weights survive the round trip.",
            ),
        ),
        see_also=("examples/generated/simple_psd",),
    ),
    "mesh_generation": HelpTopic(
        title="Mesh Generation",
        summary="Turn a sprite's alpha into a deformable cutout mesh.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Traces the active image's alpha contour into an annulus mesh you",
                "can weight-paint and deform. Interior Mode (on the panel header)",
                "picks SIMPLE (sparse, Spine-like) or DENSE (uniform + bone-aware fill).",
            ),
            _section(
                "Automesh from Alpha",
                "One-shot trace using the panel defaults. Re-runs preserve the",
                "UV-pinned base quad via the proscenio_base_sprite vertex group.",
            ),
            _section(
                "Automesh Interactive / Debug Pipeline",
                "Interactive is a modal preview that lets you cut / extend / fold",
                "the silhouette before the geometry commits. Debug Pipeline emits",
                "per-stage wireframe companions for inspecting the trace.",
            ),
            _section(
                "Where it fits",
                "Authoring only - the generated geometry exports as a Polygon2D, but",
                "the trace tool itself never reaches the .proscenio.",
            ),
        ),
        see_also=(),
    ),
    "weight_paint": HelpTopic(
        title="Weight Paint",
        summary="Bind a cutout mesh to the rig and refine its bone weights.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Mesh-only panel. Bind the active mesh to the picked armature, then",
                "refine the per-bone weights. Bind + the resulting weights export to",
                "the Polygon2D; the edit and snapshot tools are blender-side.",
            ),
            _section(
                "Bind",
                "Binds to the armature picked in the Skeleton panel. Per-bone",
                "Soft / Hard rows override the default falloff for individual bones.",
            ),
            _section(
                "Edit Weights / Snapshot",
                "Edit Weights enters a modal weight-paint session with brush presets.",
                "Snapshot tracks paint provenance, restores the last saved weights, and",
                "exports / imports the weight snapshot to a file.",
            ),
            _section(
                "Weight Transfer",
                "Copies weights from the active mesh to the other selected meshes",
                "- handy for symmetric or split cutouts.",
            ),
        ),
        see_also=(),
    ),
    "helpers": HelpTopic(
        title="Helpers",
        summary="Viewport authoring aids that are not part of the export pipeline.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Convenience tools that set up the Blender viewport for 2D cutout",
                "work. None of them touch the .proscenio export.",
            ),
            _section(
                "Preview Camera",
                "Drops an orthographic front camera framed the way the Godot",
                "importer expects, so what you see matches the runtime framing.",
            ),
        ),
        see_also=(),
    ),
    "active_mesh": HelpTopic(
        title="Active Mesh",
        summary="The Polygon2D fields of the selected mesh element.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Shown when the active element type is Mesh. The mesh exports as a",
                "Polygon2D - a deformable cutout with UVs + bone weights. The vertices",
                "carry their own positions, so the Blender origin is baked in at export.",
            ),
        ),
        see_also=(),
    ),
    "active_sprite": HelpTopic(
        title="Active Sprite",
        summary="The Sprite2D spritesheet fields of the selected sprite element.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Shown when the active element type is Sprite. The mesh exports as a",
                "Sprite2D that slices a spritesheet: an hframes x vframes grid + a frame",
                "index. The quad geometry itself is not exported - only this metadata.",
            ),
            _section(
                "Fields",
                "- hframes / vframes: the spritesheet grid (columns x rows).",
                "- frame: the cell shown at rest pose; animation tracks override it.",
                "- centered: Godot Sprite2D.centered - texture centered on the node",
                "  origin (on) or top-left at the origin (off).",
            ),
        ),
        see_also=(),
    ),
    "texture_region": HelpTopic(
        title="Texture Region",
        summary="Which part of the texture this element samples.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Auto reads the region from the mesh UV bounds at export. Manual reads",
                "region_x/y/w/h verbatim - use it for atlas slicing. 'Snap to UV bounds'",
                "fills the manual fields from the current UV layout.",
            ),
        ),
        see_also=(),
    ),
    "bind": HelpTopic(
        title="Bind",
        summary="Bind the active mesh to the picker armature's bones.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Builds the vertex weights that let the rig deform this mesh. Mode picks",
                "the algorithm; Bone Heat (Blender native) is the default and best for",
                "most 2D pickers. Proximity / Envelope / Single-nearest / Empty are",
                "fallbacks exposed via F3 redo.",
            ),
            _section(
                "Per-bone Soft / Hard",
                "Override a single bone's falloff. Soft = proximity falloff: the bone",
                "shares weight smoothly with neighbours (good for cloth, hair). Hard =",
                "single-nearest: a crisp boundary, no bleed (good for finger joints).",
                "A bone with no override uses the Mode's default family.",
            ),
        ),
        see_also=(),
    ),
    "edit_weights": HelpTopic(
        title="Edit Weights",
        summary="Modal weight-paint session with 2D brush-curve presets.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Enters Weight Paint on the active group with a provenance overlay",
                "(which verts are auto-seed vs hand-painted). The brush-curve presets",
                "(Hard Edge / Soft Falloff / Crease / Smooth Blend) shape the brush",
                "falloff for common 2D tasks without a trip to the curve editor.",
            ),
            _section(
                _SECTION_HOW,
                "1. Bind the mesh first (the button is disabled until then).",
                "2. Click Edit Weights; paint; ESC exits and restores brush state.",
            ),
            _section(
                "Viewport display + posing",
                "Weight Opacity + Zero Weights (the native Viewport Overlay levers) let",
                "the texture show through the weight gradient while painting; opacity 0",
                "is not fully invisible (Blender 145603). To test deformation, pose the",
                "bones live inside Weight Paint mode - select the armature, enter Pose,",
                "and scrub or rotate while painting (no separate preview needed).",
            ),
        ),
        see_also=(),
    ),
    "snapshot": HelpTopic(
        title="Snapshot",
        summary="Save + restore weights so an automesh regen does not wipe paint.",
        sections=(
            _section(
                _SECTION_WHAT,
                "The weight snapshot stores, per vertex, a UV anchor + its weights +",
                "where they came from (auto-seed / hand paint / reprojected). It is the",
                "safety net that survives a mesh rebuild.",
            ),
            _section(
                "Controls",
                "- Preserve weights on regen: before an Automesh re-run, snapshot the",
                "  weights by UV, then reproject them onto the new mesh. Off = the",
                "  regen wipes paint.",
                "- Reset to Last Saved Weights: revert the live weights to the last",
                "  snapshot (undo paint back to the saved baseline).",
                "- The N paint / M seed / K reprojected pill shows where each vert's",
                "  weight came from.",
            ),
            _section(
                "File export / import",
                "- Export Snapshot: write the weight snapshot to a JSON file (version-",
                "  control weights in git, or move them between files).",
                "- Import Snapshot: load one back. It applies onto the live weights when",
                "  the mesh topology still matches; otherwise it stores the snapshot only",
                "  (re-run Automesh with Preserve weights on regen to reproject).",
            ),
        ),
        see_also=(),
    ),
    "weight_transfer": HelpTopic(
        title="Weight Transfer",
        summary="Copy weights from the active mesh to the other selected meshes.",
        sections=(
            _section(
                _SECTION_WHAT,
                "For each vertex of every other selected mesh, copies the weights of",
                "the nearest vertex on the active mesh (by world position). An imprint:",
                "the meshes must overlap in space; different vertex counts are fine",
                "(each target vert grabs its own nearest source).",
            ),
            _section(
                "Caveats",
                "Target verts beyond the Max Distance (F3 redo) get no weights. Use it",
                "for layered or split cutouts that sit on top of a rigged base.",
            ),
        ),
        see_also=(),
    ),
    "automesh_alpha": HelpTopic(
        title="Automesh from Alpha",
        summary="One-shot trace of the sprite alpha into a deformable mesh.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Walks the image alpha contour into an annulus mesh you can weight-paint.",
                "Re-runs preserve the UV-pinned base quad (the proscenio_base_sprite group).",
            ),
            _section(
                "Key settings",
                "- Trace resolution: an image downscale factor. HIGHER (1.0 =",
                "  full image) traces a finer silhouette but costs more; it sets",
                "  outline fidelity, not vertex count.",
                "- Interior Mode (parent panel): Simple (sparse) or Dense (filled).",
                "- Density follows bones (Dense only, off by default): pack more",
                "  triangles near the picker's bones, where deformation happens.",
            ),
        ),
        see_also=(),
    ),
    "automesh_interactive": HelpTopic(
        title="Automesh Interactive",
        summary="Step through the trace, editing the silhouette before it commits.",
        sections=(
            _section(
                _SECTION_WHAT,
                "A modal preview of the same trace. Advance through stages to cut /",
                "extend the outline and place interior points, then commit the mesh.",
                "Nothing is written until you confirm the final stage.",
            ),
            _section(
                _SECTION_HOW,
                "1. Select a mesh with an image texture; click Author Mesh (interactive).",
                "2. ENTER advances a stage, BACKSPACE steps back, ESC cancels.",
                "3. The final stage builds the mesh (same result as Automesh from Alpha",
                "   plus your edits).",
            ),
        ),
        see_also=(),
    ),
    "debug_pipeline": HelpTopic(
        title="Debug Pipeline",
        summary="Emit per-stage wireframe companions for inspecting the trace.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Developer aid (shown only with debug mode on). Picks a stage of the",
                "alpha trace (raw contours, smoothed, resampled, interior, bridges,",
                "fill); the next Automesh run leaves a wireframe companion in the",
                "Proscenio.Debug collection. Clear Debug Companions removes them.",
            ),
        ),
        see_also=(),
    ),
    "active_slot": HelpTopic(
        title="Active Slot",
        summary="The attachment detail of the selected slot.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Lists the slot's child meshes (its attachments), lets you mark which",
                "one is visible at scene load (the SOLO star = default), and add the",
                "selected mesh as a new attachment. See the Slots help for the overview.",
            ),
            _section(
                "Editing raw Custom Properties",
                "The SOLO star sets the default through the panel. Editing the raw",
                "proscenio_slot_default Custom Property directly exports and validates",
                "the same value, but the panel does not live-refresh to a raw edit -",
                "use the panel buttons as the expected workflow.",
            ),
        ),
        see_also=(),
    ),
    "armature": HelpTopic(
        title="Armature",
        summary="Read-only bone hierarchy of the picked armature.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Lists every bone the writer would export, indented by depth, with",
                "connected / relative flags. Click a bone to select it in the viewport.",
                "Inspection only - it never changes the .proscenio output.",
            ),
        ),
        see_also=(),
    ),
    "pose_mode": HelpTopic(
        title="Pose Mode",
        summary="Pose-only authoring shortcuts (blender-only).",
        sections=(
            _section(
                _SECTION_WHAT,
                "Bake Current Pose keys every bone at the playhead. Toggle IK adds /",
                "removes a test IK constraint. Save Pose to Library stores the pose as",
                "a Blender asset. None of these reach the .proscenio - they are",
                "authoring conveniences.",
            ),
        ),
        see_also=(),
    ),
}


# Base URL of the per-panel Blender addon reference (docs/02-blender-addon).
# topic_for injects the matching page (and section anchor) as the topic's
# doc_url so the help popup's "Open online docs" button lands on it - the URL
# scheme lives here once instead of on every HelpTopic literal.
_DOCS_BASE = "https://firebound.github.io/proscenio/blender-addon/"

_DOC_PATHS: dict[str, str] = {
    "outliner": "outliner",
    "active_element": "element",
    "active_mesh": "element#active-mesh",
    "active_sprite": "element#active-sprite",
    "texture_region": "element#texture-region",
    "drive_from_bone": "element#drive-from-bone",
    "slot_system": "slots",
    "active_slot": "slots#active-slot",
    "skeleton": "skeleton",
    "armature": "skeleton#armature",
    "pose_mode": "skeleton#pose-mode",
    "quick_armature": "skeleton#quick-armature",
    "mesh_generation": "mesh-generation",
    "automesh_alpha": "mesh-generation#automesh-from-alpha",
    "automesh_interactive": "mesh-generation#automesh-interactive",
    "debug_pipeline": "mesh-generation#debug-pipeline",
    "weight_paint": "weight-paint",
    "bind": "weight-paint#bind",
    "edit_weights": "weight-paint#edit-weights",
    "snapshot": "weight-paint#snapshot",
    "weight_transfer": "weight-paint#weight-transfer",
    "animation": "animation",
    "atlas": "atlas",
    "validation": "validation",
    "import_photoshop": "pipeline#import",
    "export": "pipeline#export",
    "helpers": "helpers",
    "status_legend": "#status-badges",
}


def topic_for(topic_id: str) -> HelpTopic | None:
    """Return the help topic for an id, or ``None`` for unknown ids.

    Topics listed in ``_DOC_PATHS`` get their ``doc_url`` filled from the
    addon reference base so the popup's "Open online docs" button works
    without repeating the URL on every literal.
    """
    topic = HELP_TOPICS.get(topic_id)
    if topic is None:
        return None
    rel = _DOC_PATHS.get(topic_id)
    if rel and not topic.doc_url:
        return replace(topic, doc_url=_DOCS_BASE + rel)
    return topic


def known_topic_ids() -> tuple[str, ...]:
    """Return every topic id in registration order. Useful for tests."""
    return tuple(HELP_TOPICS.keys())
