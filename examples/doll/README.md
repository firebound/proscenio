# doll fixture (SPEC 007)

The **comprehensive showcase fixture** for the Proscenio pipeline. A full humanoid character authored by hand in `doll.blend` (~22 mesh objects + `doll.rig` armature) with multi-bone weights, sprite_frame eyes, and authored actions. Layer PNGs are rendered from the `.blend` per [SPEC 007 D2](../../specs/007-testing-fixtures/STUDY.md). Demonstrates everything the addon supports today; grows feature-by-feature as future SPECs ship (slot system, UV animation, driver-based texture swap).

## Contents

```plaintext
doll/
├── layers/                         flat 2D layer PNGs rendered from doll.blend
│   ├── head.png                    each mesh in the .blend → its own PNG
│   ├── chest.png / belly.png / waist.png
│   ├── arm.L/R, forearm.L/R, hand.L/R
│   ├── leg.L/R, thigh.L/R, foot.L/R
│   ├── brow.L/R, ear.L/R, eye.L/R
│   └── ...
├── doll.blend                      authored: mesh objects + doll.rig armature
├── doll.expected.proscenio         golden — CI diffs against re-export
├── doll_pieces_sheet.png           contact sheet of every layer (visual debug)
├── Doll.tscn                       Godot wrapper (manual user pattern, SPEC 001)
├── Doll.gd                         empty stub
└── README.md
```

## Skeleton

The armature lives inside `doll.blend` as `doll.rig` — open the `.blend` in Blender to read the exact bone names and parenting. The hierarchy is a simplified humanoid: `root` → pelvic split + per-side leg chain (thigh / shin / foot), plus a 4-segment spine column that ends at `neck → head` with the usual face attachments (brow, ear, eye, lip). The arms branch off the upper spine (shoulder → arm → forearm → hand). The `.blend` is the source of truth — this README does not duplicate the bone list because it would drift the moment the rig is tweaked.

## Sprites (highlights)

Each top-level mesh in `doll.blend` becomes one PNG layer when `render_doll_layers.py` runs. Sprite kinds:

| Mesh kind | Examples | Why it exists |
| --- | --- | --- |
| polygon, multi-bone weights | spine-region meshes (`chest` / `belly` / `waist`), pelvic mesh weighted 0.5/0.5 across `pelvis.L`/`pelvis.R` | Demonstrates **multi-bone weights** + falloff distribution. |
| polygon, multi-bone spillover | `forearm.L` / `forearm.R` | 1.0 forearm + 0.3 spillover to the upper arm. Future home for driver-driven texture swap (when SPEC 004 + 5.1.d ship). |
| sprite_frame | `eye.L` / `eye.R` | Hframes=4 spritesheet, animated by the `blink` action. |
| polygon, slot-ready | `brow.L` / `brow.R` | Future home for the slot system (SPEC 004) — brow-up / brow-down swap. |
| polygon, single primary bone | everything else (`head`, `arm.L/R`, `leg.L/R`, `thigh.L/R`, `foot.L/R`, `hand.L/R`, `ear.L/R`, ...) | Standard parented sprites. |

## Visual style

Each mesh in `doll.blend` carries its own material; `render_doll_layers.py` reads each material's Principled BSDF Base Color and stamps a flat-shaded PNG (Workbench engine, transparent background). Region colors are the artist's choice in the `.blend`, not hardcoded — change a material's Base Color, re-run the render, the layer PNG updates.

Why flat-shaded layers (no lighting) — the layered 2D output mirrors the future Photoshop-driven workflow (one layer per region) and keeps weight-paint smearing across bone seams visually obvious.

## Actions

| Action | Frames | Animates | Why |
| --- | --- | --- | --- |
| `idle` | 30, loop | spine.001 + spine.002 vertical bob (breath) | bone_transform tracks across multiple bones |
| `wave` | 30 | upper_arm.R + forearm.R rotation | demonstrates IK-friendly chain (no IK constraint exported, but Blender-side Toggle IK works) |
| `blink` | 12 | eye.L + eye.R `proscenio.frame` 0→1→2→3→2→1→0 | exercises sprite_frame track type |
| `walk` | 30, loop | thigh.L/R + shin.L/R rotation, spine sway | full-body coordination |

Future actions land as future SPECs require (talk action when lip phonemes ship under SPEC 008, etc).

## Building from source

`doll.blend` is the authored source of truth (hand-modelled meshes + `doll.rig` armature). Layer PNGs fall out of it via headless Blender:

```bash
# 1. Render every mesh in doll.blend to examples/doll/layers/<name>.png
#    (Workbench flat shading, ortho front view, transparent background).
blender --background examples/doll/doll.blend \
    --python scripts/fixtures/render_doll_layers.py

# 2. Generate the golden .proscenio.
blender --background examples/doll/doll.blend \
    --python scripts/fixtures/export_proscenio.py
```

Helpers under `scripts/fixtures/`:

- `render_doll_layers.py` — bpy: opens `doll.blend`, renders each mesh as a flat 2D layer
- `preview_doll_pieces.py` — Pillow: contact sheet of every layer PNG (visual sanity check)
- `export_proscenio.py` — bpy: re-exports the opened `.blend` to the golden `.proscenio`

Weights and actions are authored inside `doll.blend` directly (vertex groups + weight paint + action editor). No separate script applies them.

## What this fixture catches when broken

- Anything end-to-end that touches polygon meshes + weights + actions + sprite_frame.
- Multi-bone weight export regression (pelvic mesh, spine-region meshes, `forearm.L/R`).
- sprite_frame eye animation regression.
- Multi-action authoring regression.
- Schema bumps that affect more than one feature at once.

## Future growth

| When | Adds |
| --- | --- |
| SPEC 004 (slots) ships | Slot on `hand.L.attachment` (sword vs bow swap). Slot on `brow.L/R` (brow-up vs brow-down). |
| SPEC 006 (PS importer) ships | A `doll.psd` source + JSX manifest input as cross-validation. |
| SPEC 008 (UV animation) ships | Iris-scroll track on `eye.L` / `eye.R`. |
| Driver-based texture swap (5.1.d + SPEC 004) | Forearm rotation drives forearm front/back texture swap. |

Each addition extends the fixture without invalidating older actions — golden `.proscenio` diff catches surprise regressions.
