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
|---|---|---|
| **A — End-to-end** | `.blend` source + builder script + golden `.proscenio` + Godot wrapper | Default. Tests writer + importer together. |
| **B — Importer-only** | Hand-written `.proscenio` (no `.blend`) | Only for edge cases the writer cannot produce — invalid `format_version`, unknown track types, minimum-fields-default tests |

In v1 of SPEC 007, only Type A fixtures ship. Type B starts when an actual edge case shows up in production debugging.

## Three Type A fixtures

| Fixture | Role | Rough size |
|---|---|---|
| **`doll/`** | **Comprehensive showcase.** Full humanoid rig (~37 bones), sprites covering polygon + sprite_frame + IK + multi-bone weights + multi-action authoring. The fixture grows as new features ship — SPEC 004 adds a slot, SPEC 008 adds UV-animated iris, etc. The integration test for cross-feature interactions and the visual demo for users learning the pipeline. | ~25 sprites, ~5 actions, evolving |
| **`blink_eyes/`** | **Sprite_frame end-to-end isolation test.** A single sprite_frame mesh + 1 spritesheet PNG + 1 action animating frame index. Tests writer→`.proscenio`→importer for the sprite_frame path. | 1 sprite, 1 action, ~150 LOC builder |
| **`shared_atlas/`** | **Sliced atlas packer isolation test.** Three quads referencing one shared atlas PNG with partial UV bounds. Tests the slicing logic introduced in SPEC 005.1.c.2.1. | 3 sprites, no animation, ~120 LOC builder |

The three together cover every feature path end-to-end. `dummy/`, `effect/`, `skinned_dummy/` get retired in a follow-up PR after the new fixtures land and run green in CI.

## `doll/` — the showcase fixture

### Skeleton

37 bones in a Rigify-inspired but simplified humanoid:

```
root
├── pelvis.L                 (asymmetric pelvis bones — wiggle / hip motion)
├── pelvis.R
├── thigh.L → shin.L → foot.L
├── thigh.R → shin.R → foot.R
└── spine
    └── spine.001
        └── spine.002
            └── spine.003
                ├── breast.L
                ├── breast.R
                ├── shoulder.L
                │   └── upper_arm.L → forearm.L → hand.L → finger.001.L → finger.002.L
                ├── shoulder.R
                │   └── upper_arm.R → forearm.R → hand.R → finger.001.R → finger.002.R
                └── neck
                    └── head
                        └── face
                            ├── brow.L
                            ├── brow.R
                            ├── ear.L
                            ├── ear.R
                            ├── eye.L
                            ├── eye.R
                            ├── jaw
                            ├── lip.T
                            └── lip.B
```

`pelvis.L/R` are intentionally asymmetric — useful for hip-sway / butt-jiggle weight paint demos.

### Sprite layout

| Region | Mesh kind | Rationale |
|---|---|---|
| `pelvis_block`, `spine_block` | polygon, weighted across N bones | Demonstrates multi-bone weight paint distribution. Pelvis mesh weighted 0.5/0.5 across `pelvis.L`/`pelvis.R`; spine mesh weighted across all 4 spine bones with falloff. |
| `head_base`, `breast.L`, `breast.R`, `arm.L`, `arm.R`, `hand.L`, `hand.R`, `leg.L`, `leg.R`, `foot.L`, `foot.R` | polygon, single primary bone | Standard parented sprites. |
| `eye.L`, `eye.R` | sprite_frame | 4 frames each (open / mid / closing / closed). Driven by `blink` action. |
| `lip.T`, `lip.B` | sprite_frame (later) | Phoneme frames for talking. Defer until needed. |
| `brow.L`, `brow.R` | polygon, swap-ready | Slot system (SPEC 004) will swap between brow-up / brow-down attachments. |
| `forearm.L`, `forearm.R` | polygon, **driver-driven texture swap** | Driver on `forearm` rotation flips between front/back forearm sprite. Lands when SPEC 004 + driver shortcut (5.1.d) ship. |

### Visual style

Geometric primitives — squares, circles, triangles, rectangles, trapezoids — colored regionally. Reasoning: makes weight-paint smearing obviously visible; avoids art commitment; reproducible; readable in screenshots.

| Region | Shape | Color |
|---|---|---|
| Head base | circle | warm beige |
| Eyes | smaller circle (per frame: open/squinting/closed) | white + dark pupil |
| Brows | thin rectangle | dark brown |
| Ears | small triangle | beige |
| Jaw / lips | rectangle / thin rectangle | beige + red |
| Neck | rectangle (cylinder-ish) | beige |
| Spine block | tall rectangle | blue |
| Pelvis block | trapezoid | navy |
| Breasts | small circles | blue (lighter) |
| Shoulders | circles | green |
| Arms / forearms | rectangles | green |
| Hands | square | green-pale |
| Fingers | small rectangles | same |
| Thighs / shins | rectangles | gold |
| Feet | trapezoid | brown |

