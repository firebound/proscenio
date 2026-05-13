# SPEC 011 - TODO

Photoshop tag system + plugin UI mini-app. See [STUDY.md](STUDY.md) for the locked decisions and tag taxonomy.

**Sequencing**: this SPEC starts after SPEC 010 Wave 10.7 (JSX retirement). Until 10.7 ships, the UXP exporter is in parity-mirror mode against the JSX baseline; tags break that oracle.

## Decisions to lock

- [x] D1 - bracket-tag inline syntax as primary format (Spine-style).
- [x] D2 - XMP per-layer as secondary canonical store; bracket-tag wins on conflict.
- [x] D3 - drop the `_<name>` skip convention; `[ignore]` replaces it.
- [x] D4 - drop the `<base>_<index>` flat-aggregation fallback for sprite_frame.
- [x] D5 - v1 tag taxonomy: `[ignore]`, `[merge]`, `[folder:name]`, `[polygon]`, `[sprite]`, `[spritesheet]`, `[mesh]`, `[origin]`, `[origin:x,y]`, `[scale:n]`, `[blend:mode]`, `[path:name]`, `[name:pre*suf]`. Plus a panel-level filename template setting (per-export, no per-layer override needed - layer-level override is `[path:name]`).
- [x] D6 - document-level: PSD guides set anchor. Layer color labels NOT a tagging channel in v1 (see D12).
- [x] D7 - schema bump to v2 with `anchor`, `origin`, `blend_mode`, `subfolder`, `is_mesh` fields, `kind: "mesh"` superset.
- [x] D8 - panel grows Tags / Validate / Export tabs.
- [x] D9 - tag authoring: bracket tags in name OR click in panel; both kept in sync; bracket wins on conflict.
- [x] D10 - mini-app stays single React panel, no new deps.
- [x] D11 - tag spelling locked at `[spritesheet]` (artist-recognised term; parser does a one-line lookup to translate to `kind: "sprite_frame"` at emit time).
- [x] D12 - color labels dropped as a tagging channel. Bracket tag + XMP mirror are the single source of truth; color labels may resurface as a passive badge in a later SPEC but never set semantics here.
- [x] D13 - validator severity locked at warn-never-block.
- [x] D14 - XMP support floor resolved by SPEC 010 Wave 10.7 PS minimum bump to PS 25 / CC 2024+; `uxp.xmp` ships there, no fallback needed.

## Pre-implementation

- [ ] Confirm `uxp.xmp` import works against the target PS version. Smoke test reading + writing a custom-namespace property on one layer.
- [ ] Confirm `action.addNotificationListener` event names that matter for the tree refresh (`select`, `make`, `delete`, `set`).
- [ ] Inventory existing fixtures (doll, simple_psd, blink_eyes, mouth_drive) for tags they would acquire under the new taxonomy. Each fixture's `01_to_photoshop/*.photoshop_manifest.json` becomes the migration baseline.

## Wave 11.1 - bracket tag parser + schema v2

- [x] Bracket-tag parser at `apps/photoshop/src/domain/tag-parser.ts`. Lexes `[tag]` / `[tag:value]` tokens from layer / group names; returns stripped display name + tag bag. Unknown brackets pass through.
- [x] Planner consumes the tag bag: `[ignore]`, `[spritesheet]`, `[polygon]` / `[sprite]` / `[mesh]`, `[folder:name]`, `[path:name]`, `[scale:n]`, `[blend:mode]`, `[origin:x,y]`, `[origin]` marker layer. `[merge]` and `[name:pre*suf]` parsed but not yet wired (deferred to follow-up waves; the parser tolerates them).
- [x] Dropped the legacy `_<name>` skip path AND the `<base>_<index>` flat-aggregation pass.
- [x] Schema bumped to v2 at `schemas/psd_manifest.schema.json`. New fields: top-level `anchor`; per-entry `origin`, `blend_mode`, `subfolder`; `kind` accepts `"mesh"`.
- [x] TypeScript types in `src/domain/manifest.ts` and the ajv validator updated. Blender-side `apps/blender/core/psd_manifest.py` parser bumped to accept v2 (`anchor`, `origin`, `blend_mode`, `subfolder`, `kind: "mesh"`); the importer's downstream semantics still need wiring (Wave 11.7).
- [x] Existing fixtures bumped to `format_version: 2` (additive change; the v1 shape is a strict subset of v2).
- [x] Unit tests: 18 cases on the tag parser, 12 cases on the planner against synthetic Layer trees, 4 ajv contract cases. All v2.

