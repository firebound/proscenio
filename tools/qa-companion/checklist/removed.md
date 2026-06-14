# Removed / condensed tests

Tests retired in the 2026-06 QA restructure (452 -> ~205): the surface was re-layered into global-chrome tests, per-subpanel visual inventory sweeps, and end-to-end flows. Each block below is the original test, kept for the record, with a `reason` pointing to where its behavior now lives. The full pre-restructure snapshot is in tools/qa-companion/.backup/.

## Condensed in the 2026-06 restructure

### BL-OUTLN-09 · Sprite-mesh bone-parent suffix label (' @ <bone>')
- status: pass
- review: drop
- observe: Row label reads '<name> @ <parent_bone>'; meshes not bone-parented show just '<name>'. Doc never mentions the '@ bone' affordance.
- intent: UNDOCUMENTED
- code: apps/blender/panels/outliner.py:62-63
- note: this was fixed, can be dropped as testable item
- reason: '@ bone' suffix fixed; label presence folded into BL-OUTLN-SWEEP

### BL-ELEM-11 · Isolated material checkbox
- status: n/a
- review: rephrase
- observe: material_isolated bool toggles; Custom Property mirrors; affects Pack Atlas behavior (material kept on this object).
- intent: UNDOCUMENTED on element doc; when packing, keep this sprite's own material instead of linking to the shared PackedAtlas material.
- code: apps/blender/panels/_draw_mesh.py:24; object_props.py:157-167
- note: definitely has the checkbox... this can be condensed to one single task about the active mesh subpanel as "has the items X, Y, Z...) but the behaviour expected shouldn't be tested here since it's part of a broader workflow (blender only)
- reason: behavior in FLOW-ATLAS-01 (isolated material); existence in BL-ELEM-MESH-SWEEP

### BL-ELEM-12 · Exclude from atlas checkbox
- status: n/a
- review: rephrase
- observe: exclude_from_atlas bool toggles; Custom Property mirrors; object skipped by Pack Atlas.
- intent: UNDOCUMENTED on element doc; keep this sprite out of Pack Atlas entirely (UVs/material untouched, ships own texture).
- code: apps/blender/panels/_draw_mesh.py:25; object_props.py:168-178
- reason: behavior in FLOW-ATLAS-01 (exclude from atlas); existence in BL-ELEM-MESH-SWEEP

### BL-SLOT-20 · Keyframe attachment button (per attachment, KEYFRAME_HLT)
- status: pending
- review: keep
- pre: Slot Empty active with the named attachment as a MESH child; a frame chosen.
- steps:
  1. Move the playhead to a frame > click the keyframe icon on an attachment row.
- observe: Sets empty[PROSCENIO_SLOT_INDEX]=index, inserts a keyframe at current frame, forces all keys on that fcurve to CONSTANT interpolation; reports 'keyed "<name>" (index N) at frame F'. Non-child name reports warning + CANCELLED.
- intent: UNDOCUMENTED - keys the chosen attachment visible from the current frame (the constant-interp slot swap exported as a Godot slot_attachment track).
- code: apps/blender/panels/slots.py:152-157 -> operators/slot/attachment.py:107-152
- reason: behavior in FLOW-SLOTSWAP-01/02, FLOW-SLOTCYCLE-01; existence in BL-SLOTS-ACTIVE-SWEEP

### BL-SKEL-36 · Preview Camera (create_ortho_camera) - listed in surface, drawn in Helpers panel
- status: pending
- review: keep
- pre: Any scene with proscenio props.
- steps:
  1. (Helpers panel) click 'Preview Camera', or F3 'Preview Camera'.
- observe: Creates/updates Proscenio.PreviewCam at (0,-10,0) facing +Y, type ORTHO, ortho_scale = max(res_x,res_y)/ppu; sets scene.camera, selects it. NOTE: not rendered on the Skeleton surface.
- intent: UNDOCUMENTED in 04-skeleton - adds/focuses an ortho camera sized to pixels_per_unit.
- code: apps/blender/operators/armature/authoring_camera.py:16-53; drawn at apps/blender/panels/helpers.py:32
- reason: wrong panel; Preview Camera kept as BL-HELP-05

