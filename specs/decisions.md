# Decisions

Architectural and per-feature decisions that are locked. ADR-light: each entry records the call, the rationale, and the trigger that would force a revisit.

The rolling backlog of open work lives in [`backlog.md`](backlog.md); this file is the consolidated home for locked decisions. It carries the cross-cutting architectural calls plus the per-feature studies made while building each feature. The hand-written planning docs that once held this rationale were discarded once their features shipped, so every decision worth keeping was mirrored back here - this file, not a spec folder, is now the record.

## Core architecture

| Decision | Rationale | Revisit trigger |
| --- | --- | --- |
| **No GDExtension, no native runtime** | Plugin is GDScript-only. Generated `.scn` uses native nodes; runs on plain Godot 4 with the plugin uninstalled. | Deep Firebound integration, perf ceiling on `Polygon2D` skinning, live-link Blender ↔ Godot, binary `.proscenio`, in-Godot authoring round-trip. |
| **Conversion one-time, at editor import** | Heavy work runs at import time. Runtime uses Godot core (already C++); no GDScript performance ceiling. | Same triggers as the GDExtension entry. |
| **Strong typing everywhere** | GDScript 2.0 typed (`untyped_declaration=2` error), Python `mypy --strict`, TypeScript `strict`. Catches errors before runtime. | None. Baseline rule. |
| **Schemas are the contract (pre-launch: no bump)** | Post-launch, any change to a cross-component shape requires a `format_version` bump on the affected schema plus a migration path. Pre-launch (the current stage), the schema is still being defined: shape changes happen in place at the current `format_version`, no bump and no migration code, proven by regenerating the in-repo fixtures + goldens from source. `format_version` is a launch concern - the number freezes at first public release and only climbs afterward; bumping during pre-launch churn would write a version history that never happened. CI validates fixtures against the schemas at every stage. | First public release flips the rule to bump-plus-migration for every later cross-component shape change. |
| **Storage split by field intent** (revised) | Original call mirrored every PropertyGroup field to a raw Custom Property and read PropertyGroup-first / CP-fallback. Revised: editor-time-only fields are PropertyGroup-canonical; animatable / driver-target fields (`frame`, slot index) are Custom-Property-canonical, since Blender cannot keyframe a field nested in a PropertyGroup. The split is locked but not yet implemented - current code still mirrors uniformly. | Implement before 1.0.0, so the public surface ships the final storage contract. Plan in [`backlog.md`](backlog.md), "Split PropertyGroup vs Custom Property storage by intent". |
| **Wrapper-scene pattern for Godot reimport** | The importer overwrites `.scn` on every reimport; the user-authored wrapper `.tscn` survives intact and carries scripts and extras. | Marker-based merge stays deferred unless concrete demand emerges. |
| **One component per PR** | Photoshop, Blender, and Godot ship independent PRs. Schema bumps cross all components by definition. | None. |
| **C# / GDExtension as documented escape hatch, not active option** | Maintainer prefers strong typing over GDScript's dynamism, but stays in GDScript for plugin reach in the broader 2D community. Firebound itself stays C#. | Same as the GDExtension entry. |
| **`apps/` + `packages/` + `scripts/` split** | `apps/` holds distributable bundles (Blender, Photoshop, Godot). `packages/` holds shared building blocks consumed by apps (pydantic models, codegen CLI, fixtures, validator). `scripts/` shrinks to one-off dev tools. uv workspaces declares the Python package set at the repo root. | Adding a second TypeScript package (would warrant a root-level pnpm workspace alongside the uv workspace). |
| **Codegen artifacts land in per-app `schema_bindings/` folders** | TypeScript interfaces in `apps/photoshop/src/schema_bindings/`, GDScript Resources in `apps/godot/addons/proscenio/schema_bindings/`. JSON Schema dumped to `packages/models/schemas/` next to the pydantic models that produced it. Each generated file carries an `AUTO-GENERATED` header; committed-match tests under `tests/codegen/` reproduce the JSON Schema, TypeScript, and GDScript artifacts from the models and fail on drift (the docs Markdown is regenerable but ungated, as it depends on an npx tool). | Switching the per-app binding folder to a different name; switching JSON Schema location away from `packages/models/schemas/`. |

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

