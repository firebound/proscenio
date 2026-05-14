# Conventions - Proscenio

These rules guide both humans and LLM agents. The repo houses three apps - a Photoshop UXP plugin (TypeScript + React), a Blender addon (Python), and a Godot integration plugin (GDScript). Each follows the same spirit: typed, cohesive, readable, and small. Prefer SOLID and DRY in moderation - clarity beats clean-arch ceremony.

## Branches

```text
feat/<slug>                   # Feature
fix/<slug>                    # Bug fix
docs/<slug>                   # Documentation only
refactor/<slug>               # Refactor without behavior change
chore/<slug>                  # Maintenance, tooling, configs
test/<slug>                   # Tests only
ci/<slug>                     # Workflow changes
```

Prefix vocabulary matches [Conventional Commits](https://www.conventionalcommits.org/). When the work implements a numbered SPEC, embed the number after the prefix as a stable search token: `feat/spec-<NNN>-<slug>`. The SPEC infix is a navigation aid, not a hard gate - omit it when the work is component-wide rather than SPEC-driven.

Examples: `feat/spec-003-skinning-weights`, `feat/photoshop-ui`, `fix/blender-bugs`, `chore/install-dev`.

Reference issues in the commit body (`Refs: #42`), not in the branch name. Keep branch names readable.

## Workflow

- `main` holds planning artifacts (SPEC studies and TODOs, backlogs) and small chores. Planning docs land directly on `main` because they cross PR boundaries and inform parallel work.
- Implementation work lives on a topic branch (typically `feat/spec-<NNN>-<slug>` or `fix/<slug>`) and merges back via PR.
- Commit gradually as work progresses. The merge can squash if the PR scope warrants it, but the branch history is the audit trail while work is in flight. A long PR benefits from many small commits; a tight bugfix is fine as one.

## Files and folders

| Convention | Used for |
| --- | --- |
| `snake_case.py` | Python modules |
| `PascalCase` | Python class names |
| `CATEGORY_OT_*` / `CATEGORY_PT_*` | Blender operator and panel class names (Blender requirement validated at register time; lint naming rules silenced for these) |
| `snake_case.gd` | GDScript files - one class per file |
| `PascalCase` | GDScript `class_name` |
| `PascalCase.tsx` | React components |
| `useCamelCase.ts` | React hooks |
| `kebab-case.ts` | TypeScript modules |
| `camelCase` | TS variables, functions, props |
| `PascalCase` | TS types, interfaces, classes |
| `kebab-case` | Config and workflow file names |
| `lower-case-no-spaces.proscenio` | Asset files |
| `UPPER_SNAKE_CASE` | Module-level constants |

## JSON keys

Cross-component JSON formats (`.proscenio`, PSD manifest) use `snake_case` keys throughout. The schemas under `schemas/` are the source of truth - any new field must follow the same rule and be added to the schema before being emitted or consumed.

## Module organization (Blender addon)

Every concern lives in its own module; `__init__.py` orchestrates registration only.

- Addon root chains `register()` / `unregister()` of `properties`, `operators`, `panels` in dependency order (properties first; panels last).
- `operators/`, `panels/`, `properties/` are packages, not single files. Each subpackage `__init__.py` is a thin orchestrator that imports topical submodules and calls each submodule's `register()` / `unregister()` in turn. No operator or panel class definitions live in `__init__.py`.
- One submodule per topical concern. Aim for around 300 LOC per submodule. Above that, ask whether the file has absorbed multiple concerns - if yes, split. Treat the budget as a smell threshold, not a hard ceiling.
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
- `from __future__ import annotations` at the top of new files.
- Strict static analysis is part of CI; warnings fail the build. `Any` is allowed only at the `bpy` boundary, documented inline.
- Prefer `@dataclass` / `TypedDict` over loose dicts when shape is known. Use `Literal[...]` over raw strings for closed value sets (track type, interpolation, severity, ...).

### TypeScript (Photoshop UXP plugin)

- `strict` TypeScript with `noImplicitAny`, `noImplicitReturns`, `noFallthroughCasesInSwitch`. No `any` outside narrow adapter boundaries.
- React function components with hooks. No class components. One hook per file under a `useXxx` name.
- Keep the panel a thin composition: components render, hooks own state, domain modules stay pure (no UXP API imports), io / adapters touch the Photoshop API. Layered direction: panels -> hooks / controllers -> domain + io -> adapters.
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
- Ruff with the standard quality lint families enabled (errors, imports, bugbear, pyupgrade, naming, ruff-specific, simplify). Blender's `CATEGORY_OT_*` / `CATEGORY_PT_*` naming requirements are exempted from the naming family.
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

## Versioning

Three independent SemVer streams plus one integer schema version per cross-component format:

| Stream | Tag prefix |
| --- | --- |
| Photoshop plugin | `photoshop-vX.Y.Z` |
| Blender addon | `blender-vX.Y.Z` |
| Godot plugin | `godot-vX.Y.Z` |

Each cross-component JSON schema carries its own integer `format_version`, independent of component versions. Bump only on a breaking change to the document shape.

A schema change is a multi-component PR by definition (schema bump + producer + consumer guard).

## Commits

### Grouping

- One commit per cohesive unit of work.
- Do not mix components in a single commit unless the change is a schema bump (which crosses by design).
- Prefer short subjects; use the body only when the *why* is non-obvious.

### Format

Conventional Commits:

```text
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Use for |
| --- | --- |
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Refactor without behavior change |
| `style` | Formatting, whitespace, no behavior change |
| `perf` | Performance improvement |
| `test` | Tests |
| `chore` | Maintenance, tooling, configs |
| `ci` | CI workflow changes |

### Scopes

Scope is the area touched. Use the smallest label that lets a reader locate the change. Recommended top-level scopes:

| Scope | Area |
| --- | --- |
| `blender` | Blender addon |
| `godot` | Godot plugin |
| `photoshop` | Photoshop UXP plugin |
| `schema` | Cross-component JSON schemas |
| `specs` | Planning specs |
| `ci` | CI workflows |
| `repo` | Root meta (license, configs, dotfiles) |

Sub-scopes like `photoshop/runtime` or `fixtures/doll` are allowed when they aid navigation. Keep them kebab-case, short, and consistent across a PR. Avoid one-off feature names as scopes unless they refer to a long-lived module.

### Examples

```text
feat(blender): add Photoshop JSON importer
fix(godot): flip Y on bone transform tracks
feat(schema): bump format_version to 2 for cubic interpolation
chore(repo): pin ruff version
```

## Pull requests

### Title

Same format as the commit subject:

```text
feat(blender): add Photoshop JSON importer
```

### Description

1. What changed - short summary.
2. Why - motivation if non-obvious.
3. How to test - concrete steps, including which Blender / Godot / Photoshop version.
4. Schema impact - if `format_version` bumped, link to the migration note.

### Template

```markdown
## What changed
<!-- one or two sentences -->

## Why
<!-- only if non-obvious -->

## How to test
<!-- concrete steps -->

## Checklist
- [ ] Per-language lint and format pass
- [ ] Per-language typecheck passes
- [ ] Tests pass for the affected app
- [ ] Schemas validate against examples and fixtures
- [ ] If `format_version` changed, migration documented
```

## Code review

What to review:

1. Correctness - does it do what the PR claims?
2. Boundary discipline - Photoshop knows nothing of Blender; Blender knows nothing of Godot internals; Godot reads only the exported document. Cross-component contracts go through the schema, not through shared code.
3. Schema fidelity - producer output and consumer input both match the schema.
4. No GDExtension creep - the Godot side stays pure GDScript with built-in nodes only.
5. Reload safety - Blender addon `register()` / `unregister()` symmetry, no leaked classes.
6. Test coverage - non-trivial logic gets a fixture or a unit test.
7. Cohesion and size - if a file or function has grown past the comfortable reading window, consider splitting before merging.

What not to review:

- Code style - formatters handle it.
- Personal preferences when a convention already chose.
- Formatting - covered by the editor and lint hooks.
