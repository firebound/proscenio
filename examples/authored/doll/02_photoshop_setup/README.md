# 02 - Photoshop setup (workbench)

Artist workbench. Two PSDs live here, both descended from `../01_photoshop_base/doll_ps_base.psd` but taken in different directions:

| PSD | Role |
| --- | --- |
| `doll_tagged.psd` | The **real character** workbench. Clean artist edits + bracket tags for an actual working figure, authored to demonstrate the pipeline end-to-end. This is the file the authoring flow continues from (step 03 rigging). Work in progress. |
| `debug/doll_tagged_debug.psd` | The **tag-taxonomy parity oracle / stress fixture**. Exercises the full photoshop-tag-system v1 taxonomy in one file, with geometry intentionally deformed (scale, custom origins, blend-stack duplicates) so every tag proves its semantics. Looks broken on purpose; never rigged; used only for systematic tests / fixtures, never for authoring. Lives in `debug/` to keep it out of the real-character flow. |

Re-exporting either produces the manifest + PNGs the downstream steps consume. The oracle is the parity reference for the photoshop tag system; the real character is the clean end-to-end demonstration figure.

## Contents

| Path | Origin | Notes |
| --- | --- | --- |
| `doll_tagged.psd` | manual artist edits on top of step 01 | the real character (work in progress) |
| `doll_tagged.photoshop_exported.json` + `images/<...>.png` | Proscenio Exporter panel | the real-character export (clean; one entry per body part) |
| `debug/doll_tagged_debug.psd` | manual artist edits on top of step 01 | the tag oracle: every bracket tag exercised (see below) |
| `debug/doll_tagged_debug.photoshop_exported.json` | Proscenio Exporter panel | the photoshop tag system v1 manifest emitted from the oracle PSD |
| `debug/images/<...>.png` | Proscenio Exporter panel | one PNG per mesh entry + per sprite_frame frame |

> The exports are regenerated artefacts. Commit `debug/doll_tagged_debug.photoshop_exported.json` so the parity test in `tests/test_doll_tagged_debug_manifest.py` runs in CI - while that manifest is absent the test skips.

## Tags exercised (debug/doll_tagged_debug.psd)

| Tag | Where in doll_tagged_debug.psd |
| --- | --- |
| `[ignore]` | `head 2` layer |
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

## Warnings expected on export (debug/doll_tagged_debug.psd)

- `scale-subpixel` from `arm.R [scale:2.5]` (bounds * 2.5 yield non-integer x/y/w/h).
- `empty-bounds` from `Camada 1` (empty placeholder layer).
- `duplicate-path` (x2) when two layers sanitise to the same on-disk path (e.g. an intentional `foot.L` duplicate).

## Regenerate the oracle export

1. Open `debug/doll_tagged_debug.psd` in Photoshop.
2. Open the **Proscenio Exporter** panel; output folder = `./debug/`.
3. Click **Export manifest + PNGs**. Overwrites `debug/doll_tagged_debug.photoshop_exported.json` + `debug/images/`.
4. From the repo root, `uv run pytest tests/test_doll_tagged_debug_manifest.py` should pass (13 assertions over the full taxonomy).

## Regenerate the real-character export

1. Open `doll_tagged.psd` in Photoshop.
2. Open the **Proscenio Exporter** panel; output folder = `./` (this directory).
3. Click **Export manifest + PNGs**. Writes `doll_tagged.photoshop_exported.json` + `images/`.

## Verification (debug/doll_tagged_debug.psd vs step 01)

- The layer tree of `doll_tagged_debug.psd` is a superset of `doll_ps_base.psd`: same baseline layers plus the tag rename + a handful of new layers for blend / dup / origin tests.
- `debug/doll_tagged_debug.photoshop_exported.json::layers` has one entry per non-`[ignore]`, non-empty layer. Total entry count matches the **Proscenio Validate** panel badge minus the skipped count.
- `debug/images/<path>.png` exists for every entry's `path` and every sprite_frame `frames[].path`.
- The **Proscenio Validate** panel shows only the expected warnings (`scale-subpixel`, `empty-bounds`, possibly `duplicate-path`); no `sprite-frame-malformed` (means brow_states emitted a real sprite_frame, not a passthrough fallback).

## Outputs going downstream

Step 03 (`../03_blender_setup/`) consumes the oracle export:

- `debug/doll_tagged_debug.photoshop_exported.json` (manifest)
- `debug/images/<...>` (textures, paths relative to the manifest)

Both should be referenced via the Blender Proscenio importer (`Import Photoshop manifest...`).