### BL-SKEL-37 · Set Bone Mode (set_bone_mode) - listed in surface, belongs to Skinning panel
- status: pending
- review: keep
- pre: Active object is a MESH (operator poll).
- steps:
  1. (Skinning panel bind sub-box) toggle a per-bone mode row.
- observe: Writes obj['proscenio_bone_modes'] JSON; CLEAR drops the override. NOTE: this control does NOT appear on the Skeleton panel - it is INTERNAL and Skinning-owned.
- intent: UNDOCUMENTED in 04-skeleton - overrides per-bone bind mode SOFT/HARD/CLEAR (a Skinning feature).
- code: apps/blender/operators/skinning/set_bone_mode.py:23-62
- reason: wrong panel; Set Bone Mode kept as BL-WPAINT-OVERRIDE

### BL-WPAINT-32 · 'Show provenance overlay' checkbox
- status: pending
- review: keep
- observe: Toggles scene.proscenio.skinning.show_provenance_overlay. Outside the modal nothing is drawn - no draw handler is added/removed by this toggle (only edit_weights.invoke registers/forces the overlay). See finding.
- intent: UNDOCUMENTED on this surface (doc mentions a provenance overlay only inside the Edit Weights modal).
- code: apps/blender/panels/weight_paint.py:338 ; scene_props.py:299
- reason: no observable effect on this surface; covered by BL-WPAINT-18

### BL-WPAINT-17 · Edit Weights button (modal entry)
- status: pending
- review: keep
- pre: Mesh active; ENABLED only when picker set AND >=1 vertex group AND sidecar present (_edit_weights_button_enabled).
- steps:
  1. After binding, click 'Edit Weights'
- observe: Enters WEIGHT_PAINT mode, applies 2D paint preset (Front Faces off, mirror from picker), shows provenance overlay (cyan/white/gray), adds status-bar hints. Disabled (greyed) before bind.
- intent: Enters a modal weight-paint session on the active group with a provenance overlay; disabled until Bind.
- code: apps/blender/panels/weight_paint.py:265 -> operators/skinning/edit_weights.py:69 invoke
- reason: behavior in FLOW-DOLL-02 (Edit Weights modal); enable predicate in BL-WPAINT-SWEEP

### BL-ATLAS-12 · Pack Atlas button
- status: pending
- review: keep
- pre: Blend saved to disk (bpy.data.filepath set); Object Mode; at least one MESH with a source image and not exclude_from_atlas
- steps:
  1. Save .blend > Object Mode > select/have sprite meshes with source images > click 'Pack Atlas'.
- observe: Writes <stem>.atlas.png + <stem>.atlas.json next to the .blend; INFO report 'packed N sprite(s) into WxH px atlas -> file.png'; UVs and materials unchanged. Apply button then appears.
- intent: Walks every sprite with a texture, runs MaxRects packing, writes <blend>.atlas.png + .atlas.json; non-destructive (UVs/materials untouched).
- code: apps/blender/panels/atlas.py:58 -> operators/atlas_pack/pack.py:36
- reason: behavior in FLOW-ATLAS-01/02 (Pack); existence in BL-ATLAS-READOUT-SWEEP

### BL-ATLAS-17 · Apply Packed Atlas button
- status: pending
- review: keep
- pre: Saved blend; <blend>.atlas.json exists (Pack Atlas ran); Object Mode
- steps:
  1. After Pack Atlas, click 'Apply Packed Atlas' (FILE_REFRESH icon).
- observe: Per matching mesh: pre_pack CP + '<uv>.pre_pack' UV layer created, UVs remapped into the packed slot, material relinked to 'Proscenio.PackedAtlas' (or image swapped if material_isolated). INFO 'applied packed atlas to N sprite(s)...'. Unpack button now appears.
- intent: Snapshots pre-apply state, then rewrites every sprite's UVs and material to address the packed atlas.
- code: apps/blender/panels/atlas.py:60 -> operators/atlas_pack/apply.py:31
- reason: behavior in FLOW-ATLAS-01 (Apply)

### BL-ATLAS-26 · Unpack Atlas button
- status: pending
- review: keep
- pre: At least one mesh carries a pre_pack snapshot (Apply was run); Object Mode
- steps:
  1. After Apply, click 'Unpack Atlas' (LOOP_BACK icon).
