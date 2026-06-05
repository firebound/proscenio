# Photoshop web-app layout - TODO

See [STUDY.md](STUDY.md) for the evaluation and decisions D1-D9 (re-layout to `api / lib / hooks / components / panels / utils`; pure logic = `lib/`, PS boundary = `api/`).

Each phase is one PR, behavior-preserving, proven by the Photoshop gate: `tsc --noEmit` + `vitest` + ESLint. Phases 1-2 are folder renames (touch every import but mechanical); 3-4 carry the absorbed cleanups; 5 records the change. Order matters: `lib/` and `api/` exist before the hooks and UI rewire against them.

## Decision lock-in

- [x] D1 - pure logic -> `lib/`.
- [x] D2 - single `api/` tier = `io/` + `adapters/` + the flow orchestrators.
- [x] D3 - UXP entry shim -> `src/entry.ts` (keep `@ts-nocheck`).
- [x] D4 - `components/` (reusable UI) + `panels/` (screens).
- [x] D5 - `util/` -> `utils/`; `collapseKey.ts` -> `collapse-key.ts`.
- [x] D6 - layer purity: hooks read PS only through `api/`.
- [x] D7 - absorb the audit cleanups into the move.
- [x] D8 - update the `code.md` "Layered direction" line.
- [x] D9 - leave `planner.ts` as-is (explicit non-action).

## Phase 1 - introduce `lib/`

- [ ] Rename `domain/` -> `lib/`; update every importer (mechanical).
- [ ] Extract the `EntryRef` match (reimplemented at `DebugSection.tsx:80`, `RevealOutputSection.tsx:70`, `ReexportSection.tsx`, `controllers/export-flow.ts:224`) into pure `lib/entry-match.ts`; rewire all four call sites.
- [ ] Lift the tag-value diff/validation from `panels/sections/tags/Details.tsx:53-127` into pure `lib/tag-form.ts`, reusing the `lib/tag-parser` validators; `Details.tsx` keeps form state + JSX only.
- [ ] Gate green.

## Phase 2 - introduce `api/`

- [ ] Move `io/*` into `api/`; update imports.
- [ ] Move `adapters/photoshop-layer.ts` -> `api/adapt-document.ts`; move `controllers/export-flow.ts` + `import-flow.ts` -> `api/`; update imports.
- [ ] Replace `api/png-writer.ts` `resolveLayer` with the shared `findLayerByPath` (also fixes the non-Array UXP-collection robustness gap).
- [ ] Delete the now-empty `adapters/` and `controllers/` folders (the entry shim moves in phase 4).
- [ ] Gate green.

## Phase 3 - hooks layer purity

- [ ] Add `api/active-document.ts` (`readDocSnapshot()`, `readActiveLayerTree()`) and `api/ps-notifications.ts` (event subscription); rewire `hooks/useTagTree.ts:121`, `useDocSnapshot.ts:46`, `useDocumentChanges.ts:89` to consume them instead of reading `app` / `action` from `"photoshop"` directly.
- [ ] Add `hooks/useLayerSelection.ts` for the frequent `selectLayerByPath` calls in `ValidateSection.tsx`, `Row.tsx`, `Details.tsx`, `MigrationSection.tsx`; rewire those sections through it.
- [ ] Drop the unused read API from `api/xmp.ts` (`isXmpAvailable`, `XmpUnavailableError`, `readLayerTagsFromXmp`).
- [ ] Gate green.

## Phase 4 - UI, utils, entry shim

- [ ] Move `panels/common/*` (`Accordion`, `KeyValueRow`) -> `components/`; update imports.
- [ ] Move `controllers/PanelController.tsx` -> `src/entry.ts` (keep the `@ts-nocheck` UXP-compat exception); update the entry wiring in `index.tsx`.
- [ ] Rename `util/` -> `utils/` and `collapseKey.ts` -> `collapse-key.ts`; update imports.
- [ ] Remove the domain re-export at `panels/sections/TagsSection.tsx:139`; import `writeLayerName` from `lib/tag-writer` at the call/test site.
- [ ] Fix the stale "v1" comment in `api/manifest-writer.ts:1-3` (emits v2).
- [ ] Gate green.

## Phase 5 - record the change

- [ ] Update [`../../.ai/conventions/code.md`](../../.ai/conventions/code.md) "TypeScript (Photoshop UXP plugin)": the "Layered direction" line becomes `panels -> hooks -> api + lib` (components leaf UI, utils leaf helpers); restate the purity rule (`lib/` no UXP, `api/` the only boundary).
- [ ] Mirror the re-layout into [`../decisions.md`](../decisions.md) as a per-feature decision (call, rationale, revisit trigger), referencing the UXP-has-no-canonical-architecture rationale.

## Out of scope

No behavior change, no schema or `format_version` bump. `schema_bindings/` and `types/` untouched. No feature-folder reorg (layout stays layer-based). Godot and docs are spec 017; Blender is spec 016.