## Wave 11.2 - origin / pivot semantics

- [x] `[origin]` marker layer inside a sprite_frame OR `[merge]` group: planner skips its PNG output and records the marker's bbox-center as the entry's `origin`.
- [x] `[origin:x,y]` on the layer / group itself: planner reads the explicit coords, no marker needed; wins over an inner marker.
- [x] Document-level anchor from PSD guides: adapter reads `doc.guides`, picks first vertical + first horizontal, surfaces as `anchor` at the manifest root.
- [x] Blender importer companion: armature object placed at the manifest `anchor` (world-space conversion in `_anchor_world`); per-entry `origin` becomes the mesh's `Object.location` with a baked geometry offset so the visible texture stays where the bbox says.
- [ ] Fixture: a small PSD with one `[origin]` marker layer per body part, golden-diffed against the manifest the importer expects. (Deferred to a follow-up; the smoke test against the user's doll PSD covers the planner + writer paths.)

## Wave 11.3 - tags UI mini-app (Tags tab)

- [ ] React tree component listing the active document's layer hierarchy. Lazy-render below 100 visible nodes; virtualise above.
- [ ] Row per layer: thumbnail, name (bracket tags as badges), kind override dropdown, `[ignore]` checkbox, `[merge]` checkbox.
- [ ] "Set origin from selection" button: reads `app.activeDocument.selection` bounds, writes `[origin:x,y]` on the active layer.
- [ ] Subscribe to `action.addNotificationListener` for `select`, `make`, `delete`, `set`; refresh affected sub-tree only.
- [ ] Writing a tag from the UI: edit both the layer name AND the XMP record under `proscenio:v1`. Read path: XMP first, name fallback.

## Wave 11.4 - Validate tab

- [ ] Pre-export validator runs the planner with a `dryRun: true` flag that collects warnings instead of writing.
- [ ] Warning categories: duplicate names after sanitize, sprite_frame index gaps, sprite_frame mixed conventions, `[origin]` outside a polygon, empty bbox layers, `[scale:n]` paired with sub-pixel bounds, `[folder]` collision, conflicting tags on same layer.
- [ ] Each warning row clickable -> selects the offending layer in PS via batchPlay.
- [ ] Validate tab runs continuously when the panel is visible (refreshed on the same notifications as Tags), so warnings update live.

## Wave 11.5 - Reveal-output helper + filename template

- [ ] In the Export tab, after a layer is selected in PS, show:
  - The manifest entry that would be emitted (kind, name, path, position, size, origin).
  - The output PNG path on disk under the current chosen folder.
- [ ] Quick "Re-export this layer only" path that runs the modal flow against a single entry (debugging aid; not part of the canonical export).
- [ ] Filename template setting (F6). Persist in `localStorage` per plugin. Tokens: `{name}`, `{group}`, `{layer}`, `{kind}`, `{index}`. Default: `{name}.png` polygons / `{name}/{index}.png` sprite_frame frames (matches SPEC 010 layout). Reveal-output preview updates live as the template changes.

## Wave 11.6 - XMP polish + legacy migration

- [ ] XMP write path: surface a clear error if `uxp.xmp` is unavailable (PS < 25 / CC 2024). The plugin's `host.minVersion` already enforces 25.0, so this is a defensive guard, not a fallback mode.
- [ ] Migration helper: "Convert `_` prefixes to `[ignore]`" button in the Tags tab. One-shot rewrite of all layer names with `_` prefix to `[ignore]` + strip the prefix.

## Wave 11.7 - Blender importer companion

- [ ] Importer reads `format_version: 2`; falls back to existing v1 path otherwise.
- [ ] Read `anchor`, per-entry `origin`, `blend_mode`, `subfolder`, `is_mesh`. Translate:
  - `anchor` -> root bone position.
  - `origin` -> mesh `Object.location`; otherwise bbox center.
  - `blend_mode` -> material blend mode (`alpha_blend`, `additive`, `multiply`, `screen`).
  - `is_mesh` -> tag the mesh's PropertyGroup for downstream SPEC 002 / 008 work; no actual deformation yet.
- [ ] Fixture: doll PSD with `[origin]` markers + guide-defined anchor; goldens regenerated.

## Wave 11.8 - Documentation + parity oracle

- [ ] Update [`docs/PHOTOSHOP-WORKFLOW.md`](../../docs/PHOTOSHOP-WORKFLOW.md): tag table replaces the underscore-prefix section.
- [ ] Update [`.ai/skills/photoshop-uxp-dev.md`](../../.ai/skills/photoshop-uxp-dev.md) with the tag parser internals + XMP namespace.
- [ ] Add a new fixture `examples/authored/doll_tagged/` (or extend the existing doll) that exercises every tag in the v1 taxonomy. Becomes the SPEC 011 parity oracle.
- [ ] Re-run the SPEC 010 doll-roundtrip oracle once schema v2 ships; verify the v1 baseline still validates against the legacy importer path.

## Additional work surfaced during implementation

Items discovered while building the Tags / Validate / Export UI that
were not in the original TODO but landed (or were registered) along
the way.

### Done outside the original scope

- **Logger module** ([`apps/photoshop/src/util/log.ts`](../../apps/photoshop/src/util/log.ts)) with 6 levels (trace/debug/info/warn/error/off), localStorage persistence, cross-panel sync via 500ms cache, and `window.proscenio.setLogLevel` debug surface. Added because the UXP DevTools console is the only debugger available and we needed gated tracing.
- **Polling fallback** for UXP builds where `action.addNotificationListener` returns `void` (no teardown handle, no events). Implemented for `useDocumentChanges`, `useActiveLayerPath` (300ms), `useTagTree` (1.5s). Bails when `document.hidden` is true so background panels do not burn cycles.
- **Structural reuse** in `buildTagTreeReusing` to keep `TagTreeNode` references stable across polls when nothing changed. Drives `React.memo` short-circuit on `prev.node === next.node` (single pointer compare instead of structural walk). Fast path also skips `parseLayerName` regex when the row is being reused.
- **Pixels-per-unit UI control** in the Export tab (with persisted value + live "Canvas height = N units" hint). Out of scope of the SPEC but the manifest field exists and downstream needs a way to set it without code edits.
- **Legacy migration helper** ([`apps/photoshop/src/domain/legacy-migration.ts`](../../apps/photoshop/src/domain/legacy-migration.ts)) for Wave 11.6's `_<name>` -> `[ignore]` rewrite. Pure planner + UXP applier separated; the planner has unit tests.
- **Shared layer-find helper** ([`apps/photoshop/src/io/_layer-find.ts`](../../apps/photoshop/src/io/_layer-find.ts)) used by both `layer-rename` and `legacy-migration` (was duplicated).
- **Shared `elementsEqual<T>`** in [`apps/photoshop/src/util/arrays.ts`](../../apps/photoshop/src/util/arrays.ts) (was duplicated four ways across hooks and section components).

### Still open

- [ ] `log.trace` in `_layer-find` serialises `liveAtDepth` to JSON on every miss (debug spam at trace level). Acceptable while debugging; trim before merge if signal-to-noise becomes a problem.
- [ ] Blender importer places meshes with a consistent ~3 px Z-offset vs the manifest's `position + size/2` centre. Suspected off-by-one in the importer's bbox -> world transform. Cosmetic (0.17% on a 1731 px doc) but worth tracing in Wave 11.7.
- [ ] `useTagTree` polls every 1.5 s even when the panel is focused but idle. Could drop to 3-5 s in idle state; not urgent on the doll-sized PSD.
- [ ] Spectrum web components (`sp-action-button`, `sp-textfield`) carry shadow-DOM init cost on mount. Acceptable today (panels are not interaction-heavy); revisit if larger PSDs surface lag.

## Risks

- **XMP API stability**. `uxp.xmp` is relatively new and may differ between PS minor versions. Mitigation: feature-detect; degrade gracefully to bracket-tag-only.
- **Live tree performance on huge PSDs**. Some character PSDs run 200+ layers. Mitigation: virtualise the list, only attach event listeners while the panel is visible, lazy-load thumbnails.
- **Bracket-tag collisions with artist naming**. Some artists already use `[Final]` or `[OLD]` in layer names. The parser must accept only the locked tag vocabulary; unknown brackets pass through as part of the display name. Test: a layer named `arm [OLD]` is treated as `arm [OLD]`, not `arm` with an unknown `[OLD]` tag.
- **Schema v2 fixture churn**. Every fixture's `*.photoshop_manifest.json` may shift slightly when the importer starts writing `format_version: 2`. Plan: regenerate all goldens in one PR, diff carefully.
- **Tag <-> XMP sync drift**. If a layer name changes outside the plugin, the XMP may go stale. Mitigation: on every refresh, the plugin reconciles XMP from name (name wins). The reverse direction (XMP wins) is never invoked.
