# Contributing to Proscenio

Read [AGENTS.md](AGENTS.md) first. It points to [`.ai/skills/`](.ai/skills/README.md) - load the skill that matches your task before touching code.

New to the tool itself? The end-to-end usage walkthrough lives in [`docs/WALKTHROUGH.md`](docs/WALKTHROUGH.md), with per-tool guides under [`docs/`](docs/README.md).

## Setup

Install Git LFS once, then clone - the LFS filter pulls the example assets during clone:

```sh
git lfs install
git clone https://github.com/Space-Wizard-Studios/firebound-proscenio
cd firebound-proscenio
```

For component-specific setup, see the corresponding skill in [`.ai/skills/`](.ai/skills/README.md).

## PR rules

- One component per PR (Photoshop, Blender, Godot). Exception: format-version bumps cross all components by definition.
- Conventional Commits in commit messages and PR titles.
- Squash merge.
- A schema change requires a `format_version` bump in [`packages/models/schemas/proscenio.schema.json`](packages/models/schemas/proscenio.schema.json) and a migration note in the PR body.

## Testing

Run lint and tests before pushing. Per-component commands live in [`.ai/skills/testing.md`](.ai/skills/testing.md).

## License

By contributing you agree your contributions are licensed under GPL-3.0-or-later.
