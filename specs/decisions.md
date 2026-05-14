# Decisions

Architectural and per-SPEC decisions that are locked. ADR-light: each entry records the call, the rationale, and the trigger that would force a revisit.

Per-SPEC design rationale lives in `<NNN>/STUDY.md` alongside this file; the rolling backlog of open work lives in [`backlog.md`](backlog.md). This file aggregates the cross-cutting decisions plus the per-SPEC tradeoffs worth surfacing outside their STUDY.

## Core architecture

| Decision | Rationale | Revisit trigger |
| --- | --- | --- |
| **No GDExtension, no native runtime** | Plugin is GDScript-only. Generated `.scn` uses native nodes; runs on plain Godot 4 with the plugin uninstalled. | Deep Firebound integration, perf ceiling on `Polygon2D` skinning, live-link Blender ↔ Godot, binary `.proscenio`, in-Godot authoring round-trip. |
| **Conversion one-time, at editor import** | Heavy work runs at import time. Runtime uses Godot core (already C++); no GDScript performance ceiling. | Same triggers as the GDExtension entry. |
| **Strong typing everywhere** | GDScript 2.0 typed (`untyped_declaration=2` error), Python `mypy --strict`, TypeScript `strict`. Catches errors before runtime. | None. Baseline rule. |
| **Schemas are the contract** | Any change to a cross-component shape requires a `format_version` bump on the affected schema plus a migration path. CI validates fixtures against the schemas. | None. Bumps are how the schemas evolve; bumps are not breakage. |
| **PropertyGroup canonical, Custom Property fallback** | Blender authoring uses typed PropertyGroup; raw Custom Properties remain readable for legacy assets. The writer reads PropertyGroup first, falls back to Custom Properties. | None. Legacy Custom Properties stay for backwards compatibility. |
| **Wrapper-scene pattern for Godot reimport** | The importer overwrites `.scn` on every reimport; the user-authored wrapper `.tscn` survives intact and carries scripts and extras. | Marker-based merge stays deferred unless concrete demand emerges. |
| **One component per PR** | Photoshop, Blender, and Godot ship independent PRs. Schema bumps cross all components by definition. | None. |
| **C# / GDExtension as documented escape hatch, not active option** | Maintainer prefers strong typing over GDScript's dynamism, but stays in GDScript for plugin reach in the broader 2D community. Firebound itself stays C#. | Same as the GDExtension entry. |

## Validation gates

Layered defenses, cheapest first:

1. **Editor / IDE.** Live diagnostics through each language's standard extensions (Pylance for Python, gdtoolkit for GDScript, TypeScript LSP for TS), plus a shared spell-checker.
2. **Pre-commit.** Per-language formatters and linters, schema validation against staged JSON files, spell-checker.
3. **CI - Python.** `ruff` + `mypy --strict` + pytest against the Blender addon's typed surface.
4. **CI - TypeScript.** `tsc --noEmit` + `vitest` against the Photoshop plugin.
5. **CI - GDScript.** `gdformat --check` + `gdlint` against the Godot plugin.
6. **CI - schemas.** Every fixture under `examples/` and per-app `tests/fixtures/` is validated against the cross-component schemas.

The schemas themselves are enforced at four points: producer output (writer / exporter validates before any test diff), consumer input (runtime check on the Photoshop side, format-version guard on the Godot side), CI fixture validation, and the migration path on any future version bump.

## Per-SPEC tradeoffs

Highlights that crossed component boundaries or shaped a contract. Full decision logs live in each `<NNN>/STUDY.md`.

### SPEC 000 - Phase 1 MVP

- **Animation tracks ship resolved values, not rest+delta.** Exporter resolves into absolute positions, rotations, scales; the importer just reads. Simpler consumer side; the cost is bigger animation payloads.

### SPEC 001 - Reimport-merge

- **Full overwrite + wrapper-scene pattern chosen over marker-based merge.** Marker-based merge would lose user-attached scripts on a bone rename (no stable IDs in the schema) and duplicate code paths. Deferred unless concrete pain surfaces that the wrapper pattern genuinely cannot serve.

### SPEC 002 - Spritesheet / Sprite2D

- **`type` discriminator additive in the schema, not a `format_version` bump.** The `sprite_frame` variant lives alongside `polygon` under a `type` field that defaults to `"polygon"` when omitted - keeps pre-discriminator fixtures backwards-compatible.

### SPEC 003 - Skinning weights

