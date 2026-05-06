# doll fixture (SPEC 007)

The **comprehensive showcase fixture** for the Proscenio pipeline. A full humanoid character with 37 bones, ~25 sprite meshes, multi-bone weights, sprite_frame eyes, and four authored actions. Demonstrates everything the addon supports today; grows feature-by-feature as future SPECs ship (slot system, UV animation, driver-based texture swap).

## Contents (after running the build script)

```
doll/
├── layers/                         generated PNGs, geometric primitives per region
│   ├── head_base.png               circle, beige
│   ├── eye_0.png … eye_3.png       sprite_frame frames (open / partial / closed)
│   ├── eye_spritesheet.png         128×32 strip used by both eyes
│   ├── spine_block.png             rectangle, blue
│   ├── pelvis_block.png            trapezoid, navy
│   ├── shoulder.L.png … etc        circles + rectangles + trapezoids
│   └── ...
├── doll.blend                      ~37 bones, ~25 sprites, 4 actions
├── doll.expected.proscenio         golden — CI diffs against re-export
├── Doll.tscn                       Godot wrapper (manual user pattern, SPEC 001)
├── Doll.gd                         empty stub
└── README.md
```

## Skeleton (37 bones)

```
root
├── pelvis.L                        asymmetric pelvis — hip motion + butt-jiggle weights
├── pelvis.R
├── thigh.L → shin.L → foot.L
├── thigh.R → shin.R → foot.R
└── spine → spine.001 → spine.002 → spine.003
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
                ├── eye.L                     sprite_frame
                ├── eye.R                     sprite_frame
                ├── jaw
                ├── lip.T
                └── lip.B
```

## Sprites (highlights)

| Sprite | Mesh kind | Why it exists |
|---|---|---|
| `pelvis_block` | polygon | Demonstrates **multi-bone weights**: 0.5 / 0.5 across `pelvis.L` and `pelvis.R`. |
| `spine_block` | polygon | Demonstrates **falloff weights**: 0.4 / 0.4 / 0.15 / 0.05 across the four spine bones. |
| `forearm.L` / `forearm.R` | polygon | Multi-bone weight spillover (1.0 forearm + 0.3 upper_arm). Future home for driver-driven texture swap (when SPEC 004 + 5.1.d ship). |
| `eye.L` / `eye.R` | sprite_frame | Hframes=4 spritesheet, animated by the `blink` action. |
| `brow.L` / `brow.R` | polygon | Future home for slot-system swap (brow-up / brow-down) when SPEC 004 ships. |

All other sprites are standard polygon meshes parented + weighted to a single bone.

## Visual style

Geometric primitives only — circles, rectangles, triangles, trapezoids — colored by body region. Reasoning:

- Weight-paint smearing across a bone seam is instantly visible (color bleeds where weights interpolate).
- No artist labor needed; everything is reproducible from a Python script.
- Diffs in `git` show real changes, not coloring tweaks.

| Region | Color |
|---|---|
| Skin (head / neck / jaw / ears) | warm beige |
| Eyes | white iris + dark pupil |
| Brows | dark brown |
| Lips | red |
| Torso (spine) | blue |
| Pelvis | navy |
| Breasts | light blue |
| Shoulders / arms / hands | green (varying brightness) |
| Thighs / shins | gold |
| Feet | brown |

## Actions

| Action | Frames | Animates | Why |
|---|---|---|---|
| `idle` | 30, loop | spine.001 + spine.002 vertical bob (breath) | bone_transform tracks across multiple bones |
| `wave` | 30 | upper_arm.R + forearm.R rotation | demonstrates IK-friendly chain (no IK constraint exported, but Blender-side Toggle IK works) |
| `blink` | 12 | eye.L + eye.R `proscenio.frame` 0→1→2→3→2→1→0 | exercises sprite_frame track type |
| `walk` | 30, loop | thigh.L/R + shin.L/R rotation, spine sway | full-body coordination |

Future actions land as future SPECs require (talk action when lip phonemes ship under SPEC 008, etc).

## Building from source

Two-stage: PNG generation runs without Blender, `.blend` assembly runs in headless Blender.

```bash
# 1. Generate every body PNG + eye spritesheet (Python + Pillow).
python scripts/fixtures/draw_doll.py

# 2. Assemble the .blend (37-bone armature + sprite meshes + weights + 4 actions).
blender --background --python scripts/fixtures/build_doll.py

# 3. Generate the golden .proscenio.
blender --background examples/doll/doll.blend \
    --python scripts/fixtures/export_proscenio.py
```

Builder is split into helpers under `scripts/fixtures/`:

- `_draw.py` — Pillow-based shape rasterizer (no bpy)
- `draw_doll.py` — Pillow orchestrator: every body PNG + eye spritesheet
- `_doll_armature.py` — bpy: 37-bone hierarchy
- `_doll_meshes.py` — bpy: load PNGs, build sprite planes + materials
- `_doll_weights.py` — bpy: vertex groups + weights
- `_doll_actions.py` — bpy: idle / wave / blink / walk
- `build_doll.py` — bpy orchestrator

## What this fixture catches when broken

- Anything end-to-end that touches polygon meshes + weights + actions + sprite_frame.
- Multi-bone weight export regression (pelvis_block, spine_block, forearm.L/R).
- sprite_frame eye animation regression.
- Multi-action authoring regression.
- Schema bumps that affect more than one feature at once.

## Future growth

| When | Adds |
|---|---|
| SPEC 004 (slots) ships | Slot on `hand.L.attachment` (sword vs bow swap). Slot on `brow.L/R` (brow-up vs brow-down). |
| SPEC 006 (PS importer) ships | A `doll.psd` source + JSX manifest input as cross-validation. |
| SPEC 008 (UV animation) ships | Iris-scroll track on `eye.L` / `eye.R`. |
| Driver-based texture swap (5.1.d + SPEC 004) | Forearm rotation drives forearm front/back texture swap. |

Each addition extends the fixture without invalidating older actions — golden `.proscenio` diff catches surprise regressions.
