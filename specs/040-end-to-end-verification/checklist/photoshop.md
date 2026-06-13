# Photoshop plugin — manual-test checklist

A standing, re-runnable manual-test surface for the Proscenio Photoshop UXP plugin: every option, field, button, and flow across the Exporter, Import, Tags, and auxiliary (Validate / Debug / Migration / Doc) sections, audited against documented intent.

## Surface tokens

| Token | Panel / section |
| --- | --- |
| EXPORT | Exporter panel: Output folder + Export options + Pixels per unit + Filename templates + Run export + Re-export selected sections, plus the export -> manifest + PNG write path |
| IMPORT | Import section: rebuild PSD from manifest (png-placer, manifest-reader) |
| TAGS | Tags panel + tag vocabulary (parse/tree/write/form) + tagging UI |
| AUX | Validate + Migration + Doc + Debug sections |

## Exporter panel: Output folder + Export options + Pixels per unit + Filename templates + Run export + Re-export selected sections, plus the export -> manifest + PNG write path

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| PS-EXPORT-01 | Output folder — path display / 'No folder picked.' placeholder | With no folder: 'No folder picked.' card. After picking: the folder.nativePath string is shown and is the title tooltip. | Shows where the export writes the manifest + PNGs; the path persists across plugin reloads. | apps/photoshop/src/panels/sections/FolderSection.tsx:17-23 | pending |
| PS-EXPORT-04 | Output folder accordion header + hint tooltip | Chevron toggles v/>; body shows/hides; native title tooltip shows the hint text. | Collapsible Output-folder section; hint explains it persists across reloads. | apps/photoshop/src/components/Accordion.tsx:44-59 (title='Output folder') | pending |
| PS-EXPORT-05 | Skip hidden layers checkbox | When checked (default true), hidden layers are dropped from the plan (planner.ts:324 reason 'hidden'); when unchecked, hidden layers are included in writes. | Export options section; doc implies hidden/ignored layers are excluded (use [ignore] tag to exclude). Skip-hidden toggle itself is UNDOCUMENTED by name. | apps/photoshop/src/panels/sections/ExportSection.tsx:82-84 -> onSkipHidden -> useExportFlow.setOption('skipHidden') | pending |
| PS-EXPORT-06 | Export options accordion header + hint | Tooltip shows the [ignore]-tag hint; section collapses/expands. | Hint: use the [ignore] tag in a layer/group name to exclude it from export. | apps/photoshop/src/panels/sections/ExportSection.tsx:78-85 | pending |
| PS-EXPORT-07 | Pixels per unit (ppu) text field | Valid finite >0 values persist (localStorage) and become manifest.pixels_per_unit; invalid/zero/negative inputs are ignored (no state change). canvas row updates docHeight/ppu units. | UNDOCUMENTED on this doc page — conversion factor for Blender/Godot; higher PPU = smaller world-space objects (hint only). Doc index.md does not mention PPU. | apps/photoshop/src/panels/sections/ExportSection.tsx:91-95 -> onPpuInput -> usePixelsPerUnit.setPixelsPerUnit | pending |
| PS-EXPORT-08 | canvas read-only row (NNpx = NN.NN units) | Displays e.g. '1024px = 16.00 units'; hidden entirely when docHeight is null or ppu <= 0. | UNDOCUMENTED — shows doc height converted to world units at the current PPU. | apps/photoshop/src/panels/sections/ExportSection.tsx:97-103 (heightInUnits) | pending |
| PS-EXPORT-09 | Reset to {default} ppu button | ppu returns to 100 and persists; the button is disabled (greyed) when ppu already equals the default. | UNDOCUMENTED — resets ppu to the default (100). | apps/photoshop/src/panels/sections/ExportSection.tsx:104-106 -> onPpuReset -> usePixelsPerUnit (DEFAULT 100) | pending |
| PS-EXPORT-10 | mesh filename template field | Value persists to localStorage; empty string normalises back to '{name}.png'; mesh PNG paths in the preview/Reveal reflect the template under images/. | Filename templates section; tokens {name} and {kind} for meshes; images/ prefix and [folder:...] subfolder added automatically. | apps/photoshop/src/panels/sections/ExportSection.tsx:113-118 -> onPolygonInput -> useFilenameTemplate.setPolygonTemplate; consumed planner.ts:641 | pending |
| PS-EXPORT-11 | sprite (frames) filename template field | Persists; empty normalises to '{name}/{index}.png'; sprite frame paths reflect the template. | Tokens {name} and {index} for frames; images/ prefix + subfolder added automatically. | apps/photoshop/src/panels/sections/ExportSection.tsx:120-125 -> onFramesInput -> setFramesTemplate; consumed planner.ts:500/675 | pending |
| PS-EXPORT-12 | Reset to defaults (templates) button | Both templates revert to {name}.png and {name}/{index}.png; button disabled when both already equal defaults. | UNDOCUMENTED — resets both filename templates to defaults. | apps/photoshop/src/panels/sections/ExportSection.tsx:127-129 -> onResetTemplates -> useFilenameTemplate.reset | pending |
| PS-EXPORT-13 | Filename templates accordion (collapsed by default) | Starts closed (chevron '>'); expands on click; tooltip lists {name}/{kind}/{index} tokens. | Section with token hint; collapsed by default. | apps/photoshop/src/panels/sections/ExportSection.tsx:108-112 (defaultOpen={false}) | pending |
| PS-EXPORT-15 | Export button disabled state | Button greyed/disabled when busy OR folder===null OR doc(snapshot)===null; enabled only when all three are satisfied. | Export should be unavailable until prerequisites are met (folder + document). | apps/photoshop/src/panels/ProscenioExporter.tsx:65 exportDisabled; ExportSection.tsx:132 disabled | pending |
| PS-EXPORT-16 | Export result — OK view ('Wrote N entry(ies) to <file>') | Shows entryCount and manifestFile; lists any PNG write rows where !r.ok with skippedReason. | Confirms the manifest filename and entry count written. | apps/photoshop/src/panels/sections/ExportSection.tsx:141-156 (ExportResultView ok) | pending |
| PS-EXPORT-17 | Export result — error view (validation-failed / no-document / failed) | Shows 'Export <kind>.' plus the errors[] list; note 'failed' shows the raw Error.message or per-PNG 'path: reason' strings. | Surfaces why an export did not complete (validation gate or write failure). | apps/photoshop/src/panels/sections/ExportSection.tsx:158-164 (ExportResultView error) | pending |
| PS-EXPORT-18 | Run export accordion header + hint | Tooltip shows the write hint; section collapses/expands. | Hint: writes the manifest JSON + all PNGs to the output folder. | apps/photoshop/src/panels/sections/ExportSection.tsx:131 | pending |
| PS-EXPORT-19 | Re-export selected — entry / kind detail rows or placeholder | When matched: 'entry' (mono name) and 'kind' rows shown; when no match: placeholder 'Select a layer in Photoshop that maps to a manifest entry.' | Rewrites the PNG(s) for the layer selected in Photoshop; manifest JSON is not touched. | apps/photoshop/src/panels/sections/ReexportSection.tsx:49-58 (findMatchedEntry) | pending |
| PS-EXPORT-21 | Re-export button disabled state | Disabled when busy, no matched entry, or no folder; enabled only when both a match and a folder exist. | Re-export unavailable without a matched entry + folder. | apps/photoshop/src/panels/sections/ReexportSection.tsx:65 (disabled = busy \|\| matched===null \|\| folder===null) | pending |
| PS-EXPORT-22 | Re-export result rows (ok / error) | ok: 'Wrote N PNG(s).'; error: 'Re-export <kind>.' plus errors[] (e.g. 'not-found' or per-PNG failure). | Confirms how many PNGs were rewritten, or surfaces re-export errors. | apps/photoshop/src/panels/sections/ReexportSection.tsx:92-108 (ReexportResult) | pending |
| PS-EXPORT-26 | empty / zero-layer document export | Validation passes (empty layers array is schema-valid); manifest written with 'layers: []'; result 'Wrote 0 entry(ies)'. No PNGs written. | A recursive walk produces one PNG per layer plus a manifest; doc does not state behaviour when no exportable layers exist. | apps/photoshop/src/lib/planner.ts:133-148 (layers: []) ; schema layers has no minItems | pending |