### Actions

Built into the `.blend` initially:

| Action | Frames | Animates | Why |
|---|---|---|---|
| `idle` | 30, loop | spine bob + breath | tests bone_transform tracks across multiple bones |
| `wave` | 30 | shoulder.R + upper_arm.R + forearm.R rotation | demonstrates IK chain (target on hand.R) |
| `blink` | 12 | `eye.L.proscenio.frame` + `eye.R.proscenio.frame` | exercises sprite_frame track |
| `walk` | 30, loop | thigh / shin / foot rotation, spine sway | full-body coordination test |

Future actions land as future SPECs require them (talk for SPEC 008 lips, etc).

## Decisions to lock

### D1 — Where do fixtures live?

**Locked: `examples/`** (current). Same directory as `dummy/` already. CI already points there.

### D2 — How are PNGs created?

**Locked: programmatically generated via Pillow.** Each fixture has a two-stage builder:

- `scripts/fixtures/draw_<fixture>.py` — pure Python + Pillow, generates PNG layers. Run with `python scripts/fixtures/draw_<fixture>.py`. **No Blender required.**
- `scripts/fixtures/build_<fixture>.py` — bpy-only, loads PNGs from disk and assembles `.blend`. Run with `blender --background --python scripts/fixtures/build_<fixture>.py`.

The split lets a developer iterate visuals without booting Blender (a faster cycle) and lets the drawing code be exercised in plain pytest if needed. Pillow is a tiny, ubiquitous dev dependency listed under `blender-addon/pyproject.toml [dependency-groups.dev]`; it is **not** bundled with the addon — strictly fixture / dev tooling.

**Why not bpy.types.Image directly:** earlier iteration used bpy for the drawing too. Coupled image generation to Blender unnecessarily — cycle was slower (Blender boot ~3s every iteration), helpers untestable in pytest, and a contributor wanting to tweak just visuals had to install Blender. Splitting out PNG generation removed all three pain points at the cost of one well-known dev dependency.

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

**Locked: Blender symmetric naming** (`name.L` / `name.R`). Indexed sub-bones use `name.001` / `name.002`. Neutral generics (`finger.001.L` not `index.001.L`) so future swaps (sword vs bow grip) do not require renaming.

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
|---|---|---|
| `examples/dummy/` | DELETE | `doll/` (polygon + weights + bone_transform), `shared_atlas/` (sliced packer) |
| `examples/effect/` | DELETE | `blink_eyes/` (end-to-end sprite_frame), `doll/` (sprite_frame mid-action) |
| `examples/skinned_dummy/` | DELETE | `doll/` (multi-bone weights end-to-end) |

The retirement PR ships only after the three new fixtures' goldens are committed and CI is green against them.

## Mockup directory layout

```text
examples/
├── doll/
│   ├── README.md
│   ├── layers/                          generated PNGs, one per sprite
│   │   ├── head_base.png
│   │   ├── eye_0.png … eye_3.png
│   │   ├── ...
│   ├── doll.blend
│   ├── doll.expected.proscenio
│   ├── Doll.tscn
│   └── Doll.gd
├── blink_eyes/
│   ├── README.md
│   ├── layers/eye_0.png … eye_3.png
│   ├── eye_spritesheet.png
│   ├── blink_eyes.blend
│   ├── blink_eyes.expected.proscenio
│   ├── BlinkEyes.tscn
│   └── BlinkEyes.gd
└── shared_atlas/
    ├── README.md
    ├── atlas.png
    ├── shared_atlas.blend
    ├── shared_atlas.expected.proscenio
    ├── SharedAtlas.tscn
    └── SharedAtlas.gd

scripts/fixtures/
├── _draw.py                  Pillow shape rasterizer (no bpy)
├── _doll_armature.py         bpy — doll bone hierarchy + parenting
├── _doll_meshes.py           bpy — load PNGs, build sprite planes + UVs + materials
├── _doll_weights.py          bpy — vertex groups + weights
├── _doll_actions.py          bpy — doll idle / wave / blink / walk
├── draw_blink_eyes.py        Pillow — eye frames + spritesheet PNG
├── draw_shared_atlas.py      Pillow — shared atlas PNG
├── draw_doll.py              Pillow — every doll body PNG
├── build_blink_eyes.py       bpy — load PNGs, build .blend
├── build_shared_atlas.py     bpy — load PNG, build .blend
├── build_doll.py             bpy — orchestrator (uses _doll_*)
└── export_proscenio.py       bpy — re-export an opened .blend → golden .proscenio
```
