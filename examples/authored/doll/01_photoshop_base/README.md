# 01 - Photoshop base

Clean PSD produced by importing `../00_blender_base/doll_base.photoshop_manifest.json` into Photoshop via the Proscenio Exporter plugin (`Import manifest as PSD` button). No artist edits yet; this file is the **untouched starting point** for the manual workbench in step 02.

## Contents

| File | Origin | Notes |
| --- | --- | --- |
| `doll_ps_base.psd` | Photoshop import of step 00's manifest | one Photoshop layer per mesh, placed at the bbox the manifest declared |

## Regenerate

1. Open Photoshop.
2. Open the **Proscenio Exporter** panel.
3. Click **Import manifest as PSD** and pick `../00_blender_base/doll_base.photoshop_manifest.json`.
4. The plugin creates a new PSD with every render-layer PNG placed at its declared position. Save as `doll_ps_base.psd` here.

## Verification (vs step 00)

- Canvas size matches `doll_base.photoshop_manifest.json::size`.
- Every layer in the PSD corresponds 1:1 to an entry in the manifest's `layers` list.
- Each layer's bbox sits at `position` with the size declared in the manifest (visual sanity check).
- No tags / brackets in layer names: this is the raw baseline. Tagging happens in step 02.

## Outputs going downstream

Step 02 (`../02_photoshop_setup/`) starts from a **copy** of this PSD. Never edit `doll_ps_base.psd` in place - duplicating it forces step 02 to remain a pure superset of the base for diffing.
