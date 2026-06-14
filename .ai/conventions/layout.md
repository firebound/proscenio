# Repository layout, files, and versioning

Where code lives, how files are named, and how releases are versioned. Part of the [agent and contributor reference](../README.md).

## Repository layout

The repo is a uv-managed Python workspace alongside the Photoshop and Godot apps.

```text
apps/        self-contained apps: the pipeline plugins (blender/, photoshop/, godot/) plus the docs site (docs/)
packages/    shared building blocks consumed by apps (models, codegen, fixtures, validator)
scripts/     one-off, run-directly helpers (single file, no own dependencies); co-located at the root, per-package, or per-example
tools/       standalone dev/QA tools that are their own package (own deps/build/tests; not shipped, not a shared lib), e.g. tools/qa-companion/
specs/       planning artifacts (numbered specs, backlog, decisions)
tests/       repo-level cross-app integration tests
docs/        Docusaurus content
.ai/         agent-facing conventions and skills
```

Rules:

- New shared code goes under `packages/`, not `scripts/` or `apps/<app>/`. If two apps consume the same module or data, it belongs in a package.
- New Python packages register as uv workspace members in the root `pyproject.toml` (`tool.uv.workspace.members`). The package's own `pyproject.toml` declares `name = "proscenio-<slug>"`; the import path uses the underscored form (`proscenio_<slug>`).
- `scripts/` accepts only true one-offs: a single run-directly file with no dependency manifest of its own. The deciding question is "does it have its own deps/build?" - if yes it is not a `scripts/` one-off. A standalone dev or QA tool with its own deps, build, or test suite goes under `tools/` (e.g. `tools/qa-companion/`); a shared module consumed by the apps goes under `packages/`.
- `tools/` is internal tooling not shipped with the product, distinct from `apps/` (the shipped pipeline plugins plus the docs site). A pnpm/TypeScript tool belongs in `tools/` even though `apps/photoshop` is also pnpm/TypeScript - the split is shipped-product versus internal-tool, not language. A `tools/` package may own its working data in its own directory (the QA Companion owns its checklist surface + audit under `tools/qa-companion/`, not in a spec folder).
- Per-app folders under `apps/<app>/.../schema_bindings/` hold codegen output (TypeScript interfaces, GDScript `Resource` classes). They are never edited by hand; every file carries an `AUTO-GENERATED` header and committed-match tests under `tests/codegen/` fail on drift. See the typed-models codegen and monorepo packages decisions in [`decisions.md`](../../specs/decisions.md).
- Editing the workspace root `pyproject.toml` is allowed; do not add a real `[project]` package to it (the root is a virtual workspace marker, not a publishable distribution).

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

## Versioning

Three independent SemVer streams plus one integer schema version per cross-component format:

| Stream | Tag prefix |
| --- | --- |
| Photoshop plugin | `photoshop-vX.Y.Z` |
| Blender addon | `blender-vX.Y.Z` |
| Godot plugin | `godot-vX.Y.Z` |

Each cross-component JSON schema carries its own integer `format_version`, independent of component versions. Bump only on a breaking change to the document shape.

A schema change is a multi-component PR by definition (schema bump + producer + consumer guard).
