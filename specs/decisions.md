# Decisions

Architectural and per-feature decisions that are locked. ADR-light: each entry records the call, the rationale, and the trigger that would force a revisit.

The rolling backlog of open work lives in [`backlog.md`](backlog.md); this file is the consolidated home for locked decisions. It carries the cross-cutting architectural calls plus the per-feature studies made while building each feature. The hand-written planning docs that once held this rationale were discarded once their features shipped, so every decision worth keeping was mirrored back here - this file, not a spec folder, is now the record.

## Core architecture

| Decision | Rationale | Revisit trigger |
| --- | --- | --- |
| **No GDExtension, no native runtime** | Plugin is GDScript-only. Generated `.scn` uses native nodes; runs on plain Godot 4 with the plugin uninstalled. | Deep Firebound integration, perf ceiling on `Polygon2D` skinning, live-link Blender ↔ Godot, binary `.proscenio`, in-Godot authoring round-trip. |
| **Conversion one-time, at editor import** | Heavy work runs at import time. Runtime uses Godot core (already C++); no GDScript performance ceiling. | Same triggers as the GDExtension entry. |
| **Strong typing everywhere** | GDScript 2.0 typed (`untyped_declaration=2` error), Python `mypy --strict`, TypeScript `strict`. Catches errors before runtime. | None. Baseline rule. |
| **Schemas are the contract** | Any change to a cross-component shape requires a `format_version` bump on the affected schema plus a migration path. CI validates fixtures against the schemas. | None. Bumps are how the schemas evolve; bumps are not breakage. |
| **Storage split by field intent** (revised) | Original call mirrored every PropertyGroup field to a raw Custom Property and read PropertyGroup-first / CP-fallback. Revised: editor-time-only fields are PropertyGroup-canonical; animatable / driver-target fields (`frame`, slot index) are Custom-Property-canonical, since Blender cannot keyframe a field nested in a PropertyGroup. The split is locked but not yet implemented - current code still mirrors uniformly. | Implement before 1.0.0, so the public surface ships the final storage contract. Plan in [`backlog.md`](backlog.md), "Split PropertyGroup vs Custom Property storage by intent". |
| **Wrapper-scene pattern for Godot reimport** | The importer overwrites `.scn` on every reimport; the user-authored wrapper `.tscn` survives intact and carries scripts and extras. | Marker-based merge stays deferred unless concrete demand emerges. |
| **One component per PR** | Photoshop, Blender, and Godot ship independent PRs. Schema bumps cross all components by definition. | None. |
| **C# / GDExtension as documented escape hatch, not active option** | Maintainer prefers strong typing over GDScript's dynamism, but stays in GDScript for plugin reach in the broader 2D community. Firebound itself stays C#. | Same as the GDExtension entry. |
| **`apps/` + `packages/` + `scripts/` split** | `apps/` holds distributable bundles (Blender, Photoshop, Godot). `packages/` holds shared building blocks consumed by apps (pydantic models, codegen CLI, fixtures, validator). `scripts/` shrinks to one-off dev tools. uv workspaces declares the Python package set at the repo root. See the monorepo packages spec. | Adding a second TypeScript package (would warrant a root-level pnpm workspace alongside the uv workspace). |
| **Codegen artifacts land in per-app `schema_bindings/` folders** | TypeScript interfaces in `apps/photoshop/src/schema_bindings/`, GDScript Resources in `apps/godot/addons/proscenio/schema_bindings/`. JSON Schema dumped to `packages/models/schemas/` next to the pydantic models that produced it. Each generated file carries an `AUTO-GENERATED` header; committed-match tests under `tests/codegen/` reproduce the JSON Schema, TypeScript, and GDScript artifacts from the models and fail on drift (the docs Markdown is regenerable but ungated, as it depends on an npx tool). See the typed-models codegen spec. | Switching the per-app binding folder to a different name; switching JSON Schema location away from `packages/models/schemas/`. |

## Validation gates

Layered defenses, cheapest first:

