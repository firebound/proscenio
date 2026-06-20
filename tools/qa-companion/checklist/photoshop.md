# Photoshop plugin - manual-test checklist

Maintained by the QA Companion tool (tools/qa-companion): one block per item. `status` / `note` / `shots` are the recorded walk; `review` is your verdict on the test itself (keep / rephrase / drop / todo). Edit here or via the tool.

This file is layered and grouped by subpanel: (1) global chrome tested once across every accordion (PS-CHROME-01); (2) within each `## <panel>` group, items are ordered by subpanel/sub-area in UI order - each sub-area's inventory sweep first (confirm every control is present in one visual pass), then its standalone behavioral tests. Existence-only controls whose behavior lives in an end-to-end flow are covered in flows.md, not duplicated here.

## Global chrome (test once)

### PS-CHROME-01 · Accordion section behaves the same everywhere
- status: pending
- review: keep
- steps:
  1. Pick any one collapsible section header in the panel.
  2. Click the header, then collapse it and reopen it with Enter, then with the Space bar.
  3. Hover the header and wait for the tooltip.
  4. Glance at the little count badge on a few different section headers.
- observe: The chevron flips between down and right and the body shows or hides on each click, on Enter, and on Space (Space does not also scroll the page). Hovering shows the section's hint text as a tooltip. A section's badge shows a number when there is a count, shows "ok" when the validate total is zero, and shows nothing when there is nothing to count. Sections with no data show a muted "empty" style label.
- intent: The collapse/expand behavior, keyboard access, hint tooltip, and badge/empty-state rules are shared by every section, so they are checked once instead of per section.
- code: apps/photoshop/src/components/Accordion.tsx:33-60
- note: absorbs PS-EXPORT-04, PS-EXPORT-06, PS-EXPORT-13, PS-EXPORT-18, PS-IMPORT-01, PS-IMPORT-02, PS-IMPORT-03, PS-TAGS-01, PS-TAGS-03, PS-TAGS-04, PS-AUX-01, PS-AUX-05, PS-AUX-14, PS-AUX-23 (accordion headers, hint tooltips, keyboard toggle, badge rules, empty-state labels across all panels).

## Exporter panel

### PS-EXPORT-SWEEP · Exporter panel inventory (visual pass)
- status: pending
- review: keep
- observe: From top to bottom the Exporter panel shows: an Output-folder card with the picked folder's path (also its hover tooltip), or "No folder picked." when none is chosen; an Export options area with a "Skip hidden layers" checkbox (checked by default); a "Pixels per unit" text field with a read-only canvas line reading "NNpx = NN.NN units" (hidden when there is no document height or the value is not positive) and a "Reset to {default}" button; a "Filename templates" area (collapsed by default) with a mesh template field, a sprite (frames) template field, and a "Reset to defaults" button; and a "Run export" area with an "Export manifest + PNGs" button. After a run, success shows "Wrote N entry(ies) to <file>" with a warning row per problem PNG, and failure shows "Export <kind>." with a list of errors.
- intent: Confirm every Exporter-panel field, button, read-only line, and result message is present and labeled.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:78-164; apps/photoshop/src/panels/sections/FolderSection.tsx:17-23
- note: absorbs PS-EXPORT-01, PS-EXPORT-08, PS-EXPORT-16, PS-EXPORT-17; behavior -> FLOW-DOLL-01.

### PS-EXPORT-OPTIONS-01 · Skip hidden layers checkbox
- status: pending
- review: keep
- steps:
  1. Hide a layer in Photoshop, leave "Skip hidden layers" checked, and run a Preview/export.
  2. Uncheck "Skip hidden layers" and run again.
- observe: With the box checked (the default), the hidden layer is left out of the export. With it unchecked, the hidden layer is included.
- intent: The "Skip hidden layers" toggle decides whether hidden layers are exported, so a tester can keep work-in-progress layers out of the output.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:82-84 -> onSkipHidden -> useExportFlow.setOption('skipHidden')

