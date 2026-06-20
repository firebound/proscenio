# Spec 053: Photoshop plugin data integrity and resilience

The Photoshop UXP plugin has a cluster of paths that lose data or abort a whole batch on one bad entry, plus a group of low-severity staleness and race conditions. This spec hardens the data-integrity paths first (no silent loss, partial failures degrade), then clears the minor UX staleness group and the cosmetic review nitpicks in the same files.

Scaffolded ahead of its STUDY. The scope below marks what will be done. The data-loss items are objective; the staleness group carries a few small affordance choices (a manual Refresh, a re-pick path) noted in the TODO.

## Finding: the `[spritesheet]` item was not data loss

Measured both sides before building. The parser maps `[sprite]` and `[spritesheet]` to the same `kind: "sprite"`, and the planner keys sprite-frame detection on `tags.kind`, never on the literal token. Rewriting `[spritesheet]` to `[sprite]` on a group therefore changes nothing in the export - a group tagged `[sprite]` still yields N frames. The only thing lost is the artist-facing word in the layer name. Re-scoped from the data-loss core (PR 1) to round-trip stability (PR 3): the writer now re-emits whichever token was authored, but this is cosmetic, not the non-destructive promise the backlog claimed.

## Scope

- Route layer targeting by id, not first-name-match, so duplicate siblings are not mis-edited.
- Wrap each import entry so one rejected open or stamp degrades to a per-entry warning instead of aborting the batch.
- Promote a filename template that drops `{name}` to a blocking error, since it collapses every mesh onto one overwritten path.
- Surface invalid advanced-field input instead of dropping it silently while the form shows the rejected value.
- Clear the minor staleness and race group (pre-busy import window, path-separator assumption, no-marquee no-op, Validate refresh). Re-emit the authored `[spritesheet]` token for round-trip stability.
- Fold in the cosmetic Photoshop review nitpicks touching the same components.

## Delivered

All scoped items shipped in `feat/spec-053-photoshop-data-integrity`:

- PR 1: filename-template collapse blocked, id-routed migration, surfaced invalid advanced-field input.
- PR 2: per-entry (and per-frame) import guard.
- PR 3: `[spritesheet]` round-trip, import path-separator fix, pre-busy import disable, Validate Doc-Refresh re-run, no-marquee report, stray-JSX / spurious-key cosmetics.
- Stale output folder at export: `runExport` returns a `stale-folder` result, drops the persistent token, and the panel falls back to the picker. `isStaleFolderError` classifies the not-found family.
- Tag-draft stale baseline: the advanced-fields reset keys on node identity (`tagNodeIdentity`: layer id, else display path) as well as `rawName`, so two same-named siblings no longer share a draft.

Two backlog items resolved as decisions rather than code:

- The redundant-`disabled` ternary nitpick is rejected: `disabled={cond ? true : undefined}` is load-bearing for the UXP spectrum web components under React 16. For a custom element React routes the prop through `setValueForAttribute`, which does `setAttribute("disabled", "false")` for a boolean `false` rather than removing it, pinning the button disabled. The ternary keeps `undefined` -> attribute removed.
- Closed-document export-button disable was already satisfied (`ProscenioExporter` guards `doc === null`).

## Sources

Drains [`backlog-photoshop.md`](../backlog-photoshop.md) (all five behavior items plus the minor staleness group) and the Photoshop cosmetic items in [`backlog-coderabbit-nitpicks.md`](../backlog-coderabbit-nitpicks.md) (`photoshop-redundant-disabled-ternary`, `photoshop-spurious-key-on-select`, `photoshop-stray-empty-jsx`). The `shared adaptation per tick` item in [`deferred.md`](../deferred.md) rides PR 2 if the read paths are already open.
