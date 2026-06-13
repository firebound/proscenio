# Spec 041: Photoshop plugin overhaul

Make the UXP plugin usable again. Two independent failures put it below the
usability line at the same time: the Tags panel visibly tears down and rebuilds on
every interaction (an IPC-cost problem rooted in the DOM-API adapter), and the
manifest export can fail outright so an artist cannot get a manifest onto disk at
all (a resilience problem in the writer leg). Spec 040's end-to-end audit surfaced
the export failure as its trigger; the [photoshop-performance backlog](../backlog-photoshop-performance.md)
already diagnosed the lag. This spec folds both into one pass because they share
the same fix surface - the boundary between the React panels and the live
Photoshop process - and because re-validating the plugin by hand is expensive
enough that it should happen once, against both fixes.

## Scope

- **Replace the DOM-API document walk with a single `batchPlay` multiGet** - the
  keystone; the IPC cost that makes every interaction janky.
- **Share one document adaptation per event tick** across the tag-tree, export
  preview, active-layer, and doc-snapshot consumers.
- **Make the export writer resilient** - a single problematic or renamed layer
  must not make the whole manifest export impossible (the spec 040 trigger).
- **Key the tag tree on a stable layer identity** so a rename stops remounting the
  whole subtree.
- **Tune the fallback polling** so an idle panel is not paying a full IPC walk
  every 1.5s.
- **Window / collapse large documents** so a heavy PSD does not mount thousands of
  UXP controls (lower priority; demand-gated).
- **Fix the imported pixels-per-unit not reaching the live session** (040 finding
  F-14).

## Study

### Surface notes

**The pure core is healthy; the rot is in two boundary layers.** The plugin's
logic tier is well-shaped and unit-tested - `lib/planner.ts`, `lib/tag-tree.ts`,
`lib/manifest.ts`, `lib/tag-parser.ts`, and `api/manifest-validator.ts` all operate
on plain data (`AdaptedDocument`, `Layer[]`, `Manifest`) and never touch Photoshop.
Everything that is slow or fragile lives at the edges: the IPC adapter
([`adapt-document.ts`](../../apps/photoshop/src/api/adapt-document.ts)) and the
export writer ([`png-writer.ts`](../../apps/photoshop/src/api/png-writer.ts) +
[`export-flow.ts`](../../apps/photoshop/src/api/export-flow.ts)). This bounds the
overhaul: the work is a rewrite of the two boundary layers behind their existing
shapes, not a rewrite of the plugin. The user's "complete refactor" framing is
right about the symptom (unusable) but the cheapest cure keeps the tested core and
swaps the boundaries under it.

**Every layer property is a blocking IPC roundtrip, and the adapter walks the whole
tree synchronously.** `adaptDocument` ([`adapt-document.ts:21-31,60-75`](../../apps/photoshop/src/api/adapt-document.ts))
maps `doc.layers` recursively, reading `.name`, `.visible`, and `.bounds` per layer
through the UXP DOM API. Each getter is a synchronous blocking call into the
Photoshop process (`.bounds` is among the most expensive), so an N-layer document
costs hundreds of roundtrips per walk, on the single JS thread that also renders
the panel. The fix is the canonical community pattern the backlog cites: one
`batchPlay` multiGet with `extendedReference` keys (`name`, `layerID`,
`parentLayerID`, `itemIndex`, `group`, `visible`, `bounds`) and `count: -1` fetches
every layer in one IPC call; the tree is rebuilt from the flat list in pure JS,
parent/child reconstructed from `parentLayerID` + `itemIndex`, group detection from
the `group` / `layerSection` kind replacing today's duck-typed `.layers`-presence
check. Reported speedups are ~50x. The `AdaptedDocument` interface
([`adapt-document.ts:13-19`](../../apps/photoshop/src/api/adapt-document.ts)) is the
seam: replace the body, keep the shape, and `buildExportPlan`,
`buildTagTreeReusing`, and every hook stay untouched. The one additive change is
surfacing `layerID` on the adapted layer, which two other items below need.

**A single panel interaction pays at least two full tree walks plus a planner
dry-run.** On each `version` bump from
[`useDocumentChanges.ts`](../../apps/photoshop/src/hooks/useDocumentChanges.ts)
(any `select` / `make` / `delete` / `set` / `open` / `close`, debounced 150ms),
the Tags panel runs `useTagTree(version)` -> `syncOnce` -> `readActiveLayerTree` ->
`adaptDocument` (walk 1, [`useTagTree.ts:44-58,115-119`](../../apps/photoshop/src/hooks/useTagTree.ts)),
and its own effect runs `preview.refresh(opts)` ->
`previewExport` -> `adaptDocument` + `buildExportPlan` + ajv validation (walk 2,
[`ProscenioTagsPanel.tsx:38-42`](../../apps/photoshop/src/panels/ProscenioTagsPanel.tsx),
[`useExportPreview.ts:20-34`](../../apps/photoshop/src/hooks/useExportPreview.ts),
[`export-flow.ts:52-88`](../../apps/photoshop/src/api/export-flow.ts)), plus
`useActiveLayerPath(version)` walks the selection chain and `refreshDoc` re-snaps
the document. The preview is consumed only by `RevealOutputSection`, so it does not
need to be recomputed eagerly inside the same synchronous burst that rebuilds the
tag tree. Adapting once per tick and feeding both consumers (or making the preview
lazy / idle-deferred) halves the IPC cost of every event even before multiGet
lands; after multiGet it removes a redundant flat-list fetch.