- observe: Each snapshotted mesh: pre_pack UVs restored into the original layer, the '.pre_pack' layer removed, original material + image + region_mode restored, pre_pack CP deleted. INFO 'unpacked N sprite(s) - restored pre-Apply state'. Button disappears.
- intent: Reverts a previous apply from the snapshot (survives save/reload; Ctrl+Z does not).
- code: apps/blender/panels/atlas.py:66 -> operators/atlas_pack/unpack.py:36
- reason: behavior in FLOW-ATLAS-01 (Unpack)

### BL-PIPE-06 · Import Photoshop Manifest (button)
- status: pending
- review: keep
- pre: A valid PSD manifest .json on disk (from the Photoshop plugin).
- steps:
  1. Pipeline > Import > click 'Import Photoshop Manifest' > pick a manifest .json in the file dialog > Import.
- observe: File dialog filters to *.json. On import, the info bar reports 'stamped N mesh(es) (armature: <name>)' plus 'skipped K' / 'composed M spritesheet(s)' when applicable; meshes appear parented to a stub armature; scene.proscenio.pixels_per_unit is synced to the manifest's PPU; operation is undoable (Ctrl+Z).
- intent: Reads a manifest from the Photoshop plugin, stamps one mesh per layer (composing spritesheets for sprite_frame groups), parents everything to a stub root armature; re-importing reuses meshes so rotation/parenting/weights survive.
- code: apps/blender/panels/pipeline.py:58-62 -> apps/blender/operators/import_photoshop.py:26-103 -> apps/blender/importers/photoshop/__init__.py:42-91
- reason: behavior in FLOW-DOLL-01, FLOW-PSD-01 (Import Manifest)

### BL-PIPE-14 · Export (.proscenio) (button)
- status: pending
- review: keep
- pre: A scene with exportable content (armature + sprites).
- steps:
  1. Pipeline > Export > click 'Export (.proscenio)' > choose destination in the file dialog > Export.
- observe: File dialog filters to *.proscenio. Validation runs first; if any error-severity issues exist the export is blocked with 'export blocked by N validation error(s) - see Validation panel.' and nothing is written. On success: JSON written, info bar 'wrote <name>' (+bundle suffix), console '[Proscenio] exported -> <path>', and last_export_path is set to the chosen path (making Re-export appear).
- intent: Runs the writer, validates against the schema, writes the JSON next to the .blend; the path is sticky.
- code: apps/blender/panels/pipeline.py:93 -> apps/blender/operators/export_flow.py:147-178
- reason: behavior in FLOW-DOLL-03 and all flow export steps (Export .proscenio)

### BL-PIPE-16 · Re-export (button)
- status: pending
- review: keep
- pre: last_export_path is non-empty (a prior Export ran or the path was typed in).
- steps:
  1. Pipeline > Export > click 'Re-export'.
- observe: No file dialog. Validation gate runs; blocking errors abort with 're-export failed' path. On success the writer writes to abspath(last_export_path) using the SCENE pixels_per_unit, info bar 're-exported -> <name>' (+bundle suffix), console '[Proscenio] re-exported -> <path>'. Button is hidden when last_export_path is empty (and operator poll also returns False).
- intent: Re-export skips the file dialog (uses the sticky path).
- code: apps/blender/panels/pipeline.py:94-95 -> apps/blender/operators/export_flow.py:181-206
- reason: behavior in FLOW-REIMPORT-01 (Re-export)

### BL-DIAG-05 · Diagnostics header '?' help button
- status: pending
- review: keep
- pre: Debug mode ON.
- steps:
  1. Open Diagnostics header > click the '?' icon
- observe: A 480px help popup opens titled 'Proscenio pipeline overview' (NOT a Diagnostics-specific topic) - it shows the generic pipeline+status-badges content, not 'the matching help' the doc promises.
- intent: index line 26: each header carries a '?' that opens the matching help inline.
- code: apps/blender/panels/diagnostics.py:29 -> _helpers.py:84-85 (topic='pipeline_overview')
- reason: duplicate of BL-CHROME-05 (pipeline_overview defect)

