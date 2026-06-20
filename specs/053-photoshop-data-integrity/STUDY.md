# Spec 053: Photoshop plugin data integrity and resilience

The Photoshop UXP plugin has a cluster of paths that lose data or abort a whole batch on one bad entry, plus a group of low-severity staleness and race conditions. This spec hardens the data-integrity paths first (no silent loss, partial failures degrade), then clears the minor UX staleness group and the cosmetic review nitpicks in the same files.

Scaffolded ahead of its STUDY. The scope below marks what will be done. The data-loss items are objective; the staleness group carries a few small affordance choices (a manual Refresh, a re-pick path) noted in the TODO.

## Scope

- Preserve the `[spritesheet]` group semantics instead of silently rewriting it to `[sprite]`.
- Route layer targeting by id, not first-name-match, so duplicate siblings are not mis-edited.
- Wrap each import entry so one rejected open or stamp degrades to a per-entry warning instead of aborting the batch.
- Promote a filename template that drops `{name}` to a blocking error, since it collapses every mesh onto one overwritten path.
- Surface invalid advanced-field input instead of dropping it silently while the form shows the rejected value.
- Clear the minor staleness and race group (stale-token re-pick, closed-document export button, pre-busy import window, path-separator assumption, stale tag-draft baseline, no-marquee no-op, Validate refresh).
- Fold in the cosmetic Photoshop review nitpicks touching the same components.

## Sources

Drains [`backlog-photoshop.md`](../backlog-photoshop.md) (all five behavior items plus the minor staleness group) and the Photoshop cosmetic items in [`backlog-coderabbit-nitpicks.md`](../backlog-coderabbit-nitpicks.md) (`photoshop-redundant-disabled-ternary`, `photoshop-spurious-key-on-select`, `photoshop-stray-empty-jsx`). The `shared adaptation per tick` item in [`deferred.md`](../deferred.md) rides PR 2 if the read paths are already open.
