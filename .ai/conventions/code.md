# Code: JSON keys, module organization, typing, validation

Cross-component data shapes, Blender addon module layout, static typing per language, and the layered validation gates. Part of the [agent and contributor reference](../README.md).

## JSON keys

Cross-component JSON formats (`.proscenio`, PSD manifest) use `snake_case` keys throughout. The pydantic models under `packages/models/` are the source of truth (the JSON Schemas under `packages/models/schemas/` are generated from them) - any new field must follow the same rule and be added to the model before being emitted or consumed.

## Module organization (Blender addon)

Every concern lives in its own module; `__init__.py` orchestrates registration only.

- Addon root chains `register()` / `unregister()` of `properties`, `operators`, `panels` in dependency order (properties first; panels last).
- `operators/`, `panels/`, `properties/` are packages, not single files. Each subpackage `__init__.py` is a thin orchestrator that imports topical submodules and calls each submodule's `register()` / `unregister()` in turn. No operator or panel class definitions live in `__init__.py`.
- One submodule per topical concern. Aim for around 300 LOC per submodule. Above that, ask whether the file has absorbed multiple concerns - if yes, split. Treat the budget as a smell threshold, not a hard ceiling.
- **Single Responsibility at function level too.** If a function does 3 distinct steps separated by blank-line "paragraphs" or by comments like `# Step 2: ...`, those are 3 helper extractions waiting to happen. Cognitive complexity > 15 (Sonar S3776) is the mechanical signal; the readability signal is the same one humans use when their eyes glaze over scrolling past the function. Extract before either signal fires twice on the same function.
- **No premature abstraction.** Three similar lines is not a Repository. Two operators that read the same property are not a Service. Patterns earn their keep by removing duplication that ALREADY exists - never by anticipating duplication that might. Reach for `@dataclass` / `TypedDict` / `Literal` first; reach for inheritance / mixins / registries only when concrete duplication has accumulated and a one-line constructor swap would not have solved it.
- **Domain packages for features.** When a feature grows past one or two modules, group its files in a domain package: `core/<feature>/` for pure-Python helpers + `core/bpy_helpers/<feature>/` for the bpy-bound bridge. The package's `__init__.py` re-exports the public surface (functions / classes external callers use). New features adopt this layout from day one. The goal is "open `core/` and see domains, not 30 mixed files". `core/` and `core/bpy_helpers/` are grouped this way per system (`automesh/`, `skinning/`, `validation/`, `atlas/`, `slot/`, `sprite_frame/`, `psd/`, `armature/`); cross-cutting infrastructure that belongs to no single system lives in a `_shared/` package on each side (cp_keys, report, props_access, viewport math, geometry, the bpy compat shims), the leading underscore sorting it above the system folders. `operators/` mirrors this: a feature with two or more operators gets its own subpackage (`operators/automesh/`, `operators/skinning/`, `operators/armature/`, `operators/slot/`, `operators/atlas_pack/`); single-operator features stay flat. A genuinely single-module feature stays a flat file - do not wrap one module in a folder.
- Cross-cutting helpers shared by sibling submodules go in a `_helpers.py` (or similar private-prefixed module) - the underscore signals "module-internal, not the public API".
- `core/` holds bpy-free helpers. Direct children of `core/` import nothing from `bpy` at module top. They may lazy-import `bpy` inside one function and accept `Any`-typed inputs.
- `core/bpy_helpers/` (or equivalent) holds bpy-bound helpers. Modules there import `bpy` at module top. Tests either patch `bpy` first or skip when running outside Blender.
- Re-export per-validator subpackages from a single `__init__.py` so callers depend on the package, not on internal submodules.
- The Godot exporter is a package with submodules split per emission concern (skeleton, sprites, slots, animations, ...). The `__init__.py` re-exports the public `export()` entry.
- Custom Property string keys live in one single-source-of-truth module - every literal key goes there.
- Operator user-facing reports go through one shared report helper so the `"Proscenio: "` prefix lives in one place.
- Cross-package import direction: `panels` -> `operators` (only via `bl_idname` strings, never direct class imports) -> `core`. `properties` -> `core`. No cycles.