### Blender system organization

- **Layer-first hybrid, not vertical slices.** The addon stays layer-first at the top (`core/`, `operators/`, `panels/`, `properties/`, `exporters/`, `importers/`): Blender registration is type-ordered (properties -> operators -> panels) and the `core/` versus `core/bpy_helpers/` pure-vs-bpy split is the test boundary. Systems are feature subpackages WITHIN each layer, never a per-system top level. Revisit trigger: registration stops being type-ordered, or the addon splits into independently-registered sub-addons.
- **`_shared/` tier for cross-cutting infrastructure.** Modules owned by no single system (cp_keys, report, props_access, pg_cp_fallback, feature_status, hydrate, geometry / region / viewport math, the bpy compat shims) live in `core/_shared/` (pure) and `core/bpy_helpers/_shared/` (bpy-bound); the leading underscore sorts the tier above the system folders.
- **Custom Property keys live in one module.** Every CP key literal sits in `core/_shared/cp_keys.py` and call sites import the constant; the weight-sidecar, automesh-stroke, and photoshop-import keys that had drifted into local `_KEY` constants are pulled back in.
- **Behavior-preserving, proven by the full gate set.** No schema or `format_version` change; ruff + mypy + the repo-root pytest suite + the Blender fixture and operator suites + a whole-addon import sweep all stay green.

### Photoshop web-app layout

- **Layer-based layout borrowed from a conventional web app.** UXP has no canonical plugin architecture, so the plugin organizes by role: `panels/` (screens) and `components/` (reusable leaf UI) render, `hooks/` own state, `lib/` is pure logic, `api/` is the single Photoshop boundary, `utils/` are leaf helpers. Layered direction `panels -> hooks -> api + lib`. Chosen over a feature-folder (vertical-slice) split because the panel count is small and the pure-vs-boundary seam is the axis that actually needs enforcing. Revisit trigger: the plugin grows enough independent features that cross-layer churn per feature outweighs the boundary clarity.
- **`lib/` is UXP-free; `api/` is the only boundary.** Pure logic never imports a UXP module; hooks and panels reach the live document through `api/` (`active-document`, `ps-notifications`, `ps-selection`, ...), never `import { app } from "photoshop"` directly. This is what makes `lib/` unit-testable without a Photoshop host.
- **One `@ts-nocheck` exception: `src/entry.ts`.** The Adobe React UXP starter `PanelController` (Symbol-keyed private fields, untyped Component contract) is the only shape `entrypoints.setup({ panels })` parses reliably; it is vendored verbatim and excluded from the typed gate and ESLint.
- **Behavior-preserving, proven by the Photoshop gate.** No schema or `format_version` change; `tsc --noEmit` + ESLint + vitest all stay green.

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
- **Picker armature carries the mirror flag.** Single source of truth - no per-operator mirror toggle. Mirror is a property of the rig, not a per-tool option.

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

### Documentation architecture

- **The docs site is sliced into three audience navbar sections.** Guides (artist tutorials), Project (the live Schema reference plus Architecture / Comparison / Deferred for devs), and Tools (high-level per-app reference). The Features page folded into the per-app Tools pages. The section map and the "where a page belongs" rule are codified in `.ai/conventions/docs.md` "Information architecture"; the wiring is `apps/docs/sidebars.ts`.
- **Code carries what and how; rationale lives in its home, not in a comment.** The comment-routing policy (delete / tighten-inline / to-assert / to-module-docstring / to-test / to-architecture / keep, plus reference hygiene: cite a test by name, never a spec path) is the canonical rule in `.ai/conventions/code.md` "Comments and rationale". The two cross-cutting conventions it points at, the XZ picture-plane convention and the golden field-order constraint, live on the docs Architecture page.
- **Module docstrings only when non-obvious.** A trivial module gets none. A pydantic model class docstring is the schema `description`, so trimming one regenerates the schema and the TypeScript binding through codegen.
- **Enforcement in pre-commit.** Two drift hooks reject spec-path references and `# Step N` / `# Phase N` markers in code comments; the prose-density heuristic stays an on-demand advisory sweep in `docs.md`.

