# Photoshop workflow

How to author a `.psd`, run the UXP plugin, import the manifest into Blender, then re-import after edits without losing rigging work.

## The contract

The pipeline is **one-way**: PSD layers become a manifest JSON + per-layer PNGs; Blender consumes that manifest and stamps planes ready to rig. There is no Blender → PSD round-trip. The PSD stays authoritative for raster art; the manifest is regenerated on each export and consumed idempotently by the Blender importer.

The plugin also ships an inverse direction (manifest → PSD) that reconstructs PSD layers from a manifest. It exists for moving an existing manifest into a new PSD or recovering a lost source - it is **not** "edit in Blender, push back to PSD". That direction does not exist.

Rule of thumb: edit only the PSD; never hand-edit the manifest. Re-import in Blender to apply updates.

## Project layout

```text
<your project>/
├── firebound.psd                    hand-authored source
└── firebound/                       export target picked via the UXP folder picker
    ├── manifest.json                conforms to the PSD manifest schema
    ├── images/
    │   ├── torso.png                one per `kind: polygon` layer
    │   └── eye/
    │       ├── 0.png                one per frame for `kind: sprite_frame` groups
    │       └── 1.png
    └── _spritesheets/
        └── eye.png                  composed atlas per sprite_frame group
```

Blender opens the `.blend`, runs **Import Photoshop Manifest** (Active Sprite subpanel), points at `manifest.json`. Planes appear, materials wired, single `root` bone created. Rig and animate from there.

## Re-import idempotency

When the artist edits the PSD and re-exports, the Blender importer runs again. It does not start from scratch; it updates planes in place using a per-mesh tag.

| Concern | Behavior |
| --- | --- |
| Meshes identified by | manifest `name` field (matches the layer name) |
| Existing mesh with the same name | replaced: vertex data, material, image refresh; user-set rotation, parenting, vertex weights survive |
| New layer in the manifest | new plane stamped at the layer position |
| Layer removed from the manifest | matching mesh is **left alone** (user may have repurposed it) and logged as orphan in the operator report |
| Mesh tag survives via | `proscenio.import_origin = "psd:<layer_name>"` Custom Property on the mesh |

Survival list (everything outside the regenerated PNG + UV + position):

- Rotation on the plane object.
- Parenting (mesh → bone, mesh → empty, vertex group bindings).
- Vertex group weights authored in Blender.
- Per-mesh PropertyGroup metadata (sprite type, sprite_frame metadata, `is_slot` flag, region overrides).

## The `proscenio.import_origin` caveat

The tag is the linchpin of idempotency. Treat it like a contract.

| Action | Effect on idempotency |
| --- | --- |
| Rename the plane in Blender, leave the tag intact | re-import still updates the right mesh - tag wins, name is cosmetic |
| Delete the tag from a plane | re-import treats the plane as user-authored and stamps a **new** plane next to it (duplicate) |
| Edit the tag value to a different layer name | re-import routes updates to whichever name the tag now points at - intentional only if you know what you are doing |
| Rename the layer in PSD | re-import logs the old plane as orphan and stamps a fresh plane for the new name. Plan PSD layer renames as cross-DCC operations: rename in PSD, then update the matching plane's tag manually in Blender if you want to keep your weights |

Default: do not edit the tag manually. Inspect via Object Properties → Custom Properties to confirm presence after re-import.

## Bracket tag taxonomy

Layer behaviour in the manifest is controlled by **bracket tags** embedded in the layer name. A tag is a token in the form `[tag]` or `[tag:value]`; multiple tags coexist on a single layer. Tags are parsed left-to-right; the layer's display name is whatever remains once every recognized tag is stripped.

```text
arm.R [folder:body] [origin:10,20] [scale:2.5]
^^^^^                ^^^^^^^^^^^^^^ ^^^^^^^^^^^
display name        tag             tag
```

| Tag | Where it lives | Effect |
| --- | --- | --- |
| `[ignore]` | layer or group | skipped; no manifest entry, no PNG export |
| `[merge]` | group | walked as if it were a single art layer (flattens children into one PNG) |
| `[folder:NAME]` | group | becomes a Blender `Collection` named `NAME`; children inherit |
| `[polygon]` | layer | forces `kind: polygon` (the default for art layers) |
| `[mesh]` | layer | emits `kind: mesh` - a deformable-polygon hint for future downstream work |
| `[spritesheet]` | group | composes a sprite_frame; each direct child becomes one frame |
| `[origin]` | layer | marks the layer's centroid as the pivot of its parent `[spritesheet]` / `[merge]` group (marker itself is not exported) |
| `[origin:X,Y]` | layer or group | explicit pivot in PSD pixel coords; overrides the implicit centre |
| `[scale:N]` | layer or group | multiplies bbox dimensions by `N` (float); sub-pixel results trigger a validation warning |
| `[blend:multiply]` / `[blend:screen]` / `[blend:additive]` | layer | sets `blend_mode`; importer applies the matching Eevee blend method and stamps `proscenio_blend_mode` for the Godot writer |
| `[path:NAME]` | layer | overrides the on-disk export path's leaf name |
| `[name:pre*suf]` | group | name template applied to descendants; `*` is replaced by the descendant's name |

Walk rules independent of tags:

