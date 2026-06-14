# Photoshop plugin - manual-test checklist

Maintained by the QA Companion tool (tools/qa-companion): one block per item. `status` / `note` / `shots` are the recorded walk; `review` is your verdict on the test itself (keep / rephrase / drop / todo). Edit here or via the tool.

## Exporter panel: Output folder + Export options + Pixels per unit + Filename templates + Run export + Re-export selected sections, plus the export -> manifest + PNG write path

### PS-EXPORT-01 · Output folder - path display / 'No folder picked.' placeholder
- status: pending
- review: keep
- observe: With no folder: 'No folder picked.' card. After picking: the folder.nativePath string is shown and is the title tooltip.
- intent: Shows where the export writes the manifest + PNGs; the path persists across plugin reloads.
- code: apps/photoshop/src/panels/sections/FolderSection.tsx:17-23

### PS-EXPORT-04 · Output folder accordion header + hint tooltip
- status: pending
- review: keep
- observe: Chevron toggles v/>; body shows/hides; native title tooltip shows the hint text.
- intent: Collapsible Output-folder section; hint explains it persists across reloads.
- code: apps/photoshop/src/components/Accordion.tsx:44-59 (title='Output folder')

### PS-EXPORT-05 · Skip hidden layers checkbox
- status: pending
- review: keep
- observe: When checked (default true), hidden layers are dropped from the plan (planner.ts:324 reason 'hidden'); when unchecked, hidden layers are included in writes.
- intent: Export options section; doc implies hidden/ignored layers are excluded (use [ignore] tag to exclude). Skip-hidden toggle itself is UNDOCUMENTED by name.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:82-84 -> onSkipHidden -> useExportFlow.setOption('skipHidden')

### PS-EXPORT-06 · Export options accordion header + hint
- status: pending
- review: keep
- observe: Tooltip shows the [ignore]-tag hint; section collapses/expands.
- intent: Hint: use the [ignore] tag in a layer/group name to exclude it from export.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:78-85

### PS-EXPORT-07 · Pixels per unit (ppu) text field
- status: pending
- review: keep
- observe: Valid finite >0 values persist (localStorage) and become manifest.pixels_per_unit; invalid/zero/negative inputs are ignored (no state change). canvas row updates docHeight/ppu units.
- intent: UNDOCUMENTED on this doc page - conversion factor for Blender/Godot; higher PPU = smaller world-space objects (hint only). Doc index.md does not mention PPU.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:91-95 -> onPpuInput -> usePixelsPerUnit.setPixelsPerUnit

### PS-EXPORT-08 · canvas read-only row (NNpx = NN.NN units)
- status: pending
- review: keep
- observe: Displays e.g. '1024px = 16.00 units'; hidden entirely when docHeight is null or ppu <= 0.
- intent: UNDOCUMENTED - shows doc height converted to world units at the current PPU.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:97-103 (heightInUnits)

### PS-EXPORT-09 · Reset to {default} ppu button
- status: pending
- review: keep
- observe: ppu returns to 100 and persists; the button is disabled (greyed) when ppu already equals the default.
- intent: UNDOCUMENTED - resets ppu to the default (100).
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:104-106 -> onPpuReset -> usePixelsPerUnit (DEFAULT 100)

### PS-EXPORT-10 · mesh filename template field
- status: pending
- review: keep
- observe: Value persists to localStorage; empty string normalises back to '{name}.png'; mesh PNG paths in the preview/Reveal reflect the template under images/.
- intent: Filename templates section; tokens {name} and {kind} for meshes; images/ prefix and [folder:...] subfolder added automatically.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:113-118 -> onPolygonInput -> useFilenameTemplate.setPolygonTemplate; consumed planner.ts:641

### PS-EXPORT-11 · sprite (frames) filename template field
- status: pending
- review: keep
- observe: Persists; empty normalises to '{name}/{index}.png'; sprite frame paths reflect the template.
- intent: Tokens {name} and {index} for frames; images/ prefix + subfolder added automatically.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:120-125 -> onFramesInput -> setFramesTemplate; consumed planner.ts:500/675

### PS-EXPORT-12 · Reset to defaults (templates) button
- status: pending
- review: keep
- observe: Both templates revert to {name}.png and {name}/{index}.png; button disabled when both already equal defaults.
- intent: UNDOCUMENTED - resets both filename templates to defaults.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:127-129 -> onResetTemplates -> useFilenameTemplate.reset

### PS-EXPORT-13 · Filename templates accordion (collapsed by default)
- status: pending
- review: keep
- observe: Starts closed (chevron '>'); expands on click; tooltip lists {name}/{kind}/{index} tokens.
- intent: Section with token hint; collapsed by default.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:108-112 (defaultOpen={false})

### PS-EXPORT-15 · Export button disabled state
- status: pending
- review: keep
- observe: Button greyed/disabled when busy OR folder===null OR doc(snapshot)===null; enabled only when all three are satisfied.
- intent: Export should be unavailable until prerequisites are met (folder + document).
- code: apps/photoshop/src/panels/ProscenioExporter.tsx:65 exportDisabled; ExportSection.tsx:132 disabled

### PS-EXPORT-16 · Export result - OK view ('Wrote N entry(ies) to <file>')
- status: pending
- review: keep
- observe: Shows entryCount and manifestFile; lists any PNG write rows where !r.ok with skippedReason.
- intent: Confirms the manifest filename and entry count written.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:141-156 (ExportResultView ok)

