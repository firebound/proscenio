# 03 - Blender setup (rigging)

Artist re-enters Blender to rig the doll. The pipeline forks here into **two parallel artefacts**, each with a distinct purpose:

| Artefact | Source manifest | Purpose |
| --- | --- | --- |
| `doll_ps_tagged.blend` | `../02_photoshop_setup/export/doll_tagged.photoshop_exported.json` | **Parity sandbox** for SPEC 011 v1 tags. Geometry is intentionally deformed (scale 2.5 on arm.R, custom origins, blend-stack duplicates of chest / eyes) so every tag exercises its semantics end-to-end. Not used for rigging - the figure looks broken on purpose. |
| `doll_rigged.blend` | re-export of `../01_photoshop_base/doll_ps_base.psd` (clean, no artist tags) | **Rigging target**. Built from a fresh re-export of the untagged baseline PSD via the Proscenio Exporter, then hand-rigged on top. This is what step 04 (`../04_godot_import/`) consumes. |

The split exists because tagging and rigging answer different questions. Step 02 answers "does every tag in the taxonomy round-trip Blender -> PS -> Blender?" - the deformations are the signal. Step 03's rigged path answers "can the artist work the pipeline end-to-end on a real character?" - the deformations would just be noise.

## Contents

| File | Origin | Tracked? |
| --- | --- | --- |
| `doll_rigged.blend` | Blender import of the clean re-export from step 01 + **manual rigging** | **yes** - the armature + weights + actions are hand-authored work that no script can regenerate |
| `doll_ps_tagged.blend` | Blender import of `02_photoshop_setup` (tagged) | no - SPEC 011 parity sandbox; regenerable from step 02's manifest |
| `*.blend1` | Blender autosaves | no |

> `doll_rigged.blend` is tracked on purpose: its content is artist labour (humanoid armature, vertex weights, NLA tracks), not the output of a deterministic transform. Treat it the same as `00_blender_base/doll_base.blend` - source of truth, edited by hand, committed when the artist finishes a beat. The parity sandbox stays disposable because its single source of truth is the manifest in step 02.

## Regenerate `doll_ps_tagged.blend` (parity sandbox)

1. Open Blender (clean scene).
2. Enable the **Proscenio** addon.
3. `File > Import > Proscenio Photoshop manifest...` -> pick `../02_photoshop_setup/export/doll_tagged.photoshop_exported.json`.
4. The importer stamps 24 textured planes + 1 stub armature, populates collections `body` / `eyes` / `teste`, applies origins / blend modes / scale per tag.
5. Save as `doll_ps_tagged.blend`. **Do not rig this file** - it is the parity oracle, not the production figure.

## Regenerate `doll_rigged.blend` (rigging path)

1. Open `../01_photoshop_base/doll_ps_base.psd` in Photoshop.
2. Open the **Proscenio Exporter** panel; output folder = `../01_photoshop_base/export/`.
3. Click **Export manifest + PNGs**. This emits a SPEC 011 v2 manifest with no artist tags - identical body layout to the step 00 Blender manifest modulo the documented PS round-trip drift (waist 1 px shorter, AA edge bleed).
4. In Blender (clean scene), enable the Proscenio addon.
5. `File > Import > Proscenio Photoshop manifest...` -> pick `../01_photoshop_base/export/doll_ps_base.photoshop_exported.json`.
6. Author the rig on top:
   - Add an `Armature` named `doll.rig` with the humanoid bone chain (`root` -> pelvis split, spine column, arms, neck/head, face attachments).
   - Parent every imported plane to `doll.rig` (Armature deform, **with empty groups**).
   - Weight-paint each plane against the appropriate bone(s). Spine-region meshes (`chest`, `belly`, `waist`) take multi-bone weights; arm / leg meshes are single-bone.
   - Author actions: `idle` (30f, loop), `wave` (30f), `walk` (30f, loop). Push each to the NLA.
7. Save as `doll_rigged.blend`.

## Tags carried over from step 02

The Blender importer preserves the SPEC 011 v2 semantics that step 02 baked into the manifest:

- `[folder:NAME]` -> Blender collection hierarchy.
- `[polygon]` -> textured plane mesh.
- `[spritesheet]` -> driven sprite_frame setup (eyes, brow, mouth swaps - see `examples/generated/blink_eyes/` for the driver pattern this rig will eventually adopt).
- `[mesh]` -> editable polygon plane (so the artist can sculpt the silhouette if needed).
- `[origin]` / `[origin:x,y]` -> pivot point of the plane (consumed before rigging; rigger never needs to set it manually).
- `[blend:multiply|screen|additive]` -> material blend mode on the plane.

## Verification

### `doll_ps_tagged.blend` (parity sandbox vs step 02)

- 24 meshes stamped (= manifest's 24 entries; `[ignore]`-tagged + empty layers were already skipped during step 02 export).
- Collections `body`, `eyes`, `teste` exist (one per `[folder:NAME]` tag).
- Custom properties on each mesh:
  - `proscenio_psd_kind`: `polygon` (default), `mesh` (for `chest`, `chest mult`), `sprite_frame` (for `brow_states`).
  - `proscenio_blend_mode` on the duplicated blend-stack layers: `multiply` on `chest mult`, `screen` on `eyes__eye.L scrn`, `additive` on `eyes__eye.R add`.
- `arm.R` location reflects `anchor=[419, 1700]` + `origin=[10, 20]`: `(10-419)/100 = -4.09` for x, `(1700-20)/100 = 16.80` for z.
- All materials carry `blend_method = "BLEND"` in Blender 4.2+ (the manifest's exact `additive` / `multiply` / `screen` lives on the custom prop for downstream writers).

### `doll_rigged.blend` (rigging path vs step 01)

- Imported plane count matches the clean re-export's manifest length.
- Each plane's location reflects the manifest position; no SPEC 011 origins (the baseline carries none).
- After rigging: every plane is parented to `doll.rig` with non-empty vertex groups.

## Outputs going downstream

Step 04 (`../04_godot_import/`) consumes `doll_rigged.blend` via the Proscenio Godot exporter (writes `.proscenio` + textures into Godot's project).
