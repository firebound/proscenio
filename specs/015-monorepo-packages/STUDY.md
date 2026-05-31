# Monorepo packages: apps/ + packages/ split

Status: **draft**. Restructure proposal. Lands before [the typed models codegen spec](../014-typed-models-codegen/STUDY.md) so that spec can target the new layout from day one.

## Problem

The repo today has three top-level homes for code:

- `apps/` - the three distributable apps (Blender addon, Photoshop UXP plugin, Godot plugin). Each is self-contained, ships as its own bundle.
- `scripts/` - a junk drawer. Holds 4 different things at once:
  - `scripts/automesh_validator/` - a full CLI tool with its own subpackage layout, used both in tests and as a manual debug entry point.
  - `scripts/fixtures/` - shared fixture data (PSDs, `.blend` files, expected `.proscenio` outputs) consumed by tests across multiple apps.
  - `scripts/maintenance/strip_rigify_meta.py` - a one-off Blender cleanup script.
  - `scripts/godot/sync_fixtures.py` - a dev tool that copies fixtures from `examples/generated/` into `apps/godot/examples/`.
  - Plus loose `inspect_*.py`, `test_export.py`, `test_min.py` at the top level - ad-hoc debug scaffolding.
- `schemas/` - top-level JSON Schemas (`proscenio.schema.json`, `psd_manifest.schema.json`). Cross-app contract surface.

This layout has three concrete pains:

1. **`scripts/` is undifferentiated.** A new contributor opening `scripts/` cannot tell which folders are CLIs, which are dev tools, which are data, and which are stale experiments. The names give no signal.
2. **No home for cross-app shared code.** [The typed models codegen spec](../014-typed-models-codegen/STUDY.md) wants pydantic models that serve as the source of truth for `.proscenio` and the PSD manifest. Those models are consumed by the Blender writer (Python, directly) and by the Photoshop + Godot apps (indirectly via codegen artifacts). They are not specific to any single app, but the current layout has no neutral place to put them. Sticking them in `apps/blender/core/models/` would falsely imply ownership by the Blender side.
3. **`schemas/` floats at the root.** JSON Schema files live at top level disconnected from any source that produces them. After the typed models codegen spec lands, those schemas become *outputs* of the pydantic models - keeping them at the root, away from their producer, makes the source-of-truth chain less obvious.

## What we want

A two-folder split that maps cleanly onto monorepo conventions:

- **`apps/`** - distributable, self-contained things that users install. Each app bundles whatever shared code it needs at build time.
- **`packages/`** - shared building blocks that the apps consume. Has its own tests, its own pyproject (where applicable), and a clear contract with the apps that depend on it.
- **`scripts/`** - shrinks to its honest scope: one-off maintenance scripts and dev tools. No longer holds CLIs, data, or shared code.

## Reference: monorepo conventions

The layout mirrors what pnpm workspaces, Nx, Turborepo, Bazel, Cargo workspaces, and Go modules all converge on for polyglot monorepos:

- `apps/` (or `services/`) - things you ship.
- `packages/` (or `libs/`) - things shared between apps.
- A workspace tool (uv workspaces for Python here) declares the package set at the root and lets `pip install -e` link them all in one command.

The catch for this project is that the three apps are in three different languages, and only one (the Blender addon) directly imports a Python package. The Photoshop and Godot apps consume *outputs* of the codegen package (TypeScript interfaces, GDScript Resource files), not the package itself at runtime. This is fine: build-time dep graph still benefits from explicit workspace membership.

## Design space

### Axis A - What goes into `packages/`

