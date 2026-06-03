# Proscenio end-to-end walkthrough

The full Photoshop -> Blender -> Godot loop in one linear pass. For depth on any single tool, see the per-tool guides: [Photoshop](PHOTOSHOP-WORKFLOW.md), [Blender](BLENDER-WORKFLOW.md), [Godot](GODOT-WORKFLOW.md).

> [!NOTE]
> The MVP is in progress. The full quickstart will land with the first end-to-end sample; the loop below describes the flow once both sides ship.

## 1. Bring the art in

Pick whichever entry point matches your asset:

- **Photoshop authored** - open the source `.psd`, open the **Proscenio Exporter** panel (Plugins menu, loaded via the UXP plugin in [`apps/photoshop/`](../apps/photoshop/)), pick an output folder, click **Export manifest + PNGs**. The plugin writes a v1 manifest JSON + per-layer PNGs. In Blender, click **Import Photoshop Manifest** (Active Sprite subpanel) and point at the manifest. Each layer lands as a quad sprite with the right pivot, atlas region, and naming convention pre-populated.
- **Hand authored in Blender** - model your meshes directly. The panel still applies; just skip the manifest import.

## 2. Rig and weight

In the Blender sidebar (`N → Proscenio`):

- Need a quick skeleton for a doodle? **Skeleton → Quick Armature** - click-drag in the viewport to draw bones (Shift to chain). The result is a normal armature; rename and refine in Edit Mode as usual.
- Parent your meshes to the armature (`Ctrl+P → Armature Deform`). The writer reads vertex-group names and matches them to bone names - see the skinning weights entry in [`specs/decisions.md`](../specs/decisions.md#skinning-weights-export) for the matching rules.
- Use **Skeleton → Bake Current Pose** + **Toggle IK** + **Save Pose to Library** as authoring shortcuts. None of them affect the export - they only help you iterate.

## 3. Set per-sprite knobs

- **Active Sprite** - pick `Polygon` for cutout meshes or `Sprite Frame` for spritesheets. Set `hframes / vframes / frame` for sprite_frame; the in-panel preview slicer lets you preview the cell choice in the 3D viewport without exporting.
- **Texture region** - auto computes from UV bounds; manual lets you slice an atlas. Click **Snap to UV bounds** to populate from the current UV.
- Need to swap textures based on bone rotation? **Drive from Bone** wires a Blender driver between a pose bone and a sprite property in one click. For HARD swaps (forearm front/back, sword/staff), use the slot system below instead.

## 4. Slot system

For attachments that toggle between N variants - sword/staff/empty hand, brow up/down, expression swap:

1. Select the meshes you want to wrap. **Skeleton → Create Slot** anchors a slot Empty under the active bone and parents the selected meshes as attachments.
2. In **Active Slot**, pick which attachment is the default at scene load (SOLO icon).
3. Animate `proscenio_slot_index` on the slot to flip attachments per keyframe - Godot expands this into per-attachment visibility tracks at import time. See [`examples/generated/slot_cycle/`](../examples/generated/slot_cycle/) for the minimal fixture.

## 5. Find things in big rigs

Big rigs (the doll fixture has 64 bones + 22 sprite meshes) drown Blender's native outliner. Use the **Outliner** subpanel: substring filter, favorites toggle, sprite-centric flat list. Click a row to make that object active.

## 6. Validate, export, and wrap

- **Export → Validate** - checks every sprite against the armature, the atlas, and required fields. Errors block export.
- **Export → Export (.proscenio)** writes the `.proscenio` JSON next to the source `.blend`; it references the atlas already packed in the scene rather than generating one. **Re-export** silently re-uses the sticky path on subsequent saves.
- Drop the `.proscenio` into your Godot project - the `EditorImportPlugin` regenerates a `.scn` automatically.
- **Wrap the imported scene** - instance the generated `.scn` in your own `.tscn` and attach scripts there. Scripts and extra nodes on the wrapper survive every re-export from Blender; the imported scene itself is regenerated each time. See [`examples/authored/doll/`](../examples/authored/doll/) for the comprehensive showcase, plus [`examples/generated/blink_eyes/`](../examples/generated/blink_eyes/) (sprite_frame isolation test) and [`examples/generated/shared_atlas/`](../examples/generated/shared_atlas/) (sliced atlas isolation test) for feature-focused fixtures.

## 7. Iterate

Re-export from Blender whenever the rig or animation changes. Reimport in Godot is automatic.

For the full panel walkthrough, the in-panel `?` button next to every subpanel header opens a topic-specific help popup. The same content lives in [`.ai/skills/blender-dev.md`](../.ai/skills/blender-dev.md) (Blender side) and [`.ai/skills/godot-dev.md`](../.ai/skills/godot-dev.md) (Godot side).