### PS-EXPORT-17 · Export result - error view (validation-failed / no-document / failed)
- status: pending
- review: keep
- observe: Shows 'Export <kind>.' plus the errors[] list; note 'failed' shows the raw Error.message or per-PNG 'path: reason' strings.
- intent: Surfaces why an export did not complete (validation gate or write failure).
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:158-164 (ExportResultView error)

### PS-EXPORT-18 · Run export accordion header + hint
- status: pending
- review: keep
- observe: Tooltip shows the write hint; section collapses/expands.
- intent: Hint: writes the manifest JSON + all PNGs to the output folder.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:131

### PS-EXPORT-19 · Re-export selected - entry / kind detail rows or placeholder
- status: pending
- review: keep
- observe: When matched: 'entry' (mono name) and 'kind' rows shown; when no match: placeholder 'Select a layer in Photoshop that maps to a manifest entry.'
- intent: Rewrites the PNG(s) for the layer selected in Photoshop; manifest JSON is not touched.
- code: apps/photoshop/src/panels/sections/ReexportSection.tsx:49-58 (findMatchedEntry)

### PS-EXPORT-21 · Re-export button disabled state
- status: pending
- review: keep
- observe: Disabled when busy, no matched entry, or no folder; enabled only when both a match and a folder exist.
- intent: Re-export unavailable without a matched entry + folder.
- code: apps/photoshop/src/panels/sections/ReexportSection.tsx:65 (disabled = busy || matched===null || folder===null)

### PS-EXPORT-22 · Re-export result rows (ok / error)
- status: pending
- review: keep
- observe: ok: 'Wrote N PNG(s).'; error: 'Re-export <kind>.' plus errors[] (e.g. 'not-found' or per-PNG failure).
- intent: Confirms how many PNGs were rewritten, or surfaces re-export errors.
- code: apps/photoshop/src/panels/sections/ReexportSection.tsx:92-108 (ReexportResult)

### PS-EXPORT-26 · empty / zero-layer document export
- status: pending
- review: keep
- observe: Validation passes (empty layers array is schema-valid); manifest written with 'layers: []'; result 'Wrote 0 entry(ies)'. No PNGs written.
- intent: A recursive walk produces one PNG per layer plus a manifest; doc does not state behaviour when no exportable layers exist.
- code: apps/photoshop/src/lib/planner.ts:133-148 (layers: []) ; schema layers has no minItems

### PS-EXPORT-02 · Pick folder / Change folder button
- status: pending
- review: keep
- pre: Exporter panel open
- steps:
  1. Click 'Pick folder' > choose a directory in the OS picker
- observe: Path display updates to the chosen folder; a persistent token is written to localStorage key 'proscenio.exporter.folderToken'; reloading the plugin restores the same folder without prompting.
- intent: Choose the output folder; the path persists across reloads (folder-storage persistent token).
- code: apps/photoshop/src/panels/sections/FolderSection.tsx:25-27 -> useFolderCache.pick -> api/folder-storage.ts:31

### PS-EXPORT-03 · Forget button
- status: pending
- review: keep
- pre: A folder is currently picked
- steps:
  1. With a folder set, click 'Forget'
- observe: localStorage token removed; folder state resets to null; card reverts to 'No folder picked.'; Export button becomes disabled (folder === null).
- intent: UNDOCUMENTED - doc never mentions clearing the remembered folder.
- code: apps/photoshop/src/panels/sections/FolderSection.tsx:28 -> useFolderCache.clear -> api/folder-storage.ts:42 (clearRememberedFolder)

### PS-EXPORT-14 · Export manifest + PNGs button (Run export)
- status: pending
- review: keep
- pre: A document is open AND a folder is picked (else disabled). Fixture: doll PSD with tagged layers.
- steps:
  1. Pick a folder > open a layered PSD > click 'Export manifest + PNGs' > wait for the modal banner
