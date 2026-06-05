# Photoshop UXP: web-app layout (api / lib / hooks / components / panels / utils)

Status: **decisions locked, ready for TODO**. Re-layout of `apps/photoshop/src/` from the current seven-folder layering to a conventional web-app structure, treating the Photoshop API as "the backend". The Blender system reorg is [spec 016](../016-blender-app-system-organization/STUDY.md); the Godot and docs cleanups are [spec 017](../017-app-cleanups/STUDY.md). The Photoshop cleanup findings from the audit are absorbed into this move rather than done separately.

## Problem

The audit found `apps/photoshop/src/` layered cleanly (`domain/` is genuinely pure, the boundaries are real) but the layering is heavier than a UXP plugin needs and three of the seven folders are thin or misnamed:

- `adapters/` holds one file (`photoshop-layer.adaptDocument`, which reads the live document into a pure `Layer[]`). It touches the Photoshop API exactly as `io/` does - the `adapters` versus `io` split is theoretical for a single file.
- `controllers/` uses an MVC term for what are really flows / use-cases (`export-flow`, `import-flow`), and also holds `PanelController.tsx`, the UXP `entrypoints.setup` host shim - an unrelated concern the audit flagged as living in the wrong layer.
- `domain/` is the disliked name for the pure-logic tier even though the tier itself is the most valuable thing in the tree.

UXP has no canonical architecture - Adobe's samples and the common boilerplates (Bolt-UXP and similar) are flat: components plus a thin wrapper over the `photoshop` / `uxp` modules. The current structure is a domain-driven layering imposed on top, justified by real domain logic (the tag system, the export planner, manifest shapes) but carrying two near-empty folders and an overloaded "controller" word. The maintainer wants a layout that reads like a normal web app while keeping the one boundary that earns its keep: pure, framework-agnostic logic that tests in vitest without UXP.

## What we want

A web-app-idiomatic structure where every folder name is one a web developer recognizes, the Photoshop API is treated as the backend behind a single `api/` tier, and the pure logic keeps its own home (so it stays testable in isolation). Fewer, clearer layers; no `domain/`, `io/`, `adapters/`, or `controllers/`.

## Design space

### Axis A - pure-logic home (the tier formerly `domain/`)

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **A1.** `lib/` | Web-app idiom for framework-agnostic logic; pairs naturally with `api/` + `hooks/` + `components/`; signals "pure, no side-effects, testable" | A rename touching every importer | **Lock.** |
| **A2.** `core/` | Also common in web apps | `apps/blender` already uses `core/` for a different meaning (the bpy-free tier); cross-app confusion | Reject. |
| **A3.** keep `domain/` | No rename | The disliked status quo; "domain" reads heavier than the rest of the web-app vocabulary | Reject. |

### Axis B - Photoshop-boundary consolidation

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **B1.** One `api/` tier = `io/` + `adapters/` + the flow orchestrators | "The backend" reads as one thing; kills the thin `adapters` folder and the overloaded `controllers` word; every PS-touching module lives in one place | `api/` becomes the largest folder | **Lock.** |
| **B2.** Keep `io/` / `adapters/` / `controllers/` separate | Preserves the current fine-grained tiers | The split is thin (adapters = 1 file) and the names are exactly what feels "weird" | Reject. |

### Axis C - UXP entry shim home (formerly `controllers/PanelController.tsx`)

`src/entry.ts` at the source root (the web-app "bootstrap / main" idiom) versus burying it in `api/`. **Lock `src/entry.ts`**: it is the `entrypoints.setup` wiring, the app bootstrap, not a backend call. Keep its documented `@ts-nocheck` exception (forced by the UXP host shape).

## Target layout

```text
src/
  api/         "the backend" - everything that touches the Photoshop / UXP API
               manifest-reader/validator/writer, png-writer/placer, layer-find/rename,
               ps-selection*, folder-storage, xmp, legacy-migration (applier),
               adapt-document (was adapters/photoshop-layer), export-flow, import-flow (was controllers/),
               active-document + ps-notifications (NEW - raw reads pulled out of hooks)
  lib/         pure logic, ZERO UXP import, tests in vitest (was domain/)
               planner, tag-parser, tag-writer, tag-tree, manifest, layer, legacy-migration (planner),
               entry-match (NEW), tag-form (NEW)
  hooks/       React state - useExportFlow, useImportFlow, useTagTree, useDocSnapshot, ...
               + useLayerSelection (NEW)
  components/  reusable UI - Accordion, KeyValueRow (was panels/common/)
  panels/      the screens - ProscenioExporter/Tags/Validate/Debug + sections/ (incl. sections/tags/)
  utils/       generic helpers - arrays, log, collapse-key (was util/, collapseKey renamed)
  schema_bindings/   AUTO-GENERATED (untouched)
  types/             vendored .d.ts (untouched)
  index.tsx
  entry.ts     UXP entrypoints.setup shim (was controllers/PanelController.tsx)
```

