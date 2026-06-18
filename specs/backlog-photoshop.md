# Photoshop plugin backlog

Code-read defects in the Photoshop UXP plugin (`apps/photoshop/src/`), promoted from the QA Companion code-read audit on 2026-06-15 (the doc-coverage half is in [backlog-docs.md](backlog-docs.md)). Found by reading, not yet reproduced. The export-side crash pair and the live-PPU/async-preview items already shipped via specs 041/048 and are not repeated here. Distinct from the doc-coverage pass (the undocumented sections live in [backlog-code-quality.md](backlog-code-quality.md)).

## Spritesheet group silently rewritten to sprite on any tag edit

**What:** the parser maps `[spritesheet]` to `kind: "sprite"`, but the writer's `kindSegment` only emits `[mesh]` or `[sprite]`, and the kind dropdown is not disabled for groups. Selecting any kind (or any edit that rewrites the name) on a group originally tagged `[spritesheet]` silently rewrites it to `[sprite]`, losing the group-frames semantics - a real data/semantic loss on a common control.

**Where:** `apps/photoshop/src/lib/tag-writer.ts:73-80`; `tag-parser.ts:117-119`; `panels/sections/tags/Row.tsx:157-168`.

**Fix:** preserve the original `[spritesheet]` token on round-trip, or emit `[spritesheet]` when kind=sprite on a group, or disable kind editing for groups. Severity high.

## Duplicate same-name layers mis-route by name path

**What:** `findLayerByPath` matches by raw name and takes the first match; two sibling layers/groups with identical names route every select, tag edit, PNG write, and legacy-migration apply to the first one, silently mis-editing or mis-renaming the second. The rename path is already mitigated (it uses `findLayerById`), but selection, the writer, and migration still go through the first-match path.

**Where:** `apps/photoshop/src/api/_layer-find.ts:22-24`; legacy-migration apply at `api/legacy-migration.ts:60-67`.

**Fix:** thread the stable layer id through the remaining callers (selection, writer, migration), or have `findLayerByPath` disambiguate/surface ambiguity. Severity medium.

## Import has no per-entry resilience inside the modal

**What:** `placePngAt` calls `app.open(pngFile)` for every entry while the whole batch runs inside one `executeAsModal`; a nested open per layer can be rejected or stall, and there is no per-entry `try/catch` around `app.open` or around `stampEntry`/`stampMesh`/`stampSprite`. A single rejected open or stamp throws out of the import loop, aborts the modal, and loses all prior stamping progress - surfaced as a generic "Import failed." rather than a per-entry skip/warning (the export path got this resilience in spec 041; the import path did not).

**Where:** `apps/photoshop/src/api/png-placer.ts:28`; `api/import-flow.ts:31-33,62-66,99-111,134-145`.

**Fix:** wrap each entry in `try/catch` and degrade a failure to a per-entry warning/skip, mirroring the export side. Severity medium.

## Filename template without {name} silently overwrites PNGs

**What:** a template that drops `{name}` (e.g. `out.png`) collapses every mesh to the same output path. The planner emits only a non-blocking duplicate-path warning and `createFile` uses `overwrite: true`, so all but one PNG are silently overwritten; the manifest still validates and is written. Silent data loss with no export-time hard stop.

**Where:** `apps/photoshop/src/lib/planner.ts:215-249`; `api/png-writer.ts` (`createFile` overwrite).

**Fix:** promote duplicate output paths to a blocking validation error. Severity medium.

## Stale folder token surfaces as a generic failure

**What:** `writeManifest` does `folder.createFile`/`write` inside the modal; if the persisted folder token is stale (folder moved or permission revoked) the write rejects and the user gets a generic "failed" with the raw error, not a "pick the folder again" affordance. `restoreFolder` only guards the mount-time resolve, not a later write.

**Where:** `apps/photoshop/src/api/manifest-writer.ts:14-18`; `folder-storage.ts:17-29`.

**Fix:** catch the write rejection and surface a re-pick-folder affordance. Severity low.

## Export button stays enabled on a stale document snapshot

**What:** the export button is gated on a document snapshot (`useDocSnapshot`) while `runExport` reads `app.activeDocument` live. If the user closes the document after the snapshot, the button stays enabled but `runExport` hits `doc === null` and returns "no-document". The two sources of truth disagree.

**Where:** `apps/photoshop/src/panels/ProscenioExporter.tsx:65`; `hooks/useDocSnapshot.ts:20-23`; `api/export-flow.ts:94-98`.

**Fix:** re-check the live document on click, or refresh the snapshot on document-change events. Severity low.

## Import button race during the picker window

**What:** the import action button is disabled (busy) only after the file picker resolves; during the pre-busy picker/validation window a second click can open a second picker or start a concurrent run.

**Where:** `apps/photoshop/src/hooks/useImportFlow.ts:22-31`; `panels/sections/ImportSection.tsx:19`.

**Fix:** set an in-flight guard before opening the picker. Severity low.

## PNG path resolution assumes forward-slash separators

**What:** `resolveRelativeFile` splits `entry.path` on `/` and walks `getEntry` per segment; a backslash-separated or absolute path in the manifest, or a folder-name collision, resolves to null and the entry is silently skipped with only a warning. No OS-separator normalization.

**Where:** `apps/photoshop/src/api/import-flow.ts:156-178`.

**Fix:** normalize separators (`\` to `/`) before splitting. Severity low.

## Advanced tag fields drop invalid input silently

**What:** invalid `path`/`scale`/`origin`/`name-pattern` values (including a sub-pixel `[scale]`) are returned as SKIP and dropped with no surfaced error; the form still shows the typed (rejected) value while the layer name is unchanged, so the artist believes the edit applied when it did not. The doc claims a sub-pixel scale "raises a validation warning"; no warning exists.

**Where:** `apps/photoshop/src/lib/tag-form.ts:69-99,101-112`, `:76-81` (scale).

**Fix:** validate on Apply with a visible per-field error state. Severity low.

## "From selection" is a silent no-op without a marquee

**What:** with no marquee selection (or zero-area bounds), `readSelectionCenter` returns null and the handler only logs a debug warning - the button appears to do nothing, looking dead to the artist.

**Where:** `apps/photoshop/src/panels/sections/tags/Details.tsx:84-96`; `api/ps-selection-bounds.ts:24-26`.

**Fix:** surface a transient "no selection" hint. Severity low.

## Tag draft can apply a stale baseline after an external rename

**What:** the tag form resets only when `node.rawName` changes; if an external edit changes the tags but yields the same `rawName` (or a rename round-trips to an identical name), the open draft is not re-synced to on-disk truth, so a stale baseline can be applied.

**Where:** `apps/photoshop/src/panels/sections/tags/Details.tsx:30-37`.

**Fix:** also re-sync when the tag bag changes, not only on `rawName`. Severity low.

## Validate panel can go stale with no manual refresh

**What:** the Validate panel has no manual Refresh and relies solely on the `useDocumentChanges` version effect; on UXP builds where the notification listener returns void (no events fire), the list goes stale with no user-reachable way to force a re-plan (the Debug panel has Refresh, Validate does not). The Doc Refresh button does not re-run the preview - it only re-reads the document header - so a user expecting "Refresh" to update warnings/entries sees stale data.

**Where:** `apps/photoshop/src/panels/ProscenioValidatePanel.tsx:35-40`; `panels/sections/DocSection.tsx:22`; `api/ps-notifications.ts:60-63`.

**Fix:** add a Refresh control to the Validate section (mirror Debug), and have the Doc Refresh handler also re-run the preview. Severity low.
