# Pipeline

The first panel in the sidebar and the grouper for the whole Photoshop to Blender to Godot flow. The body is three subpanels in run order: Import, [Validate](#validate), and Export.

## Import

`Import Photoshop Manifest` reads a manifest written by the Proscenio Photoshop plugin, stamps one quad mesh per layer (composing spritesheet textures for `sprite_frame` groups), and parents everything to a stub root armature. The file picker carries two redo options:

- **Placement** - `Landed (Feet on Z=0)` shifts the figure so its lowest point sits on world Z=0 (the default, matching the engine convention of pivoting characters at the feet); `Centered (Canvas at World Origin)` keeps the figure centred on the manifest canvas, which helps when aligning several imports in one scene.
- **Root Bone Name** - the name of the single bone in the stub armature; `root` by default.

Each stamped mesh is tagged with its source layer, so re-importing the same manifest reuses the existing meshes - user-set rotation, parenting, and weights survive the round trip. The importer reports how many meshes it stamped, how many layers it skipped, and how many spritesheets it composed.

See [`examples/generated/simple_psd/`](../../../examples/generated/simple_psd/) for a minimal worked manifest and its imported result.

## Validate

`Validate` runs the full pre-export pass and lists what it finds; the same pass runs automatically before every export, and any `error` row blocks it. Sits between Import and Export so the run order reads top to bottom. Until you click `Validate` the panel shows `run Validate to see issues`; a clean scene shows `no issues - ready to export`.

This is structural and semantic validation of the live scene - it never runs JSON Schema validation. The schema is checked in CI and the test runner, not in the Blender session (see [Export](#export) for what export does instead).

Each finding renders as one row with an `error` or `info` icon. A row that names an offending object is a button - click it to select that object in the viewport; findings with no object (the no-armature error) render as a plain label.

### Errors block the export

- The scene has no Armature (export requires one; this is reported alone, before any other check).
- An element carries vertex groups but none resolve to armature bones - the writer would raise at export.
- A sprite element has `hframes` or `vframes` below 1.
- An element has an unknown element type (neither `mesh` nor `sprite`).
- An IK chain is driven by an animated target but its chain bones carry no keyframes - run `Bake IK to Keyframes` first (the exporter reads raw fcurves and would write flat bones).
- Two slots share a name.
- A slot has no mesh children.
- A slot's default attachment names a mesh that is not a child of the slot.

### Warnings inform but still export

- An element has no parent bone and no vertex groups matching armature bones - the writer falls back to an empty bone field.
- A bone's rest direction tilts out of the world XZ plane - the exporter projects bone angles onto XZ and would misread it.
- A bone drives a sprite's rotation but is not in XYZ Euler mode - the driver reads XYZ, so the animation will not track. Run `Active to Euler` in the [Skeleton](04-skeleton.md#active-armature) panel.
- A mesh element is not flat (it has thickness on every axis), so the flatten-to-plane step would lose geometry.
- A sprite-frame element's quad UVs do not span the full 0-1 sheet, so the `hframes` / `vframes` grid would be garbled in Godot.
- An atlas image referenced by a material is missing on disk - Godot will warn at import. This is a warning, not a blocker.
- A sprite element's mesh is no longer a single quad (a mesh tool likely ran on it).
- A mesh element has no polygons.
- A slot attachment follows a different bone than its slot.
- A slot child carries bone-transform keyframes - a slot animates visibility only.
- An object is double-driven: it carries both a raw bone parent AND a Proscenio follow constraint, so the bone's influence applies twice - `Clear Bone Follow` (or `Unbind`) keeps the position and drops both.
- A bone follow is stale: the rig's rest changed since the bind, so Blender and the Godot import disagree on the follower's rest position - re-run `Bind to Bone` to recompute it.
- A sprite is tilted off the picture plane: its quad turns edge-on to the camera (a snap bone parent to an in-plane bone, or a hand-rotated object), so its exported rest transform comes out foreshortened - keep the sprite facing front.

The Element and Active Slot subpanels surface a cheap subset of these checks inline on every redraw (the active object, the active slot), so most problems show before you click `Validate`.

## Export

The Export subpanel opens with a read-out of the rig the writer will export: `Exports: <name>`, marked `picked` when a rig is chosen in the [Skeleton](04-skeleton.md) panel or `first in scene - no rig picked` when one is inferred. Below it sit the sticky path, the two export settings, and the buttons.

- **Pixels per unit** sets the Blender-world-unit-to-Godot-pixel ratio (default 100, so 1 m in Blender becomes 100 px in Godot). The writer reads this scene field on the first export, not an operator default.
- **Bundle textures** copies every texture the document references into the export folder after a successful write. PSD-imported art lives in `images/` and `_spritesheets/` subfolders, but the `.proscenio` references textures by bare filename and the Godot importer resolves siblings only; bundling closes that gap. Sources already beside the file are left alone, and a source missing on disk is reported rather than copied.

`Export (.proscenio)` first runs the full [validation](#validate) pass and aborts when it finds any `error`; otherwise it runs the writer and writes the JSON to the path you choose in the export dialog. It does not validate against the JSON Schema - that check runs in CI and the test runner, not here.

The chosen path is remembered on the scene, so `Re-export` re-runs the writer (validation included) to that same path with no dialog. The generated scene uses native Godot nodes only - `Skeleton2D`, `Bone2D`, `Polygon2D` / `Sprite2D`, `AnimationPlayer` - with no GDExtension and no plugin runtime dependency.
