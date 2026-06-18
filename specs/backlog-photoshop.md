# Photoshop plugin backlog

Code-read gaps in the Photoshop UXP plugin (`apps/photoshop/src/`), from the QA Companion audit (2026-06-15), re-verified against current `main`. Found by reading, not yet reproduced. The export-side crash pair and the live-PPU/async-preview wins already shipped (specs 041/048). The doc-coverage half is in [backlog-docs.md](backlog-docs.md).

## Tag / spritesheet semantics (data loss)

- **`[spritesheet]` group silently rewritten to `[sprite]`** (high). The parser maps `[spritesheet]` to `kind:"sprite"` but the writer's `kindSegment` only emits `[mesh]`/`[sprite]`, and the kind dropdown is not disabled for groups; any kind edit on such a group loses the group-frames semantics. `tag-writer.ts:73-80`, `tag-parser.ts:117-119`, `tags/Row.tsx:157-168`. Preserve the token, or disable kind editing for groups.

## Duplicate-name layer targeting

- **`findLayerByPath` first-match mis-routes duplicate siblings** (med). Selection, the writer, and legacy-migration apply resolve by name path and take the first match, so two same-named siblings mis-edit/mis-rename the second. The tag rename path is already id-based (`findLayerById`, see [decisions.md](decisions.md)); thread the id through the remaining callers. `_layer-find.ts:22-24`, `legacy-migration.ts:60-67`.

## Import-path resilience (one failure aborts the batch)

- **No per-entry try/catch in the import modal** (med). `placePngAt`'s `app.open` per entry and the `stampEntry`/`stampMesh`/`stampSprite` loop run inside one `executeAsModal` with no per-entry guard; a single rejected open or stamp aborts the whole import and loses prior progress (the export side got this resilience in spec 041). `png-placer.ts:28`, `import-flow.ts:31-33,62-66,99-145`. Wrap each entry, degrade to a per-entry warning.

## Silent data loss / silent skips

- **Filename template without `{name}` overwrites PNGs** (med). A template that drops `{name}` collapses every mesh to one path; the planner only warns and `createFile` uses `overwrite:true`. `planner.ts:215-249`. Promote duplicate output paths to a blocking error.
- **Invalid advanced-field input dropped with no surfaced error** (low). Invalid path/scale/origin/name-pattern values (incl. a sub-pixel `[scale]`, which the doc says warns) are SKIP-ped silently while the form shows the rejected value. `tag-form.ts:69-99`.

## Minor UX staleness / races (low, group)

`folder-storage` stale-token write surfaces a generic failure instead of a re-pick affordance (`manifest-writer.ts:14-18`); the export button stays enabled on a closed-document snapshot (`ProscenioExporter.tsx:65`); the import button is clickable during the pre-busy picker window (`useImportFlow.ts:22-31`); PNG path resolution assumes `/` separators (`import-flow.ts:156-178`); the tag draft can apply a stale baseline when an external edit keeps the same `rawName` (`tags/Details.tsx:30-37`); "From selection" with no marquee is a silent no-op (`tags/Details.tsx:84-96`); and the Validate panel has no manual Refresh while the Doc Refresh does not re-run the preview, so the list can go stale (`ProscenioValidatePanel.tsx:35-40`, `DocSection.tsx:22`).