#### [ ] PS-EXPORT-02 · Pick folder / Change folder button
- **Intent:** Choose the output folder; the path persists across reloads (folder-storage persistent token).
- **Code:** apps/photoshop/src/panels/sections/FolderSection.tsx:25-27 -> useFolderCache.pick -> api/folder-storage.ts:31
- **Pre:** Exporter panel open
- **Steps:** Click 'Pick folder' > choose a directory in the OS picker
- **Expect:** Path display updates to the chosen folder; a persistent token is written to localStorage key 'proscenio.exporter.folderToken'; reloading the plugin restores the same folder without prompting.
- **Status:** pending

#### [ ] PS-EXPORT-03 · Forget button
- **Intent:** UNDOCUMENTED — doc never mentions clearing the remembered folder.
- **Code:** apps/photoshop/src/panels/sections/FolderSection.tsx:28 -> useFolderCache.clear -> api/folder-storage.ts:42 (clearRememberedFolder)
- **Pre:** A folder is currently picked
- **Steps:** With a folder set, click 'Forget'
- **Expect:** localStorage token removed; folder state resets to null; card reverts to 'No folder picked.'; Export button becomes disabled (folder === null).
- **Status:** pending

#### [ ] PS-EXPORT-14 · Export manifest + PNGs button (Run export)
- **Intent:** Writes the manifest JSON + all PNGs to the output folder; a recursive layer walk produces one PNG per layer plus a manifest JSON, validated before written so a broken manifest never reaches disk.
- **Code:** apps/photoshop/src/panels/sections/ExportSection.tsx:131-135 -> ProscenioExporter.onExport -> useExportFlow.run -> api/export-flow.ts:90 runExport
- **Pre:** A document is open AND a folder is picked (else disabled). Fixture: doll PSD with tagged layers.
- **Steps:** Pick a folder > open a layered PSD > click 'Export manifest + PNGs' > wait for the modal banner
- **Expect:** Button shows 'Exporting...' while busy; on success a green result 'Wrote N entry(ies) to <doc>.photoshop_exported.json' plus per-PNG warn rows for any skipped writes; the .photoshop_exported.json file and images/*.png appear on disk.
- **Status:** pending

#### [ ] PS-EXPORT-20 · Re-export this entry's PNG button
- **Intent:** Rewrites only the selected layer's PNG(s), leaving the manifest untouched.
- **Code:** apps/photoshop/src/panels/sections/ReexportSection.tsx:59-68 onReexport -> api/export-flow.ts:167 runSingleLayerExport
- **Pre:** A folder is picked AND the active PS layer matches a manifest entry
- **Steps:** Pick folder > select a matching layer > click 'Re-export this entry's PNG'
- **Expect:** Button shows 'Re-exporting...'; on success 'Wrote N PNG(s).'; only that entry's PNG file(s) rewritten on disk; the *.photoshop_exported.json manifest is NOT modified.
- **Status:** pending

#### [ ] PS-EXPORT-23 · manifest validation gate (ajv) — export path
- **Intent:** The manifest is validated against the schema with ajv before it is written, so a broken manifest never reaches disk.
- **Code:** apps/photoshop/src/api/export-flow.ts:107-111 validateManifest -> api/manifest-validator.ts:28; schema packages/models/schemas/psd_manifest.schema.json
- **Pre:** A document whose plan would produce an invalid manifest (e.g. a sub-pixel/zero size, or a layer name that strips to empty without fallback)
- **Steps:** Export a doc crafted to break a schema rule (e.g. negative/zero coordinate) and observe the result
- **Expect:** runExport returns kind 'validation-failed' with errors[]; NO files written; error block lists '(root) ...' / instancePath messages.
- **Status:** pending

#### [ ] PS-EXPORT-24 · manifest write (writeManifest) — atomicity with PNGs
- **Intent:** The manifest is persisted only if every PNG landed, so it never references missing files.
- **Code:** apps/photoshop/src/api/export-flow.ts:118-126 (executeAsModal) -> api/manifest-writer.ts:9 writeManifest
- **Pre:** A folder picked; an export where at least one PNG write fails (e.g. one layer renamed after preview)
- **Steps:** Trigger an export where one PNG write returns ok:false; inspect the folder
- **Expect:** manifestWritten=false; NO manifest JSON written; result kind 'failed' lists the failing 'outputPath: reason'. Existing PNGs that succeeded may still be on disk (partial).
- **Status:** pending

#### [ ] PS-EXPORT-25 · PNG write per layer (runWrites/writeLayerPng) — temp doc + trim + saveAs.png
- **Intent:** One PNG per layer: isolate the source layer on a temp doc, trim transparency, save PNG into the target folder.
- **Code:** apps/photoshop/src/api/png-writer.ts:23-77 runWrites/writeLayerPng
- **Pre:** Export running inside the modal; layers resolvable by path
- **Steps:** Export a multi-layer doc; verify images/*.png exist and match each layer's trimmed bounds
- **Expect:** For each write, a PNG appears at folder/<outputPath>; a layer whose path no longer resolves yields ok:false 'source layer not found'.
- **Status:** pending

## Import section: rebuild PSD from manifest (png-placer, manifest-reader)

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| PS-IMPORT-01 | Accordion header "Import (manifest to PSD)" (collapse/expand) | Section toggles open: chevron flips '>' to 'v', section className flips closed/open, body with the Import button renders. Click again collapses it (body unmounts). | UNDOCUMENTED (doc says the plugin "can rebuild a PSD from a manifest" but never describes the panel section/header). | apps/photoshop/src/panels/sections/ImportSection.tsx:14-18; apps/photoshop/src/components/Accordion.tsx:33-60 | pending |
| PS-IMPORT-02 | Accordion header keyboard toggle (Enter / Space) | Each Enter/Space press toggles open state (preventDefault stops page scroll on Space); aria-expanded reflects state. | UNDOCUMENTED (keyboard a11y affordance; not in doc). | apps/photoshop/src/components/Accordion.tsx:35-40 | pending |
| PS-IMPORT-03 | Accordion header tooltip (hint title attribute) | Native tooltip shows: "Pick a Proscenio manifest JSON. The plugin recreates the PSD with placed layers / sprite_frame groups; the document stays open and unsaved -- use File > Save As to commit it to disk." | UNDOCUMENTED (hint text describing the import behavior; only an HTML title tooltip). | apps/photoshop/src/panels/sections/ImportSection.tsx:17; apps/photoshop/src/components/Accordion.tsx:52 | pending |
| PS-IMPORT-08 | Import OK result — "Stamped N entry(ies) (M skipped). Use File > Save As" | Green "result ok" body reads "Stamped <stamped> entry(ies)" and appends " (<skipped> skipped)" only when skipped > 0, then ". Use File > Save As to commit the PSD." | UNDOCUMENTED (doc never describes the stamped/skipped counts or the result body). | apps/photoshop/src/panels/sections/ImportSection.tsx:27-42; apps/photoshop/src/api/import-flow.ts:62-73 | pending |
| PS-IMPORT-09 | Import OK result — per-entry warning rows | Yellow "result-row warn" lines, one per warning, e.g. "mesh <name>: missing PNG at <path>", "<file> bounds WxH differ from manifest WxH; using PNG bounds.", "sprite <name>: zero frames placed; group removed". | UNDOCUMENTED (warnings surface for missing PNGs / bounds mismatch / empty sprites not in doc). | apps/photoshop/src/panels/sections/ImportSection.tsx:38-40; apps/photoshop/src/api/import-flow.ts:96,107,109,123,131,142,150 | pending |
| PS-IMPORT-10 | Import failed result — "Import failed." + error rows | Red "result error" block: "Import failed." followed by one row per error message string from the caught exception. | UNDOCUMENTED (doc does not describe the modal failure surface). | apps/photoshop/src/panels/sections/ImportSection.tsx:44-52; apps/photoshop/src/api/import-flow.ts:34-41 | pending |
| PS-IMPORT-11 | "Importing..." busy state / button disable | Button label switches to "Importing..." and disabled=true for the duration; re-enables and reverts label to "Import manifest as PSD" in the finally block regardless of success/failure. | UNDOCUMENTED (busy/disable UX behavior). | apps/photoshop/src/panels/sections/ImportSection.tsx:19-21; apps/photoshop/src/hooks/useImportFlow.ts:30-36 | pending |

#### [ ] PS-IMPORT-04 · "Import manifest as PSD" action button (file picker stage)
- **Intent:** Rebuild a PSD from a manifest; pick a Proscenio manifest JSON (doc: "plugin can rebuild a PSD from a manifest").
- **Code:** apps/photoshop/src/panels/sections/ImportSection.tsx:19-21; apps/photoshop/src/hooks/useImportFlow.ts:22-28; apps/photoshop/src/api/manifest-reader.ts:26-30
- **Pre:** Import section expanded; not busy.
- **Steps:** Click "Import manifest as PSD" > UXP file picker opens (types: json).
- **Expect:** OS/UXP JSON file picker appears. Cancelling the picker (returns null) silently no-ops: no error, no result view, prior manifestErrors cleared (set to null on run start).
- **Status:** pending

#### [ ] PS-IMPORT-05 · Import flow — invalid JSON / schema-invalid manifest path
- **Intent:** Manifest is validated before use; a broken manifest never reaches disk (doc: validation gate).
- **Code:** apps/photoshop/src/api/manifest-reader.ts:32-46; apps/photoshop/src/api/manifest-validator.ts:34-42; apps/photoshop/src/hooks/useImportFlow.ts:26-29
- **Pre:** Import section expanded.
- **Steps:** Click Import > pick a .json that is malformed JSON OR valid JSON failing the v2 schema.
- **Expect:** "Manifest invalid." error block appears (ManifestErrors) listing per-error rows like "(root) must have required property 'size'" or "manifest is not valid JSON: ..."; no document is created; busy never set true.
- **Status:** pending

#### [ ] PS-IMPORT-06 · Import flow — parent-folder resolution failure path
- **Intent:** UNDOCUMENTED (doc never mentions resolving the manifest's sibling PNG folder).
- **Code:** apps/photoshop/src/api/manifest-reader.ts:47-53,60-75
- **Pre:** Import section expanded.
- **Steps:** Pick a schema-valid manifest whose parent folder cannot be resolved (no file.parent and empty/unresolvable nativePath).
- **Expect:** "Manifest invalid." block shows single error "could not resolve manifest's parent folder"; import does not proceed.
- **Status:** pending

#### [ ] PS-IMPORT-07 · Import flow — modal document build + entry stamping (happy path)
- **Intent:** Recreate the PSD with placed layers / sprite_frame groups; document stays open and unsaved (doc + hint).
- **Code:** apps/photoshop/src/api/import-flow.ts:26-74; apps/photoshop/src/api/png-placer.ts:20-71
- **Pre:** Valid manifest picked; sibling PNGs present alongside the manifest at the declared relative paths.
- **Steps:** Click Import > pick a valid manifest with PNGs on disk > wait.
- **Expect:** Button shows "Importing..." and is disabled while busy; a single "Proscenio import" modal runs; a new transparent RGB document named manifest.doc (size = manifest.size) opens with one layer per mesh entry and one group per sprite (frames as layers named by index). Entries stacked so z_order 0 ends on top. Result shows "Stamped N entry(ies). Use File > Save As to commit the PSD."
- **Status:** pending

#### [ ] PS-IMPORT-12 · Side effect — pixels_per_unit seeded into localStorage on import
- **Intent:** Seed the exporter PPU from the imported manifest so a re-export emits the imported scale (code comment / pixels-per-unit-store doc).
- **Code:** apps/photoshop/src/api/import-flow.ts:54-56; apps/photoshop/src/api/pixels-per-unit-store.ts:28-36
- **Pre:** Valid manifest with a pixels_per_unit value distinct from the current Export PPU input.
- **Steps:** Import a manifest > inspect the Export section's pixels-per-unit input (and after a panel reload).
- **Expect:** localStorage key proscenio.pixelsPerUnit is overwritten with manifest.pixels_per_unit (normalised, >0). NOTE the live Export input does NOT update this session (see finding); value only takes effect after panel reload.
- **Status:** pending

## Tags panel + tag vocabulary (parse/tree/write/form) + tagging UI

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| PS-TAGS-01 | Tags accordion header (title + chevron) | Section toggles open/closed; chevron flips between 'v' and '>'; body hides/shows. | UNDOCUMENTED - doc describes tagging but never the Tags panel/accordion chrome. | apps/photoshop/src/components/Accordion.tsx:46-59 | pending |
| PS-TAGS-02 | Tags header count badge | Badge equals the number of top-level layers (tree.length); 0 layers shows the empty-state body with no badge. | UNDOCUMENTED - count of top-level layers shown next to the title. | apps/photoshop/src/panels/sections/TagsSection.tsx:39 | pending |
| PS-TAGS-03 | Tags header hint tooltip ('?' equivalent) | Tooltip 'Layer tree with bracket-tag controls per row. Click + on a row to edit folder / path / scale / origin / name pattern.' appears. | UNDOCUMENTED - hover hint explaining the row controls; there is no visible '?' button, only an HTML title tooltip. | apps/photoshop/src/panels/sections/TagsSection.tsx:41 | pending |
| PS-TAGS-04 | Empty-state label ('No layers. Open a PSD to begin tagging.') | Body reads 'No layers. Open a PSD to begin tagging.'; no tree, no badge. | UNDOCUMENTED - placeholder when no document/layers. | apps/photoshop/src/panels/sections/TagsSection.tsx:33 | pending |
| PS-TAGS-05 | Rename-error warning row (lastError) | A red 'warn' body row appears above the tree showing the failure reason (e.g. 'layer not found', 'no active document'). | UNDOCUMENTED - surfaces a failed rename reason. | apps/photoshop/src/panels/sections/TagsSection.tsx:43-45 | pending |
| PS-TAGS-07 | Row name label (click to select layer in PS) | selectLayerByPath fires; the matching layer becomes active/selected in the PS Layers panel. Label shows display name (tag-stripped); falls back to raw name when display name is empty. Active layer's row gets 'selected' styling. | UNDOCUMENTED - clicking the row name selects/reveals that layer in Photoshop. | apps/photoshop/src/panels/sections/tags/Row.tsx:52-55 | pending |
| PS-TAGS-08 | Inline badge strip (F/P/S/O/OM/NP) | Badges render: F=folder value, P=path, S=scale, O='x,y', OM (marker, no value), NP=pattern, each with a hover title. Absent tags show no badge. | UNDOCUMENTED - read-only compact display of folder/path/scale/origin/origin-marker/name-pattern tags present on the row. | apps/photoshop/src/panels/sections/tags/Badges.tsx:19-38 | pending |
| PS-TAGS-11 | Kind dropdown (auto / mesh / sprite) | auto clears the kind tag; mesh writes '[mesh]'; sprite writes '[sprite]'. PS layer name updates accordingly. (See finding: on a [spritesheet] group this rewrites it to [sprite].) | [mesh]/[poly]/[polygon] -> kind:mesh (Polygon2D); [sprite] -> kind:sprite (Sprite2D); auto = no kind tag. | apps/photoshop/src/panels/sections/tags/Row.tsx:75-84,157-168 | pending |
| PS-TAGS-12 | Blend dropdown (none / mult / scrn / add) | none clears [blend]; multiply/screen/additive write '[blend:multiply\|screen\|additive]'. A pre-existing [blend:normal] displays as 'none'. PS layer name updates. | [blend:VALUE] records the intended blend mode (normal/multiply/screen/additive) as metadata. | apps/photoshop/src/panels/sections/tags/Row.tsx:86-95,169-181 | pending |
| PS-TAGS-14 | Advanced: folder text field | Draft only updates on type; Apply writes '[folder:NAME]'. Empty value on Apply clears the tag. Layer name updates on Apply, not per keystroke. | [folder:NAME] becomes a Blender Collection NAME; children inherit it (output subfolder under images/). | apps/photoshop/src/panels/sections/tags/Details.tsx:100-109,55-58 | pending |
| PS-TAGS-15 | Advanced: path text field | Valid value writes '[path:NAME]'; empty clears. Invalid values (containing / or \, or '.'/'..') are silently skipped (no change, no error surfaced). | [path:NAME] overrides the on-disk leaf filename stem (no slashes). | apps/photoshop/src/panels/sections/tags/Details.tsx:110-119,59-62,69-74 | pending |
| PS-TAGS-16 | Advanced: scale text field | Positive finite number writes '[scale:N]'; empty clears. 0, negative, or non-numeric are skipped (no write). No validation/sub-pixel warning is shown in the panel (see finding). | [scale:N] multiplies bounding-box size by N; a sub-pixel result raises a validation warning. | apps/photoshop/src/panels/sections/tags/Details.tsx:120-129,63-66,76-81 | pending |
| PS-TAGS-17 | Advanced: origin X field | When both X and Y parse as finite, writes '[origin:X,Y]'; both empty clears origin. Non-finite parse skips. Note: a non-numeric X/Y is skipped, not errored. | [origin:X,Y] sets an explicit pivot in PSD pixels overriding the implicit centre. | apps/photoshop/src/panels/sections/tags/Details.tsx:130-138,67-70,83-92 | pending |
| PS-TAGS-18 | Advanced: origin Y field | Combined with X to write '[origin:X,Y]'; see PS-TAGS-17. | Second component of [origin:X,Y] explicit pivot. | apps/photoshop/src/panels/sections/tags/Details.tsx:139-146,71-74,83-92 | pending |
| PS-TAGS-20 | Advanced: origin marker checkbox | Checked writes bare '[origin]'; unchecked clears it. Note: writer suppresses '[origin]' when explicit '[origin:x,y]' coords are present (mutually exclusive). | [origin] marks the layer's bbox centre as its parent [spritesheet]/[merge] group's pivot (marker layer not exported). | apps/photoshop/src/panels/sections/tags/Details.tsx:155-162,75-78,120-126 | pending |
| PS-TAGS-21 | Advanced: name pattern field (groups only) | Valid pattern (non-empty, contains '*') writes '[name:..]'; empty clears. A pattern without '*' is skipped. Field is not rendered on non-group rows. | [name:pre*suf] is a name template for descendants; * is replaced by each descendant's name. | apps/photoshop/src/panels/sections/tags/Details.tsx:163-174,79-82,94-98 | pending |

#### [ ] PS-TAGS-06 · Row disclosure triangle (expand/collapse group)
- **Intent:** UNDOCUMENTED - collapse/expand a group subtree in the panel (purely a panel-state toggle).
- **Code:** apps/photoshop/src/panels/sections/tags/Row.tsx:57-59
- **Pre:** A group (LayerSet) row with children.
- **Steps:** Click the 'v'/'>' glyph at the left of a group row (or Enter/Space).
- **Expect:** Glyph toggles 'v'<->'>'; the group's child rows show/hide. For non-group rows the glyph is blank and disabled (no-op).
- **Status:** pending

#### [ ] PS-TAGS-09 · [ignore] toggle glyph (X)
- **Intent:** [ignore] drops the layer/group entirely from export (no manifest entry, no PNG).
- **Code:** apps/photoshop/src/panels/sections/tags/Row.tsx:61-66
- **Pre:** Any layer or group row; document open.
- **Steps:** Click the 'X' glyph in the row's right cluster.
- **Expect:** Layer name gains/loses '[ignore]'; row gets/loses 'ignored' styling; PS layer name updates (renameLayer). Toggling again removes it. Disabled while busy.
- **Status:** pending

#### [ ] PS-TAGS-10 · [merge] toggle glyph (M)
- **Intent:** [merge] flattens a whole group into one PNG (group-only tag).
- **Code:** apps/photoshop/src/panels/sections/tags/Row.tsx:68-73
- **Pre:** A group (LayerSet) row; disabled on non-group rows.
- **Steps:** Click the 'M' glyph on a group row.
- **Expect:** Group name gains/loses '[merge]'; glyph active styling toggles. On a non-group row the glyph is disabled with title '[merge] only applies to groups'.
- **Status:** pending

#### [ ] PS-TAGS-13 · Advanced fields expander glyph (+ / -)
- **Intent:** UNDOCUMENTED (only as a hover hint) - opens the folder/path/scale/origin/name-pattern editor for the row.
- **Code:** apps/photoshop/src/panels/sections/tags/Row.tsx:97-99,182-188
- **Pre:** Any row.
- **Steps:** Click the '+'/'-' glyph at the far right of the row.
- **Expect:** Row expands to show the TagDetails sub-box; glyph flips to '-' (active). Click again collapses. State is per-row local (not persisted).
- **Status:** pending

#### [ ] PS-TAGS-19 · Advanced: 'From selection' button
- **Intent:** UNDOCUMENTED - fills origin X/Y from the centre of the current Photoshop marquee selection.
- **Code:** apps/photoshop/src/panels/sections/tags/Details.tsx:147-153,84-96; apps/photoshop/src/api/ps-selection-bounds.ts:15-36
- **Pre:** Row expanded; an active marquee selection in the document.
- **Steps:** Make a rectangular marquee, click 'From selection'.
- **Expect:** origin X/Y fields populate with the rounded centre of the selection bounds (draft only, requires Apply to commit). With no selection it silently does nothing (only a debug log).
- **Status:** pending

#### [ ] PS-TAGS-22 · Advanced: Apply button
- **Intent:** UNDOCUMENTED - commits the draft form as one minimal rename (delta vs baseline).
- **Code:** apps/photoshop/src/panels/sections/tags/Details.tsx:175-182,45-49; apps/photoshop/src/lib/tag-form.ts:114-129
- **Pre:** Row expanded; form dirty (differs from baseline).
- **Steps:** Edit one or more advanced fields, click Apply.
- **Expect:** Computes set/clear delta and fires a single renameLayer. Disabled when not dirty or busy. If the delta resolves to no valid set/clear (all invalid), no rename fires.
- **Status:** pending

#### [ ] PS-TAGS-23 · Advanced: Revert button
- **Intent:** UNDOCUMENTED - discards the local draft back to the on-disk baseline.
- **Code:** apps/photoshop/src/panels/sections/tags/Details.tsx:176-178,51-53
- **Pre:** Row expanded; form dirty.
- **Steps:** Edit fields, click Revert.
- **Expect:** All advanced fields snap back to baseline (node.tags); no rename fires. Disabled when not dirty or busy.
- **Status:** pending

#### [ ] PS-TAGS-24 · Layer-tree live sync (poll + notification + rename refresh)
- **Intent:** UNDOCUMENTED - panel keeps the tree current via PS notifications and a visibility-adaptive poll.
- **Code:** apps/photoshop/src/hooks/useTagTree.ts:44-91,115-119
- **Pre:** Document open; panel visible.
- **Steps:** Rename/add/remove a layer directly in PS and wait ~1.5s (active) or switch panel away/back.
- **Expect:** Tree reflects external changes without a manual refresh; unchanged subtrees keep node refs (rows don't tear down open dropdowns). Poll pauses while document.hidden.
- **Status:** pending

#### [ ] PS-TAGS-25 · renameLayer write path (XMP mirror + executeAsModal)
- **Intent:** Tag edits are persisted into the PSD layer name; re-import in Blender reads tags from names.
- **Code:** apps/photoshop/src/api/layer-rename.ts:21-58
- **Pre:** Document open; any tag-editing control invoked.
- **Steps:** Invoke any toggle/dropdown/Apply that changes a name.
- **Expect:** Target resolved outside the modal; inside executeAsModal sets target.name and mirrors tags to XMP (best-effort). On no active doc / layer-not-found / modal rejection, busy clears and lastError shows the reason.
- **Status:** pending

## Validate + Migration + Doc + Debug sections

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| PS-AUX-01 | Active document accordion header (title + chevron + hint tooltip) | Section toggles open/closed; chevron flips v <-> >; hovering shows tooltip 'Doc name + canvas dimensions'. Open by default. | UNDOCUMENTED (index.md never describes the document-header section); hint reads 'Doc name + canvas dimensions'. | apps/photoshop/src/panels/sections/DocSection.tsx:13 | pending |
| PS-AUX-02 | Active document: name row (read-only) | Label 'name' with the document's filename rendered in monospace. With no doc open, instead shows 'No document open in Photoshop.' | UNDOCUMENTED; shows the active PS document name (mono). | apps/photoshop/src/panels/sections/DocSection.tsx:18 | pending |
| PS-AUX-03 | Active document: canvas row (read-only) | Label 'canvas' shows '<width> x <height> px' matching Image > Canvas Size, in monospace. | UNDOCUMENTED; shows canvas WxH in px (mono). | apps/photoshop/src/panels/sections/DocSection.tsx:19 | pending |
| PS-AUX-05 | Validate accordion header + badge (count / 'ok') | Badge shows the integer total of warnings+skipped+validation errors, or the literal 'ok' when total is 0. Header collapses/expands; tooltip text as above. | UNDOCUMENTED as a panel; index.md only says the manifest is validated before write. Header hint: 'Planner-emitted warnings + skipped layers. Click any row to jump to the offending layer in Photoshop.' | apps/photoshop/src/panels/sections/ValidateSection.tsx:38-42 | pending |
| PS-AUX-06 | Validate: 'Open a document to begin validation.' empty-state label | Body shows muted text 'Open a document to begin validation.' | UNDOCUMENTED; placeholder shown before any preview has run (preview === null). | apps/photoshop/src/panels/sections/ValidateSection.tsx:16-20 | pending |
| PS-AUX-07 | Validate: no-document message (preview.kind === 'no-document') | Body shows the planner's first error string, or 'No document open.' when none provided. | UNDOCUMENTED; shows preview.errors[0] or fallback 'No document open.' | apps/photoshop/src/panels/sections/ValidateSection.tsx:23-30 | pending |
| PS-AUX-08 | Validate: 'No issues. Manifest looks ready to export.' clean label | Badge='ok'; body shows 'No issues. Manifest looks ready to export.' | UNDOCUMENTED; clean-state confirmation when warnings+skipped+valErrors == 0. | apps/photoshop/src/panels/sections/ValidateSection.tsx:43-44 | pending |
| PS-AUX-09 | Validate: 'Manifest invalid:' error block + per-error rows | Red 'result error' block titled 'Manifest invalid:' with one row per error string from preview.errors. | Reflects index.md's 'manifest is validated before it is written, so a broken manifest never reaches disk' — surfaces ajv validation errors here. | apps/photoshop/src/panels/sections/ValidateSection.tsx:47-54 | pending |
| PS-AUX-10 | Validate: 'Warnings (N)' subgroup header | Subgroup titled 'Warnings (N)' renders with one WarningRow per warning. | Lists the planner-emitted warnings; count in title. | apps/photoshop/src/panels/sections/ValidateSection.tsx:55-61 | pending |
| PS-AUX-12 | Validate: 'Skipped (N)' subgroup header | Subgroup titled 'Skipped (N)' with one SkippedRow per skipped layer. | Lists skipped layers (e.g. hidden / [ignore]); count in title. | apps/photoshop/src/panels/sections/ValidateSection.tsx:62-68 | pending |
| PS-AUX-14 | Preview (Debug) accordion header + entry-count badge | Badge shows manifest layer count when >0, otherwise no badge; header toggles; tooltip as above. | UNDOCUMENTED panel; hint 'Dry-run of the export. Manifest entries listed below; warnings + skipped layers live in the Proscenio Validate panel.' | apps/photoshop/src/panels/sections/DebugSection.tsx:19-23 | pending |
| PS-AUX-15 | Preview: pre-run empty state ('Click Refresh to dry-run the export. Nothing is written.') | Muted text 'Click Refresh to dry-run the export. Nothing is written.' plus a Refresh button. | UNDOCUMENTED; placeholder shown when preview === null. | apps/photoshop/src/panels/sections/DebugSection.tsx:24-30 | pending |
| PS-AUX-17 | Preview: no-document body + Refresh | Muted error text (first error or fallback) and a Refresh button. | UNDOCUMENTED; shows preview.errors[0] or 'No document open.' plus a Refresh button. | apps/photoshop/src/panels/sections/DebugSection.tsx:43-51 | pending |
| PS-AUX-18 | Preview: anchor row (read-only) | Row 'anchor' shows '(canvas centre)' when manifest.anchor==null, else '<x>, <y> px' (mono). | UNDOCUMENTED; shows manifest anchor or '(canvas centre)' when null. | apps/photoshop/src/panels/sections/DebugSection.tsx:57-62 | pending |
| PS-AUX-19 | Preview: entries / skipped / warnings count rows (read-only) | Rows 'entries', 'skipped', 'warnings' show counts matching manifest.layers.length, skipped.length, warnings.length respectively. | UNDOCUMENTED; numeric summary of the dry-run plan. | apps/photoshop/src/panels/sections/DebugSection.tsx:63-65 | pending |
| PS-AUX-20 | Preview: polygon entry row | Row shows kind, name, path, and optional badges '(folder=..., blend=..., origin=x,y)' when those fields are set. | Reflects index.md 'one PNG per layer plus a manifest JSON' — lists each polygon manifest entry (kind, name, path, badges). | apps/photoshop/src/panels/sections/DebugSection.tsx:100-108,111-117 | pending |
| PS-AUX-21 | Preview: sprite entry row | Row shows 'sprite', the name, and '<N> frames' plus any badges. | Reflects index.md spritesheet behaviour — shows 'sprite' + name + 'N frames' for a sprite_frame group. | apps/photoshop/src/panels/sections/DebugSection.tsx:90-98 | pending |
| PS-AUX-22 | Preview: active-layer row highlight (selected styling) | The matching entry row gains the 'selected' class (highlighted). Selecting a non-matching/no/multiple layers leaves no row highlighted. | UNDOCUMENTED; the entry whose EntryRef matches the artist's currently selected PS layer is highlighted. | apps/photoshop/src/panels/sections/DebugSection.tsx:69-73,80-86 (match useActiveLayerPath + entryMatchesPath) | pending |
| PS-AUX-23 | Legacy migration accordion header + count badge + hint | Section appears with badge = candidate count; defaultOpen when count>0; tooltip as above. Hidden entirely when preview.noDocument, or when count==0 and no prior result. | Reflects index.md tag vocabulary (legacy convention -> [ignore]); hint 'Convert legacy `_layerName` skip conventions to the [ignore] tag.' | apps/photoshop/src/panels/sections/MigrationSection.tsx:20-25 | pending |
| PS-AUX-24 | Legacy migration: 'No underscore-prefixed layers found.' label | Muted text 'No underscore-prefixed layers found.' shown above the result view. | UNDOCUMENTED; empty-state when count==0 but a lastResult exists (post-conversion). | apps/photoshop/src/panels/sections/MigrationSection.tsx:26-28 | pending |
| PS-AUX-25 | Legacy migration: 'N layer(s) ready to rename' + candidate rows (max 6 + 'and N more') | '8 layer(s) ready to rename:' then 6 CandidateRows then '...and 2 more.' | Previews the planned _name -> [ignore] renames before applying. | apps/photoshop/src/panels/sections/MigrationSection.tsx:30-36 | pending |
| PS-AUX-28 | Legacy migration: result view ('Renamed N layer(s)' + per-failure rows) | 'Renamed N layer(s).' on full success; on failures the block gets 'result error' class, '..., M failed:' and one warn row per failure ('<path>: <reason>'). | UNDOCUMENTED; reports renamed count and any per-candidate failures after applying. | apps/photoshop/src/panels/sections/MigrationSection.tsx:74-87 | pending |

#### [ ] PS-AUX-04 · Active document: Refresh button
- **Intent:** UNDOCUMENTED; re-reads the active document header into the panel.
- **Code:** apps/photoshop/src/panels/sections/DocSection.tsx:22 (handler ProscenioValidatePanel.tsx:37 / ProscenioDebugPanel.tsx:43 -> useDocSnapshot.refresh)
- **Pre:** Validate or Debug panel open.
- **Steps:** 1. Change the active document (rename / resize canvas / switch tabs). 2. Click 'Refresh'.
- **Expect:** name + canvas rows update synchronously to the now-active document (readDocSnapshot via app.activeDocument). No file is written.
- **Status:** pending

#### [ ] PS-AUX-11 · Validate: Warning row (click-to-select offending layer)
- **Intent:** Each row selects the offending PS layer; hint says 'Click any row to jump to the offending layer in Photoshop.'
- **Code:** apps/photoshop/src/panels/sections/ValidateSection.tsx:82-95 (handler useLayerSelection -> ps-selection.selectLayerByPath:61)
- **Pre:** At least one warning present.
- **Steps:** 1. Click a warning row (or focus it and press Enter/Space). 2. Watch the PS Layers panel.
- **Expect:** Row shows code + bold name + message. Clicking runs batchPlay 'select' on the layer matched by warning.layerPath; that layer becomes the active selection in PS. Keyboard Enter/Space also activates.
- **Status:** pending

#### [ ] PS-AUX-13 · Validate: Skipped row (click-to-select skipped layer)
- **Intent:** Row selects the skipped PS layer; shows the skip reason as the code and the layer name.
- **Code:** apps/photoshop/src/panels/sections/ValidateSection.tsx:97-107 (handler useLayerSelection -> selectLayerByPath:61)
- **Pre:** At least one skipped layer present.
- **Steps:** 1. Click a skipped row (or Enter/Space when focused). 2. Watch the PS Layers panel.
- **Expect:** Row shows skip reason code + layer name; clicking selects that layer (by its layerPath) in PS via batchPlay.
- **Status:** pending

#### [ ] PS-AUX-16 · Preview: Refresh button (dry-run)
- **Intent:** Runs a dry-run preview of the export; per index.md the recursive walk produces manifest + PNGs, but Refresh writes nothing (dry-run).
- **Code:** apps/photoshop/src/panels/sections/DebugSection.tsx:29,49,66 (handler ProscenioDebugPanel.onRefresh:31 -> useExportPreview.refresh -> previewExport)
- **Pre:** Debug panel open, document open.
- **Steps:** 1. Edit the PSD layers. 2. Click 'Refresh'.
- **Expect:** anchor/entries/skipped/warnings rows and the entries list recompute from previewExport(opts) with skipHidden:true. No file is written to disk.
- **Status:** pending

#### [ ] PS-AUX-26 · Legacy migration: candidate row (click-to-select layer)
- **Intent:** UNDOCUMENTED; clicking a candidate selects that layer in PS (shows old -> new name).
- **Code:** apps/photoshop/src/panels/sections/MigrationSection.tsx:47-72 (handler useLayerSelection -> selectLayerByPath:61)
- **Pre:** Candidate rows visible.
- **Steps:** 1. Click a candidate row (or Enter/Space when focused). 2. Watch PS Layers panel.
- **Expect:** Row shows oldName -> newName; clicking selects the layer at candidate.layerPath in PS via batchPlay.
- **Status:** pending

#### [ ] PS-AUX-27 · Legacy migration: 'Convert N layer(s) to [ignore]' button
- **Intent:** Applies the batch rename, converting _name layers to [ignore]; reflects index.md tag conventions.
- **Code:** apps/photoshop/src/panels/sections/MigrationSection.tsx:37-39 (handler useMigration.apply -> applyUnderscoreMigration -> executeAsModal:57)
- **Pre:** Doc with >=1 underscore-prefixed candidate.
- **Steps:** 1. Click 'Convert N layer(s) to [ignore]'. 2. Watch the button + PS layer names.
- **Expect:** Button label switches to 'Renaming...' and disables (busy=true). Inside one executeAsModal, candidates are renamed deepest-first to their [ignore] newName (single undo step). On finish: result view appears, preview re-reads (candidates -> 0), button re-enables.
- **Status:** pending

## Findings

| ID | Type | Sev | Control | Detail | Code |
| --- | --- | --- | --- | --- | --- |
| F-01 | suspected-bug | high | Export manifest + PNGs / PNG write | runWrites calls writeLayerPng with NO try/catch; any UXP rejection inside (documents.add, layer.duplicate, merge, trim, saveAs.png) propagates out, rejects core.executeAsModal, and the outer catch returns kind 'failed' with the manifest NEVER written. A single problematic layer makes the entire manifest export impossible — matches the reported failure. | apps/photoshop/src/api/png-writer.ts:29-43 (runWrites loop) and 46-77 (writeLayerPng, no catch); export-flow.ts:118-155 |
| F-02 | suspected-bug | high | Export manifest + PNGs / atomicity gate | Manifest is written only if results.every(r=>r.ok). If even ONE layer fails to resolve (findLayerByPath===null because the layer was renamed/deleted/reordered after the preview was built), that write returns ok:false, allOk=false, and the manifest is suppressed for the WHOLE document — the user cannot export the manifest at all until they fix that one layer. layerPath uses raw bracketed names matched byte-exactly, so any rename mid-session breaks the match. | apps/photoshop/src/api/export-flow.ts:120-137; png-writer.ts:30-38; _layer-find.ts:22-31 |
| F-03 | suspected-bug | medium | Run export / folder permission | writeManifest awaits folder.createFile(fileName,{overwrite:true}) and file.write inside the modal. If the persisted folder token is stale (folder moved/permission revoked) the createFile/write rejects, the modal rejects, and the user gets a generic kind 'failed' with the raw Error.message rather than a 'pick the folder again' affordance. restoreFolder only guards the mount-time resolve, not a later write. | apps/photoshop/src/api/manifest-writer.ts:14-18; folder-storage.ts:17-29; export-flow.ts:122,149-155 |
| F-04 | suspected-bug | medium | Export button enable / no-document race | Export is gated on the doc SNAPSHOT (useDocSnapshot, refreshed on demand) but runExport reads app.activeDocument live. If the user closes the document after the snapshot was taken, the button stays enabled yet runExport hits doc===null and returns 'no-document'. The two sources of truth can disagree. | apps/photoshop/src/panels/ProscenioExporter.tsx:65; hooks/useDocSnapshot.ts:20-23; export-flow.ts:94-98 |
| F-05 | suspected-bug | low | manifest validation gate (ajv) vs filename template | A filename template that drops {name} (e.g. 'out.png') collapses every mesh to the same output path. The planner emits only a duplicate-path WARNING (non-blocking) and createFile uses overwrite:true, so all but one PNG are silently overwritten; the manifest still validates and is written. Silent data loss with no export-time hard stop. | apps/photoshop/src/lib/planner.ts:215-249 (duplicate-path is warning only); png-writer.ts:91 createFile overwrite:true |
| F-06 | drift | low | manifest writer / validator comments | manifest-writer.ts and manifest-validator.ts comments say 'v2 manifest' / 'v2 PSD manifest', but the schema and planner emit format_version const 1 (MANIFEST_FORMAT_VERSION = 1; schema 'format_version' const 1). Comment/version label drift; could mislead a reader debugging a version mismatch. | apps/photoshop/src/api/manifest-writer.ts:1-2; manifest-validator.ts:5; lib/manifest.ts:17; schema:279-282 |
| F-07 | drift | low | manifest schema description | Schema description says 'Root of a PSD manifest v1 document' yet its $id and title are generic; manifest.ts re-export comment names it ProscenioPSDManifest. Minor inconsistency but the schema 'additionalProperties:false' at root means any future stray underscore field surviving toManifestEntry would hard-fail validation — worth noting as a fragility for the export path. | packages/models/schemas/psd_manifest.schema.json:251-252; lib/planner.ts:737-762 (toManifestEntry strips _source/_frameSources) |
| F-08 | dead | medium | RevealOutput (Selected entry) section | The audit scopes RevealOutputSection as part of the Exporter surface, but ProscenioExporter.tsx does NOT render it — it is only mounted in ProscenioTagsPanel.tsx. On the Exporter panel there is no reveal-output/selected-entry detail surface at all; the section and its resolved-PNG-path display are unreachable from the exporter. | apps/photoshop/src/panels/ProscenioExporter.tsx:75-121 (no RevealOutputSection); ProscenioTagsPanel.tsx:16,74-78 |
| F-09 | undocumented | medium | Pixels per unit field / canvas row / Reset | The PPU control, its canvas-units readout, and its reset button are not mentioned anywhere on the doc index page (docs/03-photoshop-plugin/index.md); only an in-UI hint describes them. Their effect on the manifest (pixels_per_unit) and downstream Blender/Godot scaling is undocumented at this surface. | apps/photoshop/src/panels/sections/ExportSection.tsx:86-107 |
| F-10 | undocumented | low | Filename templates (mesh/sprite) + Reset | Filename template fields and the reset button are not described on the doc index page; only the [folder:...]/[path:...]/{name}/{kind}/{index} mechanics are hinted in-UI and in the advanced guide, not here. | apps/photoshop/src/panels/sections/ExportSection.tsx:108-130 |
| F-11 | undocumented | low | Re-export selected section | Single-layer re-export (PNG-only, manifest untouched) is not mentioned on the doc index page; the doc only describes full export and mirror-back-to-PSD. | apps/photoshop/src/panels/sections/ReexportSection.tsx:25-72 |
| F-12 | undocumented | low | Forget folder button + folder persistence | The 'Forget' action that clears the remembered folder token is undocumented; doc only says the path persists across reloads, not how to clear it. | apps/photoshop/src/panels/sections/FolderSection.tsx:28; api/folder-storage.ts:42-44 |
| F-13 | suspected-bug | low | Re-export selected / executeAsModal | runSingleLayerExport wraps runWrites in executeAsModal but, like the full export, writeLayerPng inside has no per-layer try/catch — a UXP rejection rejects the modal and surfaces as a generic 'failed' with raw Error.message instead of the structured per-PNG 'outputPath: reason' the ok-path produces. | apps/photoshop/src/api/export-flow.ts:190-211; png-writer.ts:46-77 |
| F-14 | suspected-bug | medium | Side effect — pixels_per_unit seeding | import-flow calls persistPixelsPerUnit() (writes localStorage) but nothing updates the live usePixelsPerUnit React state, which only reads loadPixelsPerUnit() at mount; so the imported PPU does NOT reach the current session's Export input / re-export until the panel is reloaded, contradicting the comment 'so a re-export emits the imported scale'. | apps/photoshop/src/api/import-flow.ts:54-56; apps/photoshop/src/hooks/usePixelsPerUnit.ts:24 |
| F-15 | undocumented | low | Import section header / button label | Doc (docs/03-photoshop-plugin/index.md) only states the plugin 'can rebuild a PSD from a manifest'; it never documents the 'Import (manifest to PSD)' section, the 'Import manifest as PSD' button label, or the picker step. | apps/photoshop/src/panels/sections/ImportSection.tsx:15,20 |
| F-16 | undocumented | low | Stamped/skipped result + warnings + failure surfaces | The result body (stamped/skipped counts), per-entry warnings (missing PNG, bounds mismatch, empty sprite), and the 'Import failed.' error block are not described anywhere in the doc. | apps/photoshop/src/panels/sections/ImportSection.tsx:27-61 |
| F-17 | drift | low | Manifest validation claim | Doc says 'The manifest is validated before it is written, so a broken manifest never reaches disk' — that statement is about export. On the IMPORT path the manifest is read/validated but never written; the doc has no equivalent statement that the imported manifest is validated, while the code does validate it (parseManifest). Minor doc-vs-behavior gap in coverage. | apps/photoshop/src/api/manifest-reader.ts:43-46 |
| F-18 | suspected-bug | medium | placePngAt — app.open inside an active modal | placePngAt calls app.open(pngFile) for every entry while the whole batch already runs inside core.executeAsModal('Proscenio import'). Opening a document is itself a modal/UI operation; depending on host behavior this nested open per layer can be rejected or stall under the outer modal, and there is no per-entry try/catch around app.open — a single rejected open throws out of doImport and surfaces as a whole-import 'Import failed.' rather than a skip/warning. | apps/photoshop/src/api/png-placer.ts:28; apps/photoshop/src/api/import-flow.ts:31-33 |
| F-19 | suspected-bug | low | stampMesh / stampSprite — unguarded placePngAt rejection | stampEntry/stampMesh/stampSprite handle a null layer result but do not catch a rejected placePngAt promise (e.g. duplicate/translate throwing). A throw from any single entry aborts the entire for-loop and the modal, losing all prior stamping progress and yielding a generic failure instead of a per-entry warning. | apps/photoshop/src/api/import-flow.ts:62-66,99-111,134-145 |
| F-20 | suspected-bug | low | Import button — overlapping invocations | The action button is only disabled (busy) AFTER the file picker resolves and runImport starts; during the pre-busy picker/validation window the button is still enabled, so a second click could open a second picker / start a concurrent run before busy is set. | apps/photoshop/src/hooks/useImportFlow.ts:22-31; apps/photoshop/src/panels/sections/ImportSection.tsx:19 |
| F-21 | suspected-bug | low | resolveRelativeFile — path segment assumptions | PNG resolution splits entry.path on '/' and walks getEntry per segment; any backslash-separated or absolute path in the manifest, or a folder name collision, resolves to null and the entry is silently skipped with only a warning. No normalization of OS path separators. | apps/photoshop/src/api/import-flow.ts:156-178 |
| F-22 | undocumented | low | Sprite frame z-order within group | stampSprite places frames in manifest array order and moves each to PLACEATEND; only top-level entries are sorted by z_order (import-flow:58), frames inside a sprite group are not z-sorted. Behavior is undocumented; verify intended frame stacking. | apps/photoshop/src/api/import-flow.ts:128-147; apps/photoshop/src/api/png-placer.ts:83-85 |
| F-23 | suspected-bug | high | Kind dropdown / writer on a [spritesheet] group | Parser maps [spritesheet] -> kind:'sprite', but the writer's kindSegment only emits [mesh] or [sprite]. Selecting any kind (or any edit that rewrites the name) on a group originally tagged [spritesheet] silently rewrites it to [sprite], losing the group-frames semantics; the dropdown is also not disabled for groups even though the doc says [sprite] is a layer-only tag. | apps/photoshop/src/lib/tag-writer.ts:73-80; apps/photoshop/src/lib/tag-parser.ts:117-119; apps/photoshop/src/panels/sections/tags/Row.tsx:157-168 |
| F-24 | suspected-bug | high | Row name select / rename (findLayerByPath) | findLayerByPath matches layers by raw name and takes the first match (break). Two sibling layers/groups with identical names route every select and every tag edit to the first one, silently mis-editing the second; tag edits on the duplicate are lost or applied to the wrong layer. | apps/photoshop/src/api/_layer-find.ts:22-24 |
| F-25 | drift | medium | Advanced: scale field | Doc says a sub-pixel [scale:N] result 'raises a validation warning', but the panel surfaces no warning; the form only gates >0 finite and silently skips invalid input. The sub-pixel warning lives (if anywhere) in the exporter, not this surface. | apps/photoshop/src/lib/tag-form.ts:76-81; apps/photoshop/src/lib/tag-parser.ts:55-60 |
| F-26 | drift | low | Blend dropdown | Doc lists 'normal' as a valid [blend] value, but the dropdown offers only none/mult/scrn/add. 'normal' is intentionally collapsed to 'none' and never written, so a documented mode is unreachable from the UI (minor; normal is the default). | apps/photoshop/src/panels/sections/tags/Row.tsx:169-181,285-294; apps/photoshop/src/lib/tag-writer.ts:55-56 |
| F-27 | undocumented | medium | Tags panel / accordion / row UI (whole surface) | The advanced guide documents the bracket-tag vocabulary and export semantics but never the Tags panel itself - no mention of the layer tree, the X/M glyph toggles, kind/blend dropdowns, the '+' advanced expander, badges, 'From selection', or Apply/Revert. The entire interactive surface is undocumented. | apps/photoshop/src/panels/sections/TagsSection.tsx:21-58; apps/photoshop/src/panels/sections/tags/Row.tsx:118-200 |
| F-28 | dead | low | Advanced: 'From selection' silent no-op | When there is no marquee selection (or zero-area bounds), readSelectionCenter returns null and the handler only logs a debug warning - the button appears to do nothing with no user-visible feedback, looking dead to the artist. | apps/photoshop/src/panels/sections/tags/Details.tsx:84-96; apps/photoshop/src/api/ps-selection-bounds.ts:24-26 |
| F-29 | suspected-bug | low | Advanced fields invalid-input silent skip | Invalid path/scale/origin/name-pattern values are returned as SKIP and dropped with no error surfaced; the form still shows the typed (rejected) value while the layer name is unchanged, so the artist believes the edit applied when it did not. | apps/photoshop/src/lib/tag-form.ts:69-99,101-112 |
| F-30 | suspected-bug | low | TagDetails draft reset on external rename | The form resets only when node.rawName changes (lastRawName ref). If an external edit changes the tags but produces the same rawName, or the rename round-trips to an identical name, the open draft is not re-synced to on-disk truth, so a stale baseline can be applied. | apps/photoshop/src/panels/sections/tags/Details.tsx:30-37 |
| F-31 | undocumented | low | Active document section (DocSection) | index.md never mentions a document-header section showing name/canvas; entirely undocumented across Validate/Debug/Exporter panels. | apps/photoshop/src/panels/sections/DocSection.tsx:12-24 |
| F-32 | undocumented | medium | Validate panel / section | index.md only says 'manifest is validated before it is written'; the standalone Validate panel listing planner warnings + skipped layers with click-to-select is undocumented. | apps/photoshop/src/panels/sections/ValidateSection.tsx:15-72 |
| F-33 | undocumented | medium | Preview / Debug panel / section | The dry-run Preview panel (anchor, counts, entries list, active-layer highlight, Refresh) is entirely absent from index.md. | apps/photoshop/src/panels/sections/DebugSection.tsx:16-117 |
| F-34 | undocumented | low | Legacy migration result view + click-to-select candidate rows | The result summary and the per-candidate click-to-reveal behaviour are not described in index.md (only the bracket-tag concept is). | apps/photoshop/src/panels/sections/MigrationSection.tsx:47-87 |
| F-35 | suspected-bug | medium | Legacy migration preview / apply (no-document guard) | previewUnderscoreMigration/applyUnderscoreMigration guard with `app.activeDocument === null`, but PS UXP returns `undefined` when no doc is open; an undefined doc would slip past the null check and then `adaptDocument(undefined)` / `findLayerByPath(undefined,...)` would throw. Same `=== null` assumption is repeated across active-document.ts and ps-selection.ts. | apps/photoshop/src/api/legacy-migration.ts:31,42 |
| F-36 | suspected-bug | low | Legacy migration: candidate name-path matching during apply | applyUnderscoreMigration matches candidates by name path, not layer ID (documented as acceptable), but if two siblings share the same name, findLayerByPath resolves the first match and the second candidate may rename the wrong layer or report 'layer not found' after the first rename — silent mis-rename rather than a surfaced failure. | apps/photoshop/src/api/legacy-migration.ts:60-67 |
| F-37 | suspected-bug | low | Preview Refresh (Validate/Debug panels) — preview not awaited | previewExport is synchronous and runs inside a React effect on every document-change version bump and opts change; on a large PSD this blocks the UXP UI thread per bump (debounced 150ms) with no loading state, so rapid edits can make the panel feel frozen. No await/yield boundary. | apps/photoshop/src/hooks/useExportPreview.ts:20-34; apps/photoshop/src/panels/ProscenioValidatePanel.tsx:29-33 |
| F-38 | dead | low | Validate panel — no Refresh control | Unlike the Debug section, the Validate section exposes no manual Refresh; it relies solely on the useDocumentChanges event/version effect. On UXP builds where addNotificationListener returns void (no events fire — see ps-notifications.ts), the Validate list can go stale with no user-reachable way to force a re-plan (Debug has Refresh, Validate does not). The Doc Refresh button does NOT re-run the preview. | apps/photoshop/src/panels/ProscenioValidatePanel.tsx:35-40; apps/photoshop/src/api/ps-notifications.ts:60-63 |
| F-39 | drift | low | Doc section Refresh button | Refresh only re-reads the document header (useDocSnapshot); it does not refresh the Validate/Debug preview, so a user expecting 'Refresh' to update the whole panel will see stale warnings/entries after editing layers without a notification event. | apps/photoshop/src/panels/sections/DocSection.tsx:22; apps/photoshop/src/panels/ProscenioValidatePanel.tsx:37 |
| F-40 | suspected-bug | low | Legacy migration apply — concurrent re-entry | useMigration.apply has no guard against being invoked while busy beyond disabling the button visually; the disabled attribute is `busy ? true : undefined` and the section can re-render, but apply() itself has no in-flight lock, so a programmatic/double-fire could start a second executeAsModal that PS would reject (surfaced as a generic 'migration threw exception' failure). | apps/photoshop/src/hooks/useMigration.ts:37-58; apps/photoshop/src/panels/sections/MigrationSection.tsx:37 |
