# doll fixture (SPEC 007)

The **comprehensive showcase fixture** for the Proscenio pipeline. A full humanoid character authored by hand in `doll.blend` (~22 mesh objects + `doll.rig` armature) with multi-bone weights, sprite_frame eyes, and authored actions. Demonstrates everything the addon supports today; grows feature-by-feature as future SPECs ship.

## Directory layout

The fixture is split into subfolders by **role in the pipeline** so the input vs derived outputs stay obvious. The single source of truth lives at the root; everything under a subfolder can be regenerated from it.

```text
examples/doll/
├── doll.blend                              [SOURCE — authored Blender]
├── doll.expected.proscenio                 [GOLDEN — CI-diffed validation midpoint]
├── doll.photoshop_manifest.json            [DERIVED — bpy emits SPEC 006 v1 manifest at root]
├── render_layers/                          [DERIVED — Workbench renders, one PNG per mesh]
│   ├── arm.L.png ... waist.png
│   └── pieces_sheet.png                    contact-sheet preview of every layer
├── photoshop/                              [PSD + JSX exporter output]
│   ├── doll.psd                            JSX importer output (placed layers from manifest)
│   └── export/                             gitignored — JSX exporter run-on-doll.psd output
│       ├── doll.photoshop_exported.json    re-exported manifest (roundtrip test)
│       └── images/                         re-exported per-layer PNGs
└── godot/                                  [Godot-side wrapper artifacts]
    ├── Doll.tscn                           SPEC 001 wrapper that instances doll.scn
    └── Doll.gd                             empty-stub script attached to the wrapper
```

## Pipeline at a glance

```text
doll.blend (authored)
    │
    ├──► [render_layers/]                  scripts/fixtures/doll/render_layers.py
    │       └──► one flat PNG per mesh (Workbench, ortho front view, transparent)
    │
    ├──► doll.photoshop_manifest.json      scripts/fixtures/doll/export_psd_manifest.py
    │       │ (SPEC 006 v1; paths point at render_layers/)
    │       │
    │       └──► photoshop-exporter/proscenio_import.jsx (in Photoshop)
    │               └──► [photoshop/doll.psd] (PSD with placed layers)
    │                       │
    │                       └──► photoshop-exporter/proscenio_export.jsx (in Photoshop)
    │                               └──► [photoshop/export/]  (gitignored — roundtrip output)
    │                                       ├──► doll.photoshop_exported.json
    │                                       └──► images/<layer>.png
    │
    └──► doll.expected.proscenio           scripts/fixtures/_shared/export_proscenio.py
            └──► CI compares against re-export of doll.blend each run
```

Inputs to authoring (you edit): `doll.blend`. Everything else falls out of it deterministically.

## Edit-the-fixture flow

When tweaking the doll source:

1. Open `doll.blend` in Blender, edit mesh / rig / weights / actions.
2. Save the `.blend`.
3. Re-render layers + regenerate manifest:

   ```sh
   blender --background examples/doll/doll.blend \
       --python scripts/fixtures/doll/render_layers.py
   blender --background examples/doll/doll.blend \
       --python scripts/fixtures/doll/export_psd_manifest.py
   ```

4. (optional) Re-import into the PSD: in Photoshop, run
   `proscenio_import.jsx` against `doll.photoshop_manifest.json` →
   refreshes `photoshop/doll.psd`.
5. (optional) Re-export from the PSD: in Photoshop, run
   `proscenio_export.jsx` on `photoshop/doll.psd` → drops
   `photoshop/export/doll.photoshop_exported.json` + `images/`.
6. Diff round-trip: `doll.photoshop_manifest.json` vs
   `photoshop/export/doll.photoshop_exported.json`.

## Building from source

