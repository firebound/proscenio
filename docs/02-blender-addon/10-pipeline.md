# Pipeline

The first panel in the sidebar and the grouper for the whole Photoshop to Blender to Godot flow. The body is three subpanels in run order: Import, [Validate](09-validation.md), and Export.

## Import

`Import Photoshop Manifest` reads a manifest written by the Proscenio Photoshop plugin, stamps one quad mesh per layer (composing spritesheet textures for `sprite_frame` groups), and parents everything to a stub root armature. The file picker carries two redo options:

- **Placement** - `Landed (Feet on Z=0)` shifts the figure so its lowest point sits on world Z=0 (the default, matching the engine convention of pivoting characters at the feet); `Centered (Canvas at World Origin)` keeps the figure centred on the manifest canvas, which helps when aligning several imports in one scene.
- **Root Bone Name** - the name of the single bone in the stub armature; `root` by default.

Each stamped mesh is tagged with its source layer, so re-importing the same manifest reuses the existing meshes - user-set rotation, parenting, and weights survive the round trip. The importer reports how many meshes it stamped, how many layers it skipped, and how many spritesheets it composed.

## Export

The Export subpanel opens with a read-out of the rig the writer will export: `Exports: <name>`, marked `picked` when a rig is chosen in the [Skeleton](04-skeleton.md) panel or `first in scene - no rig picked` when one is inferred. Below it sit the sticky path, the two export settings, and the buttons.

- **Pixels per unit** sets the Blender-world-unit-to-Godot-pixel ratio (default 100, so 1 m in Blender becomes 100 px in Godot). The writer reads this scene field on the first export, not an operator default.
- **Bundle textures** copies every texture the document references into the export folder after a successful write. PSD-imported art lives in `images/` and `_spritesheets/` subfolders, but the `.proscenio` references textures by bare filename and the Godot importer resolves siblings only; bundling closes that gap. Sources already beside the file are left alone, and a source missing on disk is reported rather than copied.

`Export (.proscenio)` first runs the full [validation](09-validation.md) pass and aborts when it finds any `error`; otherwise it runs the writer and writes the JSON to the path you choose in the export dialog. It does not validate against the JSON Schema - that check runs in CI and the test runner, not here.

The chosen path is remembered on the scene, so `Re-export` re-runs the writer (validation included) to that same path with no dialog. The generated scene uses native Godot nodes only - `Skeleton2D`, `Bone2D`, `Polygon2D` / `Sprite2D`, `AnimationPlayer` - with no GDExtension and no plugin runtime dependency.
