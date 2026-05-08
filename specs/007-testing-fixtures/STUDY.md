# SPEC 007 — Testing fixtures

## Problem

The original `dummy/` fixture covers only one workflow (a single shared atlas with N sub-rects per sprite). After validating the atlas packer (5.1.c.2 + 5.1.c.2.1 + 5.1.c.2.2) on dummy, the gaps in coverage are obvious:

- **No `1 sprite = 1 PNG` test.** The packer was implemented to handle this case — the common Photoshop-first path — but no fixture exercises it.
- **No real `sprite_frame` animation test.** `effect/` (Godot-side fixture, hand-written `.proscenio`) tests the importer, but nothing tests the writer emitting a `sprite_frame` track from a real Blender action.
- **No fixture is auditable from source.** `dummy.blend` is a binary; a developer cannot read what bones / sprites it contains without opening Blender.
- **No comprehensive showcase.** A user trying to learn the pipeline has no single character that demonstrates polygon meshes + sprite_frame + weights + IK + multi-action authoring side-by-side.

Plus the Photoshop side is still scaffold — fixtures must not require Photoshop to bootstrap. Everything has to come out of `blender --background --python`.

## Reference: what other tools test against

- **Spine examples** — small, focused, deterministic; one feature per example file.
- **DragonBones samples** — separate project per skeletal style.
- **COA Tools** — minimal art, all examples deterministic.

The pattern is "small + focused + auditable + buildable from source". Fixtures are tests, not portfolio art.

## Constraints

- Run headlessly in CI. No Photoshop dependency.
- Source-controlled inputs: every PNG comes out of a Python script that draws geometric shapes (squares, circles, triangles, rectangles, cylinders) to a buffer. No artist labor on test fixtures.
- LFS-friendly: `.blend` files committed but small.
- Cover three distinct test concerns separately rather than overload one fixture.

## Two fixture types

| Type | Defines | When to use |
| --- | --- | --- |
| **A — End-to-end** | `.blend` source + builder script + golden `.proscenio` + Godot wrapper | Default. Tests writer + importer together. |
| **B — Importer-only** | Hand-written `.proscenio` (no `.blend`) | Only for edge cases the writer cannot produce — invalid `format_version`, unknown track types, minimum-fields-default tests |

In v1 of SPEC 007, only Type A fixtures ship. Type B starts when an actual edge case shows up in production debugging.

## Three Type A fixtures

| Fixture | Role | Rough size |
| --- | --- | --- |
| **`doll/`** | **Comprehensive showcase.** Full humanoid rig + per-body-part meshes covering polygon + sprite_frame + multi-bone weights + multi-action authoring. The fixture grows as new features ship — SPEC 004 adds a slot, SPEC 008 adds UV-animated iris, etc. The integration test for cross-feature interactions and the visual demo for users learning the pipeline. | ~22 sprite meshes, ~4 actions, evolving |
| **`blink_eyes/`** | **Sprite_frame end-to-end isolation test.** A single sprite_frame mesh + 1 spritesheet PNG + 1 action animating frame index. Tests writer→`.proscenio`→importer for the sprite_frame path. | 1 sprite, 1 action, ~150 LOC builder |
| **`shared_atlas/`** | **Sliced atlas packer isolation test.** Three quads referencing one shared atlas PNG with partial UV bounds. Tests the slicing logic introduced in SPEC 005.1.c.2.1. | 3 sprites, no animation, ~120 LOC builder |

The three together cover every feature path end-to-end. `dummy/`, `effect/`, `skinned_dummy/` get retired in a follow-up PR after the new fixtures land and run green in CI.

## `doll/` — the showcase fixture

### Skeleton

The armature is authored inside `doll.blend` (`doll.rig`). Hierarchy mirrors a simplified humanoid: root → pelvis split + leg chain (thigh / shin / foot) on each side, plus a 4-segment spine column ending at the neck → head with the usual face attachments (brow, ear, eye, lip). The arms branch off the upper spine (shoulder → arm → forearm → hand). `doll.blend` is the source of truth — read it in Blender for the exact bone names and counts.

### Sprite layout

Each top-level mesh in `doll.blend` is one sprite layer. Mesh names use the Blender `.L` / `.R` symmetric convention (D8). Sprite kinds:

| Mesh kind | Examples | Rationale |
| --- | --- | --- |
| polygon, single primary bone | `head`, `chest`, `belly`, `waist`, `arm.L/R`, `forearm.L/R`, `hand.L/R`, `leg.L/R`, `thigh.L/R`, `foot.L/R`, `brow.L/R`, `ear.L/R` | Standard parented sprites. |
| polygon, multi-bone weights | `chest` / `belly` / `waist` (weighted across the spine chain), pelvic meshes weighted across `pelvis.L`/`pelvis.R` | Demonstrates weight-paint distribution + falloff. |
| sprite_frame | `eye.L`, `eye.R` | 4 frames (open / mid / closing / closed). Driven by the `blink` action. |
| polygon, slot-ready | `brow.L`, `brow.R` | Future home for the slot system (SPEC 004) swapping brow-up / brow-down. |
| polygon, driver-driven texture swap | `forearm.L`, `forearm.R` | Driver on `forearm` rotation flips front/back forearm sprite. Lands when SPEC 004 + driver shortcut (5.1.d) ship. |

