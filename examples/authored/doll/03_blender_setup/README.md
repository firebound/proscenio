# 03 - Blender setup (rigging)

Artist re-enters Blender to rig the textured doll. Imports step 02's tagged manifest via the Proscenio Blender importer, then hand-authors armature + weight paint + actions on top.

This is the **second hand-edited step** in the pipeline (step 02 was the other). Everything downstream (`04_godot_import/`) consumes the rigged `.blend` produced here.

## Contents

| File | Origin | Notes |
| --- | --- | --- |
| `doll_rigged.blend` | Blender import of step 02 + manual rigging | gitignored - regenerable from step 02 |
| `doll_rigged.blend1` | Blender autosave | gitignored |

> No assets are checked in here on purpose. The rigging is reproducible from step 02's manifest + the documented authoring steps below; tracking the `.blend` would bloat the repo with binary noise on every weight-paint tweak.

## Regenerate

1. Open Blender.
2. Enable the **Proscenio** addon.
3. `File > Import > Proscenio Photoshop manifest...` and pick `../02_photoshop_setup/export/doll_tagged.photoshop_exported.json`.
4. The importer creates a fresh scene: one textured plane per manifest entry (polygons + sprite frames + meshes), positioned per the manifest's `anchor` / `origin`.
5. Author the rig on top:
   - Add an `Armature` named `doll.rig` with the humanoid bone chain (`root` -> pelvis split, spine column, arms, neck/head, face attachments).
   - Parent every imported plane to `doll.rig` (Armature deform, **with empty groups**).
   - Weight-paint each plane against the appropriate bone(s). Spine-region meshes (`chest`, `belly`, `waist`) take multi-bone weights; arm/leg meshes are single-bone.
   - Author actions: `idle` (30f, loop), `wave` (30f), `walk` (30f, loop). Push each to the NLA.
6. Save as `doll_rigged.blend`.

## Tags carried over from step 02

The Blender importer preserves the SPEC 011 v2 semantics that step 02 baked into the manifest:

- `[folder:NAME]` -> Blender collection hierarchy.
- `[polygon]` -> textured plane mesh.
- `[spritesheet]` -> driven sprite_frame setup (eyes, brow, mouth swaps - see `examples/generated/blink_eyes/` for the driver pattern this rig will eventually adopt).
- `[mesh]` -> editable polygon plane (so the artist can sculpt the silhouette if needed).
- `[origin]` / `[origin:x,y]` -> pivot point of the plane (consumed before rigging; rigger never needs to set it manually).
- `[blend:multiply|screen|additive]` -> material blend mode on the plane.

## Verification (vs step 02)

- Imported plane count matches `export/doll_tagged.photoshop_exported.json::layers.length` minus any sprite frames collapsed into a single sprite_frame node.
- Each imported plane's local position matches its manifest `anchor` / `origin`.
- Each plane carries the texture at `02_photoshop_setup/export/images/<path>.png`.
- Blend modes survive the round-trip: `chest mult` is multiply, `eye.L scrn` is screen, `eye.R add` is additive.
- After rigging: every plane is parented to `doll.rig` with non-empty vertex groups.

## Outputs going downstream

Step 04 (`../04_godot_import/`) consumes `doll_rigged.blend` via the Proscenio Godot exporter (writes `.proscenio` + textures into Godot's project).