### PS-EXPORT-OPTIONS-02 · Pixels per unit field
- status: pending
- review: keep
- steps:
  1. Type a positive number into "Pixels per unit".
  2. Type a zero, a negative number, then letters.
  3. Reopen the panel.
- observe: A valid positive number sticks (it is still there after reopening the panel) and the read-only canvas line recomputes its "units" figure. Zero, negative, or non-numeric input is ignored and the field keeps its last good value.
- intent: Pixels per unit is the scale used when the art reaches Blender/Godot, so the field must accept only sensible positive values and remember them.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:91-95 -> onPpuInput -> usePixelsPerUnit.setPixelsPerUnit

### PS-EXPORT-OPTIONS-03 · Reset pixels per unit button
- status: pending
- review: keep
- steps:
  1. Change "Pixels per unit" away from 100.
  2. Click the "Reset to {default}" button next to it.
- observe: The value returns to 100 and stays there after reopening the panel. The button is greyed out whenever the value already equals 100.
- intent: The reset button restores the default pixels-per-unit (100) in one click and is unavailable when there is nothing to reset.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:104-106 -> onPpuReset -> usePixelsPerUnit (DEFAULT 100)

### PS-EXPORT-TEMPLATES-01 · Mesh filename template field
- status: pending
- review: keep
- steps:
  1. Open "Filename templates" and edit the mesh template (it uses {name} and {kind}).
  2. Clear the field to empty, then reopen the panel.
  3. Run a Preview and look at the mesh PNG paths.
- observe: The template sticks after reopening the panel. Clearing it to empty falls back to "{name}.png". The mesh PNG paths under images/ follow whatever template you set.
- intent: The mesh filename template controls how mesh PNGs are named, with an automatic images/ prefix and any [folder:...] subfolder.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:113-118 -> onPolygonInput -> useFilenameTemplate.setPolygonTemplate; consumed planner.ts:641

### PS-EXPORT-TEMPLATES-02 · Sprite (frames) filename template field
- status: pending
- review: keep
- steps:
  1. Edit the sprite (frames) template (it uses {name} and {index}).
  2. Clear it to empty, then reopen the panel.
  3. Run a Preview and look at the sprite frame paths.
- observe: The template sticks after reopening. Clearing it falls back to "{name}/{index}.png". The sprite frame PNG paths follow whatever template you set.
- intent: The frames filename template controls how individual sprite frames are named, with an automatic images/ prefix and subfolder.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:120-125 -> onFramesInput -> setFramesTemplate; consumed planner.ts:500/675

### PS-EXPORT-TEMPLATES-03 · Reset filename templates button
- status: pending
- review: keep
- steps:
  1. Change either filename template away from its default.
  2. Click "Reset to defaults".
- observe: Both templates go back to "{name}.png" and "{name}/{index}.png". The button is greyed out when both templates already match their defaults.
- intent: The reset button restores both filename templates at once and is unavailable when there is nothing to reset.
- code: apps/photoshop/src/panels/sections/ExportSection.tsx:127-129 -> onResetTemplates -> useFilenameTemplate.reset

### PS-EXPORT-RUN-01 · Export button stays disabled until ready
- status: pending
- review: keep
- steps:
  1. With no folder picked, look at the "Export manifest + PNGs" button.
  2. Pick a folder but have no document open.
  3. Open a document with a folder picked.
- observe: The Export button is greyed out while an export is running, while no folder is picked, or while no document is open. It is clickable only once a folder and a document are both present.
- intent: Export is unavailable until its prerequisites (a folder and an open document) are in place.
- code: apps/photoshop/src/panels/ProscenioExporter.tsx:65 exportDisabled; ExportSection.tsx:132 disabled

### PS-EXPORT-RUN-02 · Exporting an empty document
- status: pending
- review: keep
- steps:
  1. Open a document with no exportable layers and run the export.
