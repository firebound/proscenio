# SPEC 007 — Testing fixtures

## Problem

The `dummy/` fixture covers only one of the workflows the addon must support — sprites whose source images all reference a **shared atlas**. The Photoshop-first workflow (the one most users will use once SPEC 006 ships) is the inverse: each layer is exported as its own PNG, then Blender either keeps `1 sprite = 1 PNG` or asks the addon to pack a fresh atlas.

After validating the atlas packer (5.1.c.2 + 5.1.c.2.1 + 5.1.c.2.2) on `dummy/`, the gaps in coverage are obvious:

- **No `1 sprite = 1 PNG` test.** The packer was implemented to handle this case (and the slicing path in 5.1.c.2.1 specifically guards it), but no fixture exercises it end-to-end.
- **No real `sprite_frame` animation test.** `effect/` (Godot-side fixture) tests the importer, but there is no Blender `.blend` that authors a `sprite_frame` mesh with an actual frame-index animation track.
- **No fixture is auditable from source.** `dummy.blend` is a binary; a developer cannot tell what bones / sprites it contains without opening Blender. Diffing changes is a coin flip.

## Reference: what other tools test against

- **Spine examples** (open-source samples shipped with their runtime) — small, focused, one-feature-per-file.
- **DragonBones samples** — separate `.dbproj` per skeletal style (mesh, basic, IK).
- **COA Tools** — `examples/` per workflow; minimal art, deterministic.

The pattern is "small, focused, deterministic, source-controlled". Fixtures are tests, not portfolio art.

## Constraints

- Must run headlessly in CI (`blender --background <fixture>.blend --python run_tests.py`).
- PNGs must be tiny (CI checkout speed; LFS already used for `.blend` files).
- `.blend` is binary, but the **inputs** that produced it (PNG sources + a build script) should be source-controlled so the `.blend` is rebuildable.
- No proprietary art assets — all fixtures use programmatically-generated images (solid colors, simple gradients).
- Must cover at least: `1-sprite-1-PNG` polygon, `sprite_frame` with animation, weighted polygon. Shared-atlas coverage stays in `dummy/`.

## Design surface

```
examples/
├── dummy/             # shared-atlas legacy + sliced-repack stress test
├── effect/            # sprite_frame importer test (Godot-side, hand-written .proscenio)
├── skinned_dummy/     # weights importer test (Godot-side, hand-written .proscenio)
├── simple_doll/       # NEW — 1 sprite = 1 PNG, weighted skinning, 2 actions
└── blink_eyes/        # NEW — sprite_frame mesh with frame-index animation track
```

### `simple_doll/`

| Aspect | Choice |
|---|---|
| Sprites | 5 polygon meshes — `head`, `torso`, `arm.L`, `arm.R`, `legs` |
| PNGs | One per sprite, programmatically generated (solid colors with thin border for visual debug) |
| Skeleton | 6 bones: `root`, `spine`, `head`, `arm.L`, `arm.R`, `legs` |
| Weights | Each sprite weighted to its parent bone (1.0); `arm.L` / `arm.R` get a 0.3 spillover to `spine` to test multi-bone weights |
| Actions | `idle` (4-frame loop), `wave` (8-frame, animates `arm.R` rotation) |
| Atlas | None initially — addon packs at export time (tests Pack + Apply path) |
| Build script | `scripts/fixtures/build_simple_doll.py` — runs in headless Blender, generates PNGs + assembles `.blend` from scratch |
| Golden | `simple_doll.expected.proscenio` checked in; CI re-exports and diffs |

### `blink_eyes/`

| Aspect | Choice |
|---|---|
| Sprite | 1 sprite_frame mesh — `eye` |
| PNG | 1 spritesheet `eye.png` — 4 frames horizontal (open / squint / closed / squint), each 32×32 |
| Skeleton | 1 bone — `head` |
| Action | `blink` (12 frames, animates `eye.proscenio.frame` from 0→1→2→3→2→1→0) — exercises the `sprite_frame` track type |
| Atlas | None initially — addon Pack/Apply rebuilds; sliced support (5.1.c.2.1) puts the spritesheet in its own slot |
| Build script | `scripts/fixtures/build_blink_eyes.py` |
| Golden | `blink_eyes.expected.proscenio` |

## Design decisions to lock

### D1 — Where do fixtures live?

- **D1.A — `examples/`** (current). Same place `dummy/` already lives.
- **D1.B — `fixtures/`** (new top-level dir). Separate "examples for users" from "fixtures for tests".

