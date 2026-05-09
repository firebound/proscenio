# Conventions — Proscenio

Inspired by the FairCut conventions, adapted to Proscenio's polyglot pipeline (Python + GDScript + JSX + a JSON schema as contract).

## Branches

```text
feat/<slug>                   # Feature — outside a SPEC
feat/spec-<NNN>-<slug>        # Feature — implementation of a numbered SPEC
fix/<slug>                    # Bug fix
fix/spec-<NNN>-<slug>         # Bug fix tied to a SPEC
docs/<slug>                   # Documentation only
refactor/<slug>               # Refactor without behavior change
chore/<slug>                  # Maintenance, tooling, configs
ci/<slug>                     # Workflow changes
```

Branch names follow the [Conventional Commits](https://www.conventionalcommits.org/) prefix vocabulary. SPEC implementation work uses the same prefixes; the SPEC number is embedded after the prefix as a stable, searchable token.

Examples: `feat/spec-003-skinning-weights`, `feat/photoshop-json-importer`, `fix/godot-bone-y-flip`, `chore/install-dev`.

When an issue exists, reference it in the commit body (`Refs: #42`), not in the branch name. Keep branch names readable.

## Workflow

- **`main`** holds planning artifacts (`specs/<NNN>-…/STUDY.md` and `TODO.md`, `specs/backlog.md`) and small chores. Spec docs land directly on `main` because they cross PR boundaries and inform parallel work.
- **`feat/spec-<NNN>-<slug>`** (or `fix/`, `chore/` if the SPEC's nature warrants) holds the implementation of a numbered SPEC. Branch from `main` once the SPEC's STUDY/TODO are reviewed. Commit gradually as TODO items close. Open a PR back to `main` when the TODO is satisfied.
- **Branches without the `spec-NNN-` infix** are for work that does not belong to a numbered SPEC.

Prefer many small commits on the working branch over a single squashed lump — the merge can squash if needed, but the branch history is the audit trail while work is in flight.

## Files and folders

| Convention | Used for |
| --- | --- |
| `snake_case.py` | Python modules |
| `PascalCase` | Python class names |
| `PROSCENIO_OT_*` / `PROSCENIO_PT_*` | Blender operator and panel class names (Blender requirement — `bpy.utils.register_class` validates the `CATEGORY_OT_name` / `CATEGORY_PT_name` shape; ruff `N801` and Sonar `python:S101` are silenced) |
| `snake_case.gd` | GDScript files — one class per file |
| `PascalCase` | GDScript `class_name` |
| `kebab-case` | Config and workflow file names (`.editorconfig`, `release.yml`) |
| `lower-case-no-spaces.proscenio` | Asset files |
| `UPPER_SNAKE_CASE` | Module-level constants |

## JSON keys

The `.proscenio` format uses `snake_case` keys throughout (`format_version`, `pixels_per_unit`). Any new field must follow this rule. The schema in [`schemas/proscenio.schema.json`](../schemas/proscenio.schema.json) is the source of truth.

## Module organization (Blender addon)

Established by SPEC 009. Every concern lives in its own module; `__init__.py` orchestrates registration only.

- `blender-addon/__init__.py` — addon root. Imports `properties`, `operators`, `panels` packages and chains their `register()` / `unregister()` in dependency order (properties first; panels last).
- `operators/`, `panels/`, `properties/` — packages, not single files. Each subpackage `__init__.py` is a thin orchestrator that imports topical submodules and calls each submodule's `register()` / `unregister()` in turn. No operator or panel class definitions live in `__init__.py`.
- One submodule per topical concern. Examples: `operators/export_flow.py`, `operators/quick_armature.py`, `operators/slot/create.py`, `panels/active_sprite.py`, `panels/outliner.py`. Aim for under ~300 LOC per submodule.
- Cross-cutting helpers shared by multiple sibling submodules go in `_helpers.py` (panels) or `_paths.py` / `_handlers.py` / `_dynamic_items.py` (private prefix conveys "module-internal, not the public API").
- `core/` — bpy-free helpers. Direct children of `core/` import nothing from `bpy` at module top. They may lazy-import `bpy` inside one function and accept `Any`-typed inputs from tests.
- `core/bpy_helpers/` — bpy-bound helpers. Modules under this subpackage import `bpy` at module top. Tests that touch them either patch `bpy` first or skip when running outside Blender.
- `core/validation/` — per-validator subpackage with `Issue`, `validate_active_sprite`, `validate_active_slot`, `validate_export`. Re-exports the public API from its `__init__.py`.
- `exporters/godot/writer/` — package, not single file. Submodules per emission concern (`scene_discovery`, `skeleton`, `sprites`, `slots`, `slot_animations`, `animations`). The `__init__.py` re-exports the public `export()` entry.
- Custom Property string keys live in `core/cp_keys.py` (single source of truth, every `proscenio_*` literal goes there).
- Operator user-facing reports go through `core/report.py` (`report_info` / `report_warn` / `report_error`) so the `"Proscenio: "` prefix lives in one place.
- Cross-package import direction: `panels` → `operators` (only via `bl_idname` strings, never direct class imports) → `core`. `properties` → `core`. No cycles.

When a single file grows past ~300 LOC, ask whether it has absorbed multiple concerns. If yes, split it.

## Static typing

Both first-class languages in this repo support static typing. **Use it everywhere — do not ship dynamic code when typed code is available.**

### GDScript (Godot plugin)

GDScript 2.0 has full static typing. The plugin must be 100% typed.

- **Variables:** `var x: int = 0`, `var bones: Array[Bone2D] = []`. Never `var x = 0`.
- **Function signatures:** every parameter typed, every return typed (`func build(data: Dictionary) -> Skeleton2D:`). Use `-> void` explicitly when no return.
- **Typed collections:** `Array[T]`, `Dictionary[K, V]` (Godot 4.4+) over bare `Array` / `Dictionary` whenever the element type is known.
- **`class_name`** on every script that is loaded by name.
- **Signals:** declare typed (`signal imported(path: String)`).
- **Constants:** `const FOO: int = 1`. Type-annotate even when the literal infers cleanly — explicit beats implicit.
- **`@export`** vars must be typed. Use `@export var atlas: Texture2D` not `@export var atlas`.
- `gdlint` runs in CI; treat any "untyped" warning as a build break.

### Python (Blender addon, scripts)

- Full type hints on every function signature.
- Use `from __future__ import annotations` at the top of new files.
- Pylance / mypy clean before commit. `Any` is allowed only at the `bpy` boundary.
- Prefer `dataclass` / `TypedDict` over loose dicts when shape is known.

### Why

Type errors caught at parse time cost zero. Type errors caught at runtime cost a Blender re-launch or a Godot reimport plus head-scratching. The asymmetry pays for the typing discipline several times over.

## Validation gates

The repo prefers **failing fast** at the earliest possible layer over discovering bugs through Blender re-launches and Godot reimports. Layered defenses, in order of cheapness:

### Editor / IDE

- **VS Code** Pylance + SonarLint + cspell + gdtoolkit live diagnostics. `.vscode/settings.json` carries the project-specific overrides.
- **Pyright config** at repo root resolves `bpy` / `mathutils` stubs as missing-but-OK and adds `blender-addon` to `extraPaths`.
- **Blender's "Treat warnings as errors"** is too coarse for an addon shipped to users; relying on Pylance + ruff suffices.
- **Godot project** sets `debug/gdscript/warnings/treat_warnings_as_errors=true` so live editor warnings break the import. `untyped_declaration=2` enforces typing; the four `unsafe_property_access` / `unsafe_method_access` / `unsafe_cast` / `unsafe_call_argument` keys are pinned to `0` because `JSON.parse` returns `Variant` by design and the importer/builders downcast — without these pinned, every line at the JSON boundary would need a `# warning-ignore`. Mirrored by `gdlint` in CI. **Do not put comments inside `[debug]` in `project.godot`** — Godot's project-settings serializer mangles them when the editor saves.

### Pre-commit hooks

A single `.pre-commit-config.yaml` runs all of: `ruff check`, `ruff format`, `mypy --strict`, `gdformat --check`, `gdlint`, `cspell`, and `check-jsonschema` against staged `.proscenio` files. Install once with `pip install pre-commit && pre-commit install`. Treat any local skip (`--no-verify`) as a bug — fix the underlying issue.

### Static analysis

- **`mypy --strict`** for `blender-addon/` and `scripts/`. `Any` only at the `bpy` boundary (documented inline). `pyproject.toml` carries the config.
- **`gdlint`** with strict typing rules in `.gdlintrc`: typed everything, `class_name` required, no untyped signals, no magic numbers.
- **`ruff check`** with `E`, `F`, `I`, `B`, `UP`, `N`, `RUF`, `SIM` selected.
- **`cspell`** custom dictionaries under `.cspell/` cover project-specific vocabulary.

### Schema as a contract

The `.proscenio` JSON Schema is the only cross-component truth. It is enforced at **three** points:

1. **Writer output** — `blender-addon/tests/run_tests.py` schema-validates the freshly exported `.proscenio` before diffing against the golden fixture. The exporter cannot ship a document the importer would reject.
2. **Importer input** — `godot-plugin/addons/proscenio/importer.gd` checks `format_version` and surfaces a clear error per missing field. Future migrators consume the version guard.
3. **CI fixtures** — `.github/workflows/ci.yml` runs `check-jsonschema` against every `.proscenio` in `examples/` and `tests/fixtures/`.

When v2 lands, the same gate ensures every existing fixture either migrates or breaks loudly — no silent drift.

### Domain types over loose dicts

In Python, model `.proscenio` shapes as `TypedDict` (or `dataclass`) inside the writer. In GDScript, prefer `class_name`'d helper resources over bare `Dictionary` once shape stabilizes. In both languages: enums (Python `Literal[...]`, GDScript `@export_enum`) over raw strings for closed value sets (track type, interpolation type, etc).

### Defensive throws / asserts

Cheap to write, expensive to skip. In Python, raise `RuntimeError` at the boundary with a context-rich message (`"Proscenio export needs an Armature in the scene"`). In GDScript, `assert(condition, msg)` is stripped from release builds — useful for invariants documented as code. In ExtendScript, `throw new Error(...)` early-fails the script with a usable message.

### Test discipline

Golden-fixture tests for both writer and importer (see [`.ai/skills/testing.md`](skills/testing.md)). Negative-case fixtures (intentionally invalid `.proscenio`) belong in `tests/fixtures/invalid/` and assert the importer surfaces the right error.

## Versioning

Three independent SemVer streams plus one integer schema version:

| Stream | Tag prefix |
| --- | --- |
| Photoshop exporter | `photoshop-exporter-vX.Y.Z` |
| Blender addon | `blender-addon-vX.Y.Z` |
| Godot plugin | `godot-plugin-vX.Y.Z` |

`schemas/proscenio.schema.json` carries its own integer `format_version`, independent of component versions. Bump only on a breaking change to the document shape.

A schema change is a multi-component PR by definition (schema bump + Blender exporter + Godot importer guard). See [`.ai/skills/format-spec.md`](skills/format-spec.md).

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
| `test` | Tests |
| `chore` | Maintenance, tooling, configs |
| `ci` | CI workflow changes |

### Scopes

| Scope | Area |
| --- | --- |
| `blender` | Blender addon |
| `godot` | Godot plugin |
| `photoshop` | Photoshop JSX exporter |
| `schema` | `.proscenio` format schema |
| `skills` | `.ai/skills/` and `.ai/conventions.md` |
| `specs` | Planning specs under `specs/` |
| `docs` | User-facing docs (future `docs/` site) |
| `ci` | Workflows in `.github/` |
| `repo` | Root meta (license, configs, `.gitattributes`, etc.) |

### Examples

```text
feat(blender): add Photoshop JSON importer
fix(godot): flip Y on bone transform tracks
feat(schema): bump format_version to 2 for cubic interpolation
docs(skills): clarify reimport merge algorithm
chore(repo): pin ruff version in pyproject
```

## Pull requests

### Title

Same format as the commit subject:

```text
feat(blender): add Photoshop JSON importer
```

### Description

1. **What changed** — short summary.
2. **Why** — motivation if non-obvious.
3. **How to test** — concrete steps, including which Blender or Godot version.
4. **Schema impact** — if `format_version` bumped, link to the migration note.

### Template

```markdown
## What changed
<!-- one or two sentences -->

## Why
<!-- only if non-obvious -->

## How to test
<!-- concrete steps -->

## Checklist
- [ ] Lint passes (`ruff check` and/or `gdlint`)
- [ ] Tests pass (Blender headless and/or GUT)
- [ ] Schema validates against examples and fixtures
- [ ] If `format_version` changed, migration documented
```

## Code review

What to review:

1. **Correctness** — does it do what the PR claims?
2. **Boundary discipline** — Photoshop knows nothing of Blender; Blender knows nothing of Godot internals; Godot reads only `.proscenio`. See [`.ai/skills/architecture.md`](skills/architecture.md).
3. **Schema fidelity** — exporter output and importer input both match `schemas/proscenio.schema.json`.
4. **No GDExtension creep** — Godot side stays pure GDScript with built-in nodes only.
5. **Reload safety** — Blender addon `register()` / `unregister()` symmetry, no leaked classes.
6. **Test coverage** — non-trivial logic gets a fixture or a unit test.

What not to review:

- Code style — `ruff` and `gdformat` handle it.
- Personal preferences when a convention already chose.
- Formatting — covered by the editor and lint hooks.