1. **Editor / IDE.** Live diagnostics through each language's standard extensions (Pylance for Python, gdtoolkit for GDScript, TypeScript LSP for TS), plus a shared spell-checker.
2. **Pre-commit.** Per-language formatters and linters, schema validation against staged JSON files, spell-checker.
3. **CI - Python.** `ruff` + `mypy --strict` + pytest against the Blender addon's typed surface.
4. **CI - TypeScript.** `tsc --noEmit` + `vitest` against the Photoshop plugin.
5. **CI - GDScript.** `gdformat --check` + `gdlint` against the Godot plugin.
6. **CI - schemas.** Every fixture under `examples/` and per-app `tests/fixtures/` is validated against the cross-component schemas.

The schemas themselves are enforced at four points: producer output (writer / exporter validates before any test diff), consumer input (runtime check on the Photoshop side, format-version guard on the Godot side), CI fixture validation, and the migration path on any future version bump.

## MVP decisions and studies

The deliberate decisions and studies made while building the MVP, one section per feature - the calls that crossed component boundaries or shaped a contract. Every feature here has shipped (a few still carry a follow-up decision not yet implemented); the hand-written planning doc was retired once the work landed, so the rationale worth keeping lives here rather than in a spec folder.

### Animation tracks

- **Tracks ship resolved values, not rest+delta.** Exporter resolves into absolute positions, rotations, scales; the importer just reads. Simpler consumer side; the cost is bigger animation payloads.

### Reimport-merge

- **Full overwrite + wrapper-scene pattern chosen over marker-based merge.** Marker-based merge would lose user-attached scripts on a bone rename (no stable IDs in the schema) and duplicate code paths. Deferred unless concrete pain surfaces that the wrapper pattern genuinely cannot serve.

### Spritesheet Sprite2D discriminator

- **`type` discriminator additive in the schema, not a `format_version` bump.** The `sprite_frame` variant lives alongside `polygon` under a `type` field that defaults to `"polygon"` when omitted - keeps pre-discriminator fixtures backwards-compatible.

### Skinning weights export

- **Skinned polygons parent to `Skeleton2D`, not to a single bone.** Weights drive vertex deformation; rigid sprites remain bone-parented. The two parenting strategies coexist by design.
- **Validation is user-driven (paint weights, observe deformation).** No programmable check covers visual quality.

### Slot system

- **Hard cut, NEAREST interpolation on `slot_attachment` tracks.** Smooth crossfade is a future extension.
- **Sprites stay in the top-level `sprites[]` array.** `slots[].attachments[]` is a list of names; the importer cross-references. The schema stays flat - no `slot:` field on `Sprite`.
- **Slot system fits inside `format_version=1`.** `slots[]` and the `slot_attachment` track type were already part of v1 - no bump.
- **Slot is kind-agnostic.** `polygon` meshes and `sprite_frame` attachments compose freely inside the same slot.

### Blender authoring panel

- **Storage split by field intent (revised).** The first cut mirrored every PropertyGroup field to a raw Custom Property and read PropertyGroup-first / CP-fallback. That uniform mirror proved over-broad: editor-only fields need no CP, while animatable / driver-target fields (`frame`, slot index) must be CP-canonical because Blender cannot keyframe a field nested in a PropertyGroup. The split-by-intent contract is locked; implementation is deferred to before 1.0.0 (see [`backlog.md`](backlog.md)).
- **Validation lazy + inline.** Lazy via the **Validate** button (heavy walk over the scene); inline status badges per subpanel are O(1) checks per redraw.

### Photoshop to Blender importer

- **The Blender side reads the manifest, never the PSD.** Direct `.psd` parsing inside Blender is fragile across PSD versions and duplicates the exporter's work. The manifest is the stable contract.
- **Sprite_frame detection has two paths.** Primary: a PSD layer group with numeric children. Fallback: flat `<name>_<index>` naming. Both detected on the Photoshop side.

### Testing fixtures

- **Five canonical fixtures cover orthogonal feature isolation.** A comprehensive showcase rig plus single-feature fixtures for sprite_frame, sliced atlas, PSD roundtrip, and slot system. A single source feeds both writer goldens and importer regenerations.

### Code modularity

- **Refactor into packages without behavior change.** Monolithic modules (writer, panels, operators, validation) split into focused subpackages. No format change, no user-facing change. Behavior tests carry the proof.
- **Per-package import discipline.** `core/` stays bpy-free at module top; `core/bpy_helpers/` is the bpy-bound boundary. Panels reach operators only via `bl_idname` strings, never via direct class imports.

### Photoshop UXP migration

