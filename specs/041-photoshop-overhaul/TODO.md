# Spec 041: Photoshop plugin overhaul - TODO

Locked call: a targeted boundary rewrite (IPC adapter + export writer) behind the
existing `AdaptedDocument` / `Manifest` shapes - the tested logic core stays.

**Status 2026-06-13:** the correctness + responsiveness work shipped and is fully
verified headless (typecheck + lint + 266 vitest tests + webpack build all green) AND
**confirmed in a real Photoshop session**: on `doll_tagged.psd` every tag write
(ignore / kind / blend / advanced Apply) applied with zero `object null is not
iterable`, and the export completed (`runExport done {entries: 22}`) - the two failures
that defined "unusable" are gone. That session also surfaced one follow-up - a tag edit
on a layer inside a renamed group missed by stale name-path - now fixed by the
layerID-based lookup below. The two items that can only be validated against a live
runtime - the `batchPlay` multiGet descriptor and the React-hook timing of the
shared-adaptation dedup - stay deferred to a GUI session rather than shipped blind
(shipping an unverifiable host-API descriptor would repeat the mock-vs-reality gap that
caused the original crash). The shipped poll + lazy work already make the panel
responsive for real (non-huge) documents; multiGet's win is a single-walk speedup that
matters most on the large-doc tail, which is gated anyway.

## Shipped

### PR 1 - null-iteration crash fix + export writer resilience

- [x] **Fix the `object null is not iterable` crash** that killed every tag write and the export. Root cause confirmed: `findLayerByPath` read a matched leaf's `.layers` even on the last path segment, and `toArray` guarded only `undefined`, so a PS art layer reporting `.layers === null` made `Array.from(null)` throw on every rename + export write, while `adaptDocument` survived via `?? []` (tree rendered, writes crashed). Fix: `toArray` now normalizes `null` + any non-iterable, and the walk no longer reads children past the last segment ([`_layer-find.ts`](../../apps/photoshop/src/api/_layer-find.ts)); `adaptDocument` routes `doc.layers` + group `.layers` through a `toLayerArray` guard and `extractAnchor` handles null guides ([`adapt-document.ts`](../../apps/photoshop/src/api/adapt-document.ts)); `readActiveLayerPath` tolerates a null `activeLayers` ([`ps-selection.ts`](../../apps/photoshop/src/api/ps-selection.ts)). Regression tests assert each function survives a null collection (closes 040 F-01/F-02 crash class).
- [x] Per-layer try/catch in [`png-writer.ts`](../../apps/photoshop/src/api/png-writer.ts) `runWrites`: a UXP rejection on one layer records `{ ok: false, skippedReason }` instead of rejecting the whole modal. Tested with a real `duplicate` rejection + a `createFile` rejection.
- [x] Partial export in [`export-flow.ts`](../../apps/photoshop/src/api/export-flow.ts): the manifest is written with the entries whose PNGs landed and a new `partial` result names the failed layers + reasons; only when every entry fails is it `failed`. Invariant preserved (manifest never references a missing PNG). Tested by asserting the **actual manifest JSON written** excludes the failed entry. UI renders the partial result actionably ([`ExportSection.tsx`](../../apps/photoshop/src/panels/sections/ExportSection.tsx)).

### PR 2 / PR 3 (partial) - layerID + live PPU

- [x] Surface the PS `layerID` on the adapted `Layer` (sync `layer.id` read, defensive) and carry it onto the tag-tree node ([`adapt-document.ts`](../../apps/photoshop/src/api/adapt-document.ts), [`layer.ts`](../../apps/photoshop/src/lib/layer.ts), [`tag-tree.ts`](../../apps/photoshop/src/lib/tag-tree.ts)).
- [x] Key the tag tree on `layerID` (fallback to the tag-stripped display path) so a tag edit no longer remounts the row + subtree ([`TagsSection.tsx`](../../apps/photoshop/src/panels/sections/TagsSection.tsx)). Test: the id survives a rename, so the key is stable.
- [x] **Resolve tag-write targets by `layerID`** (not just the cached name-path), threaded node.id -> onRename -> renameLayer -> `findLayerById` ([`_layer-find.ts`](../../apps/photoshop/src/api/_layer-find.ts), [`layer-rename.ts`](../../apps/photoshop/src/api/layer-rename.ts)). Fixes the real-session failure where a tag edit on a layer inside a renamed group missed by name (`no match at depth 0 seeking "Agrupar 1"`), and disambiguates duplicate sibling names (040 F-24). Falls back to the name-path when no id. Tested with a stale-path + duplicate-name fixture.
- [x] Fix the imported PPU not reaching the live session (040 F-14): the store now notifies subscribers on persist and `usePixelsPerUnit` subscribes, so a PSD import updates the live input + re-export without a reload ([`pixels-per-unit-store.ts`](../../apps/photoshop/src/api/pixels-per-unit-store.ts), [`usePixelsPerUnit.ts`](../../apps/photoshop/src/hooks/usePixelsPerUnit.ts)). Tested via the subscribe/notify contract.

### PR 4 (partial) - adaptive poll

- [x] Adaptive fallback poll ([`useTagTree.ts`](../../apps/photoshop/src/hooks/useTagTree.ts)): once a `version` bump proves PS notifications fire, the poll relaxes from 1.5s to a 15s safety net (60s hidden), and a tick is skipped when an event-driven sync already ran within the interval - removing the constant idle IPC walk.

### Debug logging

- [x] Diagnostic logs at the null boundaries (`adapt-document` warns when `doc.layers` is not an array; `_layer-find.toArray` traces a normalized null / non-iterable) so a debug session sees the host handing back null instead of a silent empty tree.
- [x] Log-level toggle in the Debug panel ([`LogLevelSection.tsx`](../../apps/photoshop/src/panels/sections/LogLevelSection.tsx)) driving the existing `log` util - an artist flips to trace/debug from the UI (no console command) and reads `[proscenio:<area>]` lines in UXP Developer Tools.

## Deferred - need a live-Photoshop validation session

- **multiGet document reader** (the keystone IPC fast-path) - trigger: a GUI session that can validate the `batchPlay` multiGet descriptor against a real PSD. It also makes `adaptDocument` async (a ripple through every read path), so it lands behind the descriptor proof. The DOM adapter (now hardened + carrying `layerID`) is the correct, working read path until then; the multiGet is a single-walk ~50x speedup, not a correctness fix. Build it as a try -> DOM-fallback fast path so a wrong descriptor degrades safely.
- **shared adaptation per tick / lazy preview** - trigger: same GUI session. Lifting the document adaptation into one shared snapshot (or deferring the preview off the tag-paint path) removes the second full walk per event (the real session shows `useExportPreview refresh` + `useActiveLayerPath changed` firing redundantly per version bump), but it is React-hook timing that only a real panel can validate; the layerID-key + adaptive-poll wins already cut the felt jank.
- **collapse-by-default + large-doc windowed rendering** - gate: a real Proscenio-scale-or-larger PSD makes the panel painful after the above land. Proscenio characters are flat (the doll is 22 layers), so this is the speculative large-doc tail.
