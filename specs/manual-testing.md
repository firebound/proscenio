# Manual testing checklist

Items that are technically implemented or treated but await a manual GUI / visual validation that headless CI cannot run. Each carries the fix that shipped and the smoke step that closes it: pass it in a GUI session, then check it off and drop it. Populated 2026-06-12 from the backlog reconciliation - the rule is that a treated issue whose only remaining work is manual validation lives here, not in the backlog files. Still-broken or never-started issues stay in the backlogs; this file is exclusively "done, needs a human to confirm". Run it before cutting a release tag - a failure here is a new blocking bug.

## Retests - fix shipped, GUI smoke pending

### [ ] ps-export-resilience - one bad layer no longer blocks the whole manifest export

Fix shipped in PR #115 (spec 041): per-layer try/catch in `runWrites` + partial manifest in `runExport`, unit-tested against a real `duplicate` rejection asserting the written manifest excludes the failed entry. Happy path GUI-confirmed 2026-06-13 (`doll_tagged.psd` exported 22 entries); the partial path is the remaining smoke.

Validate: Proscenio Exporter on `examples/authored/doll/02_photoshop_setup/debug/doll_tagged_debug.psd`. Force one layer to fail (a layer the UXP duplicate/saveAs rejects), then Export manifest + PNGs. Expect a `partial` result naming the failed layer + reason, the manifest written with the entries that landed (the failed one absent), and the good PNGs on disk.

### [ ] ps-tag-writes-in-renamed-group - tag edits target by layerID, survive a renamed parent group

Fix shipped in PR #115 (spec 041): the `object null is not iterable` crash hardened at every PS-API null boundary, and tag-write targets resolve by `findLayerById` (node.id threaded through all five Row handlers - ignore / merge / kind / blend / advanced). The null-crash + flat-layer tag writes were GUI-confirmed 2026-06-13; the renamed-group path is the remaining smoke. This closes the tag-edit half of finding F-24; the click-to-select + legacy-migration paths still resolve by name (tracked in the spec 040 findings).

Validate: Proscenio Tags on `debug/doll_tagged_debug.psd`. Group two layers, rename the group, then on a child run each of the five controls (X / M / kind / blend / `+` Apply). Expect every edit to apply with no `no match at depth 0` warning and no stale-path miss. With the Debug panel log level at `trace`, a null collection surfaces as `[proscenio:layer-find] normalized null .layers to []`.

### [ ] slot-transform-keys - validator detects transform keys on slot attachments

Fix shipped in #104 (a shared `action_fcurves` reader wired through `active_slot.py` + `export.py`; unit-tested against layered-action mocks).

Validate: `slot_swap` workbench. Select `club` (child of the `weapon` slot). Insert a Location keyframe. Run Validate from the Export panel. Expect a warning that the slot attachment carries transform keyframes the runtime swap will ignore. The original GUI failure predated the check and was never explained, so this confirms the layered-action path actually fires on a real 5.1.1 action.

### [ ] automesh-interactive-extend-cut - Stage 2 extend / cut works

Fix shipped in #106 (`outer_splice.py` crossing-anchored splice + hardened tests; the old nearest-vertex splice silently amputated the silhouette).

Validate: `examples/generated/automesh/automesh.blend`. Select `hand`, open Mesh Generation > Author Mesh (interactive), advance to Stage 2.

- (1.23 T1) modal enters at the OUTER stage; the cyan silhouette overlay + status pill render.
- (1.25 T6) the toggle pen extends / cuts in Stage 2; the cut overlay reads red.
- (1.25 T9) after an extend edit, the green spliced-outer overlay shows the silhouette APPLY will build, updating on commit / undo / delete.

### [ ] skeleton-row-click-select - row click selects the bone

Fix shipped in `dcd08f6` (`selection.py` select-bone-by-name wired per-row in `skeleton.py`).

Validate: doll workbench > Pose Mode > deselect all (`Alt+A`) > Proscenio > Skeleton > click a bone row in the UIList. Expect that bone selected and active in the viewport (the pose-bone selection syncs).

### [ ] pose-save-library-precheck - actionable error without a writable library

Fix shipped in `7d10f69` (writable-library pre-check + actionable error + `asset_library_reference`, `pose_library.py:68-88`).

Validate: doll workbench > Pose Mode > pose > Skeleton > Save Pose to Library.

- (a) With NO writable asset library configured: expect an actionable error naming Preferences > File Paths > Asset Libraries, not the raw "Unexpected library type".
- (b) With a writable library configured: the pose asset saves to it.

### [ ] waist-1px-drift - re-measure through the UXP path

Treated: the JSX reader is retired; the UXP png-writer trims via `Document.trim(TRANSPARENT)`, a different bbox engine than the JSX `layer.bounds` the -1px drift was logged against (Blender manifest `255x173` vs JSX-era `255x172`).

Validate: re-measure the `waist` element size on the doll roundtrip through the UXP exporter. On a persisting drift, align rounding (round-half-up on both sides) or re-document the waiver with the fresh number; on a match, close it. Known waiver alongside PPU=100.

## In-editor visual smoke - shipped spec, layout confirmation pending

### [ ] spec-022 13-panel restructure

Shipped and headless-verified (operator suite green at 50, addon registers headless), but headless cannot render panels.

Validate at a GUI Blender: the sibling-panel tree (nothing nested under the version line), the accordion subpanels collapsing independently, the warn-not-hide hints, the per-header badge + `?`, and the `debug_mode` preference showing / hiding Diagnostics + the Debug Pipeline subpanel. A layout regression found here is a new bug.

## Cross-app roundtrip (B5)

### [ ] doll full pipeline + slot fixtures

The complete-flow release bar. Validate end to end: the doll PS -> Blender -> Godot pipeline, plus `slot_swap` and `slot_cycle`, exercising the shipped appearance fields (modulate / z_index / flip). Known waivers re-measured here: the waist 1px drift (above) and PPU=100.

## Upstream watch - defensive guard shipped

### [ ] qa-gizmo-crash - watch for recurrence

Defensive mitigation shipped: the `on_depsgraph_update` handler (`_handlers.py`) is wrapped in a blanket `try/except`, so a depsgraph-callback exception cannot leave the C side mid-state during a subsequent draw. The crash (`gizmo_button2d_draw`, stack 100% Blender / AMD internals, `imm_draw_circle_fill_3d` which our `LINE_LOOP` overlays never call) is upstream and was not reproduced on retry.

Validate: re-run the snap-cursor / Quick Armature viewport flow across sessions. If it crashes 2x or more in different sessions, file a Blender bug report with the captured stack trace.