| Package | Source today | Why it belongs in `packages/` |
| --- | --- | --- |
| **models** | (does not exist yet; planned in [the typed models codegen spec](../014-typed-models-codegen/STUDY.md)) | Pydantic models for `.proscenio` and the PSD manifest. Source of truth for the cross-app data shape. Consumed by Blender (directly imports) and by codegen (introspected to emit JSON Schema). |
| **codegen** | (does not exist yet; planned in [the typed models codegen spec](../014-typed-models-codegen/STUDY.md)) | CLI that reads `models/`, emits JSON Schema, TypeScript interfaces, GDScript Resources, Markdown docs. Pure Python tool. |
| **fixtures** | `scripts/fixtures/` | Shared fixture data: PSDs, `.blend` files, expected `.proscenio` outputs. Consumed by tests in multiple apps. No Python code, just data. Likely no pyproject (just a folder of assets). |
| **validator** | `scripts/automesh_validator/` | Full CLI tool with its own subpackage layout (`addon_loader`, `cli`, `coverage`, `invariants`, `measurement`, `report`). Used as a manual debug entry point and indirectly by tests. Belongs as a proper package, not a script. |

What does **not** move:

- `scripts/maintenance/strip_rigify_meta.py` - genuine one-off maintenance script. Stays.
- `scripts/godot/sync_fixtures.py` - dev tool. Stays.
- Loose `inspect_*.py` / `test_export.py` / `test_min.py` at the top of `scripts/` - ad-hoc debug scaffolding. Either stays or gets deleted as part of this cleanup (see Open questions).

### Axis B - Workspace tool

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **B1.** `uv workspaces` (`tool.uv.workspace` in root `pyproject.toml`) | Modern, fast, lockfile management included, single `uv sync` installs all packages editable. Active development. | New dependency on uv (already a reasonable assumption for modern Python projects). | **Lock.** |
| **B2.** `pip workspaces` (PEP 735 / draft) | Pip-native eventually. | Still draft as of 2026; tooling is partial. | Reject. Not stable. |
| **B3.** No workspace, manual `pip install -e` per package | Zero new tooling. | Every contributor remembers the install order; CI repeats the invocation N times. | Reject. The whole point of `packages/` is to make the dep graph explicit; manual install fights that. |

### Axis C - Per-app binding folder naming

The per-app folder that holds codegen output (TS interfaces, GDScript Resources):

| Name | Sinaliza | Verdict |
| --- | --- | --- |
| `generated/` | State (was generated) | Reject. Sounds like self-contained internal output. Confuses "where was this produced". |
| `_generated/` | State + "do not touch" | Underscore is a Python convention, awkward in TS / Godot paths. |
| `codegen/` | Producer (came from codegen) | Mirrors `packages/codegen/`; reads as "this folder's contents come from `packages/codegen/`". Good. |
| `artifacts/` | Build artifact | Industry term but in TS world `artifacts/` usually means `dist/` - confusing inside `src/`. |
| **`schema_bindings/`** | What it IS (language bindings to the schema) | Concise, accurate, universal across the 3 languages. **Lock.** |

`schema_bindings/` describes the role precisely: TypeScript interfaces bind to the schema; GDScript Resources bind to the schema. The producer (codegen) is implicit; the contract (schema) is explicit in the name.

### Axis D - Where the JSON Schemas live

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **D1.** Stay at `schemas/` (status quo) | Familiar path. | Disconnected from the pydantic models that will produce them. | Reject after the typed models codegen spec lands. |
| **D2.** Move under `packages/models/schemas/` | Schemas live next to the source of truth that produces them. One place to look for "what does the wire format look like". | Top-level `schemas/` folder disappears, which is a visible churn point for anyone with `schemas/` muscle memory. | **Lock.** |
| **D3.** Move under `packages/codegen/output/` | Schemas live with the tool that emits them. | The schemas are not the codegen's output - the codegen reads the pydantic models and writes here. Conflates source-of-truth with build output. | Reject. |

## Architecture sketch

Layout after this spec ships (before [the typed models codegen spec](../014-typed-models-codegen/STUDY.md) starts populating `schema_bindings/`):