### Current to target mapping

| Today | Target |
| --- | --- |
| `domain/*` | `lib/*` |
| `io/*` | `api/*` |
| `adapters/photoshop-layer.ts` | `api/adapt-document.ts` |
| `controllers/export-flow.ts`, `import-flow.ts` | `api/export-flow.ts`, `api/import-flow.ts` |
| `controllers/PanelController.tsx` | `src/entry.ts` |
| `panels/common/*` | `components/*` |
| `panels/Proscenio*.tsx`, `panels/sections/**` | `panels/*` (unchanged within) |
| `util/*` (`collapseKey.ts`) | `utils/*` (`collapse-key.ts`) |
| `hooks/*`, `index.tsx`, `schema_bindings/*`, `types/*` | unchanged |

## Decisions (locked)

- **D1 (Axis A).** Pure logic lives in `lib/` (framework-agnostic, no UXP import, vitest-testable).
- **D2 (Axis B).** A single `api/` tier holds every Photoshop / UXP touch: the former `io/`, the `adaptDocument` adapter, and the `export-flow` / `import-flow` orchestrators.
- **D3 (Axis C).** The UXP entry shim is `src/entry.ts`; the `@ts-nocheck` exception stays.
- **D4.** UI splits into `components/` (reusable primitives, was `panels/common/`) and `panels/` (the screens). Panel-specific section UI stays under `panels/sections/`.
- **D5.** `util/` becomes `utils/`; `collapseKey.ts` becomes `collapse-key.ts` (kebab-case module per layout.md).
- **D6 (layer purity).** `lib/` imports no UXP. `api/` is the only Photoshop boundary. Hooks read PS only through `api/` - the three hooks reading `app.activeDocument` / events directly (`useTagTree`, `useDocSnapshot`, `useDocumentChanges`) go through new `api/active-document.ts` + `api/ps-notifications.ts`; section selection calls go through a new `useLayerSelection` hook.
- **D7 (absorbed audit cleanups).** Land as part of the move: extract the 4-times-duplicated `EntryRef` match into `lib/entry-match.ts`; lift the tag-value validation out of `panels/sections/tags/Details.tsx` into `lib/tag-form.ts` (reusing the parser validators); replace `png-writer`'s `resolveLayer` with the shared `findLayerByPath`; drop the unused `xmp` read API; remove the domain re-export at `TagsSection.tsx`; fix the stale "v1" comment in `manifest-writer`.
- **D8 (convention update).** Update the `code.md` "Layered direction" line from `panels -> hooks/controllers -> domain + io -> adapters` to `panels -> hooks -> api + lib` (components are leaf UI; utils are leaf helpers).
- **D9 (explicit non-action).** Leave `planner.ts` (754 LOC) as-is - cohesive and well-decomposed, not a god-object; it moves to `lib/` unchanged.

## Open questions

None blocking. The `api/` versus `lib/` split preserves the exact pure-vs-side-effect boundary the audit validated; only the names and the thin-folder consolidation change.

## Non-goals

- No behavior change, no schema or `format_version` bump - a re-layout proven by `vitest` + `tsc`.
- `schema_bindings/` (auto-generated) and `types/` (vendored) are untouched.
- No feature-folder / vertical-slice reorg - the layout stays layer-based, matching the maintainer's `components / api / hooks / panels / utils` mental model.
- Godot and docs are spec 017; Blender is spec 016.

## Related

- [`../../.ai/conventions/code.md`](../../.ai/conventions/code.md): the "TypeScript (Photoshop UXP plugin)" layering rules this updates (D8).
- [`../../.ai/conventions/layout.md`](../../.ai/conventions/layout.md): file naming (`kebab-case.ts`).
- [`../decisions.md`](../decisions.md): the Photoshop UXP migration and tag-system entries this layout touches.