- **Skinned polygons parent to `Skeleton2D`, not to a single bone.** Weights drive vertex deformation; rigid sprites remain bone-parented. The two parenting strategies coexist by design.
- **Validation is user-driven (paint weights, observe deformation).** No programmable check covers visual quality.

### SPEC 004 - Slot system

- **Hard cut, NEAREST interpolation on `slot_attachment` tracks.** Smooth crossfade is a future extension.
- **Sprites stay in the top-level `sprites[]` array.** `slots[].attachments[]` is a list of names; the importer cross-references. The schema stays flat - no `slot:` field on `Sprite`.
- **Slot system fits inside `format_version=1`.** `slots[]` and the `slot_attachment` track type were already part of v1 - no bump.
- **Slot is kind-agnostic.** `polygon` meshes and `sprite_frame` attachments compose freely inside the same slot.

### SPEC 005 - Blender authoring panel

- **PropertyGroup canonical, Custom Properties fallback.** The writer reads PropertyGroup first; raw Custom Properties only as a legacy path. Defaults flow through cleanly without forcing the user to touch them.
- **Validation lazy + inline.** Lazy via the **Validate** button (heavy walk over the scene); inline status badges per subpanel are O(1) checks per redraw.

### SPEC 006 - Photoshop → Blender importer

- **The Blender side reads the manifest, never the PSD.** Direct `.psd` parsing inside Blender is fragile across PSD versions and duplicates the exporter's work. The manifest is the stable contract.
- **Sprite_frame detection has two paths.** Primary: a PSD layer group with numeric children. Fallback: flat `<name>_<index>` naming. Both detected on the Photoshop side.

### SPEC 007 - Testing fixtures

- **Five canonical fixtures cover orthogonal feature isolation.** A comprehensive showcase rig plus single-feature fixtures for sprite_frame, sliced atlas, PSD roundtrip, and slot system. A single source feeds both writer goldens and importer regenerations.

### SPEC 008 - UV animation

- **`texture_region` track type targets iris-scroll and hframe-cycling.** Closes the cutout playbook: gradual region (008) + hard swap (004) + frame index (002) + driver shortcut cover all 2D animation cases. Decisions still locking.

### SPEC 009 - Code modularity (shipped)

- **Refactor into packages without behavior change.** Monolithic modules (writer, panels, operators, validation) split into focused subpackages. No format change, no user-facing change. Behavior tests carry the proof.
- **Per-package import discipline.** `core/` stays bpy-free at module top; `core/bpy_helpers/` is the bpy-bound boundary. Panels reach operators only via `bl_idname` strings, never via direct class imports.

### SPEC 010 - Photoshop UXP migration (shipped)

- **UXP is the only Photoshop entry point.** The legacy JSX exporter and importer were retired once the doll roundtrip oracle confirmed pixel-byte parity vs the captured JSX baseline.
- **Stack locked: pnpm + webpack + Babel + ajv + vitest.** Vite rejected because UXP needs CommonJS output and Vite's ESM-first defaults fight it.
- **Schema unchanged.** The migration shipped at `format_version: 1` byte-for-byte. The PSD-manifest v2 bump that adds tags, anchor, and per-entry origin landed under SPEC 011.
- **Minimum Photoshop CC 2024 / PS 25+.** Required by the `constants.*` enums, persistent tokens, and Spectrum web components the plugin relies on.
- **`localFileSystem: "fullAccess"` required.** The minimum-privilege `"request"` covers the folder picker alone; the plugin also calls `createPersistentToken` + sub-folder writes, which need `"fullAccess"`.

### SPEC 011 - Photoshop tag system (shipped)

- **Bracket-tag inline syntax is the primary tag format.** `[tag]` / `[tag:value]` tokens inside layer names; XMP per-layer is the secondary canonical store. Bracket-tag wins on conflict.
- **PSD manifest bumped to `format_version: 2`.** Adds `anchor` at the document root and per-layer `origin`, `blend_mode`, `subfolder`. New `kind: "mesh"` variant joins `polygon` and `sprite_frame`. The `.proscenio` schema stays at v1 - this bump is PSD-side only.
- **`kind: "mesh"` is a hint, not a branch.** The Blender importer stamps a `proscenio_psd_kind` Custom Property; no downstream code branches on it yet. The distinction exists so deformable-mesh and UV-animation work can tell editable polygons apart from rigid sprites later.
- **Unknown tags pass through to the display name.** Artist typos and future tags stay visible; the Tags panel surfaces them as warnings rather than silently dropping the data.
