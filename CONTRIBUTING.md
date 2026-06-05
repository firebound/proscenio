# Contributing to Proscenio

Read [AGENTS.md](AGENTS.md) first - it points to [`.ai/`](.ai/README.md), the index of repo conventions and task-scoped skills. Human or LLM, load the file that matches your task before touching code.

New to the tool itself? Start with the [end-to-end walkthrough](docs/00-guides/00-basic/index.md), backed by per-tool guides under [`docs/`](docs/README.md). Both render on the [documentation site](https://space-wizard-studios.github.io/firebound-proscenio/) for easier reading.

## Setup

Install Git LFS once, then clone - the LFS filter pulls the example assets during clone:

```sh
git lfs install
git clone https://github.com/Space-Wizard-Studios/firebound-proscenio
cd firebound-proscenio
```

For component-specific setup, see the corresponding skill in [`.ai/skills/`](.ai/README.md#skills).

## PR rules

- One component per PR (Photoshop, Blender, Godot).
  - Exception: format_version bumps cross all components by definition.
- Conventional Commits in commit messages and PR titles.
- A schema change requires a `format_version` bump in [`packages/models/schemas/proscenio.schema.json`](packages/models/schemas/proscenio.schema.json) and a migration note in the PR body.

## Testing

Run lint and tests before pushing. Per-component commands live in [`.ai/skills/testing.md`](.ai/skills/testing.md).

## License

By contributing you agree your contributions are licensed under GPL-3.0-or-later.
