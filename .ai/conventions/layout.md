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

One product version in lockstep across the three apps, plus one integer schema version per cross-component format.

The Blender addon, Photoshop plugin, and Godot plugin ship under a single SemVer number, tagged `vX.Y.Z` (no per-component prefix). The version is a compatibility coordinate, not a per-app change counter: the same number across all three means they are guaranteed to work together. A release carries one CHANGELOG; the per-app detail (what actually changed, what rode along untouched) lives in that CHANGELOG, not in the number.

- **Bump by the highest severity across components.** A breaking change in any one app makes the product MAJOR; a feature in any app makes it MINOR; the unchanged apps ride along to the same number. Pre-1.0 is `0.MINOR.PATCH` with a `-beta` suffix on the beta channel.
- **Carry-along bumps are expected and cheap.** An app with no functional change still re-stamps to the new version and republishes (one manifest line). The CHANGELOG records it as "no functional change (version aligned)". This is the price of "same number = compatible" - paid once per release, it removes the compatibility-matrix question entirely.
- **One source of truth.** The release version is held in a single place (the git tag / a root `VERSION`) and stamped into all three manifests (`blender_manifest.toml`, the Godot `plugin.cfg`, the Photoshop `manifest.json`) at release time.

Why lockstep over independent per-component SemVer: the three apps are one coupled pipeline (the addon emits a `format_version`, the importer reads the same one - they must match), so independent streams would force a compatibility matrix no small team should maintain. The locked decision is in [`specs/decisions.md`](../../specs/decisions.md).

Each cross-component JSON schema carries its own integer `format_version`, independent of the product version. Bump only on a breaking change to the document shape.

A schema change is a multi-component PR by definition (schema bump + producer + consumer guard).