- **UXP is the only Photoshop entry point.** The legacy JSX exporter and importer were retired once the doll roundtrip oracle confirmed pixel-byte parity vs the captured JSX baseline.
- **Stack locked: pnpm + webpack + Babel + ajv + vitest.** Vite rejected because UXP needs CommonJS output and Vite's ESM-first defaults fight it.
- **Schema unchanged.** The migration shipped at `format_version: 1` byte-for-byte. The PSD-manifest v2 bump that adds tags, anchor, and per-entry origin landed under the photoshop tag system.
- **Minimum Photoshop CC 2024 / PS 25+.** Required by the `constants.*` enums, persistent tokens, and Spectrum web components the plugin relies on.
- **`localFileSystem: "fullAccess"` required.** The minimum-privilege `"request"` covers the folder picker alone; the plugin also calls `createPersistentToken` + sub-folder writes, which need `"fullAccess"`.

### Photoshop tag system

- **Bracket-tag inline syntax is the primary tag format.** `[tag]` / `[tag:value]` tokens inside layer names; XMP per-layer is the secondary canonical store. Bracket-tag wins on conflict.
- **PSD manifest bumped to `format_version: 2`.** Adds `anchor` at the document root and per-layer `origin`, `blend_mode`, `subfolder`. New `kind: "mesh"` variant joins `polygon` and `sprite_frame`. The `.proscenio` schema stays at v1 - this bump is PSD-side only.
- **`kind: "mesh"` is a hint, not a branch.** The Blender importer stamps a `proscenio_psd_kind` Custom Property; no downstream code branches on it yet. The distinction exists so deformable-mesh and UV-animation work can tell editable polygons apart from rigid sprites later.
- **Unknown tags pass through to the display name.** Artist typos and future tags stay visible; the Tags panel surfaces them as warnings rather than silently dropping the data.

### Quick Armature UX

- **GPU overlay + Edit-Mode live update.** The modal draws a preview line via `gpu.draw_handler_add` AND creates the real bone on `LEFTMOUSE PRESS` with the tail updated on every `MOUSEMOVE`. The user gets both instant feedback and Edit-Mode parity.
- **Naming prefix = addon preference + F3 redo override.** One sane default per install; power users can override per-invocation.
- **Front Ortho auto-snap restores the original view on exit.** Predictable: user in Persp → Quick Armature → back to Persp. Opt-out via F3 redo for legitimate persp-view authoring.
- **Sweep empty QuickRig on cancel.** Tracks whether the operator instantiated the armature this session and only sweeps in that case; pre-existing QuickRigs the user emptied manually stay.
- **Picker armature carries the mirror flag.** Single source of truth shared with the weight-paint spec - no per-operator mirror toggle. Mirror is a property of the rig, not a per-tool option.

### Weight paint + automesh

First cut + productivity follow-up + interior modes + gesture rewrite all locked.

- **Automesh paradigm = alpha-trace one-shot, pure Python.** Walks the alpha channel; no OpenCV; zero third-party deps. The free-draw stroke alternative was deferred to the backlog.
- **Mesh topology = annulus with alpha-hole support (refined in the first cut).** Outer + inner contour + Constrained Delaunay; alpha holes are traced as constraint loops + cut via centroid post-process face prune. Lifts Spine / COA2's "no holes" restriction.
- **`proscenio_base_sprite` vertex group is the regen anchor.** Re-runs remove only verts NOT in that group; the original quad corners survive.
- **`BONE_HEAT` allowed as bind default for 2D pickers.** The pre-flight diagnosis still runs before every bind path; planar proximity demoted to fallback. Trigger for the original "never default" rule (depsgraph cost on non-2D rigs) does not apply when the picker is the 2D armature contract.
- **Sidecar JSON + UV-anchor reprojection preserves weights across regens.** Provenance overlay shows which verts are seed / paint / reprojected. Survives mesh topology changes inside the automesh `proscenio_base_sprite` envelope.
- **Pre-flight diagnosis on auto-weight failure.** Detects unapplied scale, flipped normals, overlapping verts, isolated islands, bones outside the mesh bbox; emits actionable message never a raw stack trace.
- **Density-under-bones automesh ON by default when a picker armature exists.** OFF otherwise. Reuses the picker bone positions so the interior cluster matches the rig the user already wired.
- **Interior fill mode = SIMPLE / DENSE enum.** SIMPLE drops the dense interior fill; DENSE retains it. PG default SIMPLE, `StageParams.interior_mode` default DENSE for test back-compat.
- **Toggle-modal pen for Stage 2 + Stage 4.** Shift / Ctrl tap enters the pen; LMB click = vert, drag = free-draw, RMB / Enter = finish, Esc = cancel line. Modal event routing reordered so DRAW intercepts Enter / RMB / Esc before nav. Subdivisions baked at finish, no `Stroke.subdivisions` schema field.
- **Stage 2 outer silhouette uses the same pen + spliced-outer preview.** Green overlay shows the silhouette APPLY will build after extend edits; updates on commit / undo / delete.

