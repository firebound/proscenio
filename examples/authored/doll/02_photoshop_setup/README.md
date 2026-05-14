# 02 - Photoshop setup (workbench)

Artist workbench. Copy of `../01_photoshop_base/doll_ps_base.psd` with **manual edits + bracket tags** applied. Re-exporting from here produces the manifest + PNGs that step 03 (Blender rigging) consumes.

This step exercises the full SPEC 011 v1 tag taxonomy and acts as the **parity oracle** for Wave 11.8.

## Contents

| File | Origin | Notes |
| --- | --- | --- |
| `doll_tagged.psd` | manual artist edits on top of step 01 | layers renamed with bracket tags (see below) |
| `export/doll_tagged.photoshop_exported.json` | Proscenio Exporter panel | SPEC 011 v2 manifest emitted from the tagged PSD |
| `export/images/<...>.png` | Proscenio Exporter panel | one PNG per polygon entry + per sprite_frame frame |

## Tags exercised

| Tag | Where in doll_tagged.psd |
| --- | --- |
| `[ignore]` | `head` layer |
| `[merge]` | `0`, `1`, `1.1` groups inside `brow_states` |
| `[folder:NAME]` | `eyes`, `belly` / `chest` (body), `arm.R` (teste) |
| `[polygon]` explicit | `ear.R` |
| `[spritesheet]` | `brow_states` |
| `[mesh]` | `chest`, `chest mult` |
| `[origin]` marker | direct child of `brow_states` (pivot for the sprite_frame) |
| `[origin:x,y]` | `arm.R [origin:10,20]`, `belly [origin:532,333]` |
| `[scale:n]` | `arm.R [scale:2.5]` |
| `[blend:multiply]` | `chest mult` |
| `[blend:screen]` | `eye.L scrn` |
| `[blend:additive]` | `eye.R add` |
| `[path:NAME]` | `arm.R [path:test]` |
| `[name:pre*suf]` | `hands [name:lh_*]` (parser accepts; planner currently ignores the rewrite, names cascade via joinName) |

## Warnings expected on export

- `scale-subpixel` from `arm.R [scale:2.5]` (bounds * 2.5 yield non-integer x/y/w/h).
- `empty-bounds` from `Camada 1` (empty placeholder layer).
- `duplicate-path` (x2) when two layers sanitise to the same on-disk path (e.g. an intentional `foot.L` duplicate).

## Regenerate

1. Open `doll_tagged.psd` in Photoshop.
2. Open the **Proscenio Exporter** panel; output folder = `./export/`.
3. Click **Export manifest + PNGs**. Overwrites `export/`.

## Verification (vs step 01)

- The layer tree of `doll_tagged.psd` is a superset of `doll_ps_base.psd`: same baseline layers plus the tag rename + a handful of new layers for blend / dup / origin tests.
- `export/doll_tagged.photoshop_exported.json::layers` has one entry per non-`[ignore]`, non-empty layer. Total entry count matches the **Proscenio Validate** panel badge minus the skipped count.
- `export/images/<path>.png` exists for every entry's `path` and every sprite_frame `frames[].path`.
- The **Proscenio Validate** panel shows only the expected warnings (`scale-subpixel`, `empty-bounds`, possibly `duplicate-path`); no `sprite-frame-malformed` (means brow_states emitted a real sprite_frame, not a passthrough fallback).

## Outputs going downstream

Step 03 (`../03_blender_setup/`) consumes:

- `export/doll_tagged.photoshop_exported.json` (manifest)
- `export/images/<...>` (textures, paths relative to the manifest)

Both should be referenced via the Blender Proscenio importer (`Import Photoshop manifest...`).
