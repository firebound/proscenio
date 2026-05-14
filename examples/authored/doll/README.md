# doll fixture (SPEC 007 + 011)

The **comprehensive showcase fixture** for the Proscenio pipeline. A full humanoid character authored end-to-end across the four pipeline stages, exercising every SPEC 011 v1 tag in the process. Originally planned to also cover `sprite_frame` via animated eyes, but the current `.blend` has all meshes as `sprite_type=polygon` (including `eye.L`/`eye.R`) - sprite_frame coverage lives in `examples/generated/blink_eyes/` and `examples/generated/mouth_drive/` instead.

This fixture acts as the **parity oracle for Wave 11.8** (SPEC 011): step 02's tagged PSD exercises every tag in the taxonomy; the rest of the pipeline verifies the tags survive the round-trip.

## Directory layout

```text
examples/authored/doll/
|-- 00_blender_base/        [SOURCE  ] hand-authored .blend + derived render layers + base manifest
|-- 01_photoshop_base/      [DERIVED ] clean PSD produced from 00's manifest (no artist edits)
|-- 02_photoshop_setup/     [AUTHORED] artist workbench: tagged PSD + re-exported manifest (SPEC 011 parity oracle)
|-- 03_blender_setup/       [AUTHORED] rigged .blend imported from 02 + manual armature/weights/actions
|-- 04_godot_import/        [AUTHORED] SPEC 001 wrapper scene/script that consumes 03's export
`-- scripts/                python/bpy scripts that produce the derived outputs in step 00
```

Each subfolder owns its own `README.md` documenting **what it consumes**, **what it outputs**, and **how to verify it against the previous step**. There is no global oracle - each step verifies the previous step by consuming it.

## Pipeline at a glance

```text
[00_blender_base/]        doll_base.blend  (hand-authored, source of truth)
        |
        |  scripts/render_layers.py + scripts/export_psd_manifest.py
        v
    doll_base.photoshop_manifest.json + render_layers/<mesh>.png
        |
        v
[01_photoshop_base/]      doll_ps_base.psd
        |   (Proscenio Exporter panel: Import manifest as PSD)
        |
        |   copy + manual artist edits + SPEC 011 bracket tags
        v
[02_photoshop_setup/]     doll_tagged.psd
        |   (Proscenio Exporter panel: Export manifest + PNGs)
        v
    export/doll_tagged.photoshop_exported.json + export/images/<...>.png
        |
        v
[03_blender_setup/]       doll_rigged.blend   (gitignored; regenerable)
        |   (Proscenio Blender importer + manual rig/weights/actions)
        |
        |   (Proscenio Blender exporter -> Godot project)
        v
