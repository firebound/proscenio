# Proscenio - Features

A Photoshop -> Blender -> Godot 4 pipeline for 2D cutout animation. The output is a native Godot scene with no runtime of its own.

This list is grouped by plugin and verified by reading the actual code (operators, planner, modals), not the specs or comments. For the systems behind these features and how the data flows between them, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Photoshop (UXP plugin)

- **Tag layers from their name.** Markers in brackets drive the export without touching the artwork (a UI panel ships for this too). The tags the code parses: `[ignore]`, `[merge]` (flatten a group into one PNG), `[folder:name]`, `[polygon]`, `[mesh]`, `[spritesheet]`, `[origin]` and `[origin:x,y]` (pivot), `[scale:n]`, `[blend:multiply|screen|additive]`, `[path:name]`, `[name:pre*suf]`.
- **Export.** A recursive layer walk produces one PNG per layer plus a manifest JSON. The manifest is validated before it is written, so a broken manifest never reaches disk.
- **Spritesheets.** Marking a group as a spritesheet tags it as `sprite_frame` and exports one PNG per frame (`name/0.png`, `name/1.png`, ...). Composing those into a single sheet is the Blender importer's job, not Photoshop's.
- **Mirror back to PSD.** The plugin can rebuild a PSD from a manifest. This is a way to reconstruct the source layout, not a way to round-trip Blender edits back into the PSD.

## Blender (addon)

The heavy lifting lives here.

### Mesh authoring (automesh)

- **One-click automesh.** Traces the alpha silhouette (no OpenCV), produces a deformable mesh, and densifies the interior under the bones. Parameters are tweaked via the redo panel (F3).
- **Interactive automesh.** A six-stage modal that controls the *shape* of the mesh (outer silhouette, edit silhouette, inner loops, interior detail, vertex preview, apply). Gestures use mouse + modifiers instead of key combos: LMB = vertex, Shift+LMB = fold, Ctrl+LMB = cut, Alt+LMB = delete, Ctrl+Z = undo; a click places points one by one, a drag free-draws. This modal controls the shape, not the weights.
- **Weight-preserving regeneration.** A snapshot is taken before regeneration and the weights are reprojected afterwards, so reshaping the mesh does not throw away paint work.

### Skeleton authoring (Quick Armature)

- **Draw bones in the viewport** by dragging head -> tail, with mouse + modifiers: Shift = chain, Alt = unconnected parent, X/Z = axis lock, Ctrl = grid snap, Ctrl+Z / Ctrl+Shift+Z = undo / redo, Enter = confirm, Esc / RMB = exit. The output is a plain Blender armature you refine in Edit Mode as usual.

### Weight bind and paint

Separate from automesh - automesh shapes the mesh, this binds it to the bones.

- **Five bind modes.** Bone Heat (delegates to Blender's native solver), Proximity (1/d^p), Envelope (per-bone radius), Single Nearest (one bone per vertex), and Empty (zero weights, for painting by hand).
- **Edit Weights modal** - a weight-paint wrapper adapted for 2D - plus per-bone SOFT / HARD mode and brush-curve presets.
- **Copy weights to selected** between sprites with matching topology.
- **Save / restore a weight snapshot**, and **export / import the weight sidecar** (a JSON of the weights and their provenance).

### Slots (sprite swapping)

- Create a slot, add an attachment, set the default attachment, and animate the slot index to flip attachments per keyframe.

### Atlas

- Pack regions into a single atlas, unpack it back into source images, and apply the result.

### Sprite and UV metadata

- Sprite type (`polygon` / `sprite_frame`), spritesheet metadata (`hframes` / `vframes` / `frame`), reproject UV, snap region to UV bounds, and a frame-preview material that shows the chosen cell in the viewport.

### Animation and rig shortcuts

- Drive a sprite from a bone (a driver), Toggle IK, save the current pose to the library, and bake the current pose. These sit on top of Blender's native operators - they never replace them.

### Source-art ingestion (Photoshop import)

- Imports the manifest into planes plus a root bone, with the naming convention pre-populated. The re-import is idempotent: it preserves weights, rotation, and parenting on objects that already exist.

### Export to Godot

- Validate the scene, write the `.proscenio` file (plus the atlas) next to the source `.blend`, and re-export silently to the last path on later saves.

### Support

- An orthographic preview camera, validation with per-subpanel status badges and click-to-select for the offending object, and a sprite-centric outliner (favorites and filter) that leaves Blender's native outliner untouched.

## Godot (editor plugin)

- An `EditorImportPlugin` regenerates a native scene (Skeleton2D + Bone2D + Polygon2D / Sprite2D + AnimationPlayer) on every reimport of a `.proscenio` file. The generated scene runs with the plugin uninstalled - it is plain Godot 4 nodes. A user-authored wrapper scene that instances the generated one survives every reimport.