```text
apps/                                       # distributable, self-contained
  blender/
    core/                                   # bpy-bound, app-specific
    exporters/
    importers/
    operators/
    panels/
    properties/
    wheels/                                 # bundled wheels for Blender extension
      pydantic-*.whl
      pydantic_core-*-<plat>.whl
      proscenio_models-*.whl                # built from packages/models/
    blender_manifest.toml
    pyproject.toml
    tests/

  photoshop/
    src/
      adapters/
      controllers/
      domain/
      schema_bindings/                      # codegen output (.ts); populated by the typed models codegen spec
      ...
    package.json
    tsconfig.json
    webpack.config.js

  godot/
    addons/
      proscenio/
        builders/
        schema_bindings/                    # codegen output (.gd Resources); populated by the typed models codegen spec
        importer.gd
        plugin.gd
        reimporter.gd
    examples/
    project.godot
    tests/

packages/                                   # shared building blocks
  models/                                   # pydantic source of truth (lands in the typed models codegen spec)
    pyproject.toml                          # name = "proscenio-models"
    src/proscenio_models/
      __init__.py
      proscenio.py
      psd_manifest.py
    schemas/                                # JSON Schema files dumped from the models
      proscenio.schema.json
      psd_manifest.schema.json
    tests/

  codegen/                                  # CLI: regenerates schemas + per-app bindings (lands in the typed models codegen spec)
    pyproject.toml                          # name = "proscenio-codegen"
    src/proscenio_codegen/
      __init__.py
      __main__.py                           # python -m proscenio_codegen schemas|ts|godot|docs|all
      schema_dump.py
      ts_emit.py
      godot_emit.py
      docs_emit.py
      _io.py                                # shared: paths, AUTO-GENERATED header, atomic write
    tests/

  fixtures/                                 # shared test data (was scripts/fixtures/)
    proscenio_basic/
    proscenio_atlas_pack/
    automesh/
    ...

  validator/                                # automesh CLI (was scripts/automesh_validator/)
    pyproject.toml                          # name = "proscenio-validator"
    src/proscenio_validator/
      __init__.py
      addon_loader.py
      cli.py
      coverage.py
      invariants.py
      measurement.py
      report.py
    tests/

scripts/                                    # shrinks: only true one-off dev tools
  maintenance/
    strip_rigify_meta.py
  godot/
    sync_fixtures.py

pyproject.toml                              # root: declares uv workspace members

tests/                                      # repo-level cross-app integration tests
  ...

docs/                                       # unchanged
.ai/                                        # unchanged
```

### Root `pyproject.toml`

```toml
[tool.uv.workspace]
members = [
  "apps/blender",
  "packages/models",
  "packages/codegen",
  "packages/validator",
]
```

`packages/fixtures/` is data-only, no pyproject, not a workspace member.

`apps/photoshop/` and `apps/godot/` are not Python projects; they live alongside the workspace but are managed by their own tooling (pnpm + webpack for Photoshop; Godot project file for Godot).

## Migration plan

Each phase is one PR. The whole reorganization can ship in one branch with multiple commits if preferred; the phase split below is for review clarity, not strict PR boundaries.

| Phase | Scope | Risk |
| --- | --- | --- |
| **P1.** Root workspace setup | Create root `pyproject.toml` with empty `tool.uv.workspace.members`. Document the convention in `.ai/conventions.md`. No code moves yet. | Low. |
| **P2.** Move `scripts/automesh_validator/` -> `packages/validator/` | Add pyproject, restructure to `src/proscenio_validator/`, update all imports, add to workspace members. Update tests + CI invocations. | Medium. Touches imports across tests and any caller. |
| **P3.** Move `scripts/fixtures/` -> `packages/fixtures/` | Pure data move. Update path references in tests + the photoshop tag system fixture loaders + the godot sync script. | Low. No code changes, just path updates. |
| **P4.** Trim `scripts/` ad-hoc files | Decide per-file: delete the stale `inspect_*.py`, `test_export.py`, `test_min.py` at the top of `scripts/`, OR move to `scripts/debug/`. Confirm none are referenced in CI or docs. | Low. |
| **P5.** `apps/blender/` becomes a workspace member | Add to `tool.uv.workspace.members`. Blender addon's `pyproject.toml` already exists; just register it. No code changes. | Low. |

