# Decisions

Architectural and per-SPEC decisions that are locked. ADR-light: each entry records the call, the rationale, and the trigger that would force a revisit. Live state lives in [`STATUS.md`](../STATUS.md); per-SPEC design rationale lives in [`specs/NNN-*/STUDY.md`](../specs/). This file aggregates the cross-cutting decisions and the per-SPEC tradeoffs worth surfacing outside their STUDY.

## Core architecture

| Decision | Rationale | Revisit trigger |
| --- | --- | --- |
| **No GDExtension, no native runtime** | Plugin is GDScript-only. Generated `.scn` uses native nodes; runs on plain Godot 4 with the plugin uninstalled. | Listed in [`specs/backlog.md`](../specs/backlog.md) "Architecture revisits": deep Firebound integration, perf ceiling on `Polygon2D` skinning, live link Blender↔Godot, binary `.proscenio`, in-Godot authoring round-trip. |
| **Conversion one-time, at editor import** | Heavy work happens at import time. Runtime uses Godot core (already C++); no GDScript performance ceiling. | Same as above. |
| **Strong typing everywhere** | GDScript 2.0 typed (`untyped_declaration=2` error) + Python `mypy --strict` + ExtendScript JSDoc + `@ts-check`. Catches errors before runtime. | None. Baseline rule. |
| **Schema is contract** | Any change to `.proscenio` shape requires `format_version` bump + migrator. CI validates fixtures against the schema. | None. Bumps are how the schema evolves; bumps are not breakage. |
| **PropertyGroup canonical, Custom-Property fallback** | Blender authoring uses typed PropertyGroup; raw Custom Properties remain readable for legacy assets. Writer reads PG first, CP last. | None. Legacy CP support stays for backwards compat with pre-PG fixtures. |
| **Wrapper-scene pattern (SPEC 001 Option A)** | Importer clobbers `.scn` on every reimport; user-authored `.tscn` wrapper survives intact and carries scripts/extras. | Marker-merge (Option B) deferred unless concrete demand emerges. |
| **One component per PR** | Photoshop, Blender, Godot ship independent PRs. Schema bumps cross all components by definition. | None. |
| **Branch policy: SPEC docs to `main`, implementation in `feat/spec-NNN-<slug>`** | SPEC docs inform parallel work; implementation is isolated. Conventional Commits prefixes (`feat/`, `fix/`, `chore/`). | None. |
| **C# / GDExtension as documented escape hatch, not active option** | Maintainer prefers strong typing over GDScript dynamism, but stays in GDScript for plugin reach in the broader 2D community. | Concrete triggers in `specs/backlog.md` "Architecture revisits". |

## Validation gates

Six gates, each catching errors earlier than the next:

1. **IDE.** Pylance + SonarLint + cspell + gdtoolkit live.
2. **pre-commit.** `ruff` + `mypy` + `gdformat` + `gdlint` + `cspell` + `check-jsonschema`.
3. **CI lint-python.** `ruff` + `mypy --strict` + `pytest`.
4. **CI lint-photoshop.** `tsc --noEmit` + `vitest run` against the UXP plugin in `apps/photoshop/`.
5. **CI test-blender.** Walks `examples/*/.blend`, diffs against golden `.proscenio`.
6. **CI test-godot.** Importer fixtures + idempotency check.

Schema validated at three points: writer output (test runner runs `check-jsonschema` in-process), importer input (`format_version` guard + per-field `push_error`), CI fixtures (`validate-schema` covers both the runtime `.proscenio` files and the SPEC 006 PSD manifests via `psd_manifest.schema.json`).

## Per-SPEC tradeoffs

### SPEC 000 - Phase 1 MVP

- **Rest+delta absolute, not relative, in animation tracks.** Exporter resolves into absolute values; importer just reads. Simpler at consumer side.

### SPEC 001 - Reimport-merge

- **Option A (full overwrite + wrapper) chosen over Option B (marker-merge).** Option B deferred without concrete demand. Wrapper pattern is simpler to reason about and easier to test (idempotency).

### SPEC 002 - Spritesheet / Sprite2D

- **`type` discriminator additive in schema, not a v2 bump.** New `sprite_frame` variant lives alongside `polygon` under a `type` field. Default `"polygon"` keeps pre-discriminator fixtures backwards-compatible.

### SPEC 003 - Skinning weights

- **Skinned polygons parented to `Skeleton2D`, not to a single bone.** Weights drive vertex deformation; rigid sprites remain bone-parented. Two parenting strategies coexist by design.
- **Validation is user-driven (paint weights + observe deformation).** No programmable check covers visual quality.

### SPEC 004 - Slot system (D1 to D14)

Selected highlights (full list in [`specs/004-slot-system/STUDY.md`](../specs/004-slot-system/STUDY.md)):

- **D5: Hard cut, NEAREST interpolation on `slot_attachment`.** Smooth crossfade is a future SPEC (related to CT2 issue #66 `StateData`).
- **D6: Sprites stay in top-level `sprites[]`.** `slots[].attachments[]` is a list of names; importer cross-references. Schema stays flat - no `slot:` field on `Sprite`.
- **D11: Slot system fits inside `format_version=1`.** No schema bump - `slots[]` and `slot_attachment` track type were already in v1.
- **D13: Material-Preview shader for spritesheet cells.** Drivers wire frame index into Math nodes that slice the UV. Workbench shading mode ignores this and shows the full atlas - documented caveat.
- **D14: Slot is kind-agnostic.** Polygon meshes and sprite_frame attachments compose freely inside the same slot.

### SPEC 005 - Blender authoring panel

- **D2: PropertyGroup canonical.** Writer reads PG first, Custom Properties only as legacy fallback. Defaults flow through cleanly without forcing the user to touch them.
- **D6: Validation lazy + inline.** Lazy via the **Validate** button (heavy schema check); inline status badges per subpanel are O(1) checks per redraw.

### SPEC 006 - Photoshop → Blender importer

- **D1: Manifest v1 emits `format_version`, `kind`, `pixels_per_unit`, `z_order`, `frames[]`.** `MANIFEST_FORMAT_VERSION` constant in `core/psd_manifest.py` bumps lockstep with schema.
- **D7: JSX manifest only.** Direct `.psd` parsing inside Blender deferred - fragile across PSD versions, duplicates JSX work.
- **D9: Sprite-frame detection has two paths.** Primary: PSD layer group with numeric children. Fallback: flat `<name>_<index>` naming. Both detected JSX-side.

### SPEC 007 - Testing fixtures (design-only)

- **Five Type A fixtures cover orthogonal feature isolation.** `doll` (comprehensive showcase, grows with SPECs), `blink_eyes` (sprite_frame isolation), `shared_atlas` (sliced atlas isolation), `simple_psd` (SPEC 006 roundtrip), `slot_cycle` (SPEC 004 isolation).
- **Type B fixtures (importer-only, under `apps/godot/tests/fixtures/`) retired in favor of Type A.** Type A drives both writer goldens and importer regenerations from one source.

### SPEC 008 - UV animation (design-only)

- **`texture_region` track type targets iris-scroll / hframe-cycling.** Closes the cutout playbook: gradual region (008) + hard swap (004) + frame index (002) + driver shortcut (5.1.d.1) cover all 2D animation cases. Decisions D1-Dn not yet locked.

### SPEC 009 - Code modularity (in flight)

- **Refactor into packages without behavior change.** Waves 9.1 to 9.9 split monolithic modules (writer, panels, operators, validation) into focused subpackages. No format change, no user-facing change. Behavior tests carry the proof.