- observe: Button shows 'Exporting...' while busy; on success a green result 'Wrote N entry(ies) to <doc>.photoshop_exported.json' plus per-PNG warn rows for any skipped writes; the .photoshop_exported.json file and images/*.png appear on disk.
- intent: Writes the manifest JSON + all PNGs to the output folder; a recursive layer walk produces one PNG per layer plus a manifest JSON, validated before written so a broken manifest never reaches disk.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:131-135 -> ProscenioExporter.onExport -> useExportFlow.run -> api/export-flow.ts:90 runExport

### PS-EXPORT-20 · Re-export this entry's PNG button
- status: pending
- review: keep
- pre: A folder is picked AND the active PS layer matches a manifest entry
- steps:
  1. Pick folder > select a matching layer > click 'Re-export this entry's PNG'
- observe: Button shows 'Re-exporting...'; on success 'Wrote N PNG(s).'; only that entry's PNG file(s) rewritten on disk; the *.photoshop_exported.json manifest is NOT modified.
- intent: Rewrites only the selected layer's PNG(s), leaving the manifest untouched.
- code: apps/photoshop/src/panels/sections/ReexportSection.tsx:59-68 onReexport -> api/export-flow.ts:167 runSingleLayerExport

### PS-EXPORT-23 · manifest validation gate (ajv) - export path
- status: pending
- review: keep
- pre: A document whose plan would produce an invalid manifest (e.g. a sub-pixel/zero size, or a layer name that strips to empty without fallback)
- steps:
  1. Export a doc crafted to break a schema rule (e.g. negative/zero coordinate) and observe the result
- observe: runExport returns kind 'validation-failed' with errors[]; NO files written; error block lists '(root) ...' / instancePath messages.
- intent: The manifest is validated against the schema with ajv before it is written, so a broken manifest never reaches disk.
- code: apps/photoshop/src/api/export-flow.ts:107-111 validateManifest -> api/manifest-validator.ts:28; schema packages/models/schemas/psd_manifest.schema.json

### PS-EXPORT-24 · manifest write (writeManifest) - atomicity with PNGs
- status: pending
- review: keep
- pre: A folder picked; an export where at least one PNG write fails (e.g. one layer renamed after preview)
- steps:
  1. Trigger an export where one PNG write returns ok:false; inspect the folder
- observe: manifestWritten=false; NO manifest JSON written; result kind 'failed' lists the failing 'outputPath: reason'. Existing PNGs that succeeded may still be on disk (partial).
- intent: The manifest is persisted only if every PNG landed, so it never references missing files.
- code: apps/photoshop/src/api/export-flow.ts:118-126 (executeAsModal) -> api/manifest-writer.ts:9 writeManifest

### PS-EXPORT-25 · PNG write per layer (runWrites/writeLayerPng) - temp doc + trim + saveAs.png
- status: pending
- review: keep
- pre: Export running inside the modal; layers resolvable by path
- steps:
  1. Export a multi-layer doc; verify images/*.png exist and match each layer's trimmed bounds
- observe: For each write, a PNG appears at folder/<outputPath>; a layer whose path no longer resolves yields ok:false 'source layer not found'.
- intent: One PNG per layer: isolate the source layer on a temp doc, trim transparency, save PNG into the target folder.
- code: apps/photoshop/src/api/png-writer.ts:23-77 runWrites/writeLayerPng

## Import section: rebuild PSD from manifest (png-placer, manifest-reader)

### PS-IMPORT-01 · Accordion header "Import (manifest to PSD)" (collapse/expand)
- status: pending
- review: keep
- observe: Section toggles open: chevron flips '>' to 'v', section className flips closed/open, body with the Import button renders. Click again collapses it (body unmounts).
- intent: UNDOCUMENTED (doc says the plugin "can rebuild a PSD from a manifest" but never describes the panel section/header).
- code: apps/photoshop/src/panels/sections/ImportSection.tsx:14-18; apps/photoshop/src/components/Accordion.tsx:33-60

### PS-IMPORT-02 · Accordion header keyboard toggle (Enter / Space)
- status: pending
- review: keep
- observe: Each Enter/Space press toggles open state (preventDefault stops page scroll on Space); aria-expanded reflects state.
- intent: UNDOCUMENTED (keyboard a11y affordance; not in doc).
- code: apps/photoshop/src/components/Accordion.tsx:35-40

### PS-IMPORT-03 · Accordion header tooltip (hint title attribute)
- status: pending
- review: keep
- observe: Native tooltip shows: "Pick a Proscenio manifest JSON. The plugin recreates the PSD with placed layers / sprite_frame groups; the document stays open and unsaved -- use File > Save As to commit it to disk."
- intent: UNDOCUMENTED (hint text describing the import behavior; only an HTML title tooltip).
- code: apps/photoshop/src/panels/sections/ImportSection.tsx:17; apps/photoshop/src/components/Accordion.tsx:52

### PS-IMPORT-08 · Import OK result - "Stamped N entry(ies) (M skipped). Use File > Save As"
- status: pending
- review: keep
- observe: Green "result ok" body reads "Stamped <stamped> entry(ies)" and appends " (<skipped> skipped)" only when skipped > 0, then ". Use File > Save As to commit the PSD."
- intent: UNDOCUMENTED (doc never describes the stamped/skipped counts or the result body).
- code: apps/photoshop/src/panels/sections/ImportSection.tsx:27-42; apps/photoshop/src/api/import-flow.ts:62-73

### PS-IMPORT-09 · Import OK result - per-entry warning rows
- status: pending
- review: keep
- observe: Yellow "result-row warn" lines, one per warning, e.g. "mesh <name>: missing PNG at <path>", "<file> bounds WxH differ from manifest WxH; using PNG bounds.", "sprite <name>: zero frames placed; group removed".
- intent: UNDOCUMENTED (warnings surface for missing PNGs / bounds mismatch / empty sprites not in doc).
- code: apps/photoshop/src/panels/sections/ImportSection.tsx:38-40; apps/photoshop/src/api/import-flow.ts:96,107,109,123,131,142,150

### PS-IMPORT-10 · Import failed result - "Import failed." + error rows
- status: pending
- review: keep
- observe: Red "result error" block: "Import failed." followed by one row per error message string from the caught exception.
- intent: UNDOCUMENTED (doc does not describe the modal failure surface).
- code: apps/photoshop/src/panels/sections/ImportSection.tsx:44-52; apps/photoshop/src/api/import-flow.ts:34-41

### PS-IMPORT-11 · "Importing..." busy state / button disable
- status: pending
- review: keep
- observe: Button label switches to "Importing..." and disabled=true for the duration; re-enables and reverts label to "Import manifest as PSD" in the finally block regardless of success/failure.
- intent: UNDOCUMENTED (busy/disable UX behavior).
- code: apps/photoshop/src/panels/sections/ImportSection.tsx:19-21; apps/photoshop/src/hooks/useImportFlow.ts:30-36

### PS-IMPORT-04 · "Import manifest as PSD" action button (file picker stage)
- status: pending
- review: keep
- pre: Import section expanded; not busy.
- steps:
  1. Click "Import manifest as PSD" > UXP file picker opens (types: json).
- observe: OS/UXP JSON file picker appears. Cancelling the picker (returns null) silently no-ops: no error, no result view, prior manifestErrors cleared (set to null on run start).
- intent: Rebuild a PSD from a manifest; pick a Proscenio manifest JSON (doc: "plugin can rebuild a PSD from a manifest").
- code: apps/photoshop/src/panels/sections/ImportSection.tsx:19-21; apps/photoshop/src/hooks/useImportFlow.ts:22-28; apps/photoshop/src/api/manifest-reader.ts:26-30

### PS-IMPORT-05 · Import flow - invalid JSON / schema-invalid manifest path
- status: pending
- review: keep
- pre: Import section expanded.
- steps:
  1. Click Import > pick a .json that is malformed JSON OR valid JSON failing the v2 schema.
- observe: "Manifest invalid." error block appears (ManifestErrors) listing per-error rows like "(root) must have required property 'size'" or "manifest is not valid JSON: ..."; no document is created; busy never set true.
- intent: Manifest is validated before use; a broken manifest never reaches disk (doc: validation gate).
- code: apps/photoshop/src/api/manifest-reader.ts:32-46; apps/photoshop/src/api/manifest-validator.ts:34-42; apps/photoshop/src/hooks/useImportFlow.ts:26-29

### PS-IMPORT-06 · Import flow - parent-folder resolution failure path
- status: pending
- review: keep
- pre: Import section expanded.
- steps:
  1. Pick a schema-valid manifest whose parent folder cannot be resolved (no file.parent and empty/unresolvable nativePath).
- observe: "Manifest invalid." block shows single error "could not resolve manifest's parent folder"; import does not proceed.
- intent: UNDOCUMENTED (doc never mentions resolving the manifest's sibling PNG folder).
- code: apps/photoshop/src/api/manifest-reader.ts:47-53,60-75

### PS-IMPORT-07 · Import flow - modal document build + entry stamping (happy path)
- status: pending
- review: keep
- pre: Valid manifest picked; sibling PNGs present alongside the manifest at the declared relative paths.
- steps:
  1. Click Import > pick a valid manifest with PNGs on disk > wait.
- observe: Button shows "Importing..." and is disabled while busy; a single "Proscenio import" modal runs; a new transparent RGB document named manifest.doc (size = manifest.size) opens with one layer per mesh entry and one group per sprite (frames as layers named by index). Entries stacked so z_order 0 ends on top. Result shows "Stamped N entry(ies). Use File > Save As to commit the PSD."
- intent: Recreate the PSD with placed layers / sprite_frame groups; document stays open and unsaved (doc + hint).
- code: apps/photoshop/src/api/import-flow.ts:26-74; apps/photoshop/src/api/png-placer.ts:20-71

### PS-IMPORT-12 · Side effect - pixels_per_unit seeded into localStorage on import
- status: pending
- review: keep
- pre: Valid manifest with a pixels_per_unit value distinct from the current Export PPU input.
- steps:
  1. Import a manifest > inspect the Export section's pixels-per-unit input (and after a panel reload).
- observe: localStorage key proscenio.pixelsPerUnit is overwritten with manifest.pixels_per_unit (normalised, >0). NOTE the live Export input does NOT update this session (see finding); value only takes effect after panel reload.
- intent: Seed the exporter PPU from the imported manifest so a re-export emits the imported scale (code comment / pixels-per-unit-store doc).
- code: apps/photoshop/src/api/import-flow.ts:54-56; apps/photoshop/src/api/pixels-per-unit-store.ts:28-36

## Tags panel + tag vocabulary (parse/tree/write/form) + tagging UI

### PS-TAGS-01 · Tags accordion header (title + chevron)
- status: pending
- review: keep
- observe: Section toggles open/closed; chevron flips between 'v' and '>'; body hides/shows.
- intent: UNDOCUMENTED - doc describes tagging but never the Tags panel/accordion chrome.
- code: apps/photoshop/src/components/Accordion.tsx:46-59

### PS-TAGS-02 · Tags header count badge
- status: pending
- review: keep
- observe: Badge equals the number of top-level layers (tree.length); 0 layers shows the empty-state body with no badge.
- intent: UNDOCUMENTED - count of top-level layers shown next to the title.
- code: apps/photoshop/src/panels/sections/TagsSection.tsx:39

### PS-TAGS-03 · Tags header hint tooltip ('?' equivalent)
- status: pending
- review: keep
- observe: Tooltip 'Layer tree with bracket-tag controls per row. Click + on a row to edit folder / path / scale / origin / name pattern.' appears.
- intent: UNDOCUMENTED - hover hint explaining the row controls; there is no visible '?' button, only an HTML title tooltip.
- code: apps/photoshop/src/panels/sections/TagsSection.tsx:41

### PS-TAGS-04 · Empty-state label ('No layers. Open a PSD to begin tagging.')
- status: pending
- review: keep
- observe: Body reads 'No layers. Open a PSD to begin tagging.'; no tree, no badge.
- intent: UNDOCUMENTED - placeholder when no document/layers.
- code: apps/photoshop/src/panels/sections/TagsSection.tsx:33

### PS-TAGS-05 · Rename-error warning row (lastError)
- status: pending
- review: keep
- observe: A red 'warn' body row appears above the tree showing the failure reason (e.g. 'layer not found', 'no active document').
- intent: UNDOCUMENTED - surfaces a failed rename reason.
- code: apps/photoshop/src/panels/sections/TagsSection.tsx:43-45

### PS-TAGS-07 · Row name label (click to select layer in PS)
- status: pending
- review: keep
- observe: selectLayerByPath fires; the matching layer becomes active/selected in the PS Layers panel. Label shows display name (tag-stripped); falls back to raw name when display name is empty. Active layer's row gets 'selected' styling.
- intent: UNDOCUMENTED - clicking the row name selects/reveals that layer in Photoshop.
- code: apps/photoshop/src/panels/sections/tags/Row.tsx:52-55

### PS-TAGS-08 · Inline badge strip (F/P/S/O/OM/NP)
- status: pending
- review: keep
- observe: Badges render: F=folder value, P=path, S=scale, O='x,y', OM (marker, no value), NP=pattern, each with a hover title. Absent tags show no badge.
- intent: UNDOCUMENTED - read-only compact display of folder/path/scale/origin/origin-marker/name-pattern tags present on the row.
- code: apps/photoshop/src/panels/sections/tags/Badges.tsx:19-38

### PS-TAGS-11 · Kind dropdown (auto / mesh / sprite)
- status: pending
- review: keep
- observe: auto clears the kind tag; mesh writes '[mesh]'; sprite writes '[sprite]'. PS layer name updates accordingly. (See finding: on a [spritesheet] group this rewrites it to [sprite].)
- intent: [mesh]/[poly]/[polygon] -> kind:mesh (Polygon2D); [sprite] -> kind:sprite (Sprite2D); auto = no kind tag.
- code: apps/photoshop/src/panels/sections/tags/Row.tsx:75-84,157-168

### PS-TAGS-12 · Blend dropdown (none / mult / scrn / add)
- status: pending
- review: keep
- observe: none clears [blend]; multiply/screen/additive write '[blend:multiply|screen|additive]'. A pre-existing [blend:normal] displays as 'none'. PS layer name updates.
- intent: [blend:VALUE] records the intended blend mode (normal/multiply/screen/additive) as metadata.
- code: apps/photoshop/src/panels/sections/tags/Row.tsx:86-95,169-181

### PS-TAGS-14 · Advanced: folder text field
- status: pending
- review: keep
- observe: Draft only updates on type; Apply writes '[folder:NAME]'. Empty value on Apply clears the tag. Layer name updates on Apply, not per keystroke.
- intent: [folder:NAME] becomes a Blender Collection NAME; children inherit it (output subfolder under images/).
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:100-109,55-58

### PS-TAGS-15 · Advanced: path text field
- status: pending
- review: keep
- observe: Valid value writes '[path:NAME]'; empty clears. Invalid values (containing / or \, or '.'/'..') are silently skipped (no change, no error surfaced).
- intent: [path:NAME] overrides the on-disk leaf filename stem (no slashes).
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:110-119,59-62,69-74

### PS-TAGS-16 · Advanced: scale text field
- status: pending
- review: keep
- observe: Positive finite number writes '[scale:N]'; empty clears. 0, negative, or non-numeric are skipped (no write). No validation/sub-pixel warning is shown in the panel (see finding).
- intent: [scale:N] multiplies bounding-box size by N; a sub-pixel result raises a validation warning.
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:120-129,63-66,76-81

### PS-TAGS-17 · Advanced: origin X field
- status: pending
- review: keep
- observe: When both X and Y parse as finite, writes '[origin:X,Y]'; both empty clears origin. Non-finite parse skips. Note: a non-numeric X/Y is skipped, not errored.
- intent: [origin:X,Y] sets an explicit pivot in PSD pixels overriding the implicit centre.
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:130-138,67-70,83-92

### PS-TAGS-18 · Advanced: origin Y field
- status: pending
- review: keep
- observe: Combined with X to write '[origin:X,Y]'; see PS-TAGS-17.
- intent: Second component of [origin:X,Y] explicit pivot.
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:139-146,71-74,83-92

### PS-TAGS-20 · Advanced: origin marker checkbox
- status: pending
- review: keep
- observe: Checked writes bare '[origin]'; unchecked clears it. Note: writer suppresses '[origin]' when explicit '[origin:x,y]' coords are present (mutually exclusive).
- intent: [origin] marks the layer's bbox centre as its parent [spritesheet]/[merge] group's pivot (marker layer not exported).
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:155-162,75-78,120-126

### PS-TAGS-21 · Advanced: name pattern field (groups only)
- status: pending
- review: keep
- observe: Valid pattern (non-empty, contains '*') writes '[name:..]'; empty clears. A pattern without '*' is skipped. Field is not rendered on non-group rows.
- intent: [name:pre*suf] is a name template for descendants; * is replaced by each descendant's name.
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:163-174,79-82,94-98

### PS-TAGS-06 · Row disclosure triangle (expand/collapse group)
- status: pending
- review: keep
- pre: A group (LayerSet) row with children.
- steps:
  1. Click the 'v'/'>' glyph at the left of a group row (or Enter/Space).
- observe: Glyph toggles 'v'<->'>'; the group's child rows show/hide. For non-group rows the glyph is blank and disabled (no-op).
- intent: UNDOCUMENTED - collapse/expand a group subtree in the panel (purely a panel-state toggle).
- code: apps/photoshop/src/panels/sections/tags/Row.tsx:57-59

### PS-TAGS-09 · [ignore] toggle glyph (X)
- status: pending
- review: keep
- pre: Any layer or group row; document open.
- steps:
  1. Click the 'X' glyph in the row's right cluster.
- observe: Layer name gains/loses '[ignore]'; row gets/loses 'ignored' styling; PS layer name updates (renameLayer). Toggling again removes it. Disabled while busy.
- intent: [ignore] drops the layer/group entirely from export (no manifest entry, no PNG).
- code: apps/photoshop/src/panels/sections/tags/Row.tsx:61-66

### PS-TAGS-10 · [merge] toggle glyph (M)
- status: pending
- review: keep
- pre: A group (LayerSet) row; disabled on non-group rows.
- steps:
  1. Click the 'M' glyph on a group row.
- observe: Group name gains/loses '[merge]'; glyph active styling toggles. On a non-group row the glyph is disabled with title '[merge] only applies to groups'.
- intent: [merge] flattens a whole group into one PNG (group-only tag).
- code: apps/photoshop/src/panels/sections/tags/Row.tsx:68-73

### PS-TAGS-13 · Advanced fields expander glyph (+ / -)
- status: pending
- review: keep
- pre: Any row.
- steps:
  1. Click the '+'/'-' glyph at the far right of the row.
- observe: Row expands to show the TagDetails sub-box; glyph flips to '-' (active). Click again collapses. State is per-row local (not persisted).
- intent: UNDOCUMENTED (only as a hover hint) - opens the folder/path/scale/origin/name-pattern editor for the row.
- code: apps/photoshop/src/panels/sections/tags/Row.tsx:97-99,182-188

### PS-TAGS-19 · Advanced: 'From selection' button
- status: pending
- review: keep
- pre: Row expanded; an active marquee selection in the document.
- steps:
  1. Make a rectangular marquee, click 'From selection'.
- observe: origin X/Y fields populate with the rounded centre of the selection bounds (draft only, requires Apply to commit). With no selection it silently does nothing (only a debug log).
- intent: UNDOCUMENTED - fills origin X/Y from the centre of the current Photoshop marquee selection.
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:147-153,84-96; apps/photoshop/src/api/ps-selection-bounds.ts:15-36

### PS-TAGS-22 · Advanced: Apply button
- status: pending
- review: keep
- pre: Row expanded; form dirty (differs from baseline).
- steps:
  1. Edit one or more advanced fields, click Apply.
- observe: Computes set/clear delta and fires a single renameLayer. Disabled when not dirty or busy. If the delta resolves to no valid set/clear (all invalid), no rename fires.
- intent: UNDOCUMENTED - commits the draft form as one minimal rename (delta vs baseline).
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:175-182,45-49; apps/photoshop/src/lib/tag-form.ts:114-129

### PS-TAGS-23 · Advanced: Revert button
- status: pending
- review: keep
- pre: Row expanded; form dirty.
- steps:
  1. Edit fields, click Revert.
- observe: All advanced fields snap back to baseline (node.tags); no rename fires. Disabled when not dirty or busy.
- intent: UNDOCUMENTED - discards the local draft back to the on-disk baseline.
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:176-178,51-53

### PS-TAGS-24 · Layer-tree live sync (poll + notification + rename refresh)
- status: pending
- review: keep
- pre: Document open; panel visible.
- steps:
  1. Rename/add/remove a layer directly in PS and wait ~1.5s (active) or switch panel away/back.
- observe: Tree reflects external changes without a manual refresh; unchanged subtrees keep node refs (rows don't tear down open dropdowns). Poll pauses while document.hidden.
- intent: UNDOCUMENTED - panel keeps the tree current via PS notifications and a visibility-adaptive poll.
- code: apps/photoshop/src/hooks/useTagTree.ts:44-91,115-119

### PS-TAGS-25 · renameLayer write path (XMP mirror + executeAsModal)
- status: pending
- review: keep
- pre: Document open; any tag-editing control invoked.
- steps:
  1. Invoke any toggle/dropdown/Apply that changes a name.
- observe: Target resolved outside the modal; inside executeAsModal sets target.name and mirrors tags to XMP (best-effort). On no active doc / layer-not-found / modal rejection, busy clears and lastError shows the reason.
- intent: Tag edits are persisted into the PSD layer name; re-import in Blender reads tags from names.
- code: apps/photoshop/src/api/layer-rename.ts:21-58

## Validate + Migration + Doc + Debug sections

### PS-AUX-01 · Active document accordion header (title + chevron + hint tooltip)
- status: pending
- review: keep
- observe: Section toggles open/closed; chevron flips v <-> >; hovering shows tooltip 'Doc name + canvas dimensions'. Open by default.
- intent: UNDOCUMENTED (index.md never describes the document-header section); hint reads 'Doc name + canvas dimensions'.
- code: apps/photoshop/src/panels/sections/DocSection.tsx:13

### PS-AUX-02 · Active document: name row (read-only)
- status: pending
- review: keep
- observe: Label 'name' with the document's filename rendered in monospace. With no doc open, instead shows 'No document open in Photoshop.'
- intent: UNDOCUMENTED; shows the active PS document name (mono).
- code: apps/photoshop/src/panels/sections/DocSection.tsx:18

### PS-AUX-03 · Active document: canvas row (read-only)
- status: pending
- review: keep
- observe: Label 'canvas' shows '<width> x <height> px' matching Image > Canvas Size, in monospace.
- intent: UNDOCUMENTED; shows canvas WxH in px (mono).
- code: apps/photoshop/src/panels/sections/DocSection.tsx:19

### PS-AUX-05 · Validate accordion header + badge (count / 'ok')
- status: pending
- review: keep
- observe: Badge shows the integer total of warnings+skipped+validation errors, or the literal 'ok' when total is 0. Header collapses/expands; tooltip text as above.
- intent: UNDOCUMENTED as a panel; index.md only says the manifest is validated before write. Header hint: 'Planner-emitted warnings + skipped layers. Click any row to jump to the offending layer in Photoshop.'
- code: apps/photoshop/src/panels/sections/ValidateSection.tsx:38-42

### PS-AUX-06 · Validate: 'Open a document to begin validation.' empty-state label
- status: pending
- review: keep
- observe: Body shows muted text 'Open a document to begin validation.'
- intent: UNDOCUMENTED; placeholder shown before any preview has run (preview === null).
- code: apps/photoshop/src/panels/sections/ValidateSection.tsx:16-20

### PS-AUX-07 · Validate: no-document message (preview.kind === 'no-document')
- status: pending
- review: keep
- observe: Body shows the planner's first error string, or 'No document open.' when none provided.
- intent: UNDOCUMENTED; shows preview.errors[0] or fallback 'No document open.'
- code: apps/photoshop/src/panels/sections/ValidateSection.tsx:23-30

### PS-AUX-08 · Validate: 'No issues. Manifest looks ready to export.' clean label
- status: pending
- review: keep
- observe: Badge='ok'; body shows 'No issues. Manifest looks ready to export.'
- intent: UNDOCUMENTED; clean-state confirmation when warnings+skipped+valErrors == 0.
- code: apps/photoshop/src/panels/sections/ValidateSection.tsx:43-44

### PS-AUX-09 · Validate: 'Manifest invalid:' error block + per-error rows
- status: pending
- review: keep
- observe: Red 'result error' block titled 'Manifest invalid:' with one row per error string from preview.errors.
- intent: Reflects index.md's 'manifest is validated before it is written, so a broken manifest never reaches disk' - surfaces ajv validation errors here.
- code: apps/photoshop/src/panels/sections/ValidateSection.tsx:47-54

### PS-AUX-10 · Validate: 'Warnings (N)' subgroup header
- status: pending
- review: keep
- observe: Subgroup titled 'Warnings (N)' renders with one WarningRow per warning.
- intent: Lists the planner-emitted warnings; count in title.
- code: apps/photoshop/src/panels/sections/ValidateSection.tsx:55-61

### PS-AUX-12 · Validate: 'Skipped (N)' subgroup header
- status: pending
- review: keep
- observe: Subgroup titled 'Skipped (N)' with one SkippedRow per skipped layer.
- intent: Lists skipped layers (e.g. hidden / [ignore]); count in title.
- code: apps/photoshop/src/panels/sections/ValidateSection.tsx:62-68

### PS-AUX-14 · Preview (Debug) accordion header + entry-count badge
- status: pending
- review: keep
- observe: Badge shows manifest layer count when >0, otherwise no badge; header toggles; tooltip as above.
- intent: UNDOCUMENTED panel; hint 'Dry-run of the export. Manifest entries listed below; warnings + skipped layers live in the Proscenio Validate panel.'
- code: apps/photoshop/src/panels/sections/DebugSection.tsx:19-23

### PS-AUX-15 · Preview: pre-run empty state ('Click Refresh to dry-run the export. Nothing is written.')
- status: pending
- review: keep
- observe: Muted text 'Click Refresh to dry-run the export. Nothing is written.' plus a Refresh button.
- intent: UNDOCUMENTED; placeholder shown when preview === null.
- code: apps/photoshop/src/panels/sections/DebugSection.tsx:24-30

### PS-AUX-17 · Preview: no-document body + Refresh
- status: pending
- review: keep
- observe: Muted error text (first error or fallback) and a Refresh button.
- intent: UNDOCUMENTED; shows preview.errors[0] or 'No document open.' plus a Refresh button.
- code: apps/photoshop/src/panels/sections/DebugSection.tsx:43-51

### PS-AUX-18 · Preview: anchor row (read-only)
- status: pending
- review: keep
- observe: Row 'anchor' shows '(canvas centre)' when manifest.anchor==null, else '<x>, <y> px' (mono).
- intent: UNDOCUMENTED; shows manifest anchor or '(canvas centre)' when null.
- code: apps/photoshop/src/panels/sections/DebugSection.tsx:57-62

### PS-AUX-19 · Preview: entries / skipped / warnings count rows (read-only)
- status: pending
- review: keep
- observe: Rows 'entries', 'skipped', 'warnings' show counts matching manifest.layers.length, skipped.length, warnings.length respectively.
- intent: UNDOCUMENTED; numeric summary of the dry-run plan.
- code: apps/photoshop/src/panels/sections/DebugSection.tsx:63-65

### PS-AUX-20 · Preview: polygon entry row
- status: pending
- review: keep
- observe: Row shows kind, name, path, and optional badges '(folder=..., blend=..., origin=x,y)' when those fields are set.
- intent: Reflects index.md 'one PNG per layer plus a manifest JSON' - lists each polygon manifest entry (kind, name, path, badges).
- code: apps/photoshop/src/panels/sections/DebugSection.tsx:100-108,111-117

### PS-AUX-21 · Preview: sprite entry row
- status: pending
- review: keep
- observe: Row shows 'sprite', the name, and '<N> frames' plus any badges.
- intent: Reflects index.md spritesheet behaviour - shows 'sprite' + name + 'N frames' for a sprite_frame group.
- code: apps/photoshop/src/panels/sections/DebugSection.tsx:90-98

### PS-AUX-22 · Preview: active-layer row highlight (selected styling)
- status: pending
- review: keep
- observe: The matching entry row gains the 'selected' class (highlighted). Selecting a non-matching/no/multiple layers leaves no row highlighted.
- intent: UNDOCUMENTED; the entry whose EntryRef matches the artist's currently selected PS layer is highlighted.
- code: apps/photoshop/src/panels/sections/DebugSection.tsx:69-73,80-86 (match useActiveLayerPath + entryMatchesPath)

### PS-AUX-23 · Legacy migration accordion header + count badge + hint
- status: pending
- review: keep
- observe: Section appears with badge = candidate count; defaultOpen when count>0; tooltip as above. Hidden entirely when preview.noDocument, or when count==0 and no prior result.
- intent: Reflects index.md tag vocabulary (legacy convention -> [ignore]); hint 'Convert legacy `_layerName` skip conventions to the [ignore] tag.'
- code: apps/photoshop/src/panels/sections/MigrationSection.tsx:20-25

### PS-AUX-24 · Legacy migration: 'No underscore-prefixed layers found.' label
- status: pending
- review: keep
- observe: Muted text 'No underscore-prefixed layers found.' shown above the result view.
- intent: UNDOCUMENTED; empty-state when count==0 but a lastResult exists (post-conversion).
- code: apps/photoshop/src/panels/sections/MigrationSection.tsx:26-28

### PS-AUX-25 · Legacy migration: 'N layer(s) ready to rename' + candidate rows (max 6 + 'and N more')
- status: pending
- review: keep
- observe: '8 layer(s) ready to rename:' then 6 CandidateRows then '...and 2 more.'
- intent: Previews the planned _name -> [ignore] renames before applying.
- code: apps/photoshop/src/panels/sections/MigrationSection.tsx:30-36

### PS-AUX-28 · Legacy migration: result view ('Renamed N layer(s)' + per-failure rows)
- status: pending
- review: keep
- observe: 'Renamed N layer(s).' on full success; on failures the block gets 'result error' class, '..., M failed:' and one warn row per failure ('<path>: <reason>').
- intent: UNDOCUMENTED; reports renamed count and any per-candidate failures after applying.
- code: apps/photoshop/src/panels/sections/MigrationSection.tsx:74-87

### PS-AUX-04 · Active document: Refresh button
- status: pending
- review: keep
- pre: Validate or Debug panel open.
- steps:
  1. 1. Change the active document (rename / resize canvas / switch tabs). 2. Click 'Refresh'.
- observe: name + canvas rows update synchronously to the now-active document (readDocSnapshot via app.activeDocument). No file is written.
- intent: UNDOCUMENTED; re-reads the active document header into the panel.
- code: apps/photoshop/src/panels/sections/DocSection.tsx:22 (handler ProscenioValidatePanel.tsx:37 / ProscenioDebugPanel.tsx:43 -> useDocSnapshot.refresh)

### PS-AUX-11 · Validate: Warning row (click-to-select offending layer)
- status: pending
- review: keep
- pre: At least one warning present.
- steps:
  1. 1. Click a warning row (or focus it and press Enter/Space). 2. Watch the PS Layers panel.
- observe: Row shows code + bold name + message. Clicking runs batchPlay 'select' on the layer matched by warning.layerPath; that layer becomes the active selection in PS. Keyboard Enter/Space also activates.
- intent: Each row selects the offending PS layer; hint says 'Click any row to jump to the offending layer in Photoshop.'
- code: apps/photoshop/src/panels/sections/ValidateSection.tsx:82-95 (handler useLayerSelection -> ps-selection.selectLayerByPath:61)

### PS-AUX-13 · Validate: Skipped row (click-to-select skipped layer)
- status: pending
- review: keep
- pre: At least one skipped layer present.
- steps:
  1. 1. Click a skipped row (or Enter/Space when focused). 2. Watch the PS Layers panel.
- observe: Row shows skip reason code + layer name; clicking selects that layer (by its layerPath) in PS via batchPlay.
- intent: Row selects the skipped PS layer; shows the skip reason as the code and the layer name.
- code: apps/photoshop/src/panels/sections/ValidateSection.tsx:97-107 (handler useLayerSelection -> selectLayerByPath:61)

### PS-AUX-16 · Preview: Refresh button (dry-run)
- status: pending
- review: keep
- pre: Debug panel open, document open.
- steps:
  1. 1. Edit the PSD layers. 2. Click 'Refresh'.
- observe: anchor/entries/skipped/warnings rows and the entries list recompute from previewExport(opts) with skipHidden:true. No file is written to disk.
- intent: Runs a dry-run preview of the export; per index.md the recursive walk produces manifest + PNGs, but Refresh writes nothing (dry-run).
- code: apps/photoshop/src/panels/sections/DebugSection.tsx:29,49,66 (handler ProscenioDebugPanel.onRefresh:31 -> useExportPreview.refresh -> previewExport)

### PS-AUX-26 · Legacy migration: candidate row (click-to-select layer)
- status: pending
- review: keep
- pre: Candidate rows visible.
- steps:
  1. 1. Click a candidate row (or Enter/Space when focused). 2. Watch PS Layers panel.
- observe: Row shows oldName -> newName; clicking selects the layer at candidate.layerPath in PS via batchPlay.
- intent: UNDOCUMENTED; clicking a candidate selects that layer in PS (shows old -> new name).
- code: apps/photoshop/src/panels/sections/MigrationSection.tsx:47-72 (handler useLayerSelection -> selectLayerByPath:61)

### PS-AUX-27 · Legacy migration: 'Convert N layer(s) to [ignore]' button
- status: pending
- review: keep
- pre: Doc with >=1 underscore-prefixed candidate.
- steps:
  1. 1. Click 'Convert N layer(s) to [ignore]'. 2. Watch the button + PS layer names.
- observe: Button label switches to 'Renaming...' and disables (busy=true). Inside one executeAsModal, candidates are renamed deepest-first to their [ignore] newName (single undo step). On finish: result view appears, preview re-reads (candidates -> 0), button re-enables.
- intent: Applies the batch rename, converting _name layers to [ignore]; reflects index.md tag conventions.
- code: apps/photoshop/src/panels/sections/MigrationSection.tsx:37-39 (handler useMigration.apply -> applyUnderscoreMigration -> executeAsModal:57)
