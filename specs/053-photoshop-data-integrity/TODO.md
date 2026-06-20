# Spec 053: Photoshop plugin data integrity and resilience - TODO

Three PRs. PR 1 is the data-loss core; PR 2 is import resilience; PR 3 is the low-severity staleness and cosmetic residue.

## PR 1 - stop silent data loss

- [ ] Preserve the `[spritesheet]` token: the writer's `kindSegment` emits only `[mesh]`/`[sprite]`, and the kind dropdown is not disabled for groups, so a kind edit drops the group-frames semantics. Preserve the token or disable kind editing for groups. `tag-writer.ts:73-80`, `tag-parser.ts:117-119`, `tags/Row.tsx:157-168`.
- [ ] Thread the layer id through the remaining name-path resolvers so duplicate same-named siblings are not mis-routed; the rename path is already id-based. `_layer-find.ts:22-24`, `legacy-migration.ts:60-67`.
- [ ] Promote a filename template that drops `{name}` (every mesh collapses to one `overwrite:true` path) from a warning to a blocking error. `planner.ts:215-249`.
- [ ] Surface invalid advanced-field input (path / scale / origin / name-pattern, including a sub-pixel `[scale]`) instead of SKIP-ping it silently while the form still shows the rejected value. `tag-form.ts:69-99`.

## PR 2 - import resilience

- [ ] Wrap each import entry (`placePngAt`'s `app.open`, then the `stampEntry` / `stampMesh` / `stampSprite` loop) in its own guard inside the single `executeAsModal`, degrading a rejected open or stamp to a per-entry warning so prior progress survives. `png-placer.ts:28`, `import-flow.ts:31-33,62-66,99-145`. (The export side already has this resilience.)

## PR 3 - staleness, races, cosmetics

- [ ] `folder-storage` stale-token write surfaces a re-pick affordance, not a generic failure. `manifest-writer.ts:14-18`.
- [ ] Disable the export button on a closed-document snapshot. `ProscenioExporter.tsx:65`.
- [ ] Disable the import button during the pre-busy picker window. `useImportFlow.ts:22-31`.
- [ ] PNG path resolution stops assuming `/` separators. `import-flow.ts:156-178`.
- [ ] The tag draft does not apply a stale baseline when an external edit keeps the same `rawName`. `tags/Details.tsx:30-37`.
- [ ] "From selection" with no marquee reports instead of a silent no-op. `tags/Details.tsx:84-96`.
- [ ] The Validate panel gets a manual Refresh, or Doc Refresh re-runs the preview, so the list cannot go stale. `ProscenioValidatePanel.tsx:35-40`, `DocSection.tsx:22`.
- [ ] Drop the redundant `disabled={cond ? true : undefined}` ternaries. `MigrationSection.tsx:37`, `tags/Details.tsx:167,170`.
- [ ] Remove the spurious `key` on the standalone `<select>` elements. `tags/Row.tsx:156,167`.
- [ ] Delete the stray `{ }` JSX leftover. `components/Accordion.tsx:45`.