**Recommendation: D1.A.** `examples/` already mixes worked examples + golden fixtures and CI hardcodes the path. Splitting now adds churn for no signal.

### D2 — How are PNGs created?

- **D2.A — Hand-painted by an artist** in Photoshop / Krita.
- **D2.B — Programmatically generated** by a Python script using PIL / Pillow (or `bpy.types.Image` directly).

**Recommendation: D2.B.** Fixture art is test scaffolding. Deterministic + tiny + diffable + version-controllable + buildable on any machine without Photoshop.

### D3 — Are `.blend` files committed, or rebuilt every CI run?

- **D3.A — Commit `.blend`** (current). Build script kept around for re-creation; `.blend` itself is the canonical source.
- **D3.B — Rebuild from script every CI run.** No `.blend` in repo.

**Recommendation: D3.A.** Rebuilding adds ~10s per CI job. `.blend` is < 1 MB per fixture (LFS handles it). Keep the build script for re-creation; `.blend` stays committed.

### D4 — Naming convention for sprite_frame frame layers (preps for SPEC 006)

- **D4.A — `<name>_<index>`** (e.g. `eye_0`, `eye_1`, `eye_2`, `eye_3`). Photoshop layer naming triggers sprite_frame grouping in the importer.
- **D4.B — `<name>.frame.<index>`** (e.g. `eye.frame.0`). More explicit but verbose.
- **D4.C — Folder-per-spriteframe** (PSD group `eye/` containing N layer children).

**Recommendation: D4.A.** Concise, matches Spine's naming convention, easy to author. SPEC 006 will lock this convention; SPEC 007 fixture `blink_eyes/` uses it preemptively to avoid rework.

### D5 — Build script location

- **D5.A — `scripts/fixtures/build_<name>.py`** (under repo `scripts/`).
- **D5.B — `examples/<name>/build.py`** (next to the fixture).

**Recommendation: D5.A.** Build scripts are dev tooling; `scripts/` already collects this kind of thing. Examples directory stays asset-only.

### D6 — Should the build script use Blender or a pure-Python approach?

- **D6.A — Headless Blender** (`blender --background --python build.py`). Has full bpy API.
- **D6.B — Pure Python** building `.blend` via library (e.g. `blender-asset-tracer`, but generally fragile).

**Recommendation: D6.A.** Blender is already a CI dependency for `test-blender` job. Re-using it for fixture builds is free.

### D7 — CI integration for new fixtures

- **D7.A — Add a CI job per fixture** mirroring `test-blender` for `dummy`.
- **D7.B — One `test-blender` job iterates every fixture.**

**Recommendation: D7.B.** Less CI churn; one job, one Blender download, multiple fixtures asserted.

### D8 — What about the existing `dummy/`?

- **D8.A — Keep as-is, document its limitation** (shared-atlas legacy / sliced-repack stress).
- **D8.B — Replace with PS-first workflow.**
- **D8.C — Drop entirely.**

**Recommendation: D8.A.** `dummy/` is the only fixture exercising the shared-atlas + sliced packer code path. Real-world bug catch potential is high. Cost of keeping it is zero.

## Out of scope

- A test fixture for the slot system (SPEC 004 placeholder — fixture lands when SPEC 004 ships).
- A fixture for SPEC 006 PS importer (lands with SPEC 006).
- Real character art (`firebound_character/`) — that's the integration test once SPEC 006 imports it.
- UV animation fixture — premature without SPEC 008.

## Successor considerations

- SPEC 004 (slots) adds `swap_face/` fixture: 1 mesh, 3 attachment images, slot animation track.
- SPEC 006 (PS importer) adds `simple_psd/` fixture: source `.psd` + JSX-exported manifest + expected `.blend` post-import.
- SPEC 008 (UV animation) adds `flow_water/` fixture if the SPEC ships.

## Mockup — `simple_doll/` directory layout

```text
examples/simple_doll/
├── README.md                      what this fixture tests
├── layers/
│   ├── head.png                   64x64 solid red w/ thin black border
│   ├── torso.png                  96x128 blue
│   ├── arm.L.png                  32x96 green
│   ├── arm.R.png                  32x96 green
│   └── legs.png                   80x96 gold
├── simple_doll.blend              committed binary (LFS)
├── simple_doll.expected.proscenio golden — CI diffs against re-export
├── Doll.tscn                      Godot wrapper (manual user pattern, SPEC 001)
└── Doll.gd                        empty stub script

scripts/fixtures/build_simple_doll.py    headless rebuilder
```