### BL-DIAG-11 · Help header '?' help button
- status: pending
- review: keep
- pre: None.
- steps:
  1. Open Help header > click '?'
- observe: Popup opens 'Proscenio pipeline overview' (generic), not a Help-panel-specific topic.
- intent: index line 26: '?' opens the matching help inline.
- code: apps/blender/panels/help.py:44 -> _helpers.py:84-85 (topic='pipeline_overview')
- reason: duplicate of BL-CHROME-05 (pipeline_overview defect)

### PS-EXPORT-02 · Pick folder / Change folder button
- status: pending
- review: keep
- pre: Exporter panel open
- steps:
  1. Click 'Pick folder' > choose a directory in the OS picker
- observe: Path display updates to the chosen folder; a persistent token is written to localStorage key 'proscenio.exporter.folderToken'; reloading the plugin restores the same folder without prompting.
- intent: Choose the output folder; the path persists across reloads (folder-storage persistent token).
- code: apps/photoshop/src/panels/sections/FolderSection.tsx:25-27 -> useFolderCache.pick -> api/folder-storage.ts:31
- reason: behavior in FLOW-DOLL-01 (pick folder)

### PS-EXPORT-03 · Forget button
- status: pending
- review: keep
- pre: A folder is currently picked
- steps:
  1. With a folder set, click 'Forget'
- observe: localStorage token removed; folder state resets to null; card reverts to 'No folder picked.'; Export button becomes disabled (folder === null).
- intent: UNDOCUMENTED - doc never mentions clearing the remembered folder.
- code: apps/photoshop/src/panels/sections/FolderSection.tsx:28 -> useFolderCache.clear -> api/folder-storage.ts:42 (clearRememberedFolder)
- reason: behavior in FLOW-DOLL-01 (folder forget)

### PS-EXPORT-14 · Export manifest + PNGs button (Run export)
- status: pending
- review: keep
- pre: A document is open AND a folder is picked (else disabled). Fixture: doll PSD with tagged layers.
- steps:
  1. Pick a folder > open a layered PSD > click 'Export manifest + PNGs' > wait for the modal banner