### Visual style

Each mesh in `doll.blend` carries a flat-color material. `scripts/fixtures/doll/render_layers.py` reads each material's Principled BSDF Base Color and stamps a flat-shaded PNG (Workbench engine, transparent background) under `examples/doll/render_layers/`. Region colors are the artist's choice in the `.blend` — change a Base Color, re-run the render, the layer PNG updates. Flat shading (no lighting) keeps the layer output indistinguishable from a Photoshop-painted layer, and weight-paint smearing across bone seams stays visually obvious.

### Actions

Built into the `.blend` initially:

| Action | Frames | Animates | Why |
| --- | --- | --- | --- |
| `idle` | 30, loop | spine bob + breath | tests bone_transform tracks across multiple bones |
| `wave` | 30 | shoulder.R + upper_arm.R + forearm.R rotation | demonstrates IK chain (target on hand.R) |
| `blink` | 12 | `eye.L.proscenio.frame` + `eye.R.proscenio.frame` | exercises sprite_frame track |
| `walk` | 30, loop | thigh / shin / foot rotation, spine sway | full-body coordination test |

Future actions land as future SPECs require them (talk for SPEC 008 lips, etc).

## Decisions to lock

### D1 — Where do fixtures live?

**Locked: `examples/`** (current). Same directory as `dummy/` already. CI already points there.

### D2 — How are PNGs created?

**Locked: rendered from the committed `.blend` via headless Blender.** The `.blend` is the authored source of truth for the fixture's visual; per-region PNG layers fall out of it deterministically:

- `scripts/fixtures/<fixture>/render_layers.py` — bpy-only, opens the `.blend`, walks every mesh object, and renders each one through an orthographic front camera with Workbench flat shading + transparent background. Run with `blender --background examples/<fixture>/<fixture>.blend --python scripts/fixtures/<fixture>/render_layers.py`. Output lands at `examples/<fixture>/render_layers/`.
- `scripts/fixtures/build_<fixture>.py` — kept for fixtures whose `.blend` is generated procedurally rather than authored by hand (`blink_eyes/`, `shared_atlas/`). Loads PNGs from disk and assembles `.blend`.

Rendering from the `.blend` mirrors the future Photoshop-driven workflow (one layer per body part flattened to PNG) and removes the divergence risk between an authored 3D source and a separately drawn 2D layer roster. PNG resolution = mesh bounding-box × `PIXELS_PER_UNIT` (default 100) so pixels stay square across the fixture.

### D3 — `.blend` files committed or rebuilt every CI run?

**Locked: committed**. Builders kept around for re-creation when the fixture spec changes. CI does not rebuild — it just runs the writer against the committed `.blend` and diffs.

### D4 — Sprite_frame frame layer naming convention

**Locked: `<name>_<index>`** (e.g. `eye_0` … `eye_3`). Matches Spine convention; SPEC 006 PS importer will consume this same convention to group layers into sprite_frame meshes.

### D5 — Builder script location

**Locked: `scripts/fixtures/`** (under repo `scripts/`).

### D6 — Builder runtime

**Locked: headless Blender** (`blender --background --python build_<name>.py`). Blender is already a CI dependency. Re-using it for fixture builds is free and avoids any external dependencies (Pillow, etc).

### D7 — CI integration

**Locked: one CI job iterates every fixture.** `tests/run_tests.py` walks `examples/*/` and re-exports each, diffing against the per-fixture golden.

### D8 — Bone naming

**Locked: Blender symmetric naming** (`name.L` / `name.R`). Indexed sub-bones use `name.001` / `name.002` (e.g. `spine` → `spine.001` → `spine.002`). Neutral generics over anatomical specifics where the swap target is open (e.g. an attachment slot named after the bone, not the prop, so future swaps do not require renaming).

### D9 — `pelvis.L` / `pelvis.R` keep or drop?

**Locked: keep.** Used for asymmetric hip motion + butt-jiggle weight demos. Cost is two extra bones; benefit is real-world authoring scenarios.

### D10 — Visual style

**Locked: geometric primitives** (circles, rectangles, triangles, trapezoids). Colored by body region for instant visual debugging. No artist labor needed; fully reproducible from script.

### D11 — Build order

**Locked: blink_eyes → shared_atlas → doll.** Smallest first, validates the pipeline + builder pattern, then escalating complexity. doll is large enough that we want the smaller fixtures known-good before tackling it.

## Out of scope

