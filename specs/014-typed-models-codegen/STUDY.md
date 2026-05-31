# Typed domain models as source of truth + codegen + living docs

Status: **decisions locked, ready for implementation**. Depends on [the monorepo packages spec](../015-monorepo-packages/STUDY.md) landing first so `packages/models/` and `packages/codegen/` have a home. D1-D11 closed (see Design decisions section). Open questions resolved via research + decision; see "Open questions" for the outcomes.

## Problem

The cross-component JSON schemas at the repo root under `schemas/` are currently the *de facto* source of truth for the data flowing between the three apps:

- Blender addon (Python) writes `.proscenio` and the PSD manifest.
- Photoshop UXP plugin (TypeScript) reads/writes the PSD manifest.
- Godot plugin (GDScript) reads `.proscenio`.

Each side maintains its own view of the shape:

| App | Today's representation | Pain |
| --- | --- | --- |
| Blender | `TypedDict` / loose `dict[str, Any]` inside the writer | Shape is duplicated in code and in the schema. Drift caught only by golden fixtures and ajv. |
| Photoshop | Hand-written `interface` types + ajv check at boundary | Two hand-edits per schema change. `interface` carries no runtime guard beyond ajv. |
| Godot | `Dictionary` (Variant) downcast at every access | The `unsafe_*` warning family is silenced where the JSON is touched; `Variant` propagates through importer code. No statically-typed Resource layer. |

`.ai/conventions.md` already commits to "Schema as a contract" and "Domain types over loose dicts" - this spec is the operationalization of that pledge with an explicit source-of-truth chosen.

### Why JSON Schema is a weak source of truth

JSON Schema describes a *wire shape*, not a *domain model*. Concrete weaknesses for Proscenio:

1. **No behavior.** Validators (`@field_validator`) and invariants (cross-field rules) are absent or encoded as illegible `allOf`/`oneOf` trees.
2. **Codegen produces dumb types.** `TypedDict` / `interface` carry no methods, no `__post_init__`, no branding - every consumer re-derives invariants by hand.
3. **No identity.** Concepts like `Slot`, `Bone`, `Sprite` exist only as `object`s with named properties.
4. **Versioning is bolted on.** `format_version` is a manual integer; migrations live elsewhere; no first-class migration path inside the schema.
5. **Doc generation lists fields, not concepts.** A schema-derived doc reads as a dictionary of properties, not a narrated domain.
6. **Manifest sprawl.** The photoshop tag system's PSD manifest grew the discriminator family (`kind: "raster" | "slot" | "bone" | "mesh" | "sprite_frame"`), per-entry `origin`, `blend_mode`, `subfolder`, etc. A growing union of heterogeneous shapes in one schema becomes a god-object without strong discriminators expressed as union types in code.

### What we want

A single source of truth, *executable*, that:

- captures invariants in code (validators, discriminated unions, defaults);
- generates the JSON Schemas, TypeScript types, and GDScript Resources as artifacts;
- produces Markdown for the Docusaurus site with minimal manual input;
- breaks the build (not silently the runtime) when any consumer drifts from the model.

Plus, in the same wave, tighten static analysis in all three languages and plug the unsafe-Variant hole on the Godot side.

## Reference: Firebound's docs pipeline

The Firebound game framework already runs a similar pipeline against C# code:

- [`.github/workflows/pages.yml`](https://github.com/Space-Wizard-Studios/firebound/blob/main/.github/workflows/pages.yml) - DocFX builds XML doc out of the C# project.
- [`docs/processApiFiles.js`](https://github.com/Space-Wizard-Studios/firebound/blob/main/docs/processApiFiles.js) - post-processes DocFX output into a Docusaurus-friendly layout.

The pattern - "language-native doc generator -> normalization script -> Docusaurus `content/`" - is reusable here, with three twists:

1. Source is not docstrings; it is pydantic model definitions plus `Field(description=...)`.
2. The same source also drives codegen for TS and GDScript, not only docs.
3. Three languages produce/consume the data instead of one.

## Design space

### Axis A - Source of truth

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **A1.** JSON Schema in `schemas/` (status quo) | Already in CI. Tool-rich ecosystem. | All weaknesses listed above. | Reject as source. Keep as artifact. |
| **A2.** Pydantic v2 models in `packages/models/` | Hub language is Python (Blender addon). Validators + discriminated unions land where the data is born. `model_json_schema()` is a one-liner. Pydantic v2 perf is fine for our payload sizes. | Adds runtime dep to the Blender addon. Pydantic ships pre-compiled wheels per platform; bundling resolved by the wheels declaration in the Blender extension manifest. | **Lock as default.** |
| **A3.** `msgspec` Struct models | Faster than pydantic, codegen-friendly, stdlib-only at runtime. | Smaller ecosystem; fewer docs tools target msgspec; less idiomatic on the Blender side. | Defer. Re-evaluate only if pydantic perf becomes an issue. |
| **A4.** IDL (Protobuf, Cap'n Proto, FlatBuffers) | Cross-language by design. | Toolchain weight. We do not need binary serialization. Blender authors do not want to learn `.proto`. | Reject. Overkill for a small JSON pipeline with one writer per format. |
| **A5.** TypeScript-first (`zod` schemas in Photoshop, generate Python+GDScript) | Strong runtime guards out of the box. | Photoshop is the smallest of the three apps and not the writer of either format. Wrong hub. | Reject. |

### Axis B - Codegen targets

| Target | Tool | Maturity | Notes |
| --- | --- | --- | --- |
| JSON Schema | `pydantic.BaseModel.model_json_schema()` | Built-in | Per-model, dumped by `proscenio_codegen.schema_dump`. |
| TypeScript types | `json-schema-to-typescript` (npm) | Mature | Invoked via subprocess from `proscenio_codegen.ts_emit`; reads the dumped schema; emits `apps/photoshop/src/schema_bindings/*.ts`. |
| GDScript Resources | Custom Python emitter in `proscenio_codegen.godot_emit` | Not off-the-shelf | Walks pydantic model fields and emits `class_name FooData extends Resource` with `@export` vars + a `from_dict` parser. ~150-250 LOC. |
| Markdown docs | `@adobe/jsonschema2md` or `json-schema-static-docs` | Mature | Invoked via subprocess from `proscenio_codegen.docs_emit`; reads the dumped schema; emits `docs/content/api/schemas/*.md`. |

### Axis C - Stricter typing per language

A non-codegen quality-of-life payload that pairs with the model rewrite. Already partly applied; gaps remain.

#### C1. Python (mypy strict + extra)

Today (`apps/blender/pyproject.toml`):

```toml
[tool.mypy]
strict = true
warn_unused_ignores = true
warn_unreachable = true
```

Add:

```toml
disallow_any_explicit = true
disallow_any_decorated = true
disallow_any_unimported = true
strict_equality = true
extra_checks = true
warn_return_any = true
```

Plus: investigate generating local `bpy` stubs in CI (`bpy-stubgen` or a frozen `fake-bpy-module-latest` snapshot) so the `bpy` boundary stops returning `Any` and starts returning real types. The boundary today exempts `bpy.*` via `ignore_missing_imports = true` + `disallow_subclassing_any = false`; with stubs, the second flag can stay (Operator subclassing) but `Any` would not bleed past the import.

#### C2. TypeScript (tsconfig + ESLint)

Today (`apps/photoshop/tsconfig.json`) - `strict: true` plus a few belt-and-suspenders flags. Missing the strict-strict family:

```json
"noUncheckedIndexedAccess": true,
"exactOptionalPropertyTypes": true,
"noImplicitOverride": true,
"noPropertyAccessFromIndexSignature": true,
"noUnusedLocals": true,
"noUnusedParameters": true,
"useUnknownInCatchVariables": true
```

Plus: ESLint with `@typescript-eslint/strict-type-checked`. ajv keeps the boundary check; the generated TS interfaces from `json-schema-to-typescript` give the static side.

#### C3. GDScript (project.godot warnings)

Today (`apps/godot/project.godot`):

```ini
gdscript/warnings/untyped_declaration=2
gdscript/warnings/return_value_discarded=1
gdscript/warnings/treat_warnings_as_errors=true
```

Add the unsafe family (currently silent) and a few hygiene checks:

```ini
gdscript/warnings/unsafe_property_access=2
gdscript/warnings/unsafe_method_access=2
gdscript/warnings/unsafe_cast=2
gdscript/warnings/unsafe_call_argument=2
gdscript/warnings/unsafe_void_return=2
gdscript/warnings/inference_on_variant=2
gdscript/warnings/static_called_on_instance=2
gdscript/warnings/return_value_discarded=2  ; promote 1 -> 2
gdscript/warnings/incompatible_ternary=2
gdscript/warnings/confusable_local_declaration=2
gdscript/warnings/shadowed_variable=2
gdscript/warnings/shadowed_variable_base_class=2
```

The unsafe family is what catches `Dictionary` access without prior cast. Generated `Resource` classes (B) are what unblocks turning these on without lighting up the importer end-to-end.

> Editor caveat (`.ai/conventions.md` already warns): do not place comments inside `[debug]` in `project.godot`; the editor's serializer mangles them on save.

### Axis D - Living docs pipeline

Two layers, matching Firebound's "generator -> normalizer -> Docusaurus" split:

1. **Schema docs.** `pydantic` models -> `model_json_schema()` -> `jsonschema2md` -> `docs/content/api/schemas/*.md`. `Field(description="...")` is the only authoring surface; descriptions land both in the schema and the doc.
2. **Long-form domain docs.** Hand-written Markdown in `docs/content/concepts/*.md` cross-links to schema doc anchors. The schema doc is the field reference; the long-form doc is the *concept* reference. This matches what `.ai/skills/format-spec.md` does today - the skill page narrates the format, the schema is the field list.

Optional later: GDScript class docs via `godot --doctool` -> XML -> normalizer (mirror of `processApiFiles.js`), TS docs via TypeDoc + markdown plugin. Both are deferred until the schema layer ships and proves the integration.

### Axis E - Codegen tool shape

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **E1.** One fat script (`scripts/codegen.py` with a giant `main()`) | Single entry point. | One file grows unbounded; testing each emitter in isolation needs careful sys.argv mocking. | Reject. |
| **E2.** Four separate scripts (`dump_schemas.py`, `emit_ts.sh`, `emit_godot.py`, `emit_docs.sh`) | Each script focused. | Four entry points to maintain; shell scripts in the mix breaks the "one language" principle; cross-helper code (atomic writes, header banner) gets copy-pasted. | Reject. |
| **E3.** One Python package (`packages/codegen/`) with helper modules per target + a single CLI coordinator | Each helper is a focused module with its own tests; the CLI coordinator (`__main__.py`) parses subcommands and delegates; shared code (`_io.py`) lives in one place; everything in Python (TS / docs invocations go through `subprocess`). | One more package in the workspace. | **Lock.** |

E3 ships as `packages/codegen/`, with helpers `schema_dump`, `ts_emit`, `godot_emit`, `docs_emit`, and shared `_io`. CLI surface: `python -m proscenio_codegen schemas|ts|godot|docs|all`.

## Architecture sketch

The new structure assumes [the monorepo packages spec](../015-monorepo-packages/STUDY.md) has landed. Net additions on top of that layout:

```text
packages/
  models/                                   # NEW workspace member
    pyproject.toml                          # name = "proscenio-models"
    src/proscenio_models/
      __init__.py                           # re-exports the public model classes
      proscenio.py                          # ProscenioDocument, Bone, Sprite (discriminated), Animation, Track, ...
      psd_manifest.py                       # PsdManifest discriminated union
    schemas/                                # dumped artifacts
      proscenio.schema.json
      psd_manifest.schema.json
    tests/

  codegen/                                  # NEW workspace member
    pyproject.toml                          # name = "proscenio-codegen", depends on proscenio-models
    src/proscenio_codegen/
      __init__.py
      __main__.py                           # python -m proscenio_codegen schemas|ts|godot|docs|all
      schema_dump.py                        # pydantic -> JSON Schema -> packages/models/schemas/
      ts_emit.py                            # subprocess to json-schema-to-typescript -> apps/photoshop/src/schema_bindings/
      godot_emit.py                         # custom emitter -> apps/godot/addons/proscenio/schema_bindings/
      docs_emit.py                          # subprocess to jsonschema2md -> docs/content/api/schemas/
      _io.py                                # paths, AUTO-GENERATED header, atomic write
    tests/

apps/
  blender/
    wheels/                                 # gains proscenio_models-*.whl + pydantic wheels
      pydantic-*.whl
      pydantic_core-*-<plat>.whl
      proscenio_models-*.whl                # built from packages/models/ in CI
    blender_manifest.toml                   # gains wheels = [...]

  photoshop/
    src/
      schema_bindings/                      # populated by proscenio_codegen.ts_emit
        proscenio.ts
        psd_manifest.ts

  godot/
    addons/
      proscenio/
        schema_bindings/                    # populated by proscenio_codegen.godot_emit
          proscenio_document.gd
          bone.gd
          sprite_polygon.gd
          sprite_frame.gd
          slot.gd
          animation.gd
          ...

docs/
  content/
    api/
      schemas/                              # populated by proscenio_codegen.docs_emit (P5)
        proscenio.md
        psd_manifest.md

tests/
  codegen/                                  # NEW: round-trip + smoke
    test_schema_roundtrip.py
    test_discriminated_union.py
```

`.gitattributes` marks every `schema_bindings/` path and `packages/models/schemas/` as `linguist-generated=true`; each generated file carries a `# AUTO-GENERATED - DO NOT EDIT` header; CI runs `python -m proscenio_codegen all` and fails if `git status` is non-empty.

The top-level `schemas/` folder at the repo root is deleted at the end of P2 (see Migration plan). Before then, `packages/models/schemas/` is generated alongside the old folder and a round-trip test confirms byte equality.

## Migration plan

Each phase is one PR. None of this requires a `format_version` bump in itself - the schemas should round-trip byte-for-byte against the existing hand-maintained ones until the model gains a field that the schema did not have.

| Phase | Scope | Risk |
| --- | --- | --- |
| **P1.** Pydantic models for `.proscenio` + codegen package skeleton | Create `packages/models/` (only `proscenio.py`, no PSD manifest yet) and `packages/codegen/` (only `schema_dump.py` + `_io.py`, no TS/Godot/docs emitters yet). Add both to the uv workspace. Add wheels for pydantic + `proscenio-models` to `apps/blender/blender_manifest.toml`. Round-trip test in `tests/codegen/test_schema_roundtrip.py` asserts the dumped schema matches `schemas/proscenio.schema.json` byte-for-byte. Smoke test in `tests/codegen/test_discriminated_union.py` covers the `Sprite.type` union. Writer untouched; models dormant. | Low. New files only; no existing code changes. |
| **P2.** Writer uses models + delete top-level `schemas/` | Writer swaps `dict[str, Any]` -> `ProscenioDocument.model_dump()`. Tests still diff against golden fixtures. Once the writer is green and the round-trip test stays byte-equal, delete the top-level `schemas/proscenio.schema.json` and update any reference to point at `packages/models/schemas/`. | Medium. Touches writer extensively. Golden fixtures catch shape regressions. |
| **P3.** PSD manifest model + TS codegen + Photoshop adoption | Add `packages/models/psd_manifest.py`. Add `proscenio_codegen.ts_emit`. Populate `apps/photoshop/src/schema_bindings/`. Replace hand-written manifest interfaces in the UXP plugin. Delete top-level `schemas/psd_manifest.schema.json` at the end of this phase. | Medium. UXP plugin is small; surface is the manifest reader/writer. |
| **P4.** GDScript codegen + importer adoption | Add `proscenio_codegen.godot_emit`. Populate `apps/godot/addons/proscenio/schema_bindings/`. Importer accepts `Resource` instead of `Dictionary`. Turn on unsafe-warnings family. | High. Importer is the biggest module; needs incremental migration alongside the warning bump. |
| **P5.** Docs pipeline | Add `proscenio_codegen.docs_emit`. Populate `docs/content/api/schemas/`. Docusaurus wiring in the `docs/` site (if not already present - the site itself may be its own deferred item, but the generated MD is producible regardless). | Low. Generated MD is additive. |
| **P6.** Stricter typing flags | mypy extras, tsc extras, GDScript unsafe family. One PR per language. | Low-Medium. Each flag will surface a finite list of fixes; do them inline. |

Phases P1-P2 + P6/Python are the smallest viable cut and ship value without touching the other apps.

## Design decisions (locked)

| ID | Question | Locked answer |
| --- | --- | --- |
| D1 | Source of truth | **pydantic v2**, bundled via wheels in the Blender extension manifest. Pure-Python pydantic + Rust-backed pydantic-core; pre-compiled wheels per platform (Linux x64/arm64, macOS x64/arm64, Windows x64) declared under `wheels = [...]` in `blender_manifest.toml`. |
| D2 | Generated artifact location | **Checked in.** Per-app `schema_bindings/` folders (TS + GDScript bindings); `packages/models/schemas/` for the dumped JSON Schema. CI verifies staleness on every PR. |
| D3 | `format_version` policy | Models carry `Literal["v1"]`. Future v2 lives in a separate module + `migrations/v1_to_v2.py` adapter, same shape as the current writer migrators. Pre-1.0 / PoC scope is free to break and replace without compatibility guarantees; the migrator pattern formalises once 1.0 lands. |
| D4 | GDScript layer | **Typed `Resource` classes** with `@export` vars + `from_dict` parsers. Custom Python emitter in `packages/codegen/src/proscenio_codegen/godot_emit.py` (estimated ~150-250 LOC). |
| D5 | TypeScript runtime guard | **Keep ajv** (consumes JSON Schema directly; smaller bundle; mature discriminated-union handling). Generated TS interfaces from `json-schema-to-typescript`. Revisit `z.fromJSONSchema()` once it leaves experimental and `json-schema-to-zod` matures its discriminated-union support (currently flagged "here be dragons" in its README). |
| D6 | Stricter-typing rollout | **One PR per language** (mypy / tsc / GDScript warnings tightened independently). Each PR surfaces a finite list of fixes; per-language scope keeps the noise bounded. |
| D7 | Docs site | **Generate markdown artifacts only**, fed into Docusaurus later as a separate chore. Documentation extracted from the pydantic models themselves (descriptions, types, discriminators); not extracted from docstrings or hand-written prose. Code is the source of truth. |
| D8 | Schema location | **`packages/models/schemas/`** (dumped artifacts living next to the models that produced them). Top-level `schemas/` folder deleted progressively: `proscenio.schema.json` at the end of P2, `psd_manifest.schema.json` at the end of P3. |
| D9 | TypeScript codegen tool | **`json-schema-to-typescript`** consumes the generated JSON Schema and emits TS interfaces. Standard tool, mature discriminated-union support, already aligned with the ajv runtime path. Wires into the existing webpack pipeline as a pre-build step. |
| D10 | Codegen tool shape | **One Python package (`packages/codegen/`) with helper modules per target and a single CLI coordinator.** Avoids both the fat-script and four-separate-scripts traps; shared `_io.py` lives in one place; TS / docs invocations go through `subprocess` (no shell scripts). |
| D11 | Per-app binding folder name | **`schema_bindings/`** (locked in [the monorepo packages spec](../015-monorepo-packages/STUDY.md) D3). Used in `apps/photoshop/src/schema_bindings/` and `apps/godot/addons/proscenio/schema_bindings/`. |

## Open questions (resolved)

| OQ | Outcome |
| --- | --- |
| OQ1 - pydantic in Blender's bundled Python | **Resolved: bundle wheels in the extension manifest.** Blender does not ship pydantic, but Blender 4.2+ supports declaring third-party wheels under `wheels = [...]` in `blender_manifest.toml`. pydantic v2 + pydantic-core ship pre-compiled platform wheels on PyPI; the `--split-platforms` build flag produces per-platform extension zips when bundle size becomes a concern. |
| OQ2 - pydantic + `bpy.props` on the same class | **Resolved: no.** Models live as plain pydantic in `packages/models/`, entirely outside the bpy class graph. bpy classes hold references to pydantic instances or transient data only. Documented as a guideline in this spec's implementation rules. |
| OQ3 - discriminated unions across emitters | **Resolved: smoke test in the first implementation PR.** P1 includes a fixture covering the `Sprite.type` discriminated union round-tripped through pydantic -> JSON Schema -> `json-schema-to-typescript`. If the generated TS is degraded, fix at codegen layer before continuing. |
| OQ4 - `.ai/skills/format-spec.md` source of truth | **Resolved: yes.** Once schemas move to `packages/models/schemas/`, the skill page points readers at the pydantic model file (`packages/models/src/proscenio_models/proscenio.py`) as the canonical source. Update lands in the docs-pass PR. |

## Out of scope (deferred)

- GDScript class doc -> Markdown (mirror of Firebound's `processApiFiles.js` for `--doctool` XML). Deferred until phase P5 lands; revisit when the Godot side has stabilized after P4.
- TypeDoc for the Photoshop plugin's React surface. The plugin is small; useful docs there are conceptual, not API-reference.
- Property-based testing against the generated schemas (hypothesis). Worth a future spec once models exist.
- Migration scripts beyond the current `format_version=1` baseline. No new bump is planned here.

## Acceptance (when this spec ships)

A future "this spec is done" looks like:

- Every cross-component JSON document is `model_dump()` of a pydantic model in `packages/models/`.
- `packages/models/schemas/*.schema.json` is reproducible from `python -m proscenio_codegen schemas`.
- `apps/photoshop/src/schema_bindings/*.ts` and `apps/godot/addons/proscenio/schema_bindings/*.gd` exist and are imported by their respective apps.
- `docs/content/api/schemas/*.md` is reproducible and (optionally) consumed by Docusaurus.
- mypy / tsc / Godot warnings are tightened per Axis C and the build is green at the new strictness.
- A schema field added in pydantic flows automatically to all three consumers; a consumer that does not adapt fails its build, not its runtime.
- The top-level `schemas/` folder no longer exists.