### Export correctness

- **One picker-first armature resolver, shared by writer and validator.** `resolve_export_armature(scene)` is the single home that decides which rig a scene exports (the picker pointer when it is live and in-scene, else the first ARMATURE in scene order, guarding the headless `--background` path and stale pointers); the writer (`find_armature`), the export validator, and the Skeleton panel "Exports: <name>" readout all route through it. Rationale: fixing only the writer would leave validate and export disagreeing in a multi-armature scene - the contract is that they cannot diverge.
- **`MeshElement.polygons` is additive-optional at `format_version` 1, multi-face only.** Per-face index arrays (mirroring `Polygon2D.polygons`) are emitted only when a mesh has more than one face; single-face meshes stay field-less. Rationale: an old importer ignores the field and still renders the outline, and single-face goldens stay byte-stable, so the change ships without the still-gated migration path a version bump would require.
- **`action_fcurves` is the one duck-typed reader for legacy and Blender 4.4+ layered-action fcurves.** Both the writer's track emission and the validator's transform-key check read curves through it (flat `fcurves`, else layers > strips > channelbags). Rationale: the writer already guarded layered actions while the validator did not, which was the silent-miss bug; a shared reader stops the two sides drifting again.

### Sprite appearance and orientation

- **Appearance is derived from native Blender state, never from new authoring properties.** `modulate` from object color, `z_index` from the PSD-stamped Y depth, flips from negative local-scale signs, `Sprite2D.offset` from quad-bounds-vs-origin. Rationale: the manual-GUI surface and the PG/CP mirror stay exactly as large as they were, which the storage-split work depends on.
- **Color channels are `ge=0` (HDR over-bright allowed); `z_index` is bounded to Godot's +/-4096.** Rationale: a negative channel serializes an invalid tint while over-bright is a legitimate modulate value; an out-of-range `z_index` is rejected up front to match Godot's clamp.
- **The bone-driven `sprite_frame` bake is reproduced from the posed bone, not read from the driver target, and clamps to the grid with constant interpolation.** Rationale: the driver's write target needs the addon PropertyGroup (absent in the headless CP-fallback harness), so reproducing it keeps the track exporting with or without the PG; Godot rejects an out-of-range `Sprite2D.frame`, and frames are discrete hard cuts.
- **Orientation checks are warn-only; the writer keeps its XZ-plane assumption.** Rationale: they surface a silently-wrong export class without generalizing the transform math (the full-XY generalization is gated); the mesh-flatness test compares smallest-vs-largest axis spread, so a planar cutout authored in any plane is not false-warned. Revisit: a real XY-authored rig.
- **`region_filter_clip_enabled` is set wherever `region_enabled` is set.** Rationale: stops neighbouring atlas frames bleeding at the seam on packed sprite frames.

### Mesh authoring

- **The extend splice anchors at stroke/contour crossings and picks the kept arc by area, not by nearest-outer-vertex plus index comparison.** Rationale: crossing points are unambiguous, so the result is independent of pen-click sparsity, contour winding, and where the polyline seam falls - the three traps that made the old splice silently amputate the silhouette.
- **Mesh-authoring tools gate on `element_type == "mesh"` (warn-not-hide), and the rigid sprite bind is delegated to native bone-parenting (Ctrl+P > Bone).** Rationale: a sprite element is a single-quad MESH the writer maps to a Sprite2D; meshing it silently destroys that mapping, and native parenting already provides the rigid bind, so a dedicated operator is bloat.
- **"Trace resolution" (the alpha-downscale knob) is named apart from mesh density.** Rationale: a higher factor traces a finer silhouette; vertex count is set by Contour vertices + Interior spacing - the old "Mesh resolution / lower = denser" copy steered artists backwards.

