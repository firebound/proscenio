# Proscenio - Features (verified against the code)

Pipeline Photoshop -> Blender -> Godot 4 for 2D cutout animation. Output is a native Godot scene with no runtime of its own.

Verified by reading the actual code (operators, planner, modals), ignoring specs / docstrings / comments.

## 1. Photoshop side (UXP plugin)

- Group layers and mark them as a spritesheet. The exporter does NOT produce the composed sheet image: it tags the group as `sprite_frame` in the manifest and exports one PNG per frame (`name/0.png`, `name/1.png`...). Composing them into a single image (laid out side by side, padded to the largest frame) is the Blender importer's job (`compose_spritesheet`).
- Tag layers via brackets in the layer name without touching the artwork (a UI panel ships for this too). Tags actually parsed by the code: `[ignore]`, `[merge]` (flatten a group into a single PNG), `[folder:name]`, `[polygon]`, `[mesh]`, `[spritesheet]`, `[origin]` and `[origin:x,y]` (pivot), `[scale:n]`, `[blend:multiply/screen/additive]`, `[path:name]`, `[name:pre*suf]`.
- Manifest validation before save.
- Mirror manifest -> PSD (rebuilds a PSD from the manifest; this is NOT a way to round-trip Blender edits back into the PSD).

## 2. Mesh authoring (automesh)

- Simple automesh: one click, traces the alpha-channel silhouette (no OpenCV), produces a deformable annulus mesh, densifies the interior under bones. Parameters via redo (F3).
- Interactive automesh: a six-stage modal that controls the SHAPE of the mesh (outer silhouette, edit silhouette, inner loops, interior detail, vertex preview, apply). Gestures use mouse + modifiers instead of keyboard combos: LMB = vertex, Shift+LMB = fold, Ctrl+LMB = cut, Alt+LMB = delete, Ctrl+Z = undo; click = pen (point by point), drag = free-draw. IMPORTANT: the interactive modal controls the shape, NOT the weights.
- Mesh regeneration that preserves weights: snapshot before, weight reprojection after.

## 3. Skeleton authoring (Quick Armature)

- Draw bones by dragging in the viewport (head -> tail), with mouse + modifiers: Shift = chain, Alt = unconnected parent, X/Z = axis lock, Ctrl = grid snap, Ctrl+Z / Ctrl+Shift+Z = undo / redo, Enter = confirm, Esc / RMB = exit. Output is a standard Blender armature.

## 4. Weight bind and paint (separate from automesh)

- Bind the mesh to the skeleton with five auto-weight modes: Bone Heat (delegates to Blender's native solver), Proximity (1/d^p), Envelope (per-bone radius), Single Nearest (one bone per vertex), Empty (zero weights, for painting by hand). Only three modes actually compute weights; bone heat is Blender's and empty is zero by definition.
- Per-bone SOFT / HARD mode.
- "Edit Weights" modal (a weight-paint wrapper adapted for 2D).
- Brush curve presets, copy weights to selected.
- Save / restore weight snapshot; export / import weight sidecar.

## 5. Slots (sprite swapping)

- Create a slot, add an attachment, set the default attachment, animate the slot index.

## 6. Atlas

- Pack, unpack, and apply atlas.

## 7. Sprite and UV metadata

- Sprite type (polygon / sprite_frame), spritesheet metadata (hframes / vframes / frame), reproject UV, snap region to UV, frame-preview material.

## 8. Animation / rig shortcuts

- Drive a sprite from a bone (driver), Toggle IK, save current pose to the library, bake current pose.

## 9. Support

- Orthographic preview camera.
- Validation with per-subpanel badges and click-to-select the offending object.
- A dedicated outliner (favorites / selection).

## 10. Photoshop import

- Imports the manifest (planes + root bone + names). Idempotent re-import that preserves weights, rotation, and parenting.

## 11. Godot export

- Validate, export `.proscenio` (plus atlas), re-export with a sticky path.

## 12. Godot side

- The importer regenerates a native scene (Skeleton2D + Bone2D + Polygon2D + AnimationPlayer) on every reimport; the scene runs without the plugin installed. (Builders exist in the code; detailed verification focused on Photoshop and Blender.)
