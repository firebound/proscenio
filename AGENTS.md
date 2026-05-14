# AGENTS.md

Three apps bridge Photoshop → Blender → Godot 4 for 2D cutout animation:

- `apps/photoshop/` - UXP plugin (TypeScript + React). Slices PSD layers and emits a manifest JSON.
- `apps/blender/` - Blender 4.2+ addon (Python). Imports the manifest, hosts rig + animation, exports `.proscenio`.
- `apps/godot/` - Godot 4.3+ editor plugin (GDScript). Imports `.proscenio` into a native `.tscn`.

For LLM agents and human contributors: detailed guidance lives under `.ai/skills/`. Load the skill that matches your task before touching code. Repository-wide conventions (branches, commits, code review) live in `.ai/conventions.md` - read those first.

## Hard rules

1. **Schemas are the contract.** Any change to a cross-component shape (`.proscenio`, PSD manifest) requires a `format_version` bump on the relevant schema plus a migration note. CI validates every example and fixture against the schemas.
2. **Blender addon is GPL-3.0-or-later.** No relicensing. The repo is GPL-3.0 throughout for simplicity.
3. **No GDExtension. No native runtime.** The Godot plugin runs only at editor import time. Generated scenes use built-in nodes only (`Skeleton2D`, `Bone2D`, `Polygon2D`, `Sprite2D`, `Node2D`, `AnimationPlayer`, `AnimationLibrary`). Operational test: open a generated `.tscn` in a stock Godot project without the plugin installed - it must work.
4. **Strict dependency direction.** Photoshop knows nothing of Blender. Blender knows nothing of Godot internals. Godot reads only `.proscenio`. The schemas are the only shared artifacts.
5. **One component per PR** unless the change is a schema bump (which crosses by design).
6. **Conventional Commits.** Branch names use the same prefix vocabulary.

## Repository layout

```text
apps/<photoshop|blender|godot>/   per-app source
schemas/                          cross-component JSON schemas
specs/                            numbered planning specs + STATUS / backlog
examples/                         end-to-end fixtures
docs/                             user-facing docs
.ai/                              skills + conventions for agents and contributors
.github/workflows/                CI + release
```

## Status

Pre-alpha. Formats unstable. Not for production. Active planning lives under `specs/`; the rolling backlog is in `specs/backlog.md`.
