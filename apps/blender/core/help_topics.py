"""In-panel help-topic dispatch table for Proscenio.

Powers the ``?`` button surfaced next to every Proscenio subpanel. Each topic
carries a title + ordered sections of plain-text content that the help operator
renders inside an ``invoke_popup`` window. Pure Python - no bpy imports - so the
dispatch can be unit-tested and so the panel module can read content without a
draw-time import cycle.

Adding a new help topic:

1. Add a ``HelpTopic`` row to ``HELP_TOPICS`` keyed by a stable id.
2. Reference the id from the panel via the subpanel header / help button.
3. Optionally cross-link to a docs page or example under ``see_also``.

Content guidelines:

- Lead with "What it does" so the user gets the answer in one line.
- Follow with "How to use it" - click order, expected selection state.
- Close with "Where it fits" mapping the feature to the
  Photoshop -> Blender -> Godot pipeline.
- Optionally "Caveats" for known foot-guns.

Each ``HelpSection.body`` is one paragraph string. Prose flows free and is
reflowed to the popup width at draw time (:func:`reflow_paragraph`); a bullet or
numbered list keeps an explicit ``\\n`` between items so the structure survives
the reflow. No Markdown - the popup renders one ``layout.label`` per wrapped line.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

#: The help popup width passed to ``invoke_popup``, in pixels.
POPUP_WIDTH = 480

#: Greedy word-wrap budget tuned to ``POPUP_WIDTH``: ``layout.label`` cannot wrap
#: and Blender exposes no draw-time text metrics in a popup, so prose is reflowed
#: against a fixed character count that fills the popup at default UI scale. The
#: old hand-wrapping sat near 55 chars, leaving the right third of the popup empty.
POPUP_WRAP_CHARS = 72


@dataclass(frozen=True)
class HelpSection:
    heading: str
    body: str  # one paragraph; "\n" separates explicit list items / steps


@dataclass(frozen=True)
class HelpTopic:
    """One help entry surfaced via the ``?`` button.

    Sections render in order. ``see_also`` is rendered as a tail list of docs /
    example URLs for users who want to dive deeper.
    """

    title: str
    summary: str  # one-liner shown at the top of the popup
    sections: tuple[HelpSection, ...]
    see_also: tuple[str, ...] = field(default_factory=tuple)
    doc_url: str = ""  # full URL to the online docs page; empty hides the button


_SECTION_WHAT = "What it does"
_SECTION_HOW = "How to use it"


def _section(heading: str, *parts: str) -> HelpSection:
    """A prose section: ``parts`` join with spaces into one reflowed paragraph."""
    return HelpSection(heading=heading, body=" ".join(parts))


def _list_section(heading: str, *items: str) -> HelpSection:
    """A list/step section: ``items`` join with newlines so each keeps its own line."""
    return HelpSection(heading=heading, body="\n".join(items))


def _is_list_item(text: str) -> bool:
    """True when a paragraph is a bullet (``- ``) or numbered (``1. ``) item."""
    stripped = text.lstrip()
    if stripped.startswith("- "):
        return True
    head = stripped.split(" ", 1)[0]
    return len(head) > 1 and head.endswith(".") and head[:-1].isdigit()


def reflow_paragraph(text: str, width: int) -> list[str]:
    """Greedy word-wrap one logical line to ``width`` characters.

    ``layout.label`` does not wrap, so the popup reflows each paragraph here. A
    bullet / numbered item keeps a two-space hanging indent on its wrapped
    continuation lines so the marker stays visually distinct. Blank input yields
    no lines.
    """
    words = text.split()
    if not words:
        return []
    cont = "  " if _is_list_item(text) else ""
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        indent = cont if lines else ""
        if len(indent) + len(current) + 1 + len(word) > width:
            lines.append((cont if lines else "") + current)
            current = word
        else:
            current = f"{current} {word}"
    lines.append((cont if lines else "") + current)
    return lines


HELP_TOPICS: dict[str, HelpTopic] = {
    "status_legend": HelpTopic(
        title="Status badges",
        summary="Legend for the icons next to every Proscenio panel header.",
        sections=(
            _section(
                "godot-ready",
                "Exports to .proscenio and ships in the Godot importer. Edits to fields"
                " under this panel reach the runtime scene.",
            ),
            _section(
                "blender-only",
                "An authoring shortcut. Lives entirely on the Blender side - the"
                " .proscenio export ignores it. Posing, IK chains, preview cameras,"
                " driver shortcuts.",
            ),
            _section(
                "planned",
                "Designed but not yet implemented. The UI surface exists today as a"
                " placeholder so the future feature has a discoverable home.",
            ),
            _section(
                "out-of-scope",
                "Intentionally not exported. Authored in Blender for the user's own"
                " workflow only - IK constraints, shape keys, anything Godot does not"
                " consume.",
            ),
            _section(
                "Per-feature status",
                "Each panel header shows the badge for that feature. Hover it for that"
                " feature's band; click it to re-open this legend.",
            ),
        ),
    ),
    "pipeline_overview": HelpTopic(
        title="Proscenio pipeline overview",
        summary="Photoshop -> Blender -> Godot, one JSON contract between every step.",
        sections=(
            _list_section(
                "The pipeline",
                "1. Photoshop authors layered art (or skip it and author meshes in Blender).",
                "2. The UXP plugin writes a manifest; the Blender importer stamps planes.",
                "3. Blender authors the armature, weights, actions, regions.",
                "4. The Proscenio writer emits .proscenio (JSON Schema v1).",
                "5. The Godot import plugin reads .proscenio into a .scn"
                " (Skeleton2D + Polygon2D + AnimationPlayer).",
                "6. You wrap the .scn in a Wrapper.tscn for scripts and extra nodes.",
            ),
            _section(
                "Why a JSON contract",
                "The .proscenio file is the single source of truth between the three"
                " sides. Photoshop never knows about Blender; Blender never knows about"
                " Godot. A schema change needs a coordinated multi-component PR and a"
                " format_version bump.",
            ),
            _list_section(
                "Status badges",
                "godot-ready - exports to .proscenio and ships in the Godot importer.",
                "blender-only - an editor authoring shortcut, never reaches the .proscenio.",
                "planned - designed on paper, a UI placeholder, not yet implemented.",
                "out-of-scope - intentionally not exported.",
            ),
            _list_section(
                "Operators (F3 to search)",
                "Every Proscenio action is also an operator, searchable in the F3 menu by"
                " its 'Proscenio: ...' label:",
                "- Validate, Export Proscenio, Re-export, Import Photoshop Manifest.",
                "- Preview Camera, Bake Current Pose, Toggle IK, Quick Armature.",
                "- Reproject UV, Snap region to UV bounds.",
                "- Pack Atlas, Apply Packed Atlas, Unpack Atlas.",
                "- Select Issue Object, Select Outliner Object, Toggle Outliner Favorite.",
            ),
        ),
    ),
    "active_element": HelpTopic(
        title="Active Element",
        summary="Per-element settings that drive writer behavior and Godot node choice.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Surfaces every per-mesh field the writer reads when emitting an element"
                " into the .proscenio. Shown only when the active object is a mesh.",
            ),
            _list_section(
                "Element type",
                "Mesh -> Polygon2D (cutout, deformable, weight paint).",
                "Sprite -> Sprite2D (spritesheet, hframes x vframes grid + frame index).",
                "Pick by use case: Mesh for a deformable cutout, Sprite for grid-cycled"
                " animations.",
            ),
            _list_section(
                "Texture region",
                "Auto - the writer computes it from the mesh UV bounds at export.",
                "Manual - the writer reads region_x/y/w/h verbatim; use it for atlas slicing.",
                "Snap to UV bounds fills the manual fields from the current UV.",
            ),
            _section(
                "Drive from bone",
                "Wires a Blender driver between the picked pose bone and a sprite"
                " proscenio.* property - useful for iris scrolling or threshold flags. For"
                " HARD texture swaps (forearm front/back) use the slot system instead.",
            ),
        ),
    ),
    "skeleton": HelpTopic(
        title="Skeleton",
        summary="The project-wide armature picker plus a read-only bone summary.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Picks the armature every Proscenio skeleton operation targets and lists"
                " the bones the writer will emit. The pose-mode helpers (Bake Pose, Toggle"
                " IK) are blender-only conveniences and never affect the .proscenio.",
            ),
            _section(
                "Bake Current Pose",
                "Inserts location/rotation/scale keyframes on every pose bone at the"
                " playhead - a shortcut to author a rest pose plus key offsets in one click.",
            ),
            _section(
                "Toggle IK",
                "Adds or removes a 'Proscenio IK' constraint on the active pose bone so you"
                " can pose-test with IK while authoring. The constraint never reaches the"
                " .proscenio; IK in Godot is added post-import via Skeleton2D IK.",
            ),
        ),
    ),
    "animation": HelpTopic(
        title="Animation",
        summary="The actions the writer would emit as Godot AnimationLibrary entries.",
        sections=(
            _section(
                _SECTION_WHAT,
                "A read-only summary of every action in the file. The writer iterates them"
                " and emits a track per fcurve, mapping bone-transform and sprite-frame"
                " paths to Godot AnimationPlayer tracks. Click an action to assign it to the"
                " Skeleton-picked armature so the timeline plays it.",
            ),
            _section(
                "Where they go",
                "All actions land in the imported scene's AnimationPlayer under the default"
                " ('') library. Your Wrapper.tscn can host a second AnimationPlayer for"
                " game-side animations without colliding.",
            ),
        ),
    ),
    "atlas": HelpTopic(
        title="Atlas",
        summary="Pack source images into a shared atlas, rewrite UVs, restore via Unpack.",
        sections=(
            _section(
                "Pack Atlas",
                "Walks every sprite mesh, collects its source image, runs MaxRects-BSSF"
                " packing, and writes <blend>.atlas.png + <blend>.atlas.json."
                " Non-destructive - UVs and materials are not touched yet.",
            ),
            _section(
                "Apply Packed Atlas",
                "Reads the manifest, snapshots the pre-Apply state into a Custom Property"
                " (proscenio_pre_pack), then rewrites every sprite's UVs and material to"
                " address the packed atlas.",
            ),
            _section(
                "Unpack Atlas",
                "Reverts a previous Apply by reading the snapshot back. It survives a .blend"
                " save/reload (Ctrl+Z does not). Use it when you need to edit a source image"
                " and re-pack from scratch.",
            ),
            _section(
                "Renamed materials",
                "The snapshot stores each material by name and Apply also stamps an origin"
                " marker, so a material renamed between Apply and Unpack is still rescued."
                " Two cases the marker cannot cover: a deleted material (Unpack restores UVs"
                " only), and an old name reused by a different material (the by-name match"
                " wins and links the wrong material).",
            ),
        ),
    ),
    "validation": HelpTopic(
        title="Validation",
        summary="Walks the scene and reports issues that would block export.",
        sections=(
            _list_section(
                "What it catches",
                "- A missing armature when sprites carry vertex groups.",
                "- Bone references that no longer exist on the armature.",
                "- Atlas image files missing from disk.",
                "- Sprite meshes without hframes/vframes.",
            ),
            _section(
                _SECTION_HOW,
                "Click Validate; rows render below, each click-to-select on the offending"
                " object. Errors block Export; warnings are informational.",
            ),
        ),
    ),
    "export": HelpTopic(
        title="Export",
        summary="Write the active scene to a .proscenio JSON file.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Runs the writer, validates the result against the Proscenio JSON schema,"
                " and writes the file. The path is sticky - remembered next to the .blend so"
                " Re-export skips the file dialog.",
            ),
            _section(
                "Pixels per unit",
                "The conversion ratio between Blender world units and Godot pixels. Default"
                " 100, so 1 m in Blender = 100 px in Godot.",
            ),
            _section(
                "What lands in Godot",
                "The .proscenio is read by the import plugin into a .scn of Skeleton2D +"
                " Bone2D + Polygon2D/Sprite2D + AnimationPlayer - all native nodes, no"
                " GDExtension, no plugin runtime dependency.",
            ),
        ),
    ),
    "drive_from_bone": HelpTopic(
        title="Drive from Bone",
        summary="Wire a Blender driver between a pose bone and a sprite property.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Adds a TRANSFORMS driver variable that feeds the picked bone channel into"
                " the chosen proscenio.* property. Re-running on the same (sprite, target)"
                " pair replaces the existing driver, so there are no duplicates. The"
                " existing drivers list below removes them one at a time.",
            ),
            _list_section(
                _SECTION_HOW,
                "1. Select the sprite mesh as the active object.",
                "2. Pick an Armature in the box (any object, no selection needed).",
                "3. Pick a Bone from the dropdown (lists every bone of the armature).",
                "4. Pick the source axis (default ROT_Y = rotation into the screen).",
                "5. Click Drive from Bone; the driver lands in the Drivers Editor.",
            ),
            _section(
                "Caveats",
                "The two-range map covers most cases; the Advanced toggle swaps in a raw"
                " expression. region_x and friends are clamped [0,1], so a large bone"
                " rotation saturates - tune the input/output ranges or the expression.",
            ),
            _section(
                "Hard swap vs gradual",
                "This shortcut is for GRADUAL parameter mapping (iris scroll, region nudge)."
                " For HARD texture swaps (forearm front/back), the slot system is the right"
                " primitive.",
            ),
        ),
    ),
    "sprite_bone_parent": HelpTopic(
        title="Attach to Bone",
        summary="Rigid-attach a sprite to one bone without a slot.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Parents the active sprite to a single bone as a rigid attachment, the"
                " non-slot way to make a sprite follow a bone. It is authored"
                " keep-transform, so the sprite stays where it is instead of jumping to"
                " the bone tail. The sprite then rides that bone's pose. Clear Bone Parent"
                " removes it, leaving the sprite where it sits.",
            ),
            _list_section(
                _SECTION_HOW,
                "1. Select the sprite as the active object.",
                "2. Pick the rig in the Skeleton panel (or be in Pose Mode with the"
                " target bone active to prefill it).",
                "3. Click Parent To Bone and confirm the bone in the dialog.",
                "4. Clear Bone Parent detaches it again.",
            ),
            _section(
                "Where it fits",
                "Exports as a Sprite2D parented to that Bone2D (the element's bone field)."
                " Use it for a static prop or facial part pinned to one bone.",
            ),
            _section(
                "Caveats",
                "A bone in the picture plane (drawn up/across the figure) rotates the rigid"
                " sprite out of the camera plane - the panel warns when this happens. For a"
                " flat follow on any bone, or for swappable attachments, use a slot instead.",
            ),
        ),
    ),
    "quick_armature": HelpTopic(
        title="Quick Armature",
        summary="Click-drag in the viewport to draw bones without entering Edit Mode.",
        sections=(
            _section(
                _SECTION_WHAT,
                "A modal viewport tool that creates or extends a 'Proscenio.QuickRig'"
                " armature, one bone per click-drag. Each press records the bone head on the"
                " world Y=0 picture plane; each release records the tail and lands the bone."
                " It speeds up the rough-sketch phase before refining in Edit Mode.",
            ),
            _list_section(
                _SECTION_HOW,
                "1. Click 'Quick Armature' in the Skeleton subpanel.",
                "2. Click-drag in the 3D viewport: press = head, release = tail.",
                "3. Hold Shift on press to start a new root instead of chaining"
                " (chaining is the default; see the subpanel toggle).",
                "4. Hold Ctrl to snap to the world grid; Esc or right-click exits.",
            ),
            _section(
                "Caveats",
                "Bones are flat on the Y=0 plane (this is a 2D pipeline). Drags shorter than"
                " 1e-4 world units are skipped to avoid degenerate zero-length bones. The"
                " QuickRig armature is identical to any hand-built one - rename it, parent"
                " meshes, weight-paint, or merge it into your main rig as usual.",
            ),
        ),
    ),
    "outliner": HelpTopic(
        title="Outliner",
        summary="A sprite-centric flat list of slots, sprite meshes, and armatures.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Filters every Blender object down to the ones Proscenio cares about, sorts"
                " them by category (slots, then attachments, then sprite meshes, then"
                " armatures), and lets you click a row to make that object active. It"
                " replaces Blender's native outliner for big rigs where finding one mesh"
                " means scrolling and expanding every time.",
            ),
            _list_section(
                _SECTION_HOW,
                "1. Type in the filter input - a live filter on object names.",
                "2. Click a row to make that object active + selected (the active-element"
                " and skeleton subpanels populate accordingly).",
                "3. Shift / Ctrl-click extends or toggles the selection; the radio dot marks"
                " every selected row, not just the active one.",
                "4. Click the SOLO icon to pin a favorite; toggle 'Favorites only' to hide"
                " everything else.",
            ),
            _section(
                "Where it fits",
                "A pure authoring shortcut - favorites and filter state live entirely on the"
                " Blender side. The .proscenio export is untouched.",
            ),
        ),
    ),
    "slot_system": HelpTopic(
        title="Slot system",
        summary="Empty + child meshes = one slot; animation flips visibility per key.",
        sections=(
            _section(
                _SECTION_WHAT,
                "A slot presents one of N attachment meshes at a time. Use it for hard"
                " texture swaps - forearm front/back, sword/staff/empty, brow up/down,"
                " expression swap. It differs from the driver shortcut, which is for gradual"
                " parameter mapping.",
            ),
            _list_section(
                _SECTION_HOW,
                "1. Click 'Create Slot'. With meshes selected they wrap into the new Empty"
                " as attachments; without, an empty slot anchors at the active bone.",
                "2. Promote selected meshes into an existing slot via 'Add Selected' in the"
                " Active Slot panel.",
                "3. Click the SOLO icon next to a row to pick the attachment shown at scene"
                " load (the default).",
                "4. Animate the swap by keyframing the slot's attachment value in the Action"
                " editor.",
            ),
            _section(
                "Mixing mesh + sprite attachments",
                "Slots are kind-agnostic: one slot can hold mesh (weight-painted) AND sprite"
                " (texture-sliced) children - say an eye slot with two mesh attachments"
                " (open/closed) plus one sprite (a 4-cell glow cycle). How each child was"
                " produced in Photoshop does not matter.",
            ),
            _section(
                "What lands in Godot",
                "Each slot becomes a Node2D parent under the bone with N sibling"
                " Polygon2D/Sprite2D children. The default attachment starts visible, the"
                " others hidden; the slot_attachment track flips visibility per key with"
                " constant interpolation.",
            ),
        ),
    ),
    "sprite_frame_preview": HelpTopic(
        title="Sprite-frame preview material",
        summary="Slice the spritesheet live in Material Preview via shader nodes + drivers.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Inserts a SpriteFrameSlicer node group between the material's TexCoord and"
                " ImageTexture nodes, then drives the slicer inputs from"
                " obj.proscenio.frame/hframes/vframes so the visible cell tracks the panel"
                " and animation values. Without it, Blender shows the full atlas on the quad.",
            ),
            _list_section(
                _SECTION_HOW,
                "1. Select a sprite mesh.",
                "2. Click 'Setup Preview' in the Active Element panel.",
                "3. Switch to Material Preview - the active cell shows on the quad and"
                " updates live as 'frame' animates.",
                "4. 'Remove Preview' un-wires the slicer and drops the drivers, restoring the"
                " full-atlas render.",
            ),
            _list_section(
                "Caveats",
                "- Solid / Workbench engines only honor diffuse_color, so the slicer is"
                " invisible there.",
                "- Atlases with padding between cells are not yet supported; the slicer"
                " assumes contiguous cells.",
                "- Setup Preview is idempotent: an existing slicer + drivers are refreshed"
                " without duplicating nodes.",
            ),
        ),
    ),
    "pose_library": HelpTopic(
        title="Save Pose to Library",
        summary="Bundle the current armature pose into a Blender Asset Browser entry.",
        sections=(
            _section(
                _SECTION_WHAT,
                "A thin shim over Blender's native poselib.create_pose_asset, wrapped with"
                " sensible defaults so authors get a one-click entry point in the Skeleton"
                " subpanel instead of digging through the menus every time.",
            ),
            _list_section(
                _SECTION_HOW,
                "1. Enter Pose Mode on the active armature.",
                "2. Set the desired pose - rotate / translate / scale bones.",
                "3. Click 'Save Pose to Library'.",
                "4. The pose lands in the Asset Browser as '<action>.<frame>' (or"
                " '<armature>.<frame>' when no action is active).",
                "5. Open Window > Asset Browser to apply the saved pose later.",
            ),
            _section(
                "Where it fits",
                "Pose assets live entirely on the Blender side - they never reach the"
                " .proscenio. Use them to library and reuse poses across animations,"
                " characters, or projects; animation tracks still drive the runtime.",
            ),
            _section(
                "Caveats",
                "Requires a Blender with the poselib operator. The shim does not curate the"
                " Asset Browser layout - assets land in the active asset library, configured"
                " via Preferences > File Paths > Asset Libraries.",
            ),
        ),
    ),
    "import_photoshop": HelpTopic(
        title="Import Photoshop Manifest",
        summary="Stamp planes + a stub armature from a v1 PSD manifest.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Reads a manifest emitted by the Proscenio Photoshop UXP plugin, stamps one"
                " mesh per layer, composes spritesheet textures for sprite groups, and"
                " parents everything to a stub root armature.",
            ),
            _list_section(
                _SECTION_HOW,
                "1. Run the Proscenio Exporter panel in Photoshop on a layered PSD.",
                "2. Click Import Photoshop Manifest and pick the resulting .json.",
                "3. Choose placement: landed (feet on Z=0) or centered (manifest center).",
                "4. Refine the stub armature and paint weights in Blender.",
            ),
            _section(
                "Idempotent re-import",
                "Meshes carry a proscenio_import_origin = 'psd:<layer>' tag, so re-running on"
                " the same manifest reuses existing meshes - user-set rotation, parenting,"
                " and weights survive the round trip.",
            ),
        ),
        see_also=(
            "https://github.com/firebound/proscenio/tree/main/examples/generated/simple_psd",
        ),
    ),
    "mesh_generation": HelpTopic(
        title="Mesh Generation",
        summary="Turn a sprite's alpha into a deformable cutout mesh.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Traces the active image's alpha contour into a mesh you can weight-paint and"
                " deform. Interior Mode picks SIMPLE (sparse, Spine-like) or DENSE (a uniform"
                " plus bone-aware fill).",
            ),
            _section(
                "Automesh from Alpha",
                "A one-shot trace using the panel defaults. Re-runs preserve the UV-pinned"
                " base quad via the proscenio_base_sprite vertex group.",
            ),
            _section(
                "Automesh Interactive / Debug Pipeline",
                "Interactive is a modal preview that lets you cut / extend / fold the"
                " silhouette before the geometry commits. Debug Pipeline emits per-stage"
                " wireframe companions for inspecting the trace.",
            ),
            _section(
                "Where it fits",
                "Authoring only - the generated geometry exports as a Polygon2D, but the"
                " trace tool itself never reaches the .proscenio.",
            ),
        ),
    ),
    "weight_paint": HelpTopic(
        title="Weight Paint",
        summary="Bind a cutout mesh to the rig and refine its bone weights.",
        sections=(
            _section(
                _SECTION_WHAT,
                "A mesh-only panel: bind the active mesh to the picked armature, then refine"
                " the per-bone weights. Bind and the resulting weights export to the"
                " Polygon2D; the edit and snapshot tools are blender-side.",
            ),
            _section(
                "Bind",
                "Binds to the armature picked in the Skeleton panel. Per-bone Soft / Hard"
                " rows override the default falloff for individual bones.",
            ),
            _section(
                "Edit Weights / Snapshot",
                "Edit Weights enters a modal weight-paint session with brush presets."
                " Snapshot tracks paint provenance, restores saved weights, and"
                " exports/imports the weight snapshot to a file.",
            ),
            _section(
                "Weight Transfer",
                "Copies weights from the active mesh to the other selected meshes - handy for"
                " symmetric or split cutouts.",
            ),
        ),
    ),
    "helpers": HelpTopic(
        title="Helpers",
        summary="Viewport authoring aids that are not part of the export pipeline.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Convenience tools that set up the Blender viewport for 2D cutout work. None"
                " of them touch the .proscenio export.",
            ),
            _section(
                "Preview Camera",
                "Drops an orthographic front camera framed the way the Godot importer"
                " expects, so what you see matches the runtime framing.",
            ),
        ),
    ),
    "active_mesh": HelpTopic(
        title="Active Mesh",
        summary="The Polygon2D fields of the selected mesh element.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Shown when the active element type is Mesh. The mesh exports as a Polygon2D"
                " - a deformable cutout with UVs and bone weights. The vertices carry their"
                " own positions, so the Blender origin is baked in at export.",
            ),
        ),
    ),
    "active_sprite": HelpTopic(
        title="Active Sprite",
        summary="The Sprite2D spritesheet fields of the selected sprite element.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Shown when the active element type is Sprite. The mesh exports as a Sprite2D"
                " that slices a spritesheet: an hframes x vframes grid plus a frame index."
                " The quad geometry itself is not exported - only this metadata.",
            ),
            _list_section(
                "Fields",
                "- hframes / vframes: the spritesheet grid (columns x rows).",
                "- frame: the cell shown at rest pose; animation tracks override it.",
            ),
            _section(
                "Origin and the pivot",
                "A sprite is always centered on its node (Godot Sprite2D.centered is a fixed"
                " internal constant - flipping it would break the exporter's offset math, so"
                " it is no longer an authoring toggle). The PSD [origin] tag sets the pivot:"
                " the importer places the object origin there and the exporter writes a"
                " Sprite2D offset that shifts the texture so it lines up with that origin."
                " [origin] is sprite-only - on a Mesh it has no pivot to set and is ignored.",
            ),
        ),
    ),
    "texture_region": HelpTopic(
        title="Texture Region",
        summary="Which part of the texture this element samples.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Auto reads the region from the mesh UV bounds at export. Manual reads"
                " region_x/y/w/h verbatim - use it for atlas slicing. 'Snap to UV bounds'"
                " fills the manual fields from the current UV layout.",
            ),
            _section(
                "Reproject UV vs region",
                "Three controls, three jobs. Reproject UV rebuilds the mesh's UV layout from"
                " its geometry (a planar projection: U follows X, V follows Z) so the texture"
                " lines up again after you move vertices. The region (Auto / Manual) then"
                " decides which slice of the texture those UVs sample. Snap to UV bounds"
                " freezes the current Auto bounds into the Manual fields. Reproject changes"
                " the UVs; the region only reads them.",
            ),
        ),
    ),
    "bind": HelpTopic(
        title="Bind",
        summary="Bind the active mesh to the target armature's bones.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Builds the vertex weights that let the rig deform this mesh. Mode picks the"
                " algorithm; Bone Heat (Blender native) is the default and best for most 2D"
                " rigs. Proximity / Envelope / Single-nearest / Empty are fallbacks exposed"
                " via the F3 redo panel.",
            ),
            _section(
                "Per-bone Soft / Hard",
                "Override a single bone's falloff. Soft = proximity falloff: the bone shares"
                " weight smoothly with neighbours (good for cloth, hair). Hard ="
                " single-nearest: a crisp boundary, no bleed (good for finger joints). A bone"
                " with no override uses the Mode's default family. The list scrolls, so a"
                " many-bone rig does not push the Bind button off-screen.",
            ),
        ),
    ),
    "edit_weights": HelpTopic(
        title="Edit Weights",
        summary="Modal weight-paint session with 2D brush-curve presets.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Enters Weight Paint on the active group with a provenance overlay (which"
                " verts are auto-seed vs hand-painted). The brush-curve presets (Hard Edge /"
                " Soft Falloff / Crease / Smooth Blend) shape the brush falloff for common 2D"
                " tasks without a trip to the curve editor.",
            ),
            _list_section(
                _SECTION_HOW,
                "1. Bind the mesh first (the button is disabled until then).",
                "2. Click Edit Weights, paint, then ESC to exit and restore brush state.",
            ),
            _section(
                "Viewport display + posing",
                "Weight Opacity and Zero Weights (the native Viewport Overlay levers) let the"
                " texture show through the weight gradient while painting. To test"
                " deformation, pose the bones live inside Weight Paint mode - select the"
                " armature, enter Pose, and scrub or rotate while painting.",
            ),
        ),
    ),
    "snapshot": HelpTopic(
        title="Snapshot",
        summary="Save + restore weights so an automesh regen does not wipe paint.",
        sections=(
            _section(
                _SECTION_WHAT,
                "The weight snapshot stores, per vertex, a UV anchor + its weights + where"
                " they came from (auto-seed / hand paint / reprojected). It is the safety net"
                " that survives a mesh rebuild.",
            ),
            _list_section(
                "Controls",
                "- Preserve weights on regen: before an Automesh re-run, snapshot the weights"
                " by UV and reproject them onto the new mesh. Off = the regen wipes paint.",
                "- Reset to Last Saved Weights: revert the live weights to the last snapshot.",
                "- The N paint / M seed / K reprojected pill shows where each vert's weight"
                " came from.",
            ),
            _list_section(
                "File export / import",
                "- Export Snapshot: write the weight snapshot to a JSON file (version-control"
                " weights, or move them between files).",
                "- Import Snapshot: load one back. It applies onto the live weights when the"
                " topology still matches; otherwise it stores the snapshot only (re-run"
                " Automesh with Preserve weights on regen to reproject).",
            ),
        ),
    ),
    "weight_transfer": HelpTopic(
        title="Weight Transfer",
        summary="Copy weights from the active mesh to the other selected meshes.",
        sections=(
            _section(
                _SECTION_WHAT,
                "For each vertex of every other selected mesh, copies the weights of the"
                " nearest vertex on the active mesh (by world position). It is an imprint:"
                " the meshes must overlap in space, but different vertex counts are fine.",
            ),
            _section(
                "Caveats",
                "Target verts beyond the Max Distance (F3 redo) get no weights. Use it for"
                " layered or split cutouts that sit on top of a rigged base.",
            ),
        ),
    ),
    "automesh_alpha": HelpTopic(
        title="Automesh from Alpha",
        summary="A one-shot trace of the sprite alpha into a deformable mesh.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Walks the image alpha contour into a mesh you can weight-paint. Re-runs"
                " preserve the UV-pinned base quad (the proscenio_base_sprite group).",
            ),
            _list_section(
                "Key settings",
                "- Trace resolution: an image downscale factor. Higher (1.0 = full image)"
                " traces a finer silhouette but costs more; it sets outline fidelity, not"
                " vertex count.",
                "- Interior Mode (parent panel): Simple (sparse) or Dense (filled).",
                "- Density follows bones (Dense only, off by default): pack more triangles"
                " near the target's bones, where deformation happens.",
            ),
        ),
    ),
    "automesh_interactive": HelpTopic(
        title="Automesh Interactive",
        summary="Step through the trace, editing the silhouette before it commits.",
        sections=(
            _section(
                _SECTION_WHAT,
                "A modal preview of the same trace. Advance through the stages to cut /"
                " extend the outline and place interior points, then commit the mesh. Nothing"
                " is written until you confirm the final stage.",
            ),
            _list_section(
                _SECTION_HOW,
                "1. Select a mesh with an image texture; click Author Mesh (interactive).",
                "2. ENTER advances a stage, BACKSPACE steps back, ESC cancels.",
                "3. The final stage builds the mesh (the same result as Automesh from Alpha"
                " plus your edits).",
            ),
        ),
    ),
    "debug_pipeline": HelpTopic(
        title="Debug Pipeline",
        summary="Emit per-stage wireframe companions for inspecting the trace.",
        sections=(
            _section(
                _SECTION_WHAT,
                "A developer aid (shown only with debug mode on). Pick a stage of the alpha"
                " trace (raw contours, smoothed, resampled, interior, bridges, fill) and the"
                " next Automesh run leaves a wireframe companion in the Proscenio.Debug"
                " collection. Clear Debug Companions removes them.",
            ),
        ),
    ),
    "active_slot": HelpTopic(
        title="Active Slot",
        summary="The attachment detail of the selected slot.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Lists the slot's child meshes (its attachments), lets you mark which one is"
                " visible at scene load (the SOLO star = default), and adds the selected mesh"
                " as a new attachment. See the Slots help for the overview.",
            ),
            _section(
                "Bind to Bone / Unbind",
                "Bind to Bone makes the slot follow a bone in the viewport the same way it"
                " follows at runtime in Godot: an object-parent plus a Child Of constraint"
                " that cancels the bone rest, staying flat for any bone orientation. Hand"
                " bone-parenting the Empty also works and exports, but only for bones"
                " pointing into the screen - an in-plane bone collapses the attachment quads,"
                " and the panel warns when it does. Bind refuses when a slot already follows;"
                " to rebind after moving it, Unbind then Bind.",
            ),
            _section(
                "Editing raw Custom Properties",
                "The SOLO star sets the default through the panel. Editing the raw"
                " proscenio_slot_default Custom Property directly exports and validates the"
                " same value, but the panel does not live-refresh to a raw edit - use the"
                " panel buttons as the expected workflow.",
            ),
        ),
    ),
    "armature": HelpTopic(
        title="Armature",
        summary="Read-only bone hierarchy of the picked armature.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Lists every bone the writer would export, indented by depth, with"
                " connected / relative flags. Click a bone to select it in the viewport;"
                " Shift / Ctrl extend or toggle the selection. Inspection only - it never"
                " changes the .proscenio output.",
            ),
        ),
    ),
    "pose_mode": HelpTopic(
        title="Pose Mode",
        summary="Pose-only authoring shortcuts (blender-only).",
        sections=(
            _section(
                _SECTION_WHAT,
                "Bake Current Pose keys every bone at the playhead. Toggle IK adds or removes"
                " an IK constraint plus a control bone at the chain tip. Save Pose to Library"
                " stores the pose as a Blender asset. None of these reach the .proscenio -"
                " they are authoring conveniences.",
            ),
        ),
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