## Static typing

Both languages we target support full static typing. Use it everywhere. Type errors caught at parse time cost zero; type errors caught at runtime cost a Blender re-launch or a Godot reimport.

### GDScript (Godot plugin)

GDScript 2.0 has full static typing. The plugin is 100% typed.

- Variables: `var x: int = 0`, `var bones: Array[Bone2D] = []`. Never `var x = 0`.
- Function signatures: every parameter typed, every return typed. Use `-> void` explicitly when no return.
- Typed collections: `Array[T]`, `Dictionary[K, V]` whenever element types are known and stable. Bare `Dictionary` is acceptable at the JSON decode boundary (`JSON.parse` returns `Variant`); downcast as soon as the shape is known.
- `class_name` on every script that is loaded by name.
- Signals: declare typed (`signal imported(path: String)`).
- Constants: `const FOO: int = 1`. Type-annotate even when the literal infers cleanly - explicit beats implicit.
- `@export` vars must be typed.
- The Godot project is configured to treat warnings as errors and to enforce typed declarations. Lint enforces the same in CI.

### Python (Blender addon, scripts)

- Full type hints on every function signature.
- `from __future__ import annotations` at the top of new files - with one carve-out: any class registered via `bpy.utils.register_class` (Operator, PropertyGroup, Panel, Header, etc.) that **declares `bpy.props.*Property` annotations and references TYPE_CHECKING-only types in sibling `ClassVar` annotations** must drop PEP 563 from that file. Blender 5.x calls `typing.get_type_hints(cls)` at register time and a single `NameError` from a TYPE_CHECKING-imported name aborts the whole annotation walk silently, so no bpy.props ever promotes to RNA. Import the referenced types at module top (not under `TYPE_CHECKING`) and document the constraint in the module docstring. See `apps/blender/operators/quick_armature.py` for the reference setup and `tests/BUGS_FOUND.md` post-mortem for the long-form rationale.
- Strict static analysis is part of CI; warnings fail the build. `Any` is allowed only at the `bpy` boundary, documented inline.
- Prefer `@dataclass` / `TypedDict` over loose dicts when shape is known. Use `Literal[...]` over raw strings for closed value sets (track type, interpolation, severity, ...).

### TypeScript (Photoshop UXP plugin)

- `strict` TypeScript with `noImplicitAny`, `noImplicitReturns`, `noFallthroughCasesInSwitch`. No `any` outside narrow adapter boundaries.
- React function components with hooks. No class components. One hook per file under a `useXxx` name.
- Keep the panel a thin composition: panels and components render, hooks own state, `lib/` modules stay pure (no UXP API imports), `api/` is the single Photoshop-boundary tier (document/layer reads, notifications, batchPlay, file writes). Layered direction: `panels -> hooks -> api + lib` (components are leaf UI, utils are leaf helpers). Purity rule: nothing in `lib/` may import a UXP module; a hook or panel that needs the live document goes through `api/`, never `import { app } from "photoshop"` directly. The `@ts-nocheck` host shim is `src/entry.ts` (the only file exempt from the typed gate).
- Validate cross-process payloads (manifest JSON) at the boundary with a schema-driven runtime check (ajv against the manifest schema). Treat schema mismatch as a hard fail.
- Prefer discriminated unions over loose `string` tags for closed sets (`kind: "polygon" | "sprite_frame" | "mesh"`).

## Validation gates

Prefer failing fast at the earliest possible layer over discovering bugs through Blender re-launches and Godot reimports. Layered defenses, cheapest first:

### Editor / IDE

- Live diagnostics through the standard typed-language extensions for each app (Pylance for Python, gdtoolkit for GDScript, TypeScript LSP for TS). Project-local settings carry the per-repo overrides.
- The Godot project treats warnings as errors so live editor warnings break the import. Untyped declarations are an error; the unsafe-access family is tuned for the JSON boundary where downcasts are unavoidable. Do not put comments inside `[debug]` in `project.godot` - the editor's serializer mangles them on save.

