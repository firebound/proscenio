# SPEC 001 — TODO

Closes the reimport-merge question by adopting **Option A** (full overwrite, wrapper scene for customization) and documenting the workflow. See [STUDY.md](STUDY.md) for the full rationale and the alternative options.

## Decision lock-in

- [x] Confirm Option A with maintainers before any of the following work begins.
- [x] Move "Reimport non-destructive merge" from [`specs/backlog.md`](../backlog.md) to "resolved by SPEC 001" with a one-line summary.

## Documentation

- [x] Add a "Customizing an imported scene" subsection to [`.ai/skills/godot-plugin-dev.md`](../../.ai/skills/godot-plugin-dev.md). Describe the wrapper-scene pattern: instance the generated `.scn`, attach scripts and extra nodes to the wrapper.
- [x] Document the bone-rename caveat (Q4): a Blender bone rename invalidates wrapper-scene `NodePath`s referencing the old name. State this explicitly so users know to plan renames as cross-DCC operations.
- [x] Document the animation-extension pattern (Q3): the wrapper's `AnimationPlayer` can hold a second library for user-authored animations.
- [x] Update [`README.md`](../../README.md) iteration-loop section to point at the wrapper-scene pattern as the recommended workflow.

## Example asset

- [x] Add `examples/dummy/Dummy.tscn` — a wrapper scene that instances the generated `dummy.scn`, attaches a tiny `Dummy.gd` (one exported property: a default animation name), and lives next to the source `.proscenio`. This is the documentation-by-example.
- [x] Add a one-sentence note in `examples/dummy/` (or update its README, if any) explaining the difference between `dummy.proscenio`, `dummy.scn` (generated), and `Dummy.tscn` (user-authored wrapper). _(Fixture retired in SPEC 007 reorg; doll fixture covers the same role.)_

## Importer hardening (no behavior change)

The importer already overwrites on every reimport. Add explicit safety so the user is not surprised:

- [x] If the target `.scn` already exists when the importer runs, log a single-line confirmation: `Proscenio: regenerating <path> (existing scene will be overwritten)`. Use `print_verbose` so it is suppressible.
- [x] Add a unit test (GUT) that runs the importer twice on the same `.proscenio` and asserts the resulting `.scn` is byte-identical (or at least produces an identical `PackedScene` tree). Catches non-determinism early. *Implemented in [`godot-plugin/tests/test_importer.gd`](../../godot-plugin/tests/test_importer.gd) as a structural diff (node hierarchy + transforms + animation libraries) since `EditorImportPlugin._import` is editor-only and unsuitable for headless byte-equality.*

## Defer (potential SPEC 001.1 if demand emerges)

Track but do not implement:

- Marker-based merge (Option B) gated behind an importer flag.
- A small helper for attaching a script to a Bone2D inside the generated scene without "Editable Children".
- Stable-ID extension to the schema for rename-survivable merges. This belongs to a v2 format conversation, not this spec.