| Convention | Behavior |
| --- | --- |
| Hidden layers | skipped |
| Layer groups (untagged) | walked recursively; output names join with `__` (e.g. `body__torso`) |
| Frame size mismatch inside `[spritesheet]` | each frame is padded with transparent fill to the bbox of the largest, so the spritesheet grid is regular |
| Locked layers | treated like normal layers; lock state ignored |
| Z-order | top of the layer stack = highest `z_order`; importer translates to `mesh_center.y = z_order * Z_EPSILON` (default `0.001`) to avoid Z-fighting |
| Document anchor (guide) | a horizontal + vertical PSD guide define the figure's pivot; emitted as `manifest.anchor`. Blender importer places world `(0, 0, 0)` at the anchor |

Layer name sanitization is minimal: stick to ASCII, dashes, underscores, and dots in display names if you intend to address layers by name later. Bracket tags themselves are stripped before sanitization, so spaces inside a tag are fine.

## Recipes

### 1. First import of a new character

1. Author the PSD: one layer per body part, `[spritesheet]`-tagged groups for animated attachments, `[ignore]`-tagged layers for refs and annotations.
2. UXP plugin: pick the output folder (cached for the session), click **Export**.
3. Blender: open the target `.blend`, click **Import Photoshop Manifest**, select `manifest.json`.
4. Result: planes stamped at PSD positions, materials linked, single `root` bone created. Begin rigging.

### 2. Iteration

1. Edit the PSD (paint, reposition, rename, add or remove layers).
2. UXP plugin: **Export** to the same folder. Manifest + PNGs overwritten.
3. Blender: **Import Photoshop Manifest** again, point at the same `manifest.json`.
4. Result: planes updated in place where tags match; new layers stamped; removed-layer planes logged as orphans (not deleted).

### 3. Sprite_frame group

Author either as a group with numeric children (`eye/` containing `0`, `1`, `2`) or as flat siblings (`eye_0`, `eye_1`, `eye_2`). Both produce the same manifest entry.

### 4. Renaming a layer mid-project

The fragile recipe. To rename `torso` to `chest` without losing weights:

1. In Blender, note the existing plane's `proscenio.import_origin` value.
2. Rename the layer in PSD.
3. Re-export from PSD.
4. In Blender, **before** re-importing, change the tag on the existing plane from `psd:torso` to `psd:chest`. Re-import will then route updates to it.
5. Re-import. The plane's UV/PNG refresh; weights persist.

Skipping step 4 stamps a fresh `chest` plane and orphans the original `torso` plane (with its weights intact, but disconnected from the new layer). Recoverable but tedious.

### 5. Adding a new sprite_frame variant after rigging

PSD-side: add the new frame to the existing sprite_frame group. Re-export.

Blender-side: re-import. The existing mesh's metadata bumps to include the new frame; sprite_frame `vframes` / `hframes` recompute. Existing animation tracks targeting `:frame` continue to work and you can keyframe up to the new index.

## PSD feature support

| Feature | Status |
| --- | --- |
| Raster pixel layers | supported (canonical input) |
| Layer groups (folders) | supported (walked recursively) |
| Hidden layers | supported (skipped) |
| `[ignore]`-tagged layers / groups | supported (skipped) |
| `[merge]` groups | supported (flatten children into a single PNG) |
| `[folder:NAME]` groups | supported (round-trip into Blender `Collection`) |
| `[spritesheet]` groups | supported (composes a sprite_frame) |
| `[mesh]` layers | supported (manifest `kind: mesh`; importer stamps `proscenio_psd_kind`) |
| `[blend:*]` tags | supported (manifest `blend_mode`; importer sets Eevee blend method + custom prop for the Godot writer) |
| `[origin:X,Y]` / `[scale:N]` / `[path:NAME]` | supported (sub-pixel scale warns) |
| Frame size mismatch within a sprite_frame group | supported (padded to bbox of the largest) |
| Smart objects, layer effects, adjustment layers, masks | not guaranteed (PSD export rasterizes into the PNG; not separable from the layer raster) |
| Text / vector / shape layers | not guaranteed (rasterized on export; vector data lost) |
| Non-RGB color modes (CMYK, etc.) | not supported (pipeline assumes RGB(A) PNG output) |
| 16-bit / 32-bit color depth | not guaranteed (exported PNG forced to 8-bit) |

When a feature is **not guaranteed**, the safe path is to flatten or rasterize it into a plain pixel layer before authoring rigs on top of it.

## Cross-DCC outlook

The PSD manifest schema is **DCC-agnostic by design**. A Krita or GIMP exporter that emits a conforming manifest hooks into the same Blender importer with no addon changes - Photoshop is proven first because the UXP plugin is in place; the schema is the value, not the path through Adobe.

## Why no Blender → PSD round-trip?

Out of scope:

- Blender is a rigging tool, not a paint tool. Pushing rig state back to a paint program has no clear use case.
- The PSD format is rich (smart objects, text, masks, effects). Faithful reconstruction from Blender is impossible; lossy reconstruction destroys artist intent.
- Live link Blender ↔ Photoshop is parked as a long-term idea. If demand surfaces, the question gets reopened then.

The manifest-mirror direction (manifest → PSD) is **manifest-to-PSD**, not Blender-to-PSD. It rebuilds a PSD from a manifest and per-layer PNGs - useful for moving manifests to fresh PSDs, not for pushing rig edits.
