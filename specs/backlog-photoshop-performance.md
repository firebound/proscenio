# Photoshop plugin performance backlog

Findings from the 2026-06-11 performance evaluation of the UXP plugin, prompted by user-visible lag in the Tags panel (list visibly tearing down and rebuilding on row clicks and group expansion). Root cause is architectural, not React: every property access on the Photoshop DOM API (`layer.name`, `layer.visible`, `layer.bounds`, `doc.layers`) looks synchronous but is a blocking IPC roundtrip into the Photoshop process, and the panel performs full recursive layer-tree walks through that API several times per interaction, on the same single thread that renders the UI. The existing memoization strategy (`React.memo` on `TagRow` plus ref-preserving `buildTagTreeReusing`) is correct and should stay; it is undermined by the issues below rather than being the problem itself.

Community references backing the diagnosis: [bubblydoo/uxp-toolkit](https://github.com/bubblydoo/uxp-toolkit) ("when using the DOM API, e.g. `document.layers[0].name`, it looks synchronous, but under the hood it makes several IPC calls; with a lot of layers this can get very slow"), [batchPlay multiGet reference](https://developer.adobe.com/photoshop/uxp/2022/ps_reference/media/batchplay/) (`count: -1` element-range fetches all layers in one call), [forum perf test on batchPlay get flavors](https://forums.creativeclouddeveloper.com/t/results-of-perf-test-on-batchplay-get/11635), [forum thread on UXP HTML rendering performance](https://forums.creativeclouddeveloper.com/t/html-ui-rendering-performance-of-the-uxp-plug-in-on-windows-and-mac/6244) (UXP renders 10k elements in ~2s vs <1s in Chrome, 100k in ~2min; Windows measurably worse than Mac), and [Adobe community report of ~250ms per layer iteration](https://experienceleaguecommunities.adobe.com/t5/adobe-developer-questions/photoshop-uxp-layer-iteration/td-p/584460).

Related existing entry: ["Spectrum web-component shadow-DOM init cost"](backlog.md#spectrum-web-component-shadow-dom-init-cost) in `backlog.md` tracks the `sp-*` component side; this file tracks the IPC and re-render side. Each entry promotes into a numbered spec under `specs/` when work begins.

## DOM API layer walks pay one synchronous IPC call per property

**What:** [`adapt-document.ts`](../apps/photoshop/src/api/adapt-document.ts) walks the document recursively through the UXP DOM API: `doc.layers`, then per layer `.name`, `.visible`, `.bounds` (art layers), `.layers` (groups). Each getter is a synchronous blocking IPC call into the Photoshop process; `.bounds` is among the most expensive. A document with N layers costs hundreds of roundtrips per walk, and the walk runs on the UI thread (UXP has one JS thread for both panel rendering and scripting).

**Why it matters:** This is the dominant cost behind the reported Tags-panel lag. Every walk freezes the panel for its duration; when the thread unblocks, React commits all accumulated state changes at once, which reads as the list "rebuilding". The fix is the canonical community pattern: one `batchPlay` `multiGet` descriptor with `extendedReference` keys (`name`, `layerID`, `parentLayerID`, `itemIndex`, `group`, `visible`, `bounds`) and `count: -1` fetches every layer in a single IPC call; the tree is then rebuilt from the flat list in pure JS. Reported speedups for this conversion are in the 50x range.

**Scope sketch:** Replace the body of `adaptDocument` with a multiGet-backed reader returning the same `AdaptedDocument` shape, so `buildTagTreeReusing`, the planner, and all hooks stay untouched. Keep the duck-typed group detection rationale (the `group` / `layerSection` kind from multiGet replaces the `.layers`-presence check). Reconstruct parent/child nesting from `parentLayerID` + `itemIndex`. Surface `layerID` on the adapted layer for downstream use (stable React keys, unambiguous batchPlay selection - `ps-selection.ts` already resolves to `_id` but pays a DOM walk to find it).

**Trigger to revisit:** This is the first entry to promote when Tags-panel lag work is scheduled; the other entries below shrink in severity once this lands.

## Every document event triggers two full layer-tree adaptations plus an export dry-run

**What:** On each `version` bump from [`useDocumentChanges.ts`](../apps/photoshop/src/hooks/useDocumentChanges.ts) (any `select`/`make`/`delete`/`set`/`open`/`close` event, debounced 150ms), [`ProscenioTagsPanel.tsx:38-42`](../apps/photoshop/src/panels/ProscenioTagsPanel.tsx) runs `refreshDoc()` plus `preview.refresh(opts)`, and [`useTagTree.ts`](../apps/photoshop/src/hooks/useTagTree.ts) runs `syncOnce()`. `previewExport` ([`export-flow.ts:52`](../apps/photoshop/src/api/export-flow.ts)) calls `adaptDocument` and then `buildExportPlan` + ajv validation; `syncOnce` calls `adaptDocument` again via `readActiveLayerTree`. Net: clicking a layer name costs a modal batchPlay select, then two full IPC tree walks, a planner dry-run, and a schema validation, all synchronous on the UI thread.

**Why it matters:** The preview is consumed only by `RevealOutputSection`; it does not need to be recomputed eagerly inside the same synchronous burst that rebuilds the tag tree. Sharing one adaptation per tick halves the IPC cost of every event even before the multiGet conversion lands.

**Scope sketch:** Adapt the document once per version bump and feed both consumers (lift the adapted snapshot into the panel or a shared hook), or make the preview lazy (compute on expand of the reveal section, or defer it behind `requestAnimationFrame`/idle callback so the tree paint is not blocked by planner + ajv work).

**Trigger to revisit:** Together with the multiGet entry above, or independently if a quick win is wanted first - it is a pure hook-wiring change.

## The global busy flag defeats React.memo across the whole tag list

**What:** Every rename flips `busy` true and back ([`useTagTree.ts:95-110`](../apps/photoshop/src/hooks/useTagTree.ts)), and `busy` is a prop of every `TagRow`, so `tagRowEqual` ([`Row.tsx:204`](../apps/photoshop/src/panels/sections/tags/Row.tsx)) fails for all rows and the entire list re-renders twice per tag toggle. In UXP, re-rendered attribute changes (e.g. `disabled`) mutate native controls, which is far slower than in a browser.

**Why it matters:** Tag toggles (ignore/merge/kind/blend) are the panel's hottest interaction, and each one currently pays two full-list re-render passes on the slow UXP UI engine, on top of the IPC cascade from the entry above.

**Scope sketch:** Either scope busy-ness to the affected row (e.g. track the in-flight `layerPath` instead of a boolean), pass busy through context consumed only by the leaf controls, or drop the disable behavior entirely - renames resolve quickly and the rename queue already serializes through PS.

**Trigger to revisit:** Alongside any Tags-panel re-render work; cheap and self-contained.

## React keys derive from raw layer names, remounting subtrees on rename

**What:** [`TagsSection.tsx:81`](../apps/photoshop/src/panels/sections/TagsSection.tsx) keys each branch with `node.layerPath.join("/")`, where `layerPath` is the chain of raw PS names (brackets included). Renaming a layer - which every tag toggle does - changes the key of that node and of every descendant, so React unmounts and remounts the whole subtree, losing local state (the `expanded` details flag) and paying UXP native-control creation cost for every remounted row.

**Why it matters:** This is the literal "list torn down and rebuilt" the user sees on tag edits. The collapse-state mechanism already solved the same instability by keying on `displayPath` ([`collapse-key.ts`](../apps/photoshop/src/utils/collapse-key.ts)); React keys need the same treatment. The truly stable identity is the PS `layerID`, which the multiGet conversion surfaces for free (display names can also change on rename, so `displayPath` is only a partial fix).

**Scope sketch:** Key `TagNodeBranch` on `layerID` once available (interim: `displayPath` join, accepting the narrower display-rename remount). Audit `TagDetails` local-state reset logic afterwards - it currently leans on remount behavior via the `lastRawName` ref and should keep working under stable keys.

**Trigger to revisit:** Together with the multiGet entry (which provides `layerID`), or immediately in the interim `displayPath` form if rename UX comes up before then.

## Polling cadence runs full-tree IPC reads even when idle

**What:** [`useTagTree.ts:23-24`](../apps/photoshop/src/hooks/useTagTree.ts) polls a full `adaptDocument` walk every 1.5s while visible (4s hidden), and [`useActiveLayerPath.ts:15`](../apps/photoshop/src/hooks/useActiveLayerPath.ts) polls the selection chain every 300ms. Both exist as fallbacks for UXP builds where `addNotificationListener` never fires. Net effect today: the panel performs a full synchronous IPC tree walk every 1.5 seconds forever, even with no user activity.

**Why it matters:** Constant background jank floor, and on Windows (the primary dev platform here) the UXP engine is measurably slower, so poll ticks can visibly stutter interactions they overlap with.

**Scope sketch:** Keep the fallback but make it adaptive: detect at startup whether notifications actually fire (first event received disables or radically slows the poll), skip a poll tick when an event-driven sync ran within the interval, and after the multiGet conversion re-tune cadence against its much lower cost. The selection poll can also bail early via a single-property batchPlay get instead of walking the parent chain through DOM getters.

**Trigger to revisit:** After the multiGet conversion lands - re-measure first, since the poll may become cheap enough to keep as-is.

## Large documents render every row with no virtualization

**What:** The Tags panel mounts one row (two spans, two glyph toggles, two `<select>`s with options) per visible tree node, with collapsed groups pruning their children. There is no cap or virtualization; a fully expanded 500-layer PSD mounts thousands of UXP native controls.

**Why it matters:** UXP's UI engine degrades non-linearly with DOM size (forum measurements: 10k elements ~2s, 100k elements ~2min, vs sub-second in Chrome). 500+ layer documents are not a target for Proscenio but can occur; today such a document would make the panel unusable independent of the IPC fixes.

**Scope sketch:** Cheapest first: collapse all top-level groups by default on document open so the initial mount is shallow. Full fix: windowed rendering over the flattened visible-row list (the tree already flattens naturally since rows render as a flat sequence with indent padding, so a virtual list is structurally straightforward; UXP has no `react-window`-tested guarantee, so a hand-rolled scroll window over fixed-height rows is the safer route).

**Trigger to revisit:** First report of a painful real-world document after the IPC entries land, or before marketing the plugin for heavy production PSDs.
