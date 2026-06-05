# Features

What each plugin actually does today, grouped by plugin and verified against the code (operators, planner, modals), not the specs or comments. For how the three fit together and where the data flows, see [Architecture](01-architecture.md).

## Photoshop (UXP plugin)

- **Tag layers from their name.** Markers in brackets (`[ignore]`, `[spritesheet]`, `[folder:name]`, and more) drive the export without touching the artwork - a UI panel ships for this too. Full vocabulary in the [Photoshop guide](../00-guides/01-advanced/01-photoshop.md#bracket-tags).

- **Export.** A recursive layer walk produces one PNG per layer plus a manifest JSON. The manifest is validated before it is written, so a broken manifest never reaches disk.

- **Spritesheets.** Marking a group as a spritesheet tags it as `sprite_frame` and exports one PNG per frame (`name/0.png`, `name/1.png`, ...). Composing those into a single sheet is the Blender importer's job, not Photoshop's.

- **Mirror back to PSD.** The plugin can rebuild a PSD from a manifest. This is a way to reconstruct the source layout, not a way to round-trip Blender edits back into the PSD.

## Blender (addon)

The heavy lifting lives here.

### Mesh authoring (automesh)

- **One-click automesh.** Traces the alpha silhouette, produces a deformable mesh, and densifies the interior under the bones. Parameters are tweaked via the redo panel (<kbd>F3</kbd>).

- **Interactive automesh.** A multi-stage modal that controls the *shape* of the mesh (silhouette, inner loops, interior detail, preview, apply), driven by mouse + modifier gestures rather than key combos. It shapes the mesh, not the weights.

- **Weight-preserving Automesh regeneration.** When you re-densify an already-skinned mesh, a snapshot is taken before and the weights are reprojected after, so reshaping does not throw away paint work. (This is the Automesh path only - a PSD re-import rebuilds the mesh and does *not* preserve weights.)

### Skeleton authoring (Quick Armature)

- **Draw bones in the viewport** by dragging head → tail, with mouse + modifier chords (the full chord map is in the [Blender walkthrough](../00-guides/00-basic/02-blender.md#build-the-skeleton)). The output is a plain Blender armature you refine in Edit Mode as usual.

### Weight bind and paint

Separate from automesh - automesh shapes the mesh, this binds it to the bones.

- **Five bind modes**, from fully automatic to fully manual:
  - `Bone Heat` - hands off to Blender's built-in automatic weights. Ideal when the bones lie inside or touching the mesh. But the heat solver depends on that contact, so a 2D rig whose bones sit off the sprite plane - or away from a given sprite's area, a common cutout setup - weights poorly or fails to solve. Reach for `Proximity` in that case.
  - `Proximity` - every nearby bone pulls on the vertex by how close it is: influence falls off with distance (by default with the square of the distance), then each vertex's weights are normalized to sum to 1. The smooth, general-purpose default.
  - `Envelope` - each bone has a radius; a vertex inside that radius binds to the bone, and where several radii overlap it splits evenly between them.
  - `Single Nearest` - each vertex binds fully to its one closest bone. Rigid, no blending - good for hard props.
  - `Empty` - no weights at all; you paint every weight by hand.

- **Edit Weights modal** - a weight-paint wrapper adapted for 2D - plus per-bone `SOFT` / `HARD` mode and brush-curve presets.

- **Copy weights to selected** between sprites with matching topology.

- **Save / restore a weight snapshot**, and **export / import the weight sidecar** (a JSON of the weights and their provenance).

### Slots (sprite swapping)

- Create a slot, add an attachment, set the default attachment, and animate the slot index to flip attachments per keyframe.

### Atlas

- Pack regions into a single atlas, unpack it back into source images, and apply the result.

### Sprite and UV metadata

- Sprite type (`polygon` / `sprite_frame`), spritesheet metadata (`hframes` / `vframes` / `frame`), reproject UV, snap region to UV bounds, and a frame-preview material that shows the chosen cell in the viewport.

### Animation and rig shortcuts

- `Drive from Bone` (wire a sprite property to a pose bone through a Blender driver), `Toggle IK`, `Save Pose to Library`, and `Bake Current Pose`. These sit on top of Blender's native operators - they never replace them.

### Source-art ingestion (Photoshop import)

- Imports the manifest into planes plus a root bone, with the naming convention pre-populated. Re-import is idempotent for object-level data - rotation, parenting, and per-sprite settings on existing objects carry over - but it rebuilds each mesh from the new art, so painted weights and Automesh density are not preserved ([details](../00-guides/01-advanced/01-photoshop.md#re-importing-after-psd-edits)).

### Export to Godot

- Validate the scene, write the `.proscenio` file (plus the atlas) next to the source `.blend`, and re-export silently to the last path on later saves.

### Support

- An orthographic preview camera, validation with per-subpanel status badges and click-to-select for the offending object, and a sprite-centric outliner (favorites and filter) that leaves Blender's native outliner untouched.

## Godot (editor plugin)

- An `EditorImportPlugin` regenerates a native scene (Skeleton2D + Bone2D + Polygon2D / Sprite2D + AnimationPlayer) on every reimport of a `.proscenio` file. The generated scene runs with the plugin uninstalled - it is plain Godot 4 nodes. A user-authored wrapper scene that instances the generated one survives every reimport.