- observe: The export succeeds, the result reads "Wrote 0 entry(ies)", a manifest file is written with an empty layer list, and no PNGs are created.
- intent: Exporting a document with nothing to export writes a valid empty manifest instead of failing.
- code: apps/photoshop/src/lib/planner.ts:133-148 (layers: []) ; schema layers has no minItems

### PS-EXPORT-RUN-03 · A broken manifest is blocked before it is written
- status: pending
- review: keep
- pre: A document whose export would produce an invalid manifest (for example a zero or negative size, or a layer name that ends up empty with no fallback).
- steps:
  1. Export a document crafted to break a manifest rule (for example a negative or zero coordinate) and read the result.
- observe: The export fails with a "validation failed" result and a list of errors, and no files are written to the folder.
- intent: The manifest is checked against its schema before anything is saved, so a broken manifest never reaches disk.
- code: apps/photoshop/src/api/export-flow.ts:107-111 validateManifest -> api/manifest-validator.ts:28; schema packages/models/schemas/psd_manifest.schema.json

### PS-EXPORT-RUN-04 · Manifest is saved only if every PNG was written
- status: pending
- review: keep
- pre: A folder is picked and the export is set up so at least one PNG fails to write (for example a layer renamed after Preview).
- steps:
  1. Run an export where one PNG write fails, then look in the folder.
- observe: No manifest JSON is written and the result is a failure that lists the failing "outputPath: reason". PNGs that already succeeded may still be sitting in the folder (a partial write).
- intent: The manifest is saved only when every PNG landed, so it never points at files that are missing.
- code: apps/photoshop/src/api/export-flow.ts:118-126 (executeAsModal) -> api/manifest-writer.ts:9 writeManifest

