# AGENTS.md

This repository ships three components that bridge Blender → Godot 4 for 2D cutout animation:

- `photoshop-exporter/` — Photoshop JSX exporter (PSD layers + position JSON)
- `blender-addon/` — Blender 4.2+ addon (sprite import, rigging, animation, `.proscenio` export)
- `godot-plugin/` — Godot 4.3+ editor plugin (`.proscenio` → native `.tscn`)

For LLM agents and human contributors: detailed guidance lives in [`.ai/skills/`](.ai/skills/). Load the skill that matches your task before touching code. Repository-wide conventions (branches, commits, code review) live in [`.ai/conventions.md`](.ai/conventions.md) — read those first.

## Skills index

| Task | Skill |
| --- | --- |
| Understand repo layout, components, boundaries | [.ai/skills/architecture.md](.ai/skills/architecture.md) |
| Touch the `.proscenio` format or schema | [.ai/skills/format-spec.md](.ai/skills/format-spec.md) |
| Edit Blender addon code | [.ai/skills/blender-addon-dev.md](.ai/skills/blender-addon-dev.md) |
| Edit Godot plugin code | [.ai/skills/godot-plugin-dev.md](.ai/skills/godot-plugin-dev.md) |
| Edit Photoshop JSX exporter | [.ai/skills/photoshop-jsx-dev.md](.ai/skills/photoshop-jsx-dev.md) |
| Run or write tests | [.ai/skills/testing.md](.ai/skills/testing.md) |
| Package, version, release | [.ai/skills/release.md](.ai/skills/release.md) |
| Domain terms (bone, slot, atlas, weights) | [.ai/skills/glossary.md](.ai/skills/glossary.md) |
| External prior art and Godot/Blender docs | [.ai/skills/references.md](.ai/skills/references.md) |

## Hard rules

1. **Format is contract.** Any change to the `.proscenio` shape requires a `format_version` bump in [schemas/proscenio.schema.json](schemas/proscenio.schema.json) and a migration note. CI validates every example and fixture against the schema.
2. **Blender addon is GPL-3.0-or-later.** No relicensing. Repo is GPL-3.0 throughout for simplicity.
3. **No GDExtension. No native runtime.** The Godot plugin runs only at editor import time. Generated scenes use built-in nodes (`Skeleton2D`, `Bone2D`, `Polygon2D`, `AnimationPlayer`, `AnimationLibrary`). Verify by opening a generated `.tscn` in a stock Godot project without the plugin installed — it must work.
4. **Strict dependency direction.** Photoshop knows nothing of Blender. Blender knows nothing of Godot internals. Godot knows only `.proscenio`. The schema is the only shared artifact.
5. **One component per PR** unless the change is a format bump (which by definition crosses components).
6. **Conventional Commits.** Squash merge.
7. **Branch policy.** SPEC docs (`specs/<NNN>-…/STUDY.md` and `TODO.md`) land directly on `main`. Implementation lives on a `feat/spec-<NNN>-<slug>` branch (or `fix/spec-<NNN>-<slug>`, `chore/spec-<NNN>-<slug>` if the SPEC's nature warrants) and merges back via PR when the SPEC's TODO is satisfied. Branch names follow Conventional Commits prefixes everywhere. Full convention in [`.ai/conventions.md`](.ai/conventions.md#branches).

## Repository layout

```text
.
├── AGENTS.md                  # this file — entry point
├── README.md                  # user-facing
├── LICENSE                    # GPL-3.0
├── CONTRIBUTING.md
├── .ai/skills/                # LLM-oriented guidance
├── .github/workflows/         # CI + release
├── docs/                      # user docs (mkdocs later)
├── schemas/                   # .proscenio JSON Schema
├── examples/                  # end-to-end samples (LFS for binaries)
├── photoshop-exporter/        # JSX
├── blender-addon/             # Python (Blender Extensions package)
└── godot-plugin/              # GDScript (dev project + addon)
```

## Status

Pre-alpha. Format unstable. Not for production. The current planning spec is [`specs/000-initial-plan/`](specs/000-initial-plan/) — read [`STUDY.md`](specs/000-initial-plan/STUDY.md) for the rationale and [`TODO.md`](specs/000-initial-plan/TODO.md) for the actionable plan.
