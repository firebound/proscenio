"""The ``HELP_TOPICS`` table - one entry per Proscenio ``?`` button.

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
"""

from __future__ import annotations

from .help_topics_model import (
    _SECTION_HOW,
    _SECTION_WHAT,
    _SECTION_WHERE,
    HelpTopic,
    _list_section,
    _section,
)

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
                "experimental",
                "Implemented and usable, but under active development - the surface"
                " and its output may still change. Test before relying on it.",
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
        summary=(
            "The Pipeline panel is the addon's in and out: import a Photoshop manifest,"
            " validate the scene, and export .proscenio. The whole flow is"
            " Photoshop -> Blender -> Godot over one JSON contract."
        ),
        sections=(),
    ),
    "active_element": HelpTopic(
        title="Active Element",
        summary=(
            "The Element panel holds the per-element settings the writer reads for the"
            " active mesh - chiefly the element type that picks the Godot node"
            " (Mesh -> Polygon2D, Sprite -> Sprite2D)."
        ),
        sections=(),
    ),
    "skeleton": HelpTopic(
        title="Skeleton",
        summary=(
            "The Skeleton panel picks the project-wide armature that every skeleton"
            " operation, bind, and automesh step targets - the single source of truth"
            " for the rig. It serves the rigging stage."
        ),
        sections=(),
    ),
    "rig_ui": HelpTopic(
        title="Rig UI",
        summary=(
            "Per-collection select buttons + visibility toggles built from the picked"
            " armature's native bone collections. Nested collections (Blender 4.1+)"
            " group into a labelled row of child buttons. A Blender-only authoring"
            " convenience - it selects and shows bones, it does not export."
        ),
        sections=(
            _section(
                _SECTION_HOW,
                "Each row's button selects that collection's bones in the viewport"
                " (a parent grabs its whole subtree). The eye toggles the"
                " collection's visibility (a hidden parent hides its children). The"
                " theme selector's columns line up on every row, but only a"
                " top-level row's picker is live and colors that whole subtree -"
                " one color control per tree; nested rows reserve the columns."
                " Assign bones to collections in Blender's native Bone Collections"
                " panel; this panel only consumes them.",
            ),
        ),
    ),
    "animation": HelpTopic(
        title="Animation",
        summary=(
            "The Animation panel lists every action in the file - the actions the writer"
            " emits as Godot AnimationPlayer tracks at export. Click one to assign it to"
            " the picked armature so the timeline plays it."
        ),
        sections=(),
    ),
    "atlas": HelpTopic(
        title="Atlas",
        summary=(
            "The Atlas panel packs the scene's source images into one shared atlas,"
            " rewrites UVs to address it, and restores the originals on Unpack. An"
            " optional optimization before export."
        ),
        sections=(),
    ),
    "validation": HelpTopic(
        title="Validate",
        summary=(
            "Part of Pipeline. Walks the scene and reports issues before you export."
            " Click Validate; each row click-selects the offending object. Errors block"
            " Export; warnings inform but still export."
        ),
        sections=(
            _list_section(
                "What it catches",
                "- A missing armature when meshes carry vertex groups.",
                "- Bone references that no longer exist on the armature.",
                "- Atlas image files missing from disk.",
                "- Sprite elements without hframes/vframes.",
            ),
        ),
    ),
    "export": HelpTopic(
        title="Export",
        summary=(
            "Part of Pipeline. Runs the writer, validates the result against the"
            " Proscenio JSON schema, and writes the .proscenio. The path is sticky -"
            " remembered next to the .blend so Re-export skips the file dialog."
        ),
        sections=(
            _section(
                "Pixels per unit",
                "The conversion ratio between Blender world units and Godot pixels. Default"
                " 100, so 1 m in Blender = 100 px in Godot.",
            ),
        ),
    ),
    "drive_from_bone": HelpTopic(
        title="Drive from Bone",
        summary=(
            "Part of Element. Wires a Blender driver from a pose bone into a sprite"
            " proscenio.* property, for changes that vary continuously with rotation (iris"
            " scroll, a threshold flag). For a clean either/or swap, use a slot instead."
        ),
        sections=(
            _section(
                "Caveats",
                "Re-running on the same target replaces its driver, so there are no"
                " duplicates; the existing-drivers list removes them one at a time. The"
                " default clamped linear map covers most cases; the Advanced toggle swaps in"
                " a raw expression. region_x and friends clamp to [0,1], so a large bone"
                " rotation saturates - tune the ranges or the expression.",
            ),
        ),
    ),
    "sprite_bone_parent": HelpTopic(
        title="Attach to Bone",
        summary=(
            "Part of Element, shown for a Sprite element. Rigidly parents the sprite to a"
            " single bone - the non-slot way to make it follow one bone, with no swap. It"
            " exports as a Sprite2D parented to that Bone2D."
        ),
        sections=(
            _section(
                "Caveats",
                "Authored keep-transform, so the sprite stays put instead of jumping to the"
                " bone tail; Clear Bone Parent detaches it. A bone in the picture plane"
                " rotates the rigid sprite out of the camera plane - the panel warns, and a"
                " slot is the right primitive for a flat follow on any bone or a swappable"
                " attachment.",
            ),
        ),
    ),
    "quick_armature": HelpTopic(
        title="Quick Armature",
        summary=(
            "Part of Skeleton. A modal viewport tool that draws bones onto the Y=0 picture"
            " plane one press-drag at a time (press = head, release = tail) without"
            " entering Edit Mode, building or extending a Proscenio.QuickRig armature."
        ),
        sections=(
            _section(
                _SECTION_HOW,
                "Click-drag in the 3D viewport; hold Shift on press to start a new root"
                " instead of chaining, Ctrl to snap to the grid, Esc or right-click to exit."
                " Drags under 1e-4 units are skipped. The QuickRig armature is identical to a"
                " hand-built one - rename, parent, weight-paint, or merge it as usual.",
            ),
        ),
    ),
    "outliner": HelpTopic(
        title="Outliner",
        summary=(
            "The Outliner panel is an element-centric flat list of the objects Proscenio"
            " cares about - slots, attachments, meshes, armatures - so you select one"
            " fast on a big rig. A pure authoring shortcut."
        ),
        sections=(),
    ),
    "slot_system": HelpTopic(
        title="Slot system",
        summary=(
            "The Slots panel builds slots: an Empty plus child meshes where one"
            " attachment shows at a time, for hard either/or swaps (forearm front/back,"
            " sword/staff). Animation flips which one shows per key."
        ),
        sections=(),
    ),
    "sprite_frame_preview": HelpTopic(
        title="Material Preview",
        summary=(
            "The Material Preview sub-box of Active Sprite. Setup Preview wires a"
            " SpriteFrameSlicer node group plus drivers so Material Preview shows the"
            " active cell on the quad instead of the full atlas, tracking frame live."
        ),
        sections=(
            _section(
                "Caveats",
                "Setup Preview is idempotent - re-running refreshes the slicer without"
                " duplicating nodes; Remove Preview un-wires it. The slicer is invisible"
                " under the Solid / Workbench engines (diffuse_color only) and assumes"
                " contiguous cells - atlases with padding are not yet supported.",
            ),
        ),
    ),
    "pose_library": HelpTopic(
        title="Save Pose to Library",
        summary=(
            "The Save Pose to Library button in Pose Mode. A one-click shim over Blender's"
            " native poselib.create_pose_asset: set a pose, click it, and the pose lands in"
            " the Asset Browser as <action>.<frame> (or <armature>.<frame>)."
        ),
        sections=(
            _section(
                _SECTION_WHERE,
                "Pose assets are blender-only - they never reach the .proscenio; animation"
                " tracks still drive the runtime. Reuse them across animations, characters,"
                " or projects. Assets land in the active asset library (Preferences > File"
                " Paths > Asset Libraries); apply them from Window > Asset Browser.",
            ),
        ),
    ),
    "import_photoshop": HelpTopic(
        title="Import Photoshop Manifest",
        summary=(
            "Part of Pipeline. Reads a manifest from the Proscenio Photoshop plugin,"
            " stamps one mesh per layer, composes spritesheet textures for sprite groups,"
            " and parents everything to a stub root armature you then refine."
        ),
        sections=(
            _section(
                "Idempotent re-import",
                "Meshes carry a proscenio_import_origin = 'psd:<layer>' tag, so re-running"
                " on the same manifest reuses existing meshes - user-set rotation,"
                " parenting, and painted weights survive the round trip (reprojected from"
                " the sidecar when a layer moved).",
            ),
        ),
    ),
    "mesh_generation": HelpTopic(
        title="Mesh Generation",
        summary=(
            "The Mesh Generation panel traces a sprite's alpha contour into a deformable"
            " cutout mesh you can weight-paint - one-shot or through an interactive"
            " modal. The mesh-authoring stage before rigging."
        ),
        sections=(),
    ),
    "weight_paint": HelpTopic(
        title="Weight Paint",
        summary=(
            "The Weight Paint panel binds a cutout mesh to the picked rig and refines its"
            " per-bone weights - the mesh-only step that makes a Polygon2D deform. It"
            " serves the rigging stage."
        ),
        sections=(),
    ),
    "helpers": HelpTopic(
        title="Helpers",
        summary=(
            "The Helpers panel collects viewport convenience tools for 2D cutout work -"
            " chiefly a front orthographic Preview Camera framed the way the Godot"
            " importer expects. None of them touch the export."
        ),
        sections=(),
    ),
    "active_mesh": HelpTopic(
        title="Active Mesh",
        summary="Part of Element, shown when the element type is Mesh.",
        sections=(
            _section(
                _SECTION_WHAT,
                "The mesh exports as a Polygon2D - a deformable cutout with UVs and bone"
                " weights. Its vertices carry their own positions, so the Blender origin is"
                " baked in at export.",
            ),
        ),
    ),
    "active_sprite": HelpTopic(
        title="Active Sprite",
        summary=(
            "Part of Element, shown when the element type is Sprite. The element exports as"
            " a Sprite2D that slices a spritesheet; only this metadata is exported, not the"
            " quad geometry."
        ),
        sections=(
            _list_section(
                "Fields",
                "- hframes / vframes: the spritesheet grid (columns x rows).",
                "- frame: the cell shown at rest pose; animation tracks override it.",
            ),
        ),
    ),
    "texture_region": HelpTopic(
        title="Texture Region",
        summary=(
            "Part of Element. Which part of the texture this element samples: Auto reads it"
            " from the mesh UV bounds at export; Manual reads region_x/y/w/h verbatim for"
            " atlas slicing."
        ),
        sections=(
            _section(
                _SECTION_HOW,
                "On a mesh in Manual mode, Snap to UV bounds fills the four fields from the"
                " current UV layout. Reproject UV (over in Active Mesh) rebuilds the UVs;"
                " the region only reads them.",
            ),
        ),
    ),
    "bind": HelpTopic(
        title="Bind",
        summary=(
            "Part of Weight Paint. Builds the vertex weights that let the picked rig deform"
            " this mesh. Mode picks the algorithm - Bone Heat (Blender native) is the"
            " default; Proximity / Envelope / Single-nearest / Empty are alternatives."
        ),
        sections=(
            _section(
                "Per-bone Soft / Hard",
                "Override a single bone's falloff. Soft shares weight smoothly with"
                " neighbours (cloth, hair); Hard gives a crisp single-nearest boundary"
                " (finger joints); the X clears it back to the Mode default. These apply only"
                " to the planar modes - Bone Heat ignores them. The list scrolls so a"
                " many-bone rig does not push the Bind button off-screen.",
            ),
        ),
    ),
    "edit_weights": HelpTopic(
        title="Edit Weights",
        summary=(
            "Part of Weight Paint. Enters a modal weight-paint session on the active group"
            " with a provenance overlay (auto-seed vs hand-painted) and brush-curve presets"
            " (Hard Edge / Soft Falloff / Crease / Smooth Blend) for common 2D tasks."
        ),
        sections=(
            _section(
                _SECTION_HOW,
                "Bind the mesh first (the button is disabled until then). Paint, then ESC to"
                " exit and restore brush state. The Viewport display box surfaces Weight"
                " Opacity and Zero Weights so the texture shows through the gradient; to test"
                " deformation, pose the bones live in Weight Paint mode.",
            ),
        ),
    ),
    "snapshot": HelpTopic(
        title="Snapshot",
        summary=(
            "Part of Weight Paint. The weight snapshot stores per vertex a UV anchor plus"
            " its weights and provenance (auto-seed / hand-paint / reprojected) - the safety"
            " net that survives a mesh rebuild."
        ),
        sections=(
            _section(
                "Controls",
                "Preserve weights on regen snapshots the weights by UV before an Automesh"
                " re-run and reprojects them onto the new mesh, so the regen preserves paint"
                " (off, it wipes it). Reset to Last Saved Weights reverts to the snapshot."
                " Export / Import Snapshot move the snapshot through a JSON file; an import"
                " applies onto the live mesh when the topology matches, else it stores only.",
            ),
        ),
    ),
    "weight_transfer": HelpTopic(
        title="Weight Transfer",
        summary=(
            "Part of Weight Paint. Copies weights from the active mesh to every other"
            " selected mesh by nearest world-space vertex - an imprint for layered or split"
            " cutouts that overlap a rigged base. Different vertex counts are fine."
        ),
        sections=(
            _section(
                "Caveats",
                "The meshes must overlap in space; target verts beyond the Max Distance (the"
                " panel field, also in the F9 redo) get no weights.",
            ),
        ),
    ),
    "automesh_alpha": HelpTopic(
        title="Automesh from Alpha",
        summary=(
            "Part of Mesh Generation. A one-shot trace that walks the image alpha contour"
            " into a deformable mesh using the panel defaults; re-runs preserve the"
            " UV-pinned base quad."
        ),
        sections=(
            _list_section(
                "Key settings",
                "- Trace resolution: an image downscale factor (1.0 = full image). It sets"
                " outline fidelity, not vertex count - higher traces finer but costs more.",
                "- Preserve weights on regen: snapshots paint by UV and reprojects it onto"
                " the new mesh, so the regen does not wipe weights.",
            ),
        ),
    ),
    "automesh_interactive": HelpTopic(
        title="Automesh Interactive",
        summary=(
            "Part of Mesh Generation. A modal preview of the same trace: advance through the"
            " stages to cut / extend the outline and place interior points, then commit."
            " Nothing is written until you confirm the final stage."
        ),
        sections=(
            _section(
                _SECTION_HOW,
                "Select a mesh with an image texture and click Author Mesh (interactive)."
                " ENTER advances a stage, BACKSPACE steps back, ESC cancels. The final stage"
                " builds the mesh - the same result as Automesh from Alpha plus your edits.",
            ),
        ),
    ),
    "manual_mesh": HelpTopic(
        title="Manual Mesh",
        summary=(
            "Build a mesh element's silhouette by hand - click the vertices instead of"
            " tracing the alpha. A separate mode from the automeshes (one way per element);"
            " a live triangulation previews the result."
        ),
        sections=(
            _list_section(
                _SECTION_HOW,
                "Select a mesh element with an image texture, then Draw with vertices.",
                "LMB places a vertex; click the first vertex to close the loop.",
                "RMB drags a placed vertex; DEL (or Ctrl+Z) drops the last.",
                "Wheel / 0-9 subdivide the edge being drawn; X / Z lock the axis.",
                "ENTER builds the mesh, ESC cancels. The panel button toggles to Exit.",
            ),
            _section(
                _SECTION_WHERE,
                "Use this instead of Automesh when the alpha trace cannot find the shape"
                " (faint edges, overlapping art) or you want exact control. The automesh"
                " trace fields do not apply here; its own Interior mode toggle picks SIMPLE"
                " (just your contour) or DENSE (a uniform interior fill), and Tab adds"
                " interior point / fold detail inside the shape.",
            ),
        ),
    ),
    "debug_pipeline": HelpTopic(
        title="Debug Pipeline",
        summary="Part of Mesh Generation. A developer aid, shown only with debug mode on.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Pick a stage of the alpha trace (raw contours, smoothed, resampled,"
                " interior, bridges, fill) and the next Automesh run leaves a wireframe"
                " companion in the Proscenio.Debug collection. Clear Debug Companions"
                " removes them.",
            ),
        ),
    ),
    "active_slot": HelpTopic(
        title="Active Slot",
        summary=(
            "Part of Slots. Lists the active slot's child meshes (its attachments), marks"
            " which shows at scene load (the SOLO star = default), and adds the selected"
            " mesh as a new attachment."
        ),
        sections=(
            _section(
                "Bind to Bone / Unbind",
                "Bind to Bone makes the slot follow a bone the way it does at runtime in"
                " Godot: an object-parent plus a Child Of constraint that stays flat for any"
                " bone orientation. Hand bone-parenting the Empty also exports, but only for"
                " bones pointing into the screen - an in-plane bone collapses the quads and"
                " the panel warns. Bind refuses when a slot already follows; Unbind then Bind"
                " to rebind.",
            ),
        ),
    ),
    "armature": HelpTopic(
        title="Active Armature",
        summary="Part of Skeleton. Read-only bone hierarchy of the picked armature.",
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
        summary="Part of Skeleton. Pose-only authoring shortcuts, all blender-only.",
        sections=(
            _section(
                _SECTION_WHAT,
                "Bake Current Pose keys every bone at the playhead. Toggle IK adds or removes"
                " an IK constraint plus a control bone at the chain tip. Save Pose to Library"
                " stores the pose as a Blender asset (its own ? covers the asset flow). These"
                " three never reach the .proscenio. Bake IK to Keyframes is the exception: it"
                " bakes the active bone's IK chain to bone keyframes over the action range"
                " and clears the IK constraint, so the exporter reads real bone motion"
                " instead of flat fcurves - run it before export on any animated IK chain.",
            ),
        ),
    ),
}