- observe: Button shows 'Exporting...' while busy; on success a green result 'Wrote N entry(ies) to <doc>.photoshop_exported.json' plus per-PNG warn rows for any skipped writes; the .photoshop_exported.json file and images/*.png appear on disk.
- intent: Writes the manifest JSON + all PNGs to the output folder; a recursive layer walk produces one PNG per layer plus a manifest JSON, validated before written so a broken manifest never reaches disk.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:131-135 -> ProscenioExporter.onExport -> useExportFlow.run -> api/export-flow.ts:90 runExport
- reason: behavior in FLOW-DOLL-01 (export manifest + PNGs)

### PS-TAGS-18 · Advanced: origin Y field
- status: pending
- review: keep
- observe: Combined with X to write '[origin:X,Y]'; see PS-TAGS-17.
- intent: Second component of [origin:X,Y] explicit pivot.
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:139-146,71-74,83-92
- reason: merged into PS-TAGS-17 (one origin write)

### PS-TAGS-09 · [ignore] toggle glyph (X)
- status: pending
- review: keep
- pre: Any layer or group row; document open.
- steps:
  1. Click the 'X' glyph in the row's right cluster.
- observe: Layer name gains/loses '[ignore]'; row gets/loses 'ignored' styling; PS layer name updates (renameLayer). Toggling again removes it. Disabled while busy.
- intent: [ignore] drops the layer/group entirely from export (no manifest entry, no PNG).
- code: apps/photoshop/src/panels/sections/tags/Row.tsx:61-66
- reason: behavior in FLOW-PSD-03 ([ignore] glyph)

### PS-TAGS-10 · [merge] toggle glyph (M)
- status: pending
- review: keep
- pre: A group (LayerSet) row; disabled on non-group rows.
- steps:
  1. Click the 'M' glyph on a group row.
- observe: Group name gains/loses '[merge]'; glyph active styling toggles. On a non-group row the glyph is disabled with title '[merge] only applies to groups'.
- intent: [merge] flattens a whole group into one PNG (group-only tag).
- code: apps/photoshop/src/panels/sections/tags/Row.tsx:68-73
- reason: behavior in FLOW-PSD-03 ([merge] glyph)

### PS-TAGS-25 · renameLayer write path (XMP mirror + executeAsModal)
- status: pending
- review: keep
- pre: Document open; any tag-editing control invoked.
- steps:
  1. Invoke any toggle/dropdown/Apply that changes a name.
- observe: Target resolved outside the modal; inside executeAsModal sets target.name and mirrors tags to XMP (best-effort). On no active doc / layer-not-found / modal rejection, busy clears and lastError shows the reason.
- intent: Tag edits are persisted into the PSD layer name; re-import in Blender reads tags from names.
- code: apps/photoshop/src/api/layer-rename.ts:21-58
- reason: behavior in FLOW-PSD-03 (renameLayer write path)

### PS-AUX-04 · Active document: Refresh button
- status: pending
- review: keep
- pre: Validate or Debug panel open.
- steps:
  1. 1. Change the active document (rename / resize canvas / switch tabs). 2. Click 'Refresh'.
- observe: name + canvas rows update synchronously to the now-active document (readDocSnapshot via app.activeDocument). No file is written.
- intent: UNDOCUMENTED; re-reads the active document header into the panel.
- code: apps/photoshop/src/panels/sections/DocSection.tsx:22 (handler ProscenioValidatePanel.tsx:37 / ProscenioDebugPanel.tsx:43 -> useDocSnapshot.refresh)
- reason: pure doc-header re-read; covered by PS-DOC-SWEEP

### PS-AUX-11 · Validate: Warning row (click-to-select offending layer)
- status: pending
- review: keep
- pre: At least one warning present.
- steps:
  1. 1. Click a warning row (or focus it and press Enter/Space). 2. Watch the PS Layers panel.
- observe: Row shows code + bold name + message. Clicking runs batchPlay 'select' on the layer matched by warning.layerPath; that layer becomes the active selection in PS. Keyboard Enter/Space also activates.
- intent: Each row selects the offending PS layer; hint says 'Click any row to jump to the offending layer in Photoshop.'
- code: apps/photoshop/src/panels/sections/ValidateSection.tsx:82-95 (handler useLayerSelection -> ps-selection.selectLayerByPath:61)
- reason: behavior in FLOW-PSD-03 (validate click-to-select offending)

### PS-AUX-13 · Validate: Skipped row (click-to-select skipped layer)
- status: pending
- review: keep
- pre: At least one skipped layer present.
- steps:
  1. 1. Click a skipped row (or Enter/Space when focused). 2. Watch the PS Layers panel.
- observe: Row shows skip reason code + layer name; clicking selects that layer (by its layerPath) in PS via batchPlay.
- intent: Row selects the skipped PS layer; shows the skip reason as the code and the layer name.
- code: apps/photoshop/src/panels/sections/ValidateSection.tsx:97-107 (handler useLayerSelection -> selectLayerByPath:61)
- reason: behavior in FLOW-PSD-03 (validate click-to-select skipped)

### PS-AUX-16 · Preview: Refresh button (dry-run)
- status: pending
- review: keep
- pre: Debug panel open, document open.
- steps:
  1. 1. Edit the PSD layers. 2. Click 'Refresh'.
- observe: anchor/entries/skipped/warnings rows and the entries list recompute from previewExport(opts) with skipHidden:true. No file is written to disk.
- intent: Runs a dry-run preview of the export; per index.md the recursive walk produces manifest + PNGs, but Refresh writes nothing (dry-run).
- code: apps/photoshop/src/panels/sections/DebugSection.tsx:29,49,66 (handler ProscenioDebugPanel.onRefresh:31 -> useExportPreview.refresh -> previewExport)
- reason: behavior in FLOW-PSD-03 (preview refresh dry-run)

### PS-AUX-26 · Legacy migration: candidate row (click-to-select layer)
- status: pending
- review: keep
- pre: Candidate rows visible.
- steps:
  1. 1. Click a candidate row (or Enter/Space when focused). 2. Watch PS Layers panel.
- observe: Row shows oldName -> newName; clicking selects the layer at candidate.layerPath in PS via batchPlay.
- intent: UNDOCUMENTED; clicking a candidate selects that layer in PS (shows old -> new name).
- code: apps/photoshop/src/panels/sections/MigrationSection.tsx:47-72 (handler useLayerSelection -> selectLayerByPath:61)
- reason: duplicate click-to-select of PS-AUX-11/13

### GD-IMPORT-01 · Importer entry "Proscenio Character" in the Import dock
- status: pending
- review: keep
- observe: Import tab shows "Import As: Proscenio Character" as the importer with a "Default" preset; .proscenio recognized (not 'keep file').
- intent: A single EditorImportPlugin that turns a .proscenio file into a native Godot scene on every reimport.
- code: apps/godot/addons/proscenio/importer.gd:17-18
- reason: folded into GD-CHROME-01 (importer entry on registration)

### GD-IMPORT-02 · Recognized extension (.proscenio)
- status: pending
- review: keep
- observe: Godot routes foo.proscenio through this importer; a foo.proscenio.scn artifact appears under .godot/imported (or the file imports without 'unrecognized' warning).
- intent: The plugin claims files with the proscenio extension so they import as characters.
- code: apps/godot/addons/proscenio/importer.gd:21-22
- reason: extension recognition exercised by every flow import; no standalone value

### GD-IMPORT-03 · Save extension / resource type (.scn -> PackedScene)
- status: pending
- review: keep
- observe: Imported resource is a PackedScene saved with .scn; instancing it yields plain Node2D/Skeleton2D/Bone2D/Polygon2D/Sprite2D/AnimationPlayer with no GDExtension dependency.
- intent: Regenerates a scene as plain Godot 4 nodes with no runtime dependency.
- code: apps/godot/addons/proscenio/importer.gd:25-31
- reason: .scn/PackedScene save type observed at any flow import; no standalone value

### GD-IMPORT-04 · Preset dropdown ("Default")
- status: pending
- review: keep
- observe: Exactly one preset named "Default" is offered; selecting it changes nothing (no options follow).
- intent: UNDOCUMENTED
- code: apps/godot/addons/proscenio/importer.gd:41-46
- reason: preset count is 1, no-op; no value

### GD-IMPORT-05 · Import options list (empty)
- status: pending
- review: keep
- observe: No per-import options are shown (no checkboxes/fields); the options area is empty though _get_option_visibility returns true.
- intent: UNDOCUMENTED
- code: apps/godot/addons/proscenio/importer.gd:49-54
- reason: empty options list; no value

### GD-IMPORT-09 · Owner assignment (scene packs cleanly)
- status: pending
- review: keep
- observe: All descendant nodes are visible/persisted (owner = root) and PackedScene.pack returns OK; no nodes are dropped on save.
- intent: Generated scene runs standalone as plain Godot nodes.
- code: apps/godot/addons/proscenio/importer.gd:91-96
- reason: asserted in any flow inspect step (owner=root)

### GD-IMPORT-10 · Overwrite-existing-scene notice (print_verbose)
- status: pending
- review: keep
- observe: Verbose log prints "Proscenio: regenerating <path>.scn (existing scene will be overwritten)"; the prior .scn is replaced wholesale.
- intent: UNDOCUMENTED
- code: apps/godot/addons/proscenio/importer.gd:99-102
- reason: asserted in FLOW-REIMPORT-01 (overwrite log)

### GD-IMPORT-25 · Plugin metadata (plugin.cfg name/description/version)
- status: pending
- review: keep
- observe: Entry "Proscenio" by Space Wizard Studios, version 0.1.0, description mentioning Skeleton2D+Bone2D+Polygon2D+AnimationPlayer; script points to plugin.gd.
- intent: UNDOCUMENTED
- code: apps/godot/addons/proscenio/plugin.cfg:1-7
- reason: plugin.cfg metadata check; no runtime behavior

### GD-IMPORT-06 · Reimport button (full scene regeneration)
- status: pending
- review: keep
- pre: A valid format_version=1 .proscenio in res://, plugin enabled.
- steps:
  1. Select the .proscenio in FileSystem > Import tab > click Reimport (or edit/save the .proscenio to trigger auto-reimport).
- observe: A new .scn is built: root Node2D named after document.name (else "Character"), with Skeleton2D, AnimationPlayer, and element nodes; ResourceSaver.save returns OK; the imported scene reflects the new data.
- intent: Regenerate the scene (Skeleton2D + Bone2D + Polygon2D/Sprite2D + AnimationPlayer) whenever a .proscenio enters or changes.
- code: apps/godot/addons/proscenio/importer.gd:57-103
- reason: asserted in every flow import-and-inspect step

### GD-IMPORT-23 · Plugin registration (_enter_tree add_import_plugin)
- status: pending
- review: keep
- pre: Plugin listed in project.godot [editor_plugins] enabled.
- steps:
  1. Open the project (or toggle the plugin on in Project Settings > Plugins).
- observe: On enter_tree the importer is constructed and add_import_plugin called; "Proscenio Character" becomes selectable as an importer.
- intent: The plugin registers a single EditorImportPlugin.
- code: apps/godot/addons/proscenio/plugin.gd:9-11
- reason: folded into GD-CHROME-01 (register)

### GD-IMPORT-24 · Plugin teardown (_exit_tree remove_import_plugin)
- status: pending
- review: keep
- pre: Plugin currently enabled.
- steps:
  1. Disable the plugin in Project Settings > Plugins (or close the project).
- observe: remove_import_plugin called and _importer cleared; "Proscenio Character" importer no longer offered; no leak/errors.
- intent: UNDOCUMENTED
- code: apps/godot/addons/proscenio/plugin.gd:14-17
- reason: folded into GD-CHROME-01 (teardown)

### GD-BUILD-01 · Skeleton2D root build (SkeletonBuilder.build)
- status: pending
- review: keep
- pre: A .proscenio file in the project; reimport triggered
- steps:
  1. Author a .proscenio with a skeleton block > reimport > open generated .scn
- observe: Root Node2D contains a child named 'Skeleton2D'. With no skeleton block the Skeleton2D still appears (empty).
- intent: Plugin regenerates a scene whose skeleton is built first in order; null skeleton still yields a Skeleton2D node.
- code: apps/godot/addons/proscenio/builders/skeleton_builder.gd:5-44
- reason: asserted in FLOW-DOLL-03; folded into GD-SKEL-INV

### GD-BUILD-09 · Atlas load (importer._load_atlas)
- status: pending
- review: keep
- pre: .proscenio with document.atlas path next to file
- steps:
  1. Set document.atlas to a sibling png > reimport
- observe: Atlas Texture2D loaded and passed to element builders. Empty atlas -> null; missing path -> warning + null; non-texture -> error + null.
- intent: Importer reads atlas before slots/sprites; atlas is the scene-wide fallback texture.
- code: apps/godot/addons/proscenio/importer.gd:75,147-167
- reason: asserted in FLOW-ATLAS-02 (atlas load)

### GD-BUILD-10 · Slot anchor build (SlotBuilder.build)
- status: pending
- review: keep
- pre: .proscenio with a slots[] entry having name + attachments[]
- steps:
  1. Author a slot with bone and attachments > reimport > inspect tree
- observe: A Node2D named after the (sanitized) slot appears under the named Bone2D; under Skeleton2D root if bone empty or bone missing (with warning).
- intent: Slots build BEFORE sprites; each slot becomes a Node2D under its Bone2D (or Skeleton2D when bone empty).
- code: apps/godot/addons/proscenio/builders/slot_builder.gd:22-66
- reason: asserted in FLOW-SLOTSWAP-02/SLOTCYCLE-01; folded into GD-SLOT-INV

### GD-BUILD-13 · Slot attachment map / default attachment visibility
- status: pending
- review: keep
- pre: Slot with multiple attachments[], a default set; elements named to match attachments
- steps:
  1. Author slot default='headA' with attachments [headA,headB]; add sprite/mesh elements headA,headB > reimport
- observe: headA and headB parent under the slot Node2D; headA visible==true, headB visible==false.
- intent: Default attachment starts visible, others hidden until slot_attachment track flips them.
- code: apps/godot/addons/proscenio/builders/slot_builder.gd:32-34,65; sprite_attach_util.gd:50-54
- reason: asserted in FLOW-SLOTSWAP-02/SLOTCYCLE-01 (default visibility)

### GD-BUILD-14 · Mesh element build (MeshBuilder.attach_elements -> Polygon2D)
- status: pending
- review: keep
- pre: element with type 'mesh' (or omitted) and a polygon ring
- steps:
  1. Author a mesh element with polygon [[x,y],...] > reimport > inspect Polygon2D
- observe: A Polygon2D named after the element with .polygon set; sprite-type elements skipped by this builder.
- intent: Sprites built as Polygon2D for mesh-type elements; type absent defaults to mesh.
- code: apps/godot/addons/proscenio/builders/mesh_builder.gd:32-71; proscenio_element.gd:15-17
- reason: asserted in FLOW-PSD-02; folded into GD-MESH-INV

### GD-BUILD-20 · Sprite element build (SpriteBuilder.attach_elements -> Sprite2D)
- status: pending
- review: keep
- pre: element with type 'sprite'
- steps:
  1. Author a sprite element > reimport > inspect node
- observe: A Sprite2D named after the element; mesh-type elements skipped by this builder.
- intent: Sprites built as Sprite2D for sprite-type elements.
- code: apps/godot/addons/proscenio/builders/sprite_builder.gd:12-46; proscenio_element.gd:18-19
- reason: asserted in FLOW-PSD-02; folded into GD-SPRITE-INV

### GD-BUILD-29 · AnimationPlayer + library populate (AnimationBuilder.populate)
- status: pending
- review: keep
- pre: Skeleton present; document.animations may be null or list
- steps:
  1. Author animations[] (or none) > reimport > inspect AnimationPlayer
- observe: AnimationPlayer node exists with an unnamed AnimationLibrary; each animation added under its name. Null animations -> empty library still added.
- intent: Plugin builds an AnimationPlayer; animation built last in order.
- code: apps/godot/addons/proscenio/builders/animation_builder.gd:7-22; importer.gd:86-89
- reason: asserted in FLOW-DOLL-03; folded into GD-ANIM-INV

### GD-BUILD-32 · sprite_frame track
- status: pending
- review: keep
- pre: Animation track type 'sprite_frame' targeting a Sprite2D element name; keys carry frame
- steps:
  1. Author a sprite_frame track on a Sprite2D > reimport > inspect Animation
- observe: A value track on '<sprite>:frame' with NEAREST interpolation and integer frame keys. Target not Sprite2D -> push_error and no track.
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/animation_builder.gd:61-78,148-154
- reason: asserted in FLOW-PSD-02 (sprite_frame track); guard edge kept in GD-B-ANIM-GUARDS

### GD-BUILD-33 · slot_attachment track (per-child visibility)
- status: pending
- review: keep
- pre: A slot Node2D with attachment children; track type 'slot_attachment' targeting the slot; keys carry attachment names
- steps:
  1. Author slot_attachment keys naming attachments per time > reimport > inspect tracks
- observe: One '<slot>/<child>:visible' value track per CanvasItem child, NEAREST interp; at each key time only the named attachment is true. Empty key.attachment is skipped. Missing slot -> push_error.
- intent: Slot_attachment track flips attachment visibility at runtime (default visible, others hidden).
- code: apps/godot/addons/proscenio/builders/animation_builder.gd:79-84,127-145
- reason: asserted in FLOW-SLOTSWAP-02/SLOTCYCLE-01 (slot_attachment track)

### GD-BUILD-39 · Scene pack + owner assignment + overwrite
- status: pending
- review: keep
- pre: A previously imported .proscenio
- steps:
  1. Reimport an existing .proscenio > confirm .scn regenerates
- observe: All nodes owned by root (visible/savable), PackedScene saved to <save_path>.scn; verbose log on overwrite; wrapper scene instancing it is untouched.
- intent: Generated scene is plain Godot 4 nodes; reimport overwrites the existing .scn (wrapper-scene safety).
- code: apps/godot/addons/proscenio/importer.gd:91-103,170-174
- reason: asserted in any flow import (scene pack/owner); wrapper clause kept in GD-B-WRAPPER-SAFETY
