# Spec 053: Photoshop plugin data integrity and resilience - TODO

Three PRs. PR 1 is the data-loss core; PR 2 is import resilience; PR 3 is the low-severity staleness and cosmetic residue. Delivered on `feat/spec-053-photoshop-data-integrity` (one commit per PR-group).

## PR 1 - stop silent data loss

- [x] Thread the layer id through the remaining name-path resolvers so duplicate same-named siblings are not mis-routed; the rename path is already id-based. `_layer-find.ts`, `legacy-migration.ts` (applier prefers `findLayerById`).
- [x] Promote a filename template that drops `{name}` (every mesh collapses to one `overwrite:true` path) from a warning to a blocking error. The planner emits a `template-collapse` `PlanError`; export refuses to run. Also guards `{index}`-less frame templates. `planner.ts`, `export-flow.ts`.
- [x] Surface invalid advanced-field input (path / scale / origin / name-pattern) instead of SKIP-ping it silently while the form still shows the rejected value. `detailFormErrors` marks the row and blocks Apply. `tag-form.ts`, `tags/Details.tsx`.
- [~] Preserve the `[spritesheet]` token. Re-scoped to PR 3 (cosmetic): it is not data loss - see the STUDY finding. `[sprite]`/`[spritesheet]` both parse to `kind: "sprite"` and the planner never reads the literal token.

## PR 2 - import resilience

- [x] Wrap each import entry (`placePngAt`'s `app.open`, then the `stampEntry` / `stampMesh` / `stampSprite` loop) in its own guard inside the single `executeAsModal`, degrading a rejected open or stamp to a per-entry warning so prior progress survives. Sprite frames get the same per-frame guard. `import-flow.ts`.

## PR 3 - staleness, races, cosmetics

- [x] Re-emit the authored `[spritesheet]` token so an unrelated edit does not rewrite it to `[sprite]` (round-trip stability). An explicit kind pick drops the alias. `tag-parser.ts`, `tag-writer.ts`.
- [x] Disable the import button during the pre-busy picker window. `useImportFlow.ts` goes busy before the picker opens.
- [x] PNG path resolution stops assuming `/` separators. `import-flow.ts` `splitManifestPath` accepts `\` too.
- [x] "From selection" with no marquee reports instead of a silent no-op. `tags/Details.tsx`.
- [x] The Validate panel's Doc Refresh re-runs the preview so the list cannot go stale. `ProscenioValidatePanel.tsx`.
- [x] Remove the spurious `key` on the standalone `<select>` elements. `tags/Row.tsx`.
- [x] Delete the stray `{ }` JSX leftover. `components/Accordion.tsx`.
- [x] `folder-storage` stale-token write surfaces a re-pick affordance, not a generic failure. `runExport` returns a `stale-folder` result, drops the token, and the panel clears the folder so the picker reappears. `export-flow.ts`, `folder-storage.ts` (`isStaleFolderError`), `ProscenioExporter.tsx`, `ExportSection.tsx`.
- [x] The tag draft does not apply a stale baseline when an external edit keeps the same `rawName`. Reset keys on node identity (`tagNodeIdentity`) as well as `rawName`, so same-named siblings do not share a draft. `tag-tree.ts`, `tags/Details.tsx`.
- [rejected] Drop the redundant `disabled={cond ? true : undefined}` ternaries. Kept: load-bearing for UXP spectrum web components under React 16 - for a custom element React routes the prop through `setValueForAttribute`, so `disabled={false}` sets `disabled="false"` (present) and pins the button disabled. The ternary keeps `undefined` -> removed. `MigrationSection.tsx`, `tags/Details.tsx`.
- [already done] Disable the export button on a closed-document snapshot. `ProscenioExporter.tsx` already guards `doc === null`.