**The export writer turns one bad layer into a total failure - this is the spec
trigger.** `runWrites` ([`png-writer.ts:23-44`](../../apps/photoshop/src/api/png-writer.ts))
calls `writeLayerPng` with no try/catch; any UXP rejection inside
(`documents.add`, `layer.duplicate`, `merge`, `trim`, `saveAs.png`) propagates out
of `runWrites`, rejects `core.executeAsModal`, hits the outer catch in `runExport`
([`export-flow.ts:149-155`](../../apps/photoshop/src/api/export-flow.ts)), and
returns `kind: "failed"` with the manifest **never written** - 040 finding F-01,
and the reported real-world failure. Separately, the atomicity gate
([`export-flow.ts:118-137`](../../apps/photoshop/src/api/export-flow.ts)) writes
the manifest only if `results.every(r => r.ok)`; one layer whose
`findLayerByPath` returns null (renamed / deleted / reordered after the preview was
built) sets `ok: false` and suppresses the manifest for the entire document -
finding F-02. The null lookups are aggravated by `findLayerByPath`
([`_layer-find.ts:22-31`](../../apps/photoshop/src/api/_layer-find.ts)) matching on
exact raw layer name, so any mid-session rename breaks the match. The atomicity
intent is legitimate - a manifest must not reference PNGs that do not exist - but
the current all-or-nothing-by-throw behavior is the wrong shape: a per-layer
try/catch that records `ok: false` instead of throwing, plus a decision on partial
export (write the manifest for the entries that succeeded and report which layers
to fix, versus block with a precise "layer X failed: reason" affordance rather than
a generic failure). Resolving the lookup against `layerID` (now available from
multiGet) removes the rename-fragility class entirely.

**A null-iteration crash makes the Tags panel and export non-functional, not just
slow.** A live run (2026-06-13, `doll_tagged.psd`) surfaced a `TypeError: object null
is not iterable (cannot read property Symbol(Symbol.iterator))` thrown on *every* tag
write (the `X`/ignore glyph, the kind and blend dropdowns, the advanced `+` Apply -
all funnel through `onRename` -> `renameLayer` -> `findLayerByPath`) and again on
`Export manifest + PNGs`, with no manifest written. The whole static path is null-safe
for the doll's 22 flat layers - `adaptDocument` tolerates a null `.layers` via `?? []`
(which is why the 22 rows render), the planner runs on the already-adapted tree, and
`xmp` / `manifest-validator` never throw - so the null originates at a UXP API getter
returning `null` where the type says non-null, at a spot that then iterates or spreads.
The locus was confirmed statically: `findLayerByPath` read a matched leaf's `.layers`
even on the last path segment, and `toArray` ([`_layer-find.ts`](../../apps/photoshop/src/api/_layer-find.ts))
guarded only `undefined`, so a PS art layer whose `.layers` is `null` made
`Array.from(null)` throw on every rename + export write - the only place on both broken
paths that produces this exact message for flat layers. **Fixed (2026-06-13):** `toArray`
normalizes `null` + any non-iterable, the walk no longer reads children past the last
segment, and the sibling boundaries (`adaptDocument`, `extractAnchor`, `readActiveLayerPath`)
are hardened the same way, with regression tests. This reframed the Tags-panel work: it
was not merely janky (the perf story), it was *functionally broken*, and the fix was the
boundary-hardening this spec owns. The debug-log toggle surfaces a normalized null at
trace level so a GUI session can confirm the runtime origin.

**Renames remount the tree because React keys derive from raw names.**
`TagsSection` keys each branch on the raw name-path
([`backlog-photoshop-performance.md`](../backlog-photoshop-performance.md), entry 3:
`TagsSection.tsx:81`), and every tag toggle renames a layer, so the key of that node
and all descendants changes and React unmounts / remounts the whole subtree -
losing the `expanded` flag and paying UXP native-control creation cost per row.
This is the literal "list torn down and rebuilt" the user sees. The collapse-state
mechanism already solved the same instability by keying on `displayPath`
([`collapse-key.ts`](../../apps/photoshop/src/utils/collapse-key.ts)); the truly
stable identity is `layerID`, which the multiGet conversion surfaces for free.

**The fallback poll runs a full IPC walk forever, even idle.**
`useTagTree` polls `syncOnce` every 1500ms visible / 4000ms hidden
([`useTagTree.ts:23-24,64-91`](../../apps/photoshop/src/hooks/useTagTree.ts)), and
the active-layer hook polls the selection chain every 300ms; both exist as
fallbacks for UXP builds where `addNotificationListener` never fires. Net: a full
synchronous tree walk every 1.5s with no user activity, a constant jank floor that
is worse on Windows (the primary dev platform). The fix keeps the fallback but
makes it adaptive - detect at startup whether notifications actually fire and
disable / slow the poll once one is received, skip a tick when an event-driven sync
already ran, and re-tune cadence against multiGet's much lower cost. Sequence this
last: after multiGet, the poll may be cheap enough to leave nearly as-is, so
re-measure before tuning.

