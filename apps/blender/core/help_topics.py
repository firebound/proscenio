"""In-panel help-topic dispatch table for Proscenio (SPEC 005.1.d.5).

Powers the ``?`` button surfaced next to every Proscenio subpanel.
Each topic carries a title + ordered sections of plain-text content
that the help operator renders inside a ``invoke_popup`` window. Pure
Python -- no bpy imports -- so the dispatch can be unit-tested + so
the panel module can read content without a draw-time import cycle.

Adding a new help topic:

1. Add a ``HelpTopic`` row to ``HELP_TOPICS`` keyed by a stable id.
2. Reference the id from the panel via ``_help_button(layout, topic)``.
3. Optionally cross-link with a SPEC under ``see_also``.

Content guidelines:

- Lead with "What it does" so the user gets the answer in 1 line.
- Follow with "How to use it" -- click order, expected selection state.
- Close with "Where it fits" mapping the feature to the
  Photoshop -> Blender -> Godot pipeline.
- Optionally "Caveats" for known foot-guns.

Plain-text only. No Markdown -- Blender's UILayout renders one line
per ``layout.label``. Bullet lists are emulated with leading ``- ``.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HelpSection:
    heading: str
    body: tuple[str, ...]


@dataclass(frozen=True)
class HelpTopic:
    """One help entry surfaced via the ``?`` button.

    Sections render in order. ``see_also`` is rendered as a tail list
    of relative links to ``specs/<NNN-slug>/`` for users who want to
    dive into the design rationale.
    """

    title: str
    summary: str  # one-liner shown at the top of the popup
    sections: tuple[HelpSection, ...]
    see_also: tuple[str, ...] = field(default_factory=tuple)


_SECTION_WHAT = "What it does"
_SECTION_HOW = "How to use it"

_SPEC_INITIAL_PLAN = "specs/000-initial-plan"
_SPEC_REIMPORT_MERGE = "specs/001-reimport-merge"
_SPEC_AUTHORING_PANEL = "specs/005-blender-authoring-panel"
_SPEC_SLOT_SYSTEM = "specs/004-slot-system"


def _section(heading: str, *lines: str) -> HelpSection:
    return HelpSection(heading=heading, body=tuple(lines))


HELP_TOPICS: dict[str, HelpTopic] = {
    "status_legend": HelpTopic(
        title="Status badges",
        summary="Quick legend for the icons next to every Proscenio panel header.",
        sections=(
            _section(
                "godot-ready (CHECKMARK)",
                "Exports to .proscenio + ships in the Godot importer. Edits to",
                "fields under this panel reach the runtime scene.",
            ),
            _section(
                "blender-only (TOOL_SETTINGS)",
                "Authoring shortcut. Lives entirely on the Blender side -- the",
                ".proscenio export ignores these. Useful for posing, IK chains,",
                "preview cameras, driver shortcuts.",
            ),
            _section(
                "planned (EXPERIMENTAL)",
                "Designed in the SPECs but not yet implemented. The UI surface",
                "exists today as a placeholder so the future feature has a",
                "discoverable home.",
            ),
            _section(
                "out-of-scope (CANCEL)",
                "Intentionally not exported (see SPEC 000). Authored in Blender",
                "for the user's own workflow only -- IK constraints, shape keys,",
                "anything Godot does not consume.",
            ),
            _section(
                "Per-feature status",
                "Hover the icon for the specific band of THIS feature. Click",
                "the icon to re-open this legend.",
            ),
        ),
        see_also=("STATUS.md",),
    ),
    "pipeline_overview": HelpTopic(
        title="Proscenio pipeline overview",
        summary="Photoshop -> Blender -> Godot, one JSON contract between every step.",
        sections=(
            _section(
                "The pipeline",
                "1. Photoshop authors layered art (or skip + author meshes in Blender).",
                "2. JSX exporter writes a manifest (SPEC 006) -- Blender importer stamps planes.",
                "3. Blender authors armature, weights, actions, regions.",
                "4. Proscenio writer emits .proscenio (JSON Schema v1).",
                "5. Godot EditorImportPlugin reads .proscenio -> .scn",
                "   (Skeleton2D + Polygon2D + AnimationPlayer).",
                "6. User wraps .scn in a Wrapper.tscn (SPEC 001) for scripts/extra nodes.",
            ),
            _section(
                "Why a JSON contract",
                "The .proscenio file is the single source of truth between the three sides.",
                "Photoshop never knows about Blender; Blender never knows about Godot.",
                "Schema bumps require a coordinated multi-component PR + format_version bump.",
            ),
            _section(
                "Status badges",
                "godot-ready  -- exports to .proscenio + ships in the Godot importer.",
                "blender-only -- editor authoring shortcut, never reaches the .proscenio.",
                "planned      -- SPEC on paper, UI placeholder, not yet implemented.",
                "out-of-scope -- intentionally not exported (see SPEC 000).",
            ),
        ),
        see_also=(
            _SPEC_INITIAL_PLAN,
            _SPEC_REIMPORT_MERGE,
            "STATUS.md",
        ),
    ),
    "active_sprite": HelpTopic(
        title="Active Sprite",
        summary="Per-sprite Proscenio settings -- drives writer behavior + Godot node choice.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Surfaces every per-mesh field the writer reads when emitting a Sprite",
                "entry into the .proscenio. Shown only when the active object is a MESH.",
            ),
            _section(
                "Sprite type",
                "Polygon      -> Polygon2D (cutout, deformable mesh, weight paint).",
                "Sprite Frame -> Sprite2D (spritesheet, hframes x vframes grid + frame index).",
                "Pick by use case -- see SPEC 002 for the full decision matrix.",
            ),
            _section(
                "Texture region",
                "Auto   -- writer computes from the mesh UV bounds at export time.",
                "Manual -- writer reads region_x/y/w/h verbatim. Use for atlas slicing.",
                "Snap to UV bounds populates the manual fields from the current UV.",
            ),
            _section(
                "Drive from bone (5.1.d.1)",
                "Wires a Blender driver between the picked pose bone and a sprite",
                "proscenio.* property. Useful for iris-scrolling or threshold flags.",
                "For HARD texture swaps (forearm front/back), use the slot system",
                "(SPEC 004, planned) instead.",
            ),
        ),
        see_also=(
            "specs/002-spritesheet-sprite2d",
            _SPEC_AUTHORING_PANEL,
        ),
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
                "reaches the .proscenio -- IK in Godot is added post-import via",
                "Skeleton2DIK (per SPEC 000).",
            ),
        ),
        see_also=(_SPEC_INITIAL_PLAN, "specs/003-skinning-weights"),
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
        see_also=(_SPEC_INITIAL_PLAN, _SPEC_REIMPORT_MERGE),
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
                ".blend save/reload -- Ctrl+Z does not. Use this when you need to",
                "edit a source image and re-pack from scratch.",
            ),
        ),
        see_also=(_SPEC_AUTHORING_PANEL,),
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
                "- sprite_frame meshes without hframes/vframes.",
            ),
            _section(
                _SECTION_HOW,
                "Click Validate; rows render below with click-to-select on the",
                "offending object. Errors block Export; warnings are informational.",
            ),
        ),
        see_also=(_SPEC_AUTHORING_PANEL,),
    ),
    "export": HelpTopic(
        title="Export",
        summary="Write the active scene to a .proscenio JSON file.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Runs the writer, validates against schemas/proscenio.schema.json,",
                "writes the result. Sticky -- the path is remembered next to the",
                ".blend so Re-export skips the file dialog.",
            ),
            _section(
                "Pixels per unit",
                "Conversion ratio between Blender world units and Godot pixels.",
                "Default 100 -- 1 m in Blender = 100 px in Godot.",
            ),
            _section(
                "What lands in Godot",
                "The .proscenio is read by the EditorImportPlugin. A .scn is generated",
                "with Skeleton2D + Bone2D + Polygon2D/Sprite2D + AnimationPlayer -- all",
                "native nodes, no GDExtension, no plugin runtime dependency.",
            ),
        ),
        see_also=(_SPEC_INITIAL_PLAN,),
    ),
    "drive_from_bone": HelpTopic(
        title="Drive from Bone (5.1.d.1)",
        summary="Wire a Blender driver between a pose bone and a sprite Proscenio property.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Adds a TRANSFORMS driver variable that feeds the picked bone channel",
                "into the chosen proscenio.* property. Re-running on the same",
                "(sprite, target) pair replaces the existing driver -- no duplicates.",
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
                "fields like region_x are clamped [0,1] -- bone rotation > 1 rad will",
                "saturate. Edit the expression in the Drivers Editor for scaling/offsets.",
            ),
            _section(
                "Hard swap vs gradual",
                "This shortcut is for GRADUAL parameter mapping (iris scroll, region",
                "nudge). For HARD texture swaps (forearm front/back), the slot system",
                "(SPEC 004, planned) is the right primitive -- the threshold expression",
                "'1 if var > 1.5 else 0' works as a workaround until SPEC 004 ships.",
            ),
        ),
        see_also=(
            _SPEC_AUTHORING_PANEL,
            _SPEC_SLOT_SYSTEM,
        ),
    ),
    "quick_armature": HelpTopic(
        title="Quick Armature (5.1.d.3)",
        summary="Click-drag in the viewport to draw bones without entering Edit Mode.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Modal viewport tool that creates or extends a 'Proscenio.QuickRig'",
                "armature one bone per click-drag. Each press records the bone head",
                "on the world z=0 plane; each release records the tail and lands the",
                "bone. Speeds up the rough-sketch phase before refining in Edit Mode.",
            ),
            _section(
                _SECTION_HOW,
                "1. Click 'Quick Armature' in the Skeleton subpanel.",
                "2. Click-drag in the 3D viewport: press = head, release = tail.",
                "3. Hold Shift on press to auto-parent the new bone to the previous",
                "   one in the chain (use_connect=False -- head stays where you",
                "   clicked rather than snapping onto the parent's tail).",
                "4. Esc or right-click exits the modal session.",
            ),
            _section(
                "Caveats",
                "Bones are flat on the z=0 plane (this is a 2D pipeline). Drags",
                "shorter than 1e-4 world units are skipped to avoid degenerate",
                "zero-length bones. The QuickRig armature is identical to any",
                "hand-built one -- rename, parent meshes, weight-paint, or merge",
                "into your main rig as usual.",
            ),
        ),
        see_also=(_SPEC_AUTHORING_PANEL,),
    ),
    "outliner": HelpTopic(
        title="Outliner (5.1.d.4)",
        summary="Sprite-centric flat list of slots, sprite meshes, and armatures.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Filters every Blender object down to the ones Proscenio cares",
                "about, sorts them by category (slots first, then attachments,",
                "then sprite meshes, then armatures), and lets you click a row",
                "to make that object active. Replaces / supplements Blender's",
                "native outliner for big rigs (the doll fixture has 64 bones +",
                "22 sprite meshes + several slots -- finding 'brow.L mesh' in",
                "the native outliner requires scroll + expand every time).",
            ),
            _section(
                _SECTION_HOW,
                "1. Type a substring into the filter input -- live filter on object",
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
                "Pure authoring shortcut -- edits to favorites or filter state",
                "live entirely on the Blender side. The .proscenio export is",
                "untouched.",
            ),
        ),
        see_also=(_SPEC_AUTHORING_PANEL,),
    ),
    "slot_system": HelpTopic(
        title="Slot system (SPEC 004)",
        summary="Empty Object + child meshes = one slot. Animation flips visibility per key.",
        sections=(
            _section(
                _SECTION_WHAT,
                "A slot presents one of N attachment meshes at a time. Use it for",
                "hard texture swaps -- forearm front/back, sword/staff/empty, brow",
                "up/down, expression swap. Different from the driver shortcut",
                "(SPEC 005.1.d.1) which is for gradual parameter mapping.",
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
                "   value in the Action editor (Wave 4.2 -- Godot side -- ships",
                "   the runtime; Wave 4.1 just emits the data into .proscenio).",
            ),
            _section(
                "Mixing polygon + sprite_frame attachments",
                "Slots are kind-agnostic. A single slot can hold polygon",
                "(weight-painted) AND sprite_frame (texture-sliced) children",
                "freely -- e.g. an eye slot with two polygon attachments",
                "(open / closed) plus one sprite_frame attachment (4-cell glow",
                "cycle). The Photoshop import flow that produced each child",
                "(layer stack vs sprite_frame group) does not matter.",
            ),
            _section(
                "What lands in Godot",
                "(Wave 4.2) Each slot becomes a Node2D parent under the bone,",
                "with N sibling Polygon2D / Sprite2D children. Default attachment",
                "starts visible=true, others false. The slot_attachment animation",
                "track flips visibility per key with constant interpolation.",
            ),
        ),
        see_also=(_SPEC_SLOT_SYSTEM,),
    ),
    "sprite_frame_preview": HelpTopic(
        title="Sprite_frame preview material (D13)",
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
                "1. Select a sprite_frame mesh.",
                "2. Click 'Setup Preview' in the Active Sprite panel.",
                "3. Z-key cycles to Material Preview mode -- the active cell",
                "   shows on the quad, updating live as 'frame' animates.",
                "4. 'Remove Preview' un-wires the slicer + drops the drivers,",
                "   restoring the full-atlas render.",
            ),
            _section(
                "Caveats",
                "- Solid / Workbench engines only honor diffuse_color -- the",
                "  slicer is invisible there. The render_layers fixture script",
                "  uses Workbench so its output is unchanged.",
                "- Atlases with padding between cells are not yet supported;",
                "  the slicer assumes contiguous cells.",
                "- Re-runs of Setup Preview are idempotent: existing slicer",
                "  + drivers are refreshed without duplicating nodes.",
            ),
        ),
        see_also=(_SPEC_SLOT_SYSTEM, "specs/002-spritesheet-sprite2d"),
    ),
    "pose_library": HelpTopic(
        title="Save Pose to Library (5.1.d.2)",
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
                "2. Set the desired pose -- rotate / translate / scale bones.",
                "3. Click 'Save Pose to Library' in the Skeleton panel.",
                "4. The pose lands in the Asset Browser as '<action>.<frame>'",
                "   (or '<armature>.<frame>' when no action is active).",
                "5. Open Window > Asset Browser to apply the saved pose later.",
            ),
            _section(
                "Where it fits",
                "Pose assets live entirely on the Blender side -- they never",
                "reach the .proscenio export. Use them to library + reuse poses",
                "across animations, characters, or projects. Animation tracks",
                "still drive the runtime; pose assets are an authoring shortcut.",
            ),
            _section(
                "Caveats",
                "- Requires Blender 3.5+ (poselib operator availability).",
                "- The shim does not curate the Asset Browser layout -- pose",
                "  assets land in the active asset library; configure that via",
                "  Edit > Preferences > File Paths > Asset Libraries.",
            ),
        ),
        see_also=(_SPEC_AUTHORING_PANEL,),
    ),
    "import_photoshop": HelpTopic(
        title="Import Photoshop Manifest",
        summary="Stamp planes + stub armature from a SPEC 006 v1 PSD manifest.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Reads a manifest emitted by apps/photoshop/proscenio_export.jsx,",
                "stamps one polygon mesh per layer + composes spritesheet textures",
                "for sprite_frame groups, parents everything to a stub root armature.",
            ),
            _section(
                _SECTION_HOW,
                "1. Run proscenio_export.jsx in Photoshop on a layered PSD.",
                "2. Click Import Photoshop Manifest, pick the resulting .json.",
                "3. Choose placement: landed (feet on Z=0) or centered (manifest center).",
                "4. Refine the stub armature + paint weights in Blender.",
            ),
            _section(
                "Idempotent re-import",
                "Meshes carry a proscenio_import_origin = 'psd:<layer>' tag. Re-running",
                "on the same manifest reuses existing meshes -- user-set rotation,",
                "parenting, and weights survive the round trip.",
            ),
        ),
        see_also=("specs/006-photoshop-importer", "examples/generated/simple_psd"),
    ),
}


def topic_for(topic_id: str) -> HelpTopic | None:
    """Return the help topic for an id, or ``None`` for unknown ids."""
    return HELP_TOPICS.get(topic_id)


def known_topic_ids() -> tuple[str, ...]:
    """Return every topic id in registration order. Useful for tests."""
    return tuple(HELP_TOPICS.keys())