[04_godot_import/]        Doll.tscn + Doll.gd  (SPEC 001 wrapper)
```

The pipeline is **sequential**. Each numbered folder consumes the previous one and produces the inputs for the next. The two artist-authored steps are 02 (tagging in Photoshop) and 03 (rigging in Blender); the others are mechanical and reproducible from scripts/plugin actions.

## Step-by-step

| Step | Folder | What it owns | Hand-authored? |
| ---- | ------ | ------------ | -------------- |
| 00 | `00_blender_base/` | `doll_base.blend` + per-mesh render PNGs + base manifest | yes (`.blend` only) |
| 01 | `01_photoshop_base/` | `doll_ps_base.psd` placed from the manifest | no (panel import) |
| 02 | `02_photoshop_setup/` | `doll_tagged.psd` with SPEC 011 tags + re-exported manifest | yes |
| 03 | `03_blender_setup/` | `doll_rigged.blend` with armature + weights + actions | yes |
| 04 | `04_godot_import/` | `Doll.tscn` + `Doll.gd` SPEC 001 wrappers | yes |

See each step's own README for inputs/outputs/verification.

## Skeleton

The armature lives inside `03_blender_setup/doll_rigged.blend` as `doll.rig` - open the `.blend` in Blender to read the exact bone names and parenting. The hierarchy is a simplified humanoid: `root` -> pelvic split + per-side leg chain (thigh / shin / foot), plus a 4-segment spine column ending at `neck -> head` with the usual face attachments (brow, ear, eye, lip). Arms branch off the upper spine (shoulder -> arm -> forearm -> hand). The `.blend` is the source of truth - this README does not duplicate the bone list because it would drift the moment the rig is tweaked.

## Sprites (highlights)

Each top-level mesh in `00_blender_base/doll_base.blend` becomes one PNG layer when `scripts/render_layers.py` runs, and ultimately one tagged layer in `02_photoshop_setup/doll_tagged.psd`.

| Mesh kind | Examples | Why it exists |
| --- | --- | --- |
| polygon, multi-bone weights | spine-region meshes (`chest` / `belly` / `waist`), pelvic mesh weighted 0.5/0.5 across `pelvis.L`/`pelvis.R` | Demonstrates **multi-bone weights** + falloff distribution. |
| polygon, multi-bone spillover | `forearm.L` / `forearm.R` | 1.0 forearm + 0.3 spillover to the upper arm. Future home for driver-driven texture swap (SPEC 004 + 5.1.d). |
| (planned) sprite_frame | (not present in current doll.blend; eye.L/R are polygon. sprite_frame coverage in `blink_eyes/` + `mouth_drive/`.) | - |
| polygon, single primary bone | everything else | Standard parented sprites. |

> The brow slot variant (`brow.L.swap` / `brow.R.swap`) was retired together with the `doll_slots.blend` fixture - slot system coverage now lives in [`examples/generated/slot_swap/`](../../generated/slot_swap/) (single slot, bone swing) and [`examples/generated/slot_cycle/`](../../generated/slot_cycle/) (cycle pattern, 3 attachments).

## Visual style

Each mesh in `doll_base.blend` carries a flat-color material; `scripts/render_layers.py` reads each material's Principled BSDF Base Color and stamps a flat-shaded PNG (Workbench engine, transparent background). Region colors are the artist's choice in the `.blend` - change a Base Color, re-run, the layer PNG updates. Flat shading mirrors the Photoshop-driven workflow (one painted layer per region) and keeps weight-paint smearing across bone seams visually obvious.

## Actions

Authored in step 03 on top of the rigged plane set.

| Action | Frames | Animates | Why |
| --- | --- | --- | --- |
| `idle` | 30, loop | spine.001 + spine.002 vertical bob (breath) | bone_transform tracks across multiple bones |
| `wave` | 30 | upper_arm.R + forearm.R rotation | demonstrates IK-friendly chain (no IK constraint exported, but Blender-side Toggle IK works) |
| `blink` | 12 | (planned: eye.L + eye.R `proscenio.frame` 0->1->2->3->2->1->0) | sprite_frame track type test - currently lives in `blink_eyes/`; doll eyes remain polygon |
| `walk` | 30, loop | thigh.L/R + shin.L/R rotation, spine sway | full-body coordination |

Future actions land as future SPECs require.

## SPEC 011 tag coverage (parity oracle)

Every SPEC 011 v1 tag is exercised somewhere in `02_photoshop_setup/doll_tagged.psd`. See `02_photoshop_setup/README.md::Tags exercised` for the canonical table. If you add or rename a tag in SPEC 011, the parity test re-exports this PSD and diffs against the recorded baseline.

## What this fixture catches when broken

- Anything end-to-end touching polygon meshes + weights + actions (the rigged path).
- Multi-bone weight export regression (pelvic mesh, spine-region meshes, `forearm.L/R`).
- SPEC 011 tag taxonomy regression (parity oracle in step 02).
- Photoshop manifest round-trip drift (step 01 input vs step 02 re-export).
- Multi-action authoring regression.
- Schema bumps that affect more than one feature at once.

## Future growth

| When | Adds |
| --- | --- |
| SPEC 004 (slots) - coverage moved out | Slot system tests live in `examples/generated/slot_swap/` + `examples/generated/slot_cycle/` now. doll keeps a pure skinning-and-actions surface. |
| SPEC 008 (UV animation) ships | Iris-scroll track on `eye.L` / `eye.R`. |
| Driver-based texture swap (5.1.d + SPEC 004) | Forearm rotation drives forearm front/back texture swap. |

Each addition extends the fixture without invalidating older actions - golden `.proscenio` diff catches surprise regressions.