```sh
# 1. Render every mesh to render_layers/<name>.png + pieces_sheet.png.
blender --background examples/doll/doll.blend \
    --python scripts/fixtures/doll/render_layers.py
python scripts/fixtures/doll/preview_pieces.py

# 2. Emit the SPEC 006 manifest at the fixture root.
blender --background examples/doll/doll.blend \
    --python scripts/fixtures/doll/export_psd_manifest.py
# -> writes examples/doll/doll.photoshop_manifest.json

# 3. (optional) Build the PSD via the JSX importer in Photoshop:
#    File > Scripts > Browse... > photoshop-exporter/proscenio_import.jsx
#    Pick examples/doll/doll.photoshop_manifest.json.
#    Output: examples/doll/photoshop/doll.psd

# 4. (optional) Roundtrip-test by running the JSX exporter on the PSD:
#    File > Scripts > Browse... > photoshop-exporter/proscenio_export.jsx
#    Output: examples/doll/photoshop/export/ (gitignored)
#       - doll.photoshop_exported.json
#       - images/<layer>.png

# 5. Generate the golden .proscenio at the fixture root (used by run_tests.py).
blender --background examples/doll/doll.blend \
    --python scripts/fixtures/_shared/export_proscenio.py
```

## Skeleton

The armature lives inside `doll.blend` as `doll.rig` — open the `.blend` in Blender to read the exact bone names and parenting. The hierarchy is a simplified humanoid: `root` → pelvic split + per-side leg chain (thigh / shin / foot), plus a 4-segment spine column ending at `neck → head` with the usual face attachments (brow, ear, eye, lip). Arms branch off the upper spine (shoulder → arm → forearm → hand). The `.blend` is the source of truth — this README does not duplicate the bone list because it would drift the moment the rig is tweaked.

## Sprites (highlights)

Each top-level mesh in `doll.blend` becomes one PNG layer when `render_layers.py` runs.

| Mesh kind | Examples | Why it exists |
| --- | --- | --- |
| polygon, multi-bone weights | spine-region meshes (`chest` / `belly` / `waist`), pelvic mesh weighted 0.5/0.5 across `pelvis.L`/`pelvis.R` | Demonstrates **multi-bone weights** + falloff distribution. |
| polygon, multi-bone spillover | `forearm.L` / `forearm.R` | 1.0 forearm + 0.3 spillover to the upper arm. Future home for driver-driven texture swap (SPEC 004 + 5.1.d). |
| sprite_frame | `eye.L` / `eye.R` | Hframes=4 spritesheet, animated by the `blink` action. |
| polygon, slot-ready | `brow.L` / `brow.R` | Future home for the slot system (SPEC 004) — brow-up / brow-down swap. |
| polygon, single primary bone | everything else | Standard parented sprites. |

## Visual style

Each mesh in `doll.blend` carries a flat-color material; `render_layers.py` reads each material's Principled BSDF Base Color and stamps a flat-shaded PNG (Workbench engine, transparent background). Region colors are the artist's choice in the `.blend` — change a Base Color, re-run, the layer PNG updates. Flat shading mirrors the future Photoshop-driven workflow (one painted layer per region) and keeps weight-paint smearing across bone seams visually obvious.

## Actions

| Action | Frames | Animates | Why |
| --- | --- | --- | --- |
| `idle` | 30, loop | spine.001 + spine.002 vertical bob (breath) | bone_transform tracks across multiple bones |
| `wave` | 30 | upper_arm.R + forearm.R rotation | demonstrates IK-friendly chain (no IK constraint exported, but Blender-side Toggle IK works) |
| `blink` | 12 | eye.L + eye.R `proscenio.frame` 0→1→2→3→2→1→0 | exercises sprite_frame track type |
| `walk` | 30, loop | thigh.L/R + shin.L/R rotation, spine sway | full-body coordination |

Future actions land as future SPECs require.

## What this fixture catches when broken

- Anything end-to-end touching polygon meshes + weights + actions + sprite_frame.
- Multi-bone weight export regression (pelvic mesh, spine-region meshes, `forearm.L/R`).
- sprite_frame eye animation regression.
- Multi-action authoring regression.
- Schema bumps that affect more than one feature at once.

## Future growth

| When | Adds |
| --- | --- |
| SPEC 004 (slots) ships | Slot on `hand.L.attachment` (sword vs bow swap). Slot on `brow.L/R` (brow-up vs brow-down). |
| SPEC 006 importer ships fully | A `doll.psd` round-trip test using `photoshop_import/doll.psd` as input. |
| SPEC 008 (UV animation) ships | Iris-scroll track on `eye.L` / `eye.R`. |
| Driver-based texture swap (5.1.d + SPEC 004) | Forearm rotation drives forearm front/back texture swap. |

Each addition extends the fixture without invalidating older actions — golden `.proscenio` diff catches surprise regressions.
