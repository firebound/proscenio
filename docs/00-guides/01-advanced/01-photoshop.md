# Photoshop

The deep guide to the Photoshop side: how to author a `.psd` so it exports cleanly, what the bracket tags do, and how re-importing into Blender after edits behaves. For the quick version, see the [basic walkthrough](../00-basic/01-photoshop.md).

## The contract

The pipeline runs **one way**. Your PSD layers become a manifest JSON plus per-layer PNGs; Blender reads the manifest and stamps planes you can rig. The PSD stays the source of truth for the raster art, and you regenerate the manifest every time you export - there is no Blender-to-PSD round-trip ([why](#why-there-is-no-blender-to-psd-round-trip)).

Rule of thumb: edit the PSD, never the manifest by hand, and re-import in Blender to apply your changes.

## Project layout

When you export, the plugin writes the manifest and the per-layer PNGs into the folder you pick. Blender adds the `_spritesheets/` folder later, on import - that is where it composes each spritesheet group into a single sheet, not the Photoshop side:

```text
<your project>/
├── firebound.psd                    your hand-authored source
└── firebound/                       export target (you pick it in the folder picker)
    ├── manifest.json                written by the plugin
    ├── images/                      written by the plugin
    │   ├── torso.png                one per polygon layer
    │   └── eye/
    │       ├── 0.png                one per frame of a spritesheet group
    │       └── 1.png
    └── _spritesheets/               created by Blender on import
        └── eye.png                  the composed sheet per spritesheet group
```

In Blender, open the `.blend`, click `Import Photoshop Manifest` in the **Active Sprite** subpanel, and point it at `manifest.json`. You get one plane per layer with materials wired and a single `root` bone - ready to rig and animate.

## Re-importing after PSD edits

When you edit the PSD, re-export, and run the import again in Blender, it does not duplicate anything: it finds each existing plane by its tag and updates it in place. The tag is a hidden custom property, `proscenio_import_origin = "psd:<layer_name>"`, matched against each layer (the object's name is ignored - see [Three names, one link](#three-names-one-link)). A layer that still exists is updated, a new layer gets a fresh plane, and a removed layer's plane is left alone and logged as an orphan rather than deleted.

The important part is what "update in place" rebuilds. The import **regenerates the mesh** from the new art - back to a flat quad at the layer's new size and UVs - so anything stored in the mesh's vertex data is reset. The *object* is reused, so object-level data survives:

- transform (rotation, position) and parenting;
- the vertex-group names (the groups remain, but the weights painted onto their vertices are gone);
- per-sprite settings (sprite type, sprite-frame metadata, the `is_slot` flag, region overrides);
- slot membership and animation tracks that target the plane by name.

> [!WARNING]
> Re-import is **not** weight-preserving. Because it rebuilds the mesh, the Automesh density and the painted weights on every plane it touches are lost - the weight values live in the vertex data it regenerates. Do your PSD geometry iteration *before* you automesh and skin, or be ready to re-mesh and re-bind. (Non-destructive re-import is tracked on the backlog.)

So the sane order is: iterate the PSD freely - paint, reposition, add or remove layers - while the sprites are still plain quads, and automesh, weight, and rig once the art has settled.

### Three names, one link

The reason re-import is safe (and the one thing that can break it) comes down to three names that are independent of each other:

- the **PSD layer name** - say `torso`;
- the **Blender object name** - whatever you call the plane;
- the **`proscenio_import_origin` tag** on the plane - here `psd:torso`.

Only the tag is the link. On re-import, the importer pairs each PSD layer to the plane whose tag is `psd:<that layer>`, and ignores the object name entirely. Everything below follows from that one rule:

- **You rename the plane in Blender** (`torso` -> `body_main`): safe. The tag still reads `psd:torso`, so re-import finds and updates it. The object name is cosmetic.
- **You delete the tag**: the plane is now unlinked. Re-import no longer sees it as `torso`'s plane, so it stamps a fresh `torso` plane beside your now-orphaned one - you end up with a duplicate.
- **You rename the layer in the PSD** (`torso` -> `chest`): this breaks the link. The manifest now has `chest`, but your plane is still tagged `psd:torso`, so re-import orphans your plane (weights and all) and stamps a blank `chest`. To carry the weights over, edit the tag to `psd:chest` **before** re-importing (see [Rename a layer mid-project](#rename-a-layer-mid-project)).
- **You point the tag at a different layer** on purpose: re-import then feeds that layer's art into this plane. Advanced - only when you know why.

You normally never touch the tag. After a re-import you can confirm it under Object Properties > Custom Properties, as `proscenio_import_origin`.

## Bracket tags

You drive the export by writing **bracket tags** into a layer's name - tokens like `[tag]` or `[tag:value]`. A tag can sit anywhere in the name, a layer can carry several, and the keyword is case-insensitive (`[Ignore]` works). Whatever is left after the recognized tags are stripped becomes the display name; an unrecognized bracket like `[WIP]` is left in that name untouched.

```text
arm.R [folder:body] [origin:10,20] [scale:2.5]
^^^^^                ^^^^^^^^^^^^^^ ^^^^^^^^^^^
display name        tag             tag
```

| Tag | Where it goes | What it does |
| - | - | - |
| `[ignore]` | layer or group | dropped entirely - no manifest entry, no PNG |
| `[merge]` | group | flattens the whole group into one PNG, as if it were a single art layer |
| `[folder:NAME]` | group | becomes a Blender `Collection` named `NAME`; children inherit it |
| `[polygon]` / `[sprite]` | layer | forces `kind: polygon` (the default for art layers anyway) |
| `[mesh]` | layer | emits `kind: mesh` - a polygon flagged as a deformable-mesh source |
| `[spritesheet]` | group | marks the group as a sprite-frame; its numbered child layers become the frames |
| `[origin]` | layer | marks that layer's centroid as the pivot of its parent `[spritesheet]` or `[merge]` group (the marker layer itself is not exported) |
| `[origin:X,Y]` | layer or group | an explicit pivot in PSD pixels; overrides the implicit centre |
| `[scale:N]` | layer or group | multiplies the bounding-box size by `N`; a sub-pixel result raises a validation warning |
| `[blend:VALUE]` | layer | records the intended blend mode (`normal`, `multiply`, `screen`, `additive`) as metadata. Blender renders the layer as plain alpha blend (it does not preview true multiply / screen / additive), and the mode does not reach Godot yet - the `.proscenio` has no blend-mode field (backlog) |
| `[path:NAME]` | layer | overrides the leaf name of the on-disk export path (no slashes - subfolders are `[folder:NAME]`'s job) |
| `[name:pre*suf]` | group | a name template for descendants; `*` is replaced by each descendant's name |

A few things happen regardless of tags:

- Hidden and `[ignore]` layers are skipped; a layer with no visible pixels is skipped too.
- Untagged groups are walked recursively; output names join with `__` (so `body` > `torso` becomes `body__torso`).
- A group whose direct children are named with plain numbers contiguous from zero (`0`, `1`, `2`, ...) is detected as a spritesheet on its own; `[spritesheet]` just forces that grouping.
- Inside a spritesheet, frames of different sizes are padded with transparency to the largest frame's box, so the grid stays regular.
- Locked layers export like any other - the lock is ignored.
- Stacking order sets `z_order` (top of the stack is highest); Blender turns that into a tiny Y offset (`z_order * 0.001`) so planes do not Z-fight.
- A horizontal and a vertical PSD guide define the figure's pivot, exported as the document anchor; Blender places world `(0, 0, 0)` there.

Keep display names to ASCII letters, digits, dashes, and underscores. The manifest keeps your name verbatim, but anything else - dots, spaces - is replaced with `_` when the name becomes a PNG filename or a Godot node, so a clean name stays predictable across the pipeline. (Bracket tags are stripped first, so spaces inside a tag are fine.)

## Recipes

### First import of a new character

1. *Author the PSD*: one layer per body part, spritesheet groups for animated attachments, `[ignore]` on reference and annotation layers.
2. *Export*: in the plugin, pick the output folder (it is remembered for the session) and click `Export`.
3. *Import in Blender*: open the target `.blend`, click `Import Photoshop Manifest`, and select `manifest.json`.

You land with planes at their PSD positions, materials linked, and a single `root` bone. Rig from there.

### Iterate on an existing character

1. *Edit the PSD*: paint, reposition, rename, add, or remove layers.
2. *Re-export*: click `Export` to the same folder; the manifest and PNGs are overwritten.
3. *Re-import*: run `Import Photoshop Manifest` again and point at the same `manifest.json`.

Planes update in place where the tags match, new layers are stamped, and removed-layer planes are reported as orphans rather than deleted. (Remember the re-import warning above: do this before you skin a sprite.)

### Author a spritesheet group

Put the frames in a group and name each frame layer with a plain number, counting from zero - a group `eye` containing layers `0`, `1`, `2`. A group like that is detected as a spritesheet automatically; add `[spritesheet]` when you want it explicit (or to force it on an ambiguous group). Two rules the detector enforces:

- the frame names are pure numbers - `0`, not `frame0` or `eye_0`;
- they run contiguously from zero (`0`, `1`, `2`, with no gaps), and there are at least two.

### Rename a layer mid-project

The fragile one. To rename `torso` to `chest` without losing weights:

1. In Blender, note the existing plane's `proscenio_import_origin` value.
2. Rename the layer in the PSD and re-export.
3. **Before** re-importing, change that plane's tag from `psd:torso` to `psd:chest`, so the importer routes the update to it.
4. Re-import. The plane's UV and PNG refresh; the weights persist (the geometry is still rebuilt to a quad, so this is the no-automesh case).

Skip step 3 and you get a fresh `chest` plane plus an orphaned `torso` plane. Recoverable, but tedious.

### Add a spritesheet frame after rigging

Add the new numbered frame to the existing spritesheet group in the PSD and re-export, then re-import in Blender. The mesh's metadata bumps to include the new frame, `hframes` / `vframes` recompute, existing animation tracks on `:frame` keep working, and you can keyframe up to the new index.

## What survives a PSD export

The bracket tags above cover what each tag does; this is about which native Photoshop features make it through the export at all (it rasterizes each layer to a PNG):

| Photoshop feature | How it exports |
| - | - |
| Raster pixel layers | supported - the canonical input |
| Layer groups (folders) | supported - walked recursively |
| Hidden layers | supported - skipped |
| Smart objects, layer effects, adjustment layers, masks | not guaranteed - flattened into the layer's PNG on export, inseparable from its raster |
| Text, vector, and shape layers | not guaranteed - rasterized on export; the vector data is lost |
| Non-RGB color modes (CMYK, etc.) | not supported - the pipeline assumes RGB(A) PNG output |
| 16-bit / 32-bit color depth | not guaranteed - the exported PNG is forced to 8-bit |

When something is **not guaranteed**, flatten or rasterize it into a plain pixel layer before you rig on top of it.

## Beyond Photoshop

The manifest schema is DCC-agnostic on purpose: a Krita or GIMP exporter that emits a conforming manifest plugs into the same Blender importer unchanged. Photoshop is just proven first, because the UXP plugin exists. (More on this open-contract design in [Architecture](../../01-project/01-architecture.md).)

## Why there is no Blender-to-PSD round-trip

Out of scope by design. Blender is a rigging tool, not a paint tool, so pushing rig state into a paint program has no clear use - and the PSD format is too rich (smart objects, text, masks, effects) to reconstruct faithfully from Blender. A live Blender-to-Photoshop link is parked as a long-term idea.

The one reverse direction the plugin does ship, manifest-to-PSD, rebuilds a PSD from a manifest and its PNGs - for moving a manifest into a fresh PSD or recovering a lost source, not for pushing rig edits back.
