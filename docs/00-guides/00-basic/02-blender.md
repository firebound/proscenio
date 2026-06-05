# Blender: setup and animate

Blender is the hub of the pipeline: it imports the Photoshop layers, you rig and skin them here, and it exports the `.proscenio` for Godot.

At the [3D Viewport](https://docs.blender.org/manual/en/latest/editors/3dview/introduction.html), open the [Sidebar](https://docs.blender.org/manual/en/latest/editors/3dview/sidebar.html) with <kbd>N</kbd> and switch to the **Proscenio** tab - every subpanel below lives there.

Proscenio subpanels are contextual and poll on the current selection.

## Import the Photoshop manifest

1. *Open the target `.blend`*: your Blender file for this character.

2. *Import the manifest*: in the **Active Sprite** subpanel, click `Import Photoshop Manifest` and point it at the manifest you exported.

Each layer becomes a quad sprite (pivot, atlas region, and naming already filled accordingly to what was done in Photoshop side). The import also builds a stub armature named `<psd>.rig` with a single bone and parents every mesh to it, so the figure moves as one piece - the meshes are not weighted for bending yet (that is the skinning step below).

The import dialog has two options worth setting deliberately:

- `Placement`: `Landed (Feet on Z=0)` (default; matches Godot's feet-pivot convention) or `Centered (Canvas at World Origin)` when you need to align several imports in one scene.

- `Root Bone Name`: names that single armature bone (default `root`; override with `spine` or your own convention).

> [!NOTE]
> Authoring meshes by hand instead of importing? Model them directly, then pick up from [Set each sprite's type](#set-each-sprites-type) - the rest of the Blender flow is identical.

## Build the skeleton

Add the real bones onto the imported armature. Quick Armature is the fast path; you can also add bones in Edit Mode like any Blender rig.

1. *Start the modal session*: `Skeleton > Quick Armature` snaps to Front Orthographic and lets you draw bones straight in the viewport.

2. *Draw each bone*: with one **press, drag, release** (head → tail), the session stays live so you can lay down a whole chain, then confirm.

While the session is live, an on-screen cheatsheet mirrors these inputs:

| Input | What it does |
| - | - |
| <kbd>LMB</kbd> drag | New bone, `connected` - chains onto the previous bone (the new bone's head snaps to the parent's tail) |
| <kbd>Shift</kbd> + <kbd>LMB</kbd> drag | New bone, `unparented` - free-standing, no parent |
| <kbd>Alt</kbd> + <kbd>LMB</kbd> drag | New bone, `disconnected` - parented to the previous bone but the head stays where you press (leaves a gap) |
| <kbd>X</kbd> / <kbd>Z</kbd> | Toggle axis lock - constrains the drag to that axis |
| <kbd>Ctrl</kbd> (while dragging) | Grid snap - lands head and tail on the snap increment |
| <kbd>Ctrl+Z</kbd> / <kbd>Ctrl+Shift+Z</kbd> | Undo / redo the last bone in this session |
| <kbd>Enter</kbd> | Confirm and exit |
| <kbd>Esc</kbd> / right-click | Cancel and exit |

- The table assumes the default **chain** behaviour. Turn off `default_chain` in the Quick Armature options and plain <kbd>LMB</kbd> drag becomes unparented while <kbd>Shift</kbd> + <kbd>LMB</kbd> drag connects instead; every other input is unchanged.
- New bones get an auto name: the prefix plus a zero-padded index starting at zero (`qbone.000`, `qbone.001`, ...). The prefix defaults to `qbone` and is configurable in the same options.

## Shape deformable meshes (optional)

A flat imported quad cannot bend, so we need to add vertices to get cutout deformation. The more vertices, the smoother the bend - but also the heavier the rig. The exact recipe depends on the art and the animation, but here are some starting points:

To get cutout deformation, turn the sprite into a denser mesh with the **Skinning** subpanel:
`Automesh from Sprite` (one shot) or `Automesh (modal)` (interactive preview).

This is independent of the skeleton - the automesh only reshapes the geometry, it does not touch bones. Skip it for sprites that only need rigid motion or sprite-frame swapping.

## Bind and paint weights

Binding ties each mesh's vertices to bones so the mesh follows the pose.

1. *Set the picker armature*: in the **Skeleton** subpanel, pick your armature as the active armature - the Skinning bind targets it.

2. *Bind*: in the **Skinning** subpanel, click `Bind to Picker Armature` (pick a bind mode if needed).

   Native alternative: select the meshes, press <kbd>Ctrl+P</kbd>, then `Armature Deform`.

3. *Paint*: click `Edit Weights` for the in-panel weight-paint modal, or use Blender's own Weight Paint Mode.

   Either path produces vertex groups named after bones. See the [Blender workflow](../01-advanced/02-blender.md) for the full skinning recipe (automesh density, bind modes, weight transfer, snapshots).

> [!WARNING]
> **Bone names are the contract.** The writer exports a weight only when a vertex group's name matches a bone's name exactly.
>
> Blender syncs them one way: rename a **bone** and Blender auto-renames the matching vertex group on every mesh that armature deforms (default behaviour). The reverse is not true - renaming a **vertex group** does not touch the bone, so that breaks the match and the weight silently drops.
>
> So: name bones meaningfully early, and always rename from the bone side, never the vertex group. The auto-rename only reaches meshes the armature deforms - a mesh that is still only object-parented (as imported meshes are until you bind them) is skipped, so rename its vertex group by hand. See the [skinning weights rules](../../../specs/decisions.md#skinning-weights-export).

## Set each sprite's type

Imported layers arrive with their type already set from photoshop if you properly tagged them, but hand-authored meshes can be set here.

Select a mesh and work in the **Active Sprite** subpanel.

1. *Choose the sprite type*: there are two, and each maps to a Godot node:
   - `Polygon` (default) - a cutout mesh that exports to a [`Polygon2D`](https://docs.godotengine.org/en/stable/classes/class_polygon2d.html).
   - `Sprite Frame` - a spritesheet that exports to a [`Sprite2D`](https://docs.godotengine.org/en/stable/classes/class_sprite2d.html). For `Sprite Frame`, set `hframes` / `vframes` / `frame`; the in-panel preview slicer shows the chosen cell in the 3D viewport without exporting.

   A layer tagged `[mesh]` in Photoshop lands here as a `Polygon` - "mesh" is just an authoring flag, not a third type.

2. *Set the texture region*: `auto` computes the region from UV bounds at export; `manual` lets you slice an atlas by hand. Click `Snap to UV bounds` to populate the region from the current UV.

## Refine the rig (optional)

These polish the rig and are all optional.

- *Drive a sprite property from a bone (soft swap)*: click `Drive from Bone` in the **Active Sprite** subpanel to wire a Blender driver between a pose bone and a sprite property - good for changes that vary continuously with rotation, for example.

- *Pose helpers*: in Pose Mode the **Skeleton** subpanel adds `Bake Current Pose`, `Toggle IK`, and `Save Pose to Library`, all Blender-side. `Bake Current Pose` keyframes every bone at the playhead - those keys export like any other, so it is how you commit a posed (or IK-driven) frame into the animation. `Toggle IK` and `Save Pose to Library` stay in Blender: a pose asset just lands in your Asset Browser.

> [!NOTE]
> IK does not round-trip to Godot. `Toggle IK` is a Blender posing aid - the writer exports raw bone keyframes, not constraints, and the generated scene uses native nodes only. To get IK-driven motion into Godot, bake the IK result to bone keyframes first (Blender's Bake Action with visual keying), or rebuild IK in-engine after import with Godot's built-in 2D skeleton IK modifiers.

## Swap variants with slots (optional)

Use a slot when an attachment point toggles between N discrete variants: sword / staff / empty hand, mouth open / closed, brow up / down, an expression swap. The slot owns the variants; you flip between them with a single index.

1. *Create the slot*: select the meshes you want to wrap, then `Skeleton > Create Slot`. → A slot Empty is anchored under the active bone, and the selected meshes become its attachments.

2. *Pick the default variant*: in the **Active Slot** subpanel, choose which attachment is visible at scene load (the SOLO icon).

3. *Animate the swap*: keyframe `proscenio_slot_index` on the slot to flip attachments over time. → At import, Godot expands that single track into per-attachment visibility tracks.

See [`examples/generated/slot_cycle/`](../../../examples/generated/slot_cycle/) for the minimal slot fixture.

> [!TIP]
> **Soft swap vs. hard swap.** `Drive from Bone` is for continuous, driven changes. For a clean **either/or** swap - forearm front/back, sword/staff, brow up/down - use [slots](#swap-variants-with-slots-optional) instead.

## Animate

Animate with Blender's native tools (Action Editor, Dopesheet, drivers).

Proscenio does not author animation - the **Animation** subpanel is a read-only summary of the actions the writer will export. Each Action becomes one entry in the export; NLA strips are not consumed **yet**, so bake to a single Action first. Slot indices and driven sprite properties animate on the same timeline.

## Pack the atlas (optional)

Packing is optional. Skip it and each sprite keeps its own texture - the per-layer PNG, or the composed spritesheet for a `Sprite Frame` - and the export references those as-is.

If you do pack, the **Atlas** subpanel composes textures into one sheet: `Pack Atlas` builds the atlas and rewrites each sprite's `texture_region`, `Unpack Atlas` reverses it, and `Apply Packed Atlas` rebinds to an atlas you packed externally. `Pack Atlas` takes every sprite with a texture - `polygon` and `sprite_frame` alike - there is no per-sprite opt-out from the atlas itself. Set `Isolated material` on a sprite to keep its own shader (additive, custom); it still draws from the packed atlas, just not through the shared material.

A `Sprite Frame` packed this way still slices correctly: the whole sheet stays one contiguous block in the atlas (the sprite quad's UVs cover the full sheet, so the packer takes it whole), and Godot subdivides that block - the sprite's `region_rect` - by `hframes` / `vframes`, not the whole atlas. So `frame` indices stay identical to Blender; a 4-frame mouth is still frames 0-3 of its own block, wherever that block landed.

The export references whatever atlas is packed in the scene rather than generating one.

## Find things in big rigs

Big rigs drown Blender's native outliner - the doll fixture alone has 64 bones and 22 sprite meshes. The **Outliner** subpanel gives a sprite-centric flat list with a substring filter and a favorites toggle; click a row to make that object active.

## Validate and export

1. *Validate*: `Export > Validate` checks every sprite against the armature, the atlas, and the required fields. → Any error blocks the export until you fix it.

2. *Export*: `Export > Export (.proscenio)` writes the `.proscenio` JSON next to the source `.blend`. On later saves, `Re-export` reuses the sticky path with no dialog.
