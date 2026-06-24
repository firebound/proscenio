# Contributing to Proscenio

Read [AGENTS.md](AGENTS.md) first - it points to [`.ai/`](.ai/README.md), the index of repo conventions and task-scoped skills. Human or LLM, load the file that matches your task before touching code.

New to the tool itself? Start with the [end-to-end walkthrough](docs/00-guides/01-basic/index.md), backed by per-tool guides under [`docs/`](docs/README.md). Both render on the [documentation site](https://firebound.github.io/proscenio/) for easier reading.

## Prerequisites

You only need the toolchain for the component you touch. The table lists every tool the repo expects, the version CI pins, and the file that version comes from.

| Tool | Version | Needed for | Source of truth |
| --- | --- | --- | --- |
| Git LFS | any current | cloning (pulls example assets) | [`.gitattributes`](.gitattributes) |
| uv | any current | all Python work (manages the interpreter + venv) | [CI `setup-uv`](.github/workflows/ci.yml) |
| Python | 3.11+ | Python tooling floor (`uv` provisions it) | [`pyproject.toml`](pyproject.toml) `requires-python` |
| Node.js | 22 | `apps/photoshop`, `apps/docs` | [CI `node-version: "22"`](.github/workflows/ci.yml), [`apps/docs/package.json`](apps/docs/package.json) `engines.node` |
| pnpm | 9 | `apps/photoshop`, `apps/docs` | [CI `version: 9`](.github/workflows/ci.yml), [`apps/photoshop/package.json`](apps/photoshop/package.json) `packageManager` |
| Blender | 5.1.1 | building / testing the addon | [CI `blender-5.1.1`](.github/workflows/ci.yml), [`apps/blender/blender_manifest.toml`](apps/blender/blender_manifest.toml) |
| Godot | 4.6.2-stable | building / testing the plugin | [CI `godot-4.6.2-stable`](.github/workflows/ci.yml), [`apps/godot/project.godot`](apps/godot/project.godot) |
| Photoshop + UXP Developer Tools | current | loading the UXP plugin | [`.ai/skills/photoshop-uxp-dev.md`](.ai/skills/photoshop-uxp-dev.md) |

Notes on the Python runtimes:

- The repo targets Python 3.11 as its tooling floor. `uv sync` provisions a matching interpreter for you; you do not have to install Python by hand.
- Blender ships its own embedded CPython (5.1.1 bundles 3.13), and the addon and validator run inside it, not inside the `uv` venv. That is why the addon and validator type-check under `python_version = "3.13"` while the packaging floor stays at 3.11 - see the rationale comments in [`apps/blender/pyproject.toml`](apps/blender/pyproject.toml) and [`packages/validator/pyproject.toml`](packages/validator/pyproject.toml). Their pytest and goldens run via `blender --background --python ...`, never under the host venv.
- The pre-commit `ruff` hook is pinned to 0.8.4 in [`.pre-commit-config.yaml`](.pre-commit-config.yaml); CI runs `ruff` via `uvx` (latest). Pin parity matters only if a new ruff release changes a rule.

## Clone

Install Git LFS once, then clone - the LFS filter pulls the example assets (`.blend`, `.psd`, `.png`) during clone:

```sh
git lfs install
git clone https://github.com/firebound/proscenio
cd proscenio
```

## Install per language

Run only the lines for the components you work on. None of them depend on each other.

Python (all four members of the uv workspace - `apps/blender`, `packages/codegen`, `packages/models`, `packages/validator`):

```sh
uv sync --all-packages
```

Photoshop UXP plugin:

```sh
pnpm --dir apps/photoshop install
```

Docs site:

```sh
pnpm --dir apps/docs install
```

Pre-commit hooks (mirror the CI lint gate locally; install once per clone):

```sh
uv tool install pre-commit   # or: pipx install pre-commit
pre-commit install
```

Blender and Godot are external applications, not package-manager installs. Download the pinned versions from the upstream sites (Blender 5.1.1, Godot 4.6.2-stable) and put the executables on your `PATH` so the test commands below resolve `blender` / `godot`. On Windows the maintainer keeps version-pinned symlinks; see [`.ai/skills/blender-dev.md`](.ai/skills/blender-dev.md) and [`.ai/skills/godot-dev.md`](.ai/skills/godot-dev.md) for local-run details (factory-startup flags, the console build on Windows, the bundled-Python wheel install).

## Lint and test

The single command that mirrors the whole CI lint gate locally:

```sh
pre-commit run --all-files
```

Per-component entry commands follow; the canonical, always-current list lives in [`.ai/skills/testing.md`](.ai/skills/testing.md). Skipping a hook with `--no-verify` is a bug - fix the underlying issue.

Python (lint, type-check, unit tests - run from the repo root):

```sh
uvx ruff check apps/blender/
uvx ruff format --check apps/blender/
uv run --with mypy mypy --config-file apps/blender/pyproject.toml
uv run pytest tests/
```

mypy runs once per config file (`apps/blender`, `packages/validator`, `packages/models`, `packages/codegen`); see [CI](.github/workflows/ci.yml) for the full set. Run mypy from the repo root, not from inside `apps/blender` - the addon's mypy config roots the package tree at `apps/`, and a different CWD breaks its relative-import resolution.

Photoshop:

```sh
pnpm --dir apps/photoshop run typecheck
pnpm --dir apps/photoshop run lint
pnpm --dir apps/photoshop test
```

Blender addon (real `bpy`, no mocks - runs inside Blender's bundled Python):

```sh
blender --background --python apps/blender/tests/run_tests.py
```

Godot plugin (CI runs the `test_*.gd` scripts directly):

```sh
godot --headless --path apps/godot --script res://tests/test_importer.gd
```

GDScript lint:

```sh
gdformat --check apps/godot/addons/proscenio/
gdlint apps/godot/addons/proscenio/
```

## Build and preview the docs site

The docs site is Docusaurus; it serves the `docs/` content root plus the live schema reference.

```sh
pnpm --dir apps/docs start     # dev server with hot reload
pnpm --dir apps/docs build     # production build (what CI deploys)
pnpm --dir apps/docs serve     # serve the production build locally
```

## PR rules

- One component per PR (Photoshop, Blender, Godot).
  - Exception: format_version bumps cross all components by definition.
- Conventional Commits in commit messages and PR titles.
- A schema change requires a `format_version` bump in [`packages/models/schemas/proscenio.schema.json`](packages/models/schemas/proscenio.schema.json) and a migration note in the PR body.

## License

By contributing you agree your contributions are licensed under GPL-3.0-or-later.