### Typed-models codegen

- **Pydantic v2 in `packages/models/` is the source of truth.** Bundled into the Blender addon via wheels declared in `blender_manifest.toml`; the writer constructs the document and `ProscenioDocument.model_validate(...).model_dump_json(...)` is the emit path. Validators + discriminated unions live where the data is born.
- **Generated artifacts are checked in.** `packages/models/schemas/` for JSON Schema; `apps/photoshop/src/schema_bindings/` for TS; `apps/godot/addons/proscenio/schema_bindings/` for GDScript Resources; `docs/content/api/schemas/` for Markdown. Committed-match tests under `tests/codegen/` fail on drift for the JSON Schema, TypeScript, and GDScript artifacts; the docs Markdown is regenerable but ungated (it relies on an npx tool).
- **Keep ajv on the Photoshop side; TS interfaces come from `json-schema-to-typescript`.** Smaller bundle, mature discriminated-union support, already aligned with the runtime path. Revisit `z.fromJSONSchema()` once it leaves experimental.
- **Discriminated unions use callable `Discriminator`.** The polygon-sprite variant allows `type` to be absent (v1 backwards compat); the callable defaults to `"polygon"`. Returning `None` for unexpected tags surfaces a clearer `union_tag_not_found` ValidationError than the field-string variant.
- **GDScript Resources carry a `_set_fields: PackedStringArray`.** Populated by `from_dict` during parse; lets the animation builder tell "field set to JSON default" apart from "field absent in source" without re-walking the raw dictionary.
- **Every emitted Godot class is prefixed `Proscenio`.** Avoids collision with engine built-ins (`Animation`, `Skeleton`, `Bone`, `Track`, ...). Filenames follow the prefix; the dispatchers (`ProscenioSprite`, `ProscenioLayer`) sit alongside the per-variant Resources.
- **Stricter typing rolled out per language.** mypy adds `warn_return_any` + `extra_checks` + `strict_equality`; tsc adds the strict-strict family (`noUncheckedIndexedAccess`, `noPropertyAccessFromIndexSignature`, `noImplicitOverride`, `useUnknownInCatchVariables`, `noUnused*`); Godot turns on the `unsafe_*` warning family. The initially-deferred strictness (`disallow_any_*` trio, `exactOptionalPropertyTypes`, ESLint strict-type-checked) has since landed; the bpy stub snapshot and the Docusaurus docs site remain deferred (see `backlog.md`).

### Monorepo packages

- **Top-level split = `apps/` + `packages/` + `scripts/`.** Apps ship; packages are shared building blocks consumed by apps; scripts hold true one-offs (`debug/`, `godot/`, `maintenance/`). Anything with a subpackage layout, tests, or a CLI surface belongs in `packages/`.
- **uv workspaces declares the Python package set at the repo root.** `tool.uv.workspace.members` covers `apps/blender`, `packages/codegen`, `packages/models`, `packages/validator`. `packages/fixtures/` is data-only (no `pyproject.toml`).
- **`schema_bindings/` is the per-app folder name for codegen output.** Describes the role (language bindings to the schema), survives a regen, and reads cleanly across Python / TypeScript / GDScript paths. Universal naming chosen over `generated/` (sounded internal) or `bindings/` (FFI overload).
- **Package distribution names use the `proscenio-` prefix.** Folder names are unscoped inside the repo (`packages/models/`); the distribution name in `pyproject.toml` carries the prefix (`name = "proscenio-models"`) so workspace dev and the bundled wheel resolve to the same identity.