### Rigging, drivers, and IK

- **IK export protection is bake-at-export, not live constraints.** The export validator hard-errors an active-influence IK chain whose target is animated but whose member bones carry no keyframes, and "Bake IK to Keyframes" (`nla.bake` visual-keying, clear-constraints) is the one-click fix. Rationale: the import-time-only, built-in-nodes contract has no runtime IK consumer, and Godot's 2D `SkeletonModification2D` stack is experimental and flipped-rig-buggy; baking is the structural equivalent and closes the silent-wrong-export class. Revisit: the live-constraint round-trip is gated on that stack graduating.
- **Proscenio-owned IK scaffolding is identified by a `.IK` suffix on a non-deforming control bone; toggle-off deletes only suffix-matched controls.** Rationale: Toggle-IK can clean up its own control bone without touching hand-authored or hand-retargeted constraints.
- **Drive-from-Bone is a clamped two-range linear map (`build_driver_expression`, bpy-free) with a negative-spanning default input range; the raw expression is an Advanced fallback only.** Rationale: the old raw `var` default mapped bone radians straight onto a 0..N frame range, clamping negative rotation to 0 and making the flagship driver look broken on first contact.

### Slot placement

- **Create Slot places the Empty at the world-space bound-box center of the selection, written through `matrix_world`.** Rationale: the slot system's entry point must land on the visible geometry regardless of a parented seed or an unapplied origin; writing the AABB center through `matrix_world` (mirroring `parent_keep_world`) is the single fix that satisfies both. Distinct from the Slot-system decisions above (interpolation, flat array, kind-agnostic), which do not cover placement.

### Atlas packing and PPU

- **PPU round-trips via the persisted exporter value (a localStorage seed), not document metadata.** Rationale: the import flow already holds the validated manifest, so seeding the exporter PPU closes the loop without the JSX-era XMP plan; Blender import additionally syncs the scene prop so both ends stay consistent.
- **PPU stays one document-level value end to end; per-asset PPU is not adopted.** Rationale: uniform PPU is the engine-side best practice; per-asset divergence is a normalization problem, gated on a recurring real case.
- **The atlas padding ring is edge-extended (alpha bleed), default-on, no UI knob; atlas rotation is permanently rejected.** Rationale: a transparent ring seams alpha=0 into sprite edges under bilinear filtering, so edge-extend is table stakes; Godot's `AtlasTexture` / `region_rect` cannot express a rotated region, so rotation would be a Polygon2D-only footgun (dropped, not deferred).
- **The packer keeps single-heuristic MaxRects-BSSF.** Rationale: BSSF is the strongest single heuristic (~94% occupancy); trying all of them multiplies pack time for low single-digit density nobody sees at this scale.
- **Unpack material recovery is marker-Custom-Property based; the pointer-based PropertyGroup snapshot is deferred to the storage split.** Rationale: a marker stamped at Apply survives a rename and gives Unpack a rescue scan without the PG storage refactor.

### Project health gates

- **The models / codegen mypy profile drops `disallow_any_explicit` under the pydantic plugin** (the rest of the strict profile holds; `python_version = "3.11"`, not Blender's 3.13). Rationale: pydantic's plugin-synthesized methods carry explicit `Any` on every model, and the codegen emitter reasons over typing internals whose payloads are `Any` by stdlib contract, so the flag fires on the framework surface, not author looseness.
- **`release.yml` routes every `workflow_dispatch` free-text input through env vars, never `${{ inputs.* }}` expansion in a shell body, and is exercisable tagless via a dry-run that skips the gh-release upload.** Rationale: a free-text input expanded into a `run:` block is a template-injection vector (zizmor / CodeRabbit finding); and the stale `.jsx` line rotted unnoticed precisely because the job only ran on tags.