- A test fixture for the slot system (SPEC 004) — placeholder only; lands when SPEC 004 ships.
- A fixture for SPEC 006 PS importer (lands with SPEC 006).
- Real character art (`firebound_character/`) — that is the integration test for SPEC 006.
- UV animation fixture (`flow_water/`) — premature without SPEC 008.

## Successor considerations

- SPEC 004 (slots): `doll/` gains a slot for `hand.L.attachment` (sword vs bow swap).
- SPEC 006 (PS importer): `doll/` gets a PSD source + JSX manifest input alongside the build script as cross-validation.
- SPEC 008 (UV animation): `doll/` gains an iris-scroll track on `eye.L`/`eye.R`.

The doll fixture grows feature-by-feature. The two minimal fixtures (`blink_eyes`, `shared_atlas`) stay frozen — their job is to isolate one feature each.

## Migration plan

After this SPEC ships, a follow-up PR retires the legacy fixtures:

| Today | Tomorrow | Coverage migrated to |
| --- | --- | --- |
| `examples/dummy/` | DELETE | `doll/` (polygon + weights + bone_transform), `shared_atlas/` (sliced packer) |
| `examples/effect/` | DELETE | `blink_eyes/` (end-to-end sprite_frame), `doll/` (sprite_frame mid-action) |
| `examples/skinned_dummy/` | DELETE | `doll/` (multi-bone weights end-to-end) |

The retirement PR ships only after the three new fixtures' goldens are committed and CI is green against them.

## Mockup directory layout

Each fixture is split into subfolders by **role in the pipeline**: the source-of-truth `.blend` and the validation golden live at the fixture root; everything else falls into a named subfolder.

```text
examples/
├── doll/
│   ├── README.md
│   ├── doll.blend                          [SOURCE — authored Blender]
│   ├── doll.expected.proscenio             [GOLDEN — CI-diffed validation]
│   ├── render_layers/                      Workbench-rendered PNGs, one per mesh
│   │   ├── head.png / chest.png / belly.png / waist.png
│   │   ├── arm.L/R, forearm.L/R, hand.L/R
│   │   ├── leg.L/R, thigh.L/R, foot.L/R
│   │   ├── eye.L/R, brow.L/R, ear.L/R
│   │   └── pieces_sheet.png                contact sheet (visual debug)
│   ├── photoshop_import/                   Inputs to + output of the JSX importer
│   │   ├── doll.psd_manifest.json          bpy → SPEC 006 v1 manifest
│   │   └── doll.psd                        JSX importer output (PSD)
│   ├── photoshop_export/                   JSX exporter output (gitignored — roundtrip artifact)
│   │   ├── doll.json                       re-exported manifest
│   │   └── images/                         re-exported per-layer PNGs
│   └── godot/                              Godot wrapper artifacts
│       ├── Doll.tscn
│       └── Doll.gd
├── blink_eyes/
│   ├── README.md
│   ├── blink_eyes.blend                    [SOURCE — built by build_blend.py]
│   ├── blink_eyes.expected.proscenio       [GOLDEN]
│   ├── pillow_layers/                      Pillow draws + spritesheet
│   │   ├── eye_0.png … eye_3.png
│   │   └── eye_spritesheet.png
│   └── godot/
│       ├── BlinkEyes.tscn
│       └── BlinkEyes.gd
└── shared_atlas/
    ├── README.md
    ├── shared_atlas.blend                  [SOURCE]
    ├── shared_atlas.expected.proscenio     [GOLDEN]
    ├── atlas.png                           Pillow → atlas (single PNG, no subfolder)
    └── godot/
        ├── SharedAtlas.tscn
        └── SharedAtlas.gd

scripts/fixtures/
├── _shared/
│   ├── _draw.py                            Pillow rasterizer (used by every Pillow-driven fixture)
│   └── export_proscenio.py                 bpy — open <fixture>.blend → write <fixture>.expected.proscenio
├── doll/
│   ├── render_layers.py                    bpy — doll.blend → render_layers/*.png (Workbench flat)
│   ├── export_psd_manifest.py              bpy — doll.blend → photoshop_import/doll.psd_manifest.json
│   └── preview_pieces.py                   Pillow — render_layers/*.png → render_layers/pieces_sheet.png
├── blink_eyes/
│   ├── draw_layers.py                      Pillow → pillow_layers/eye_0..3.png + eye_spritesheet.png
│   └── build_blend.py                      bpy — load spritesheet, build blink_eyes.blend
└── shared_atlas/
    ├── draw_atlas.py                       Pillow → atlas.png
    └── build_blend.py                      bpy — load atlas, build shared_atlas.blend
```

The doll fixture has **no** programmatic weight or action assignment script — everything visual, weights, and animation lives inside the hand-authored `doll.blend`. The blink_eyes and shared_atlas fixtures stay procedural because they are minimal isolation tests where authoring a `.blend` by hand would add overhead with no payoff.