### PS-EXPORT-RUN-05 · One trimmed PNG per layer
- status: pending
- review: keep
- pre: An export is running and the layers can still be found by their path.
- steps:
  1. Export a multi-layer document, then check that images/*.png exists and that each PNG matches its layer's trimmed bounds.
- observe: One PNG appears at folder/<outputPath> for each layer, trimmed to the layer's visible pixels. A layer whose path can no longer be found produces a failure reading "source layer not found".
- intent: Each layer is exported as its own trimmed PNG into the target folder.
- code: apps/photoshop/src/api/png-writer.ts:23-77 runWrites/writeLayerPng

## Re-export sub-panel

### PS-REEXPORT-SWEEP · Re-export sub-panel inventory (visual pass)
- status: pending
- review: keep
- observe: When the active Photoshop layer matches a manifest entry, the sub-panel shows an "entry" row (the entry name in monospace) and a "kind" row. When nothing matches, it shows "Select a layer in Photoshop that maps to a manifest entry." It always shows a "Re-export this entry's PNG" button. After a run it shows either "Wrote N PNG(s)." on success, or "Re-export <kind>." with a list of errors (for example "not-found" or a per-PNG failure).
- intent: Confirm the re-export sub-panel's detail rows, placeholder, button, and result messages are present.
- code: apps/photoshop/src/panels/sections/ReexportSection.tsx:49-108
- note: absorbs PS-EXPORT-19, PS-EXPORT-22; behavior -> GAP-1 (single-layer re-export; see PS-REEXPORT-02).

### PS-REEXPORT-01 · Re-export button stays disabled until ready
- status: pending
- review: keep
- steps:
  1. With no folder picked and/or no matching layer selected, look at the "Re-export this entry's PNG" button.
  2. Pick a folder and select a layer that matches a manifest entry.
- observe: The button is greyed out while an export is running, while no layer matches an entry, or while no folder is picked. It is clickable only when both a matching entry and a folder are present.
- intent: Re-export is unavailable until there is a matched entry and a folder to write into.
- code: apps/photoshop/src/panels/sections/ReexportSection.tsx:65 (disabled = busy || matched===null || folder===null)

### PS-REEXPORT-02 · Re-export this entry's PNG
- status: pending
- review: keep
- pre: A folder is picked and the active Photoshop layer matches a manifest entry.
- steps:
  1. Pick a folder, select a matching layer, and click "Re-export this entry's PNG".
- observe: The button reads "Re-exporting..." during the run, then "Wrote N PNG(s)." on success. Only that one entry's PNG file(s) are rewritten on disk, and the existing manifest JSON is left completely unchanged.
- intent: Re-exporting rewrites only the selected layer's PNG(s) and leaves the manifest untouched.
- code: apps/photoshop/src/panels/sections/ReexportSection.tsx:59-68 onReexport -> api/export-flow.ts:167 runSingleLayerExport
- note: no owning flow yet - candidate flow GAP-1 (single-layer re-export partial-write path is the plugin's own write path, not covered by any existing flow).

## Import section

### PS-IMPORT-SWEEP · Import sub-panel inventory (visual pass)
- status: pending
- review: keep
- observe: The Import sub-panel shows an "Import manifest as PSD" button; during a run its label switches to "Importing..." and it is disabled, then reverts when done. A successful result reads "Stamped N entry(ies)", adds " (M skipped)" only when something was skipped, then "Use File > Save As to commit the PSD." Per-entry warning rows appear in yellow (for example "mesh <name>: missing PNG at <path>", "<file> bounds WxH differ from manifest WxH; using PNG bounds.", "sprite <name>: zero frames placed; group removed"). A failed result appears in red as "Import failed." with one row per error.
- intent: Confirm the Import sub-panel's button, busy label, success body, warning rows, and error block are all present.
- code: apps/photoshop/src/panels/sections/ImportSection.tsx:19-52; apps/photoshop/src/api/import-flow.ts:34-73
- note: absorbs PS-IMPORT-08, PS-IMPORT-09, PS-IMPORT-10, PS-IMPORT-11; behavior -> GAP-2 (PSD rebuild from manifest; see PS-IMPORT-03).

### PS-IMPORT-01 · A broken manifest is rejected on import
- status: pending
- review: keep
- pre: The Import section is expanded.
- steps:
  1. Click Import and pick a .json file that is either malformed JSON or valid JSON that fails the manifest schema.
- observe: A "Manifest invalid." error block appears listing the problems (for example "(root) must have required property 'size'" or "manifest is not valid JSON: ..."). No document is created and the panel never enters the busy state.
- intent: The manifest is validated before use, so a broken manifest never builds a document.
- code: apps/photoshop/src/api/manifest-reader.ts:32-46; apps/photoshop/src/api/manifest-validator.ts:34-42; apps/photoshop/src/hooks/useImportFlow.ts:26-29

### PS-IMPORT-02 · Import fails clearly when the PNG folder cannot be found
- status: pending
- review: keep
- pre: The Import section is expanded.
- steps:
  1. Pick a schema-valid manifest whose surrounding folder cannot be located (no resolvable parent folder).
- observe: A "Manifest invalid." block shows the single error "could not resolve manifest's parent folder" and the import does not proceed.
- intent: Import stops with a clear message when it cannot find the folder that holds the sibling PNGs.
- code: apps/photoshop/src/api/manifest-reader.ts:47-53,60-75

### PS-IMPORT-03 · Rebuild a PSD from a manifest and its PNGs
- status: pending
- review: keep
- pre: A valid manifest is picked and its sibling PNGs sit next to it at the relative paths it declares.
- steps:
  1. Click Import, pick a valid manifest that has its PNGs on disk, and wait.
- observe: A single "Proscenio import" progress runs and a new transparent document (named after the manifest, sized to the manifest) opens with one layer per mesh entry and one group per sprite (its frames as layers named by index). Entries are stacked so the first one ends on top. The document stays open and unsaved, and the result reads "Stamped N entry(ies). Use File > Save As to commit the PSD."
- intent: Import rebuilds the PSD with placed mesh layers and sprite-frame groups and leaves it open and unsaved for the user to save.
- code: apps/photoshop/src/api/import-flow.ts:26-74; apps/photoshop/src/api/png-placer.ts:20-71
- note: no owning flow yet - candidate flow GAP-2. The PSD-import flows (FLOW-PSD-01/02) drive Blender's importer, not the PS plugin's import-flow.ts + png-placer.ts rebuild path.

### PS-IMPORT-04 · Import carries the manifest's pixels-per-unit into the exporter
- status: pending
- review: keep
- pre: A valid manifest whose pixels-per-unit differs from the current Export field value.
- steps:
  1. Import the manifest, then reload the panel and look at the Export section's "Pixels per unit" field.
- observe: After a panel reload, the Export "Pixels per unit" field shows the manifest's value. Note: the live Export field does not update during the same session - the imported value only appears after a panel reload.
- intent: Importing seeds the exporter's pixels-per-unit from the manifest so a re-export uses the same scale the art came in at.
- code: apps/photoshop/src/api/import-flow.ts:54-56; apps/photoshop/src/api/pixels-per-unit-store.ts:28-36

## Tags panel

### PS-TAGS-ROW-SWEEP · Tags row inventory (visual pass)
- status: pending
- review: keep
- observe: The Tags header badge equals the number of top-level layers. Each row shows the layer's display name (with tags stripped off, falling back to the raw name when the display name is empty), and the active layer's row is highlighted as "selected". A read-only strip of small badges shows the layer's tags: F (folder), P (path), S (scale), O (origin x,y), OM (origin marker, no value), NP (name pattern); a tag that is absent shows no badge, and each visible badge has a hover tooltip. A red warning row above the tree shows the last rename failure reason (for example "layer not found", "no active document"). Group rows have a disclosure triangle (down/right) that opens and closes their children; non-group rows show no triangle.
- intent: Confirm the Tags header badge and every read-only element on a row (name, badge strip, error row, disclosure triangle) are present.
- code: apps/photoshop/src/panels/sections/TagsSection.tsx:39-45; apps/photoshop/src/panels/sections/tags/Row.tsx:52-59; apps/photoshop/src/panels/sections/tags/Badges.tsx:19-38
- note: absorbs PS-TAGS-02, PS-TAGS-05, PS-TAGS-06, PS-TAGS-07, PS-TAGS-08.

### PS-TAGS-ROW-01 · Kind dropdown (auto / mesh / sprite)
- status: pending
- review: keep
- steps:
  1. On a row, set the Kind dropdown to mesh, then sprite, then auto.
  2. Watch the layer's name in Photoshop.
- observe: "mesh" puts "[mesh]" in the layer name, "sprite" puts "[sprite]" in it, and "auto" removes the kind tag. The Photoshop layer name updates each time.
- intent: The Kind dropdown tags a layer as a mesh (Polygon2D) or a sprite (Sprite2D), or clears the tag with auto.
- code: apps/photoshop/src/panels/sections/tags/Row.tsx:75-84,157-168
- note: finding - on a [spritesheet] group this rewrites it to [sprite].

### PS-TAGS-ROW-02 · Blend dropdown (none / multiply / screen / additive)
- status: pending
- review: keep
- steps:
  1. On a row, set the Blend dropdown to multiply, screen, additive, then none.
  2. Watch the layer's name.
- observe: multiply/screen/additive write "[blend:multiply]" / "[blend:screen]" / "[blend:additive]" into the layer name, and "none" removes the blend tag. A layer that already had "[blend:normal]" reads as "none" in the dropdown. The layer name updates each time.
- intent: The Blend dropdown records the layer's intended blend mode as a tag.
- code: apps/photoshop/src/panels/sections/tags/Row.tsx:86-95,169-181

### PS-TAGS-DETAILS-SWEEP · Tag details (advanced) inventory (visual pass)
- status: pending
- review: keep
- observe: A "+"/"-" expander at the far right of a row opens and closes the advanced Tag details box (the glyph flips to "-" when open). Inside the box are a folder field, a path field, a scale field, an origin X field, an origin Y field, an origin-marker checkbox, and a name-pattern field (shown on group rows only). Three buttons are present: "From selection", Apply, and Revert; Apply and Revert are greyed out while the form has no unsaved changes or while a write is running.
- intent: Confirm the advanced expander and every Tag details field and button are present and follow the enable-when-dirty rule.
- code: apps/photoshop/src/panels/sections/tags/Row.tsx:97-99,182-188; apps/photoshop/src/panels/sections/tags/Details.tsx:100-182
- note: absorbs PS-TAGS-13, PS-TAGS-22, PS-TAGS-23.

### PS-TAGS-DETAILS-01 · Advanced: folder field
- status: pending
- review: keep
- steps:
  1. Expand a row's advanced details, type a name into the folder field, and click Apply.
  2. Clear the folder field and click Apply again.
- observe: Typing alone changes nothing in the layer name; Apply writes "[folder:NAME]" into it. Applying an empty folder field removes the tag. The layer name updates on Apply, not as you type.
- intent: The folder field assigns the layer to a Blender Collection (and an output subfolder under images/), committed on Apply.
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:100-109,55-58

### PS-TAGS-DETAILS-02 · Advanced: path field
- status: pending
- review: keep
- steps:
  1. In a row's advanced details, type a plain name into the path field and click Apply.
  2. Clear it and Apply; then try a value containing a slash or a dot.
- observe: A valid name writes "[path:NAME]" and an empty value removes the tag. A value containing "/", "\\", ".", or ".." is silently ignored - nothing changes and no error is shown.
- intent: The path field overrides the exported filename stem for the layer, and only plain names (no slashes or dots) are accepted.
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:110-119,59-62,69-74

### PS-TAGS-DETAILS-03 · Advanced: scale field
- status: pending
- review: keep
- steps:
  1. In a row's advanced details, type a positive number into the scale field and click Apply.
  2. Clear it and Apply; then try 0, a negative number, and letters.
- observe: A positive number writes "[scale:N]" and an empty value removes the tag. 0, negative, or non-numeric input is ignored (nothing is written). No sub-pixel warning appears in the panel.
- intent: The scale field multiplies the layer's bounding-box size, and only positive numbers are accepted.
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:120-129,63-66,76-81

### PS-TAGS-DETAILS-04 · Advanced: origin X / Y fields
- status: pending
- review: keep
- steps:
  1. In a row's advanced details, type numbers into both origin X and origin Y and click Apply.
  2. Clear both and Apply; then leave one field non-numeric and Apply.
- observe: With both fields valid, Apply writes "[origin:X,Y]". Clearing both removes the origin tag. If either field is non-numeric, nothing is written and no error appears.
- intent: The origin X/Y fields set an explicit pivot for the layer in pixels, overriding the default centre.
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:130-146,67-74,83-92

### PS-TAGS-DETAILS-05 · Advanced: From selection button
- status: pending
- review: keep
- pre: A row's advanced details are expanded and there is an active rectangular marquee selection in the document.
- steps:
  1. Make a rectangular marquee selection, then click "From selection".
  2. Click "From selection" again with no active selection.
- observe: The origin X and Y fields fill in with the rounded centre of the selection (this is a draft - it needs Apply to commit). With no selection, the button does nothing visible.
- intent: "From selection" fills the origin fields from the centre of the current Photoshop marquee.
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:147-153,84-96; apps/photoshop/src/api/ps-selection-bounds.ts:15-36

### PS-TAGS-DETAILS-06 · Advanced: origin marker checkbox
- status: pending
- review: keep
- steps:
  1. In a row's advanced details, tick the origin-marker checkbox and click Apply.
  2. Untick it and Apply.
- observe: Ticking writes a bare "[origin]" into the layer name and unticking removes it. When explicit origin X,Y coordinates are set, the bare "[origin]" marker is suppressed (the two are mutually exclusive).
- intent: The origin-marker checkbox marks the layer's centre as its parent group's pivot.
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:155-162,75-78,120-126

### PS-TAGS-DETAILS-07 · Advanced: name pattern field (groups only)
- status: pending
- review: keep
- pre: A group row's advanced details are expanded.
- steps:
  1. On a group row, type a pattern containing "*" into the name-pattern field and click Apply.
  2. Clear it and Apply; then try a pattern with no "*".
- observe: A non-empty pattern that contains "*" writes "[name:..]" and an empty value removes the tag. A pattern with no "*" is ignored. The field does not appear on non-group rows at all.
- intent: The name-pattern field sets a naming template for a group's descendants, where "*" stands in for each descendant's own name.
- code: apps/photoshop/src/panels/sections/tags/Details.tsx:163-174,79-82,94-98

### PS-TAGS-SYNC-01 · Layer tree stays in sync with Photoshop
- status: pending
- review: keep
- pre: A document is open and the panel is visible.
- steps:
  1. Rename, add, or remove a layer directly in Photoshop and wait about 1.5 seconds, or switch away from the panel and back.
- observe: The tags tree updates to match without any manual refresh, and untouched branches keep their state (open dropdowns are not torn down). The tree stops polling while the panel is hidden.
- intent: The panel keeps its layer tree current with Photoshop on its own.
- code: apps/photoshop/src/hooks/useTagTree.ts:44-91,115-119

## Active document sub-panel

### PS-DOC-SWEEP · Active-document sub-panel inventory (visual pass)
- status: pending
- review: keep
- observe: A "name" row shows the open document's filename in monospace, or "No document open in Photoshop." when nothing is open. A "canvas" row shows "<width> x <height> px" (matching Image > Canvas Size) in monospace.
- intent: Confirm the active-document name and canvas rows and the no-document fallback are present.
- code: apps/photoshop/src/panels/sections/DocSection.tsx:18-19
- note: absorbs PS-AUX-02, PS-AUX-03.

## Validate sub-panel

### PS-VALIDATE-SWEEP · Validate sub-panel inventory (visual pass)
- status: pending
- review: keep
- observe: The header badge shows the total of warnings plus skipped plus validation errors plus the non-sRGB color advisory, or "ok" when that total is zero. With no document, the body shows "Open a document to begin validation." or, in the no-document state, the first error or a fallback "No document open." When everything is fine, the badge reads "ok" and the body reads "No issues. Manifest looks ready to export." When invalid, a red "Manifest invalid:" block lists one row per error. Problems are grouped under "Warnings (N)" with a row each and "Skipped (N)" with a row each. A document assigned a non-sRGB color profile adds an amber "Document profile <name> is not sRGB" advisory block at the top (behavior in PS-VALIDATE-COLOR-01).
- intent: Confirm every Validate-panel state (empty, no-document, clean, invalid, non-sRGB advisory) and the warnings/skipped groups render.
- code: apps/photoshop/src/panels/sections/ValidateSection.tsx:16-85
- note: absorbs PS-AUX-06, PS-AUX-07, PS-AUX-08, PS-AUX-09, PS-AUX-10, PS-AUX-12; behavior -> FLOW-PSD-03 (Validate refresh + click-to-select offending/skipped layer).

### PS-VALIDATE-COLOR-01 · Non-sRGB document advisory
- status: pending
- review: keep
- pre: An open document. To exercise the warning path, have one assigned a non-sRGB profile (Adobe RGB (1998) or any wide-gamut profile) plus the ability to Edit > Convert to Profile.
- steps:
  1. Activate a document assigned a non-sRGB profile (Adobe RGB (1998)); open the Validate sub-panel.
  2. Edit > Convert to Profile > sRGB IEC61966-2.1, then re-read the panel.
  3. Activate an untagged document (Edit > Assign Profile > Don't Color Manage) and re-read the panel.
- observe: With the non-sRGB document, Validate shows an amber advisory "Document profile Adobe RGB (1998) is not sRGB." plus a line that out-of-gamut colors clamp on export (the engine reads PNGs as sRGB and ignores embedded profiles) and to convert via Edit > Convert to Profile; the advisory counts toward the header badge total, so an otherwise-clean manifest reads the count rather than "ok". After converting to sRGB the advisory disappears and the total drops by one. The untagged ("None") document shows no advisory.
- intent: The doc-level advisory fires only on a positively-identified non-sRGB profile - Godot reads PNG bytes as sRGB and ignores ICC, so wide-gamut authoring clamps on export - and stays silent for sRGB and untagged documents (no false positive).
- code: apps/photoshop/src/api/doc-color-profile.ts; apps/photoshop/src/panels/sections/ValidateSection.tsx:38,52-63
- note: classification covered headless by apps/photoshop/uxp-plugin-tests/doc-color-profile.test.ts.

## Preview (Debug) sub-panel

### PS-DEBUG-SWEEP · Preview (Debug) sub-panel inventory (visual pass)
- status: pending
- review: keep
- observe: The header badge shows the manifest layer count when there is one, otherwise no badge. Before a run the body shows "Click Refresh to dry-run the export. Nothing is written." with a Refresh button; with no document it shows the first error or "No document open." plus a Refresh button. An "anchor" row shows "(canvas centre)" when there is no explicit anchor, otherwise "<x>, <y> px" in monospace. Count rows show "entries", "skipped", and "warnings". Each mesh entry row shows its kind, name, path, and optional badges "(folder=..., blend=..., origin=x,y)"; each sprite entry row shows "sprite", name, "<N> frames", and any badges. The entry matching the selected Photoshop layer is highlighted as "selected".
- intent: Confirm the Preview dry-run panel's badge, empty and no-document states, anchor and count rows, and per-entry rows all render.
- code: apps/photoshop/src/panels/sections/DebugSection.tsx:19-117
- note: absorbs PS-AUX-15, PS-AUX-17, PS-AUX-18, PS-AUX-19, PS-AUX-20, PS-AUX-21, PS-AUX-22; behavior (Refresh dry-run) -> FLOW-PSD-03.

## Legacy migration sub-panel

### PS-MIGRATION-SWEEP · Legacy-migration sub-panel inventory (visual pass)
- status: pending
- review: keep
- observe: The header badge shows the candidate count and the section opens by default when there is at least one candidate. The section is hidden entirely when no document is open, or when there are zero candidates and no previous result. The empty state reads "No underscore-prefixed layers found." (shown when there are zero candidates but a previous result exists). The candidate preview reads "N layer(s) ready to rename:" then up to six rows of "oldName -> newName" and then "...and N more." A button reads "Convert N layer(s) to [ignore]". The result reads "Renamed N layer(s)." on success; on failures it turns red, reads "..., M failed:", and shows one row per failure "<path>: <reason>".
- intent: Confirm the migration panel's badge, empty state, candidate preview, Convert button, and result view all render.
- code: apps/photoshop/src/panels/sections/MigrationSection.tsx:20-87
- note: absorbs PS-AUX-24, PS-AUX-25, PS-AUX-28; behavior -> GAP-3 (migration apply; see PS-MIGRATION-01).

### PS-MIGRATION-01 · Convert underscore layers to [ignore]
- status: pending
- review: keep
- pre: A document with at least one underscore-prefixed candidate layer.
- steps:
  1. Click "Convert N layer(s) to [ignore]".
  2. Watch the button and the layer names in Photoshop.
- observe: The button reads "Renaming..." and is disabled during the run. The candidate layers are renamed to their "[ignore]" names in a single undo step. When it finishes, the result view appears, the candidate count drops to zero, and the button re-enables.
- intent: Convert renames all underscore-prefixed layers to the "[ignore]" convention in one batch and one undo step.
- code: apps/photoshop/src/panels/sections/MigrationSection.tsx:37-39 (handler useMigration.apply -> applyUnderscoreMigration -> executeAsModal:57)
- note: no owning flow yet - candidate flow GAP-3 (the plugin's own legacy [ignore] migration-apply write path is not covered by any existing flow).