Phases P1-P5 ship before the typed models codegen spec. After this spec lands, the typed models codegen spec adds `packages/models/` and `packages/codegen/` as new workspace members and starts populating the per-app `schema_bindings/` folders. The `schemas/` top-level folder is deleted as part of the typed models codegen spec's P2 (when the dumped schemas under `packages/models/schemas/` are byte-equal to the current hand-maintained files).

## Design decisions

| ID | Question | Locked answer |
| --- | --- | --- |
| D1 | Top-level split | **`apps/` + `packages/` + `scripts/`**. `apps/` = distributable. `packages/` = shared building blocks. `scripts/` = one-off dev tools only. |
| D2 | Workspace tool | **uv workspaces** (`tool.uv.workspace.members` in root `pyproject.toml`). |
| D3 | Per-app binding folder name | **`schema_bindings/`**. Describes role (binding to schema), universal across 3 languages, no underscore weirdness. |
| D4 | JSON Schema location | **`packages/models/schemas/`** after the typed models codegen spec lands. Top-level `schemas/` deleted. |
| D5 | `packages/fixtures/` packaging | **Data-only folder, no pyproject.** Not a workspace member. Test code references files by path. |
| D6 | Package naming inside the repo | **Unscoped folder names** (`packages/models/`, `packages/codegen/`). Distribution name uses prefix in pyproject (`name = "proscenio-models"`). Import path: `proscenio_models`. |
| D7 | Phase ordering | **This spec ships before the typed models codegen spec.** The typed models codegen spec targets the new layout from day one rather than landing in the old layout and migrating after. |

## Open questions

| OQ | Question | Notes |
| --- | --- | --- |
| OQ1 | Stale `scripts/` ad-hoc files | The loose `inspect_action.py`, `inspect_blend.py`, `test_export.py`, `test_min.py`, `validate_automesh.py` at the top of `scripts/` - are any still in active use, or is this dead scaffolding from earlier phases? Audit before P4. If unused, delete. If used, move to `scripts/debug/` with a one-line header documenting purpose. |
| OQ2 | `apps/photoshop/` and `apps/godot/` workspace membership | These are not Python projects, so they cannot join the uv workspace. Question: do we want a parallel pnpm workspace for the Photoshop side? Today the project has one pnpm workspace inside `apps/photoshop/`. Adding the root-level pnpm workspace is out of scope here; revisit if multiple TS packages emerge. |
| OQ3 | `tests/` at the root vs per-package `tests/` | Each new package (`models`, `codegen`, `validator`) gets its own `tests/`. The root `tests/` retains repo-level cross-app integration tests. Confirm that the current root `tests/` content is genuinely cross-app and not just app-specific tests that drifted there. Audit during P5. |

## Out of scope (deferred)

- **TypeScript / pnpm workspace at the root.** Today `apps/photoshop/` has its own pnpm workspace; expanding to a root-level one only matters if a second TS package emerges. The typed models codegen spec's TS bindings live inside `apps/photoshop/src/schema_bindings/` and are consumed by the existing Photoshop pnpm setup; no second TS package is planned.
- **Godot multi-project workspace.** Not a thing Godot supports natively; out of scope.
- **Renaming or re-organizing `docs/`, `.ai/`, `.github/`, `examples/`.** Those folders are not affected by the apps/packages split.
- **Publishing packages to PyPI.** Internal-only workspace. Prefixed distribution names (`proscenio-models`, etc.) leave the door open if needed later.

## Acceptance

When this spec ships:

- Root `pyproject.toml` declares `tool.uv.workspace.members` covering all Python workspace members.
- `packages/validator/` exists; `scripts/automesh_validator/` is gone; all imports updated; CI green.
- `packages/fixtures/` exists; `scripts/fixtures/` is gone; all path references updated; tests pass.
- `scripts/` contains only `maintenance/` and `godot/` (and a `debug/` folder if OQ1 resolves to keep some ad-hoc files).
- `apps/blender/` is a workspace member.
- `.ai/conventions.md` documents the apps + packages convention so future contributors land in the right folder by default.
- The typed models codegen spec can start, knowing exactly where its `packages/models/` and `packages/codegen/` go.