### Pre-commit hooks

A single pre-commit pipeline runs the per-language formatters and linters (ruff + mypy for Python, gdformat + gdlint for GDScript), schema validation against staged JSON files, plus a shared spell-checker. Install once and let it run on every commit. Skipping hooks (`--no-verify`) is treated as a bug - fix the underlying issue.

### Static analysis

- Strict mypy for the Blender addon's typed surface. `Any` only at the `bpy` boundary, documented inline.
- Strict gdlint with typed-everything, `class_name` required, no untyped signals.
- Ruff with the standard quality lint families enabled (errors, imports, bugbear, pyupgrade, naming, ruff-specific, simplify). Blender's `CATEGORY_OT_*` / `CATEGORY_PT_*` naming requirements are exempted from the naming family. The same exemption is mirrored in `sonar-project.properties` via `sonar.issue.ignore.multicriteria` for python:S101 - Sonar does not read ruff config, so any tooling that gates on Sonar issues must carry the exemption too.
- `tsc --noEmit` typecheck for the Photoshop plugin.
- A repo-wide spell-checker with project-specific dictionaries.

### Schema as a contract

The cross-component JSON schemas are the only shared truth between apps. Each format is enforced at three or four points:

1. Writer output is schema-validated before any test diff against a golden fixture. The exporter cannot ship a document the importer would reject.
2. Importer / consumer input is validated at runtime (ajv on the Photoshop side, format-version guard on the Godot side) and surfaces clear errors per missing field.
3. CI validates every fixture under `examples/` and per-app `tests/fixtures/` against the schema.
4. Future migrators consume the version guard - on a breaking shape change, every fixture either migrates or breaks loudly.

### Domain types over loose dicts

In Python, model JSON shapes as `TypedDict` or `dataclass` inside the writer. In TypeScript, model them as discriminated unions or `interface` types and validate at the boundary. In GDScript, prefer `class_name`'d helper resources over bare `Dictionary` once the shape stabilises.

### Defensive throws / asserts

Cheap to write, expensive to skip. In Python, raise `RuntimeError` at the boundary with a context-rich message. In GDScript, `assert(condition, msg)` is stripped from release builds - useful for invariants documented as code. In TypeScript, `throw new Error(...)` early-fails the operation with a usable message.

### Test discipline

Golden-fixture tests for both writer and importer. Negative-case fixtures (intentionally invalid payloads) live alongside the positive ones and assert that the consumer surfaces the right error.

### Headless operator pytest pattern

Introduced for the weight-paint bind operator. Use this layer when an operator's behavior depends on bpy state (vertex groups, custom properties, scene PG) that pure pytest cannot exercise.

Layout:

- Tests live under `apps/blender/tests/operators/<feature>.py`.
- `apps/blender/tests/operators/conftest.py` mounts the addon as `proscenio`, calls `register()`, and provides the `automesh_fixture` fixture (fresh-loads `examples/generated/automesh/automesh.blend` per test).
- `apps/blender/tests/run_operator_tests.py` is the CI entry: `blender --background --python apps/blender/tests/run_operator_tests.py` runs `pytest.main` on the operators dir.

When a new operator needs this layer:

1. Create `apps/blender/tests/operators/test_<operator>.py`.
2. Use the `automesh_fixture` (or write a new fixture if a different .blend is needed).
3. Assert against `bpy.data` / `bpy.context` state + the operator's return set. Note: `bpy.ops` raises `RuntimeError` when an operator reports `{"ERROR"}` and returns `{"CANCELLED"}` - use `pytest.raises(RuntimeError, match="...")` for tests that exercise the abort path.
4. CI already runs every test in the operators dir - no workflow edits needed.

Trade-off: each test pays the cost of loading the fixture .blend (~hundreds of ms). Keep tests focused; share setup via fixtures, not via test ordering.