**Large documents have no virtualization, but that is a demand-gated tail.** The
Tags panel mounts one row per visible tree node with no cap; a fully expanded
500-layer PSD mounts thousands of UXP controls, and UXP's UI engine degrades
non-linearly with DOM size. Proscenio characters are not 500-layer documents, so
this is real but speculative for the actual workload - the cheap half
(collapse top-level groups by default on open) ships with the render-churn work;
full windowed rendering waits on a real painful document.

**The imported pixels-per-unit never reaches the live session (040 F-14).**
`import-flow` calls `persistPixelsPerUnit()` (writes localStorage) but nothing
updates the live `usePixelsPerUnit` React state, which only reads
`loadPixelsPerUnit()` at mount, so an imported PPU does not reach the current
session's Export input until the panel reloads - contradicting the code's own
"so a re-export emits the imported scale" comment. Small, self-contained, and rides
this pass because it is the same import/export correctness surface.

### Assessment

Scores 1-5. Flow value: size x likelihood of the breakage the work removes
(5 = plugin unusable). Test burden: cost to build plus recurring cost. Bug surface:
complexity the change itself adds. Underuse risk: 5 = the fix protects nothing real.

| Item | Flow value | Test burden | Bug surface | Underuse risk | Verdict | Why |
| --- | --- | --- | --- | --- | --- | --- |
| multiGet document reader | 5 | 3 | 3 | 1 | now | The keystone IPC fix behind every lag symptom; replaces the body of `adaptDocument` behind its existing shape, so the tested core is untouched. ~50x on the dominant cost. |
| export writer resilience | 5 | 2 | 2 | 1 | now | The spec trigger - today a single bad / renamed layer makes the manifest impossible to export. Per-layer try/catch + a partial-vs-blocking decision + `layerID` lookup. |
| one adaptation per tick | 3 | 1 | 1 | 1 | now | Halves IPC per event even before multiGet; pure plumbing once the reader is shared. |
| tag-tree keyed on `layerID` | 3 | 1 | 1 | 1 | now | Stops the visible remount-on-rename; trivial once multiGet surfaces `layerID`. |
| pixels-per-unit live seeding (F-14) | 2 | 1 | 1 | 1 | now | Small correctness fix on the same import/export surface; cheap to fold in. |
| adaptive fallback poll | 2 | 2 | 2 | 2 | now | Removes the idle jank floor; sequence last and re-measure, since multiGet may make the poll cheap enough to leave. |
| large-doc virtualization | 1 | 4 | 3 | 4 | gate | Real but speculative for Proscenio-scale documents; ship the cheap collapse-by-default now, gate full windowing on a painful real PSD. |

### Verdict summary

Counts: **6 now, 1 gate, 0 drop.** The plugin is below the usability line for two
independent reasons and both land in this pass: the multiGet reader and the
per-tick / `layerID` / poll work remove the IPC churn that makes interaction janky,
and the writer-resilience work removes the export-impossible failure that was spec
040's trigger. The single architectural decision is below; everything else is
plumbing behind shapes that already exist. Full windowed rendering for large
documents gates on a real painful PSD - the cheap collapse-by-default half ships
now, the windowing does not, because Proscenio characters are not the heavy
documents that justify it.

### Decision: targeted boundary rewrite, not a from-scratch rewrite

The user framed this as a "complete refactor". The audit narrows that: the plugin's
logic tier (`lib/`, the validator) is healthy and unit-tested, and the
`AdaptedDocument` / `Manifest` shapes are clean seams. A from-scratch rewrite would
discard tested code (the planner, tag parsing, manifest building, ajv validation)
to re-solve problems that are already solved, and would multiply the manual
re-validation cost. The locked call: **rewrite the two boundary layers in place -
the IPC adapter (`adapt-document.ts`, behind the `AdaptedDocument` interface) and
the export writer (`png-writer.ts` + the atomicity logic in `export-flow.ts`) - and
keep the logic core.** This keeps the diff bounded, the tests mostly reusable, and
the GUI re-validation focused on the two surfaces that actually changed.

### What only a GUI session can confirm

The pure parts are unit-testable (the multiGet reader against a recorded descriptor
fixture, the planner / tag-tree against the same `AdaptedDocument` shape, the writer
result-mapping against mocked rejections). What needs a real Photoshop session:
the multiGet descriptor actually returning the expected keys on a real PSD, the
~50x improvement on a representative document, the export succeeding when one layer
is deliberately broken / renamed mid-session, the tree not remounting on a tag
toggle, the idle poll no longer stuttering on Windows, and the imported PPU reaching
the Export field without a reload. These fold into the spec 040 Photoshop checklist.
