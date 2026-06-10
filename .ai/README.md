# Agent and contributor reference

This folder holds the guidance that both human contributors and LLM agents read before working in the repo. The repo houses four apps under `apps/`: a Photoshop UXP plugin (TypeScript + React), a Blender addon (Python), a Godot integration plugin (GDScript), and the docs site (Docusaurus). The first three bridge the runtime pipeline; the fourth publishes these guides and the schema reference. Each follows the same spirit: typed, cohesive, readable, and small. Prefer SOLID and DRY in moderation - clarity beats clean-arch ceremony.

[`AGENTS.md`](../AGENTS.md) at the repo root is the entry point and routes here. Load the file that matches your task.

## Conventions

Repo-wide rules, split by theme under [`conventions/`](conventions/):

| File | Covers |
| --- | --- |
| [`conventions/git.md`](conventions/git.md) | Branches, workflow, commits, pull requests, code review |
| [`conventions/layout.md`](conventions/layout.md) | Repository layout, file and folder naming, versioning |
| [`conventions/code.md`](conventions/code.md) | JSON keys, Blender addon module organization, static typing per language, validation gates, comment routing |
| [`conventions/docs.md`](conventions/docs.md) | Documentation style and information architecture: prose rules, UI decorators, feature naming, the docs-site section map, periodic drift audit |

## Skills

Task-scoped playbooks under [`skills/`](skills/). Load the one that matches your task before touching code:

| Task | Skill |
| --- | --- |
| Understand repo layout, components, boundaries | [`skills/architecture.md`](skills/architecture.md) |
| Touch the `.proscenio` format or schema | [`skills/format-spec.md`](skills/format-spec.md) |
| Edit Blender addon code | [`skills/blender-dev.md`](skills/blender-dev.md) |
| Edit Godot plugin code | [`skills/godot-dev.md`](skills/godot-dev.md) |
| Edit Photoshop UXP plugin | [`skills/photoshop-uxp-dev.md`](skills/photoshop-uxp-dev.md) |
| Run or write tests | [`skills/testing.md`](skills/testing.md) |
| Package, version, release | [`skills/release.md`](skills/release.md) |
| Domain terms (bone, slot, atlas, weights) | [`skills/glossary.md`](skills/glossary.md) |
| External prior art and Godot/Blender docs | [`skills/references.md`](skills/references.md) |
