# Blender

The deep guide to the Blender side: how to author a Proscenio character, what survives saves and addon reloads, and what the addon does between Photoshop on one side and Godot on the other.

For the quick version, see the [basic walkthrough](../00-basic/02-blender.md).

## The contract

Blender is the **hub** of the pipeline. It reads the PSD manifest coming in and writes the `.proscenio` going out. You author the way you always do in Blender - [weight paint](https://docs.blender.org/manual/en/latest/sculpt_paint/weight_paint/index.html), [dopesheet](https://docs.blender.org/manual/en/latest/editors/dope_sheet/introduction.html), [NLA](https://docs.blender.org/manual/en/latest/editors/nla/introduction.html), [drivers](https://docs.blender.org/manual/en/latest/animation/drivers/introduction.html) - and reach for the thin **Proscenio** sidebar tab only for the pipeline-specific knobs.

Rule of thumb: work in Blender like Blender, use the Proscenio panel for the pipeline bits, and export when you are ready.

Re-export is idempotent, so you can do it as often as you like.

## Project layout

```text
<your project>/
├── firebound.psd               source PSD
├── firebound/
│   ├── manifest.json           from the Photoshop plugin
│   ├── images/                 per-layer PNGs
│   └── _spritesheets/          composed sprite-frame sheets
├── firebound.blend             your rig + animation
└── firebound.proscenio         written by the exporter (sticky path)
```

The `.blend` is yours and stays authoritative for everything you author in Blender - rig, weights, animations, slots. The `.proscenio` is regenerated on every export, so never hand-edit it.

## What survives what

| Action | What happens |
| - | - |
| Save and reopen the `.blend` | Everything persists - normal Blender. |
| Reload the addon | Scene data untouched; Proscenio settings re-hydrate on file open. You only lose live operator state, like a Quick Armature drag in progress. |
| Re-import the PSD manifest | The object survives - transform, parenting, vertex-group names, settings, slots, and name-targeted animation all carry over. But the mesh is **rebuilt** to a flat quad, so vertex data resets: Automesh density and painted weights are lost (the groups stay, the values do not). Orphaned layers are left alone and logged. See [the order that saves your skinning](01-photoshop.md#re-importing-after-psd-edits). |
| Uninstall the addon | Scene data, weights, actions, atlas materials, and the raw `proscenio_*` properties stay. The panel UI vanishes, but `Drive from Bone` drivers keep working - they are native Blender drivers. |
| Bump Blender versions | [Datablocks](https://docs.blender.org/manual/en/latest/files/data_blocks.html) carry over; the addon may break on `bpy` API drift, so test on the next LTS first. |
| Move the project folder | Files move fine, but the sticky export path is absolute today - re-pick it on the next export. |

## Why you edit through the panel

The addon stores each setting twice:

- a **typed object** - canonical, and what the panel edits;
- a raw `proscenio_*` [Custom Property](https://docs.blender.org/manual/en/latest/files/custom_properties.html) - an arbitrary key Blender lets you stash on any datablock, editable under Object Properties.

The sync runs one way: the typed object hydrates from the Custom Property when you open the file, and mirrors back to it on save.

So edit through the panel. A Custom Property you poke by hand mid-session is ignored - nothing feeds it back to the typed object until the next reopen, and the next save overwrites it. The one exception is the headless export path (`blender --background`), where the panel never registered, so the exporter falls back to the raw property.

## The authoring panel

Open the sidebar with <kbd>N</kbd> and switch to the **Proscenio** tab. Its subpanels:

- **Active Sprite** - sprite type (`polygon` / `sprite_frame`), spritesheet metadata, texture region, `Drive from Bone`, `Import Photoshop Manifest`.
- **Active Slot** - the slot anchor, default-attachment picker, and attachment list (shown when an `is_slot` [Empty](https://docs.blender.org/manual/en/latest/modeling/empties.html) is selected).
- **Skeleton** - bone count plus the pose helpers (`Bake Current Pose`, `Toggle IK`, `Save Pose to Library`, `Quick Armature`, `Create Slot`).
- **Skinning** - `Automesh from Sprite`, `Bind to Picker Armature`, `Edit Weights`, weight transfer, and snapshots.
- **Outliner** - a sprite-centric flat list with a substring filter and favorites.
- **Animation** - a read-only summary of the actions the exporter will emit.
- **Atlas** - the atlas filename plus `Pack Atlas` / `Unpack Atlas` / `Apply Packed Atlas`.
- **Validation** - the issue list, click-to-select.
- **Export** - the sticky path, `pixels_per_unit`, `Validate` / `Export` / `Re-export`, and `Preview Camera`.
- **Diagnostics** - a smoke test.

Every subpanel header has a status badge and a `?` button that opens topic-specific help.

### The naming rule that bites

The exporter pairs a [vertex group](https://docs.blender.org/manual/en/latest/modeling/meshes/properties/vertex_groups/index.html) to a bone only when their names match **exactly**.

Renaming a **bone** is safe. Blender auto-renames the matching vertex group on every mesh that armature deforms, so the pairing follows along. That is standard Blender behaviour, not something the addon adds.

Two cases still break the pairing:

- **You rename the vertex group instead of the bone.** The sync only goes one way - a group rename does not touch the bone.
- **The vertex group sits on a mesh the armature does not deform** (one still only object-parented, say). The auto-rename never reaches it.

So rename from the bone side, keep your deform meshes bound, and the match holds.

## Recipes

### First rig from a Photoshop manifest

1. *Export from Photoshop*: run the plugin and export to a folder.
2. *Import in Blender*: open the target `.blend`, then click `Import Photoshop Manifest` in the **Active Sprite** subpanel and point at the manifest. Planes land at their PSD positions, materials linked, with a single `root` bone.
3. *Add the bones*: in [Edit Mode](https://docs.blender.org/manual/en/latest/animation/armatures/bones/editing/introduction.html), or with `Quick Armature` for a modal click-drag.
4. *Bind the meshes*: select them and press <kbd>Ctrl+P</kbd>, then [`Armature Deform`](https://docs.blender.org/manual/en/latest/animation/armatures/skinning/parenting.html) (or use the **Skinning** subpanel). Paint the weights.
5. *Set each sprite's type* in **Active Sprite**.
6. *Validate and export*: `Validate`, then `Export`.

### Iterate

Edit in Blender, save, and click `Re-export` in the **Export** subpanel. The path is reused by default and Godot picks up the change the next time its window has focus.

### Rename a bone mid-project

A bone rename is lighter than it looks. Blender carries it across most of its own references automatically:

- vertex groups on deformed meshes;
- [Action](https://docs.blender.org/manual/en/latest/animation/actions.html) [F-curve](https://docs.blender.org/manual/en/latest/editors/graph_editor/fcurves/introduction.html) channels;
- drivers, constraints, and bone-parented objects.

The steps:

1. *Rename the bone* in Edit or [Pose Mode](https://docs.blender.org/manual/en/latest/animation/armatures/posing/introduction.html).
2. *Fix what Blender misses*: the gaps from [the naming rule above](#the-naming-rule-that-bites) (a vertex group on a non-deform mesh), plus any external script or out-of-scene data that hard-codes the old name.
3. *Validate and re-export*.

Still, naming bones once and sticking to it beats renaming later.

### Add a sprite-frame variant after rigging

Add the new frame to the existing spritesheet group in the PSD and re-export, then re-import the manifest in Blender. The mesh's spritesheet metadata bumps to include the new index, existing animation tracks keep working, and you can keyframe up to the new frame.

### Pack and unpack the atlas

1. The **Atlas** subpanel finds the materials that carry image textures.
2. `Pack Atlas` composes the per-sprite images into one sheet and rewrites each sprite's `texture_region`.
3. `Unpack Atlas` reverses it - each region becomes its own image again, materials updated.
4. `Apply Packed Atlas` is for when you packed externally; it rebinds materials to the existing atlas file.

The packer is deterministic for deterministic input, which is why CI uses it for byte-equality goldens.

### Multi-action animation

Each Blender Action becomes one entry in the export. Author them in the [Action Editor](https://docs.blender.org/manual/en/latest/editors/dope_sheet/modes/index.html); the exporter respects each Action's frame range. NLA strips are not consumed - bake to a single Action first.

## Feature support

| Feature | Status |
| - | - |
| Single armature per scene | supported - the canonical case |
| Meshes parented to the armature (Armature Deform) | supported - drives skinning weights |
| Meshes parented to a single bone ([Bone parent](https://docs.blender.org/manual/en/latest/scene_layout/object/editing/parent.html)) | supported - rigid attachment |
| Empties flagged `is_slot` as slot anchors | supported - both bone-parent and object-parent honoured |
| Vertex groups named after bones | supported - the exact-match rule |
| Vertex groups matching no bone | supported - dropped with a console warning |
| One F-curve per channel in an Action | supported - the canonical case |
| Drivers wired via `Drive from Bone` | supported - survive save, reopen, and addon uninstall |
| [Shape keys](https://docs.blender.org/manual/en/latest/animation/shape_keys/introduction.html) on sprite meshes | not supported - the exporter ignores them; the format has no shape-key concept |
| [IK constraints](https://docs.blender.org/manual/en/latest/animation/constraints/tracking/ik_solver.html) | Blender-only posing aid (`Toggle IK`); not exported - bake to bone keyframes for Godot, or rebuild in-engine. Full round-trip is on the backlog |
| NLA strips composing motion | not supported - bake to a single Action first; NLA-to-Action support is on the backlog |

Anything outside this table is not covered by CI fixtures - linked or library-override armatures, multi-material meshes, color-management quirks, constraints other than IK.

The safe path: flatten the scenario before you rig on top of it. And if a real workflow hits friction there, log it so it can become a spec.

## How validation works

There are two layers:

- **Inline** checks run on every redraw and are cheap: a status badge by each subpanel header and an error icon next to a broken row, catching the obvious problems without walking the scene.
- **Lazy** checks run on demand: the `Validate` button walks the whole scene and gives you an issue list you can click to select the offending object.

Both `Export` and `Re-export` gate on the lazy validator - if any issue is an `error`, the export aborts; warnings do not block. The usual errors: no armature in the scene, a sprite missing a required field, a vertex group with no matching bone, or an atlas image that cannot be found.
