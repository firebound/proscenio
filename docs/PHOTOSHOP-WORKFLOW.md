# Photoshop workflow: authoring source art and re-importing without breaking the rig

How to author a `.psd`, run the UXP plugin, import the manifest into Blender, then re-import after edits without losing rigging work, and which PSD features Proscenio can ingest.

## The contract

The pipeline is **one-way**: PSD layers become a manifest JSON + per-layer PNGs; Blender consumes that manifest and stamps planes ready to rig. There is no Blender → PSD round-trip. The PSD is the source of truth for raster art; the manifest is regenerated on each export and consumed idempotently by the Blender importer.

Two artifacts live alongside each PSD:

- **The manifest mirror back to PSD** (UXP plugin's import path, formerly `proscenio_import.jsx`) reconstructs PSD layers from a manifest. This is for moving an existing manifest to a new PSD or recovering a lost source - it is **not** "edit in Blender, push back to PSD". That direction does not exist.
- **The Blender re-import** is what runs every iteration: artist edits the PSD, exports a fresh manifest, runs **Import Photoshop Manifest** in Blender, and the addon updates planes idempotently.

The user-facing rule: **edit only the PSD; never hand-edit the manifest. Re-import in Blender to apply updates.**

## Layout

```text
apps/photoshop/                   plugin source (UXP, TypeScript + React)
└── ...

<your project>/
├── firebound.psd                     hand-authored source (Photoshop)
└── firebound/                        export target chosen via UXP folder picker
    ├── manifest.json                 conforms to schemas/psd_manifest.schema.json v1
    ├── images/
    │   ├── torso.png                 one per `kind: polygon` layer
    │   ├── arm.png
    │   └── eye/
    │       ├── 0.png                 one per frame for `kind: sprite_frame` groups
    │       ├── 1.png
    │       └── 2.png
    └── _spritesheets/
        └── eye.png                   composed atlas per sprite_frame group
```

Blender opens the `.blend`, runs **Import Photoshop Manifest** (Active Sprite subpanel), points at `manifest.json`. Planes appear, materials wired, stub armature created (single `root` bone). User rigs and animates from there.

## Re-import idempotency: the mechanism

When the artist edits the PSD and re-exports, the Blender importer runs again. It does not start from scratch; it **updates planes in place** using a per-mesh tag.

| Concern | Behavior |
| --- | --- |
| Meshes identified by | manifest `name` field (matches the layer name) |
| Existing mesh with same name | replaced: vertex data, material, image refresh; user-set rotation, parenting, vertex weights survive |
| New layer in manifest | new plane stamped at the layer position |
| Layer removed from manifest | matching mesh is **left alone** (user may have repurposed it) and logged as orphan in the operator report |
| Mesh tag survives via | `proscenio.import_origin = "psd:<layer_name>"` Custom Property on the mesh |

Survival list (everything outside the regenerated PNG + UV + position):

- Rotation on the plane object.
- Parenting (mesh → bone, mesh → empty, vertex group bindings).
- Vertex group weights authored in Blender.
- Per-mesh PropertyGroup metadata (sprite type, sprite_frame metadata, `is_slot` flag, region overrides).

## The `proscenio.import_origin` caveat

The tag is the linchpin of idempotency, the Photoshop-side equivalent of the Godot wrapper pattern's stable identity. Treat it like a contract.

| Action | Effect on idempotency |
| --- | --- |
| Rename the plane in Blender, leave tag intact | re-import still updates the right mesh - tag wins, name is cosmetic |
| Delete the tag from a plane | re-import treats the plane as user-authored and stamps a **new** plane next to it (duplicate). Original orphans |
| Edit the tag value to a different layer name | re-import routes updates to whichever name the tag now points at - intentional only if you know what you are doing |
| Rename the layer in PSD | re-import logs the old plane as orphan and stamps a fresh plane for the new name. **Plan PSD layer renames as cross-DCC operations**: rename in PSD, then update the matching plane's tag manually in Blender if you want to keep your weights. Same shape as the Godot bone-rename caveat. |

Default: **do not edit the tag manually**. Inspect via Blender's Object Properties → Custom Properties to confirm presence after re-import. The Active Sprite subpanel in the addon surfaces tag-aware status when authoring.

## Authoring conventions in PSD

The UXP plugin's layer walk applies these rules:

| Convention | Behavior |
| --- | --- |
| **Layer name prefix `_`** | excluded (use for artist annotations, color refs, comments) |
| **Hidden layers** | skipped |
| **Layer groups** | walked recursively; output names join with `__` (e.g. `body__torso`) |
| **Sprite_frame layer group** (primary detection) | a group whose **direct children are numbered** (`0`, `1`, `2`, ...) becomes a `kind: sprite_frame` entry in the manifest with `frames[]` |
| **Sprite_frame flat naming** (fallback) | siblings named `eye_0`, `eye_1`, `eye_2` collapse into a single `kind: sprite_frame` entry named `eye` |
| **Frame size mismatch** | each sprite_frame's frames are padded with transparent fill to the bounding box of the largest, so the spritesheet grid is regular |
| **Locked layers** | currently treated like normal layers - lock state ignored |
| **Z-order** | top of layer stack = highest `z_order` value; importer translates to `mesh_center.y = z_order * Z_EPSILON` (default `0.001`) to avoid Z-fighting in Blender's 3D view |

Layer name sanitization is minimal today; use only ASCII characters, dashes, underscores, and dots if you intend to address layers by name later.

## Recipes

Skeleton + description. Concrete artifact in [`examples/simple_psd/`](../examples/simple_psd/).

### 1. First import of a new character

1. Author the PSD: one layer per body part, layer groups for sprite_frame attachments (eyes, mouth states), `_`-prefixed layers for refs.
2. UXP plugin: pick output folder (cached for the session), click **Export**.
3. Blender: open the target `.blend`, click **Import Photoshop Manifest**, select `manifest.json`.
4. Result: planes stamped at PSD positions, materials linked, single `root` bone created. Begin rigging.

### 2. Iteration: edit PSD, refresh planes

1. Edit the PSD (paint, reposition, rename, add/remove layers).
2. UXP plugin: **Export** to the same folder. Manifest + PNGs overwritten.
3. Blender: **Import Photoshop Manifest** again, point at the same `manifest.json`.
4. Result: planes updated in place where tags match; new layers stamped; removed-layer planes logged as orphans (not deleted).
5. Inspect orphan list in the operator report to clean up manually if appropriate.

### 3. Authoring a sprite_frame group in PSD

Two valid patterns:

- **Group with numeric children**: `eye/` folder containing layers `0`, `1`, `2`. UXP plugin emits `kind: sprite_frame` with `frames[0..2]`.
- **Flat naming**: sibling layers `eye_0`, `eye_1`, `eye_2`. UXP plugin collapses them into the same `eye` entry.

Pick whichever matches your authoring style. Both produce the same manifest.

### 4. Renaming a layer mid-project

The fragile recipe. To rename `torso` to `chest` without losing weights:

1. In Blender, duplicate the `proscenio.import_origin` tag value or note the plane name.
2. Rename the layer in PSD.
3. Re-export from PSD.
4. In Blender, **before** re-importing, change the tag on the existing plane from `psd:torso` to `psd:chest`. Now re-import will route updates to it.
5. Re-import. The plane's UV/PNG refresh, weights persist.

Default if you skip step 4: re-import stamps a fresh `chest` plane and orphans the original `torso` plane (with its weights intact, but disconnected from the new layer). Recoverable but tedious.

### 5. Adding a new sprite_frame variant after rigging

1. In PSD, add a new frame to the existing sprite_frame group (e.g. `eye/3`).
2. Re-export.
3. In Blender, re-import. The existing `eye` mesh's metadata bumps to include the new frame; sprite_frame `vframes`/`hframes` recompute.
4. Existing animation tracks targeting `eye:frame` continue to work; you can now keyframe up to the new index.

## PSD features and what survives the manifest

Status legend: `supported` shipped + tested, `untested` plausibly works but no fixture covers it, `not supported` the plugin skips it or flattens it.

| PSD feature | Status | Notes |
| --- | --- | --- |
| Raster pixel layers | supported | the canonical input |
| Layer groups (folders) | supported | walked recursively, names joined with `__` |
| Hidden layers | supported (skipped) | flag respected |
| `_`-prefixed layers | supported (skipped) | reserved for artist annotations |
| Sprite_frame group with numeric children | supported | primary detection path (D9) |
| Sprite_frame via flat `<name>_<index>` naming | supported | fallback detection (D9) |
| Frame size mismatch within a sprite_frame group | supported | padded to bbox of largest, transparent fill (D10) |
| Locked layers | untested | currently treated as unlocked - lock flag ignored |
| Layer masks | untested | likely flattened by the underlying export-PNG step; not documented as guaranteed |
| Layer effects (drop shadow, bevel, glow) | untested | likely **burned into the exported PNG** if PSD's "Save As PNG" honors them; not separable from the layer raster |
| Adjustment layers | not supported | skipped during walk; user must flatten or convert to raster before relying on the visual |
| Smart objects (embedded) | untested | likely walked as a single rasterized layer; nested editability not preserved |
| Smart objects (linked) | untested | depends on UXP DOM behavior; treat as embedded for now |
| Vector / shape layers | untested | likely rasterized at export; high-res vector data is lost |
| Text layers | untested | likely rasterized as the visible glyphs; text content not exposed |
| 16-bit / 32-bit color depth | untested | exported PNG forced to 8-bit |
| CMYK or non-RGB color modes | not supported | manifest pipeline assumes RGB(A) PNG output |
| Clipping masks | untested | unclear whether the clipped region is what gets exported |
| Group blend modes | untested | non-Normal blend modes may not export cleanly |
| Non-rectangular layer bounds | supported | handled via the layer's bounding box during export |

When status is `untested`, the safe path is to **flatten or rasterize the feature into a plain pixel layer before authoring rigs on top of it**. The first complex PSD that surfaces a real failure should drive a SPEC item to lock the behavior.

## Tradeoffs

- **Atlas timing (D2)**. The manifest emits per-layer PNGs. Atlas packing happens **on the Blender side** via the SPEC 005.1.c.2 packer. Pros: the artist does not need to think about atlas layout in PSD; the rig drives packing decisions. Cons: pre-packing in Photoshop manually is harder to integrate. If you maintain a hand-packed atlas in PSD, expect to disable the Blender packer for that asset.
- **Z-order via `Z_EPSILON` (D6)**. `mesh_center.y = z_order * 0.001` is enough offset to avoid Z-fighting in Blender's 3D view but small enough to keep the character flat-looking. Override per-scene if your rig is dense or your viewport zoom level fights with the default.
- **JSX manifest only, no direct PSD parse (D7)**. The Blender addon reads the manifest, never the PSD. Cross-version PSD parsing is fragile; the manifest is the stable contract. Cost: PSD edits require running the UXP plugin to materialize before they reach Blender. Benefit: the Blender side never hits a PSD format quirk.
- **`pixels_per_unit` source of truth**. Set in the UXP plugin (default `100`); flows through the manifest into Blender via `mesh_size = px / pixels_per_unit`. Override in the plugin's panel before export, not in Blender after import.

## Why no Blender → PSD round-trip?

Listed as out of scope in [SPEC 006](../specs/006-photoshop-importer/STUDY.md). Reasons:

- The Blender side is a rigging tool, not a paint tool. Pushing rig state back to a paint program has no clear use case.
- The PSD format is rich (smart objects, text, masks, effects). Faithful reconstruction of those from Blender is impossible; lossy reconstruction destroys artist intent.
- Live link Blender ↔ Photoshop is tracked as a deferred SPEC. If demand surfaces, the question gets reopened then.

The manifest mirror (UXP plugin's import path, formerly `proscenio_import.jsx`) is **manifest → PSD**, not Blender → PSD. It rebuilds a PSD from a manifest and per-layer PNGs - useful for moving manifests to fresh PSDs, not for pushing rig edits.

## Cross-DCC outlook

The PSD manifest schema (`psd_manifest.schema.json`) is **DCC-agnostic by design**. A Krita or GIMP exporter that emits a conforming manifest hooks into the same Blender importer with no addon changes. Tracked as deferred SPECs in [`docs/DEFERRED.md`](DEFERRED.md). Photoshop is proven first because the UXP plugin scaffold is in place; the schema is the value, not the JSX.

## See also

- [SPEC 006 — Photoshop → Blender importer](../specs/006-photoshop-importer/STUDY.md): full design and decisions D1-D10.
- [SPEC 010 — Photoshop UXP migration](../specs/010-photoshop-uxp-migration/STUDY.md): the active replacement of ExtendScript JSX with TypeScript + React UXP plugin.
- [`.ai/skills/photoshop-uxp-dev.md`](../.ai/skills/photoshop-uxp-dev.md): plugin internals, dev loop, file system API.
- [`schemas/psd_manifest.schema.json`](../schemas/psd_manifest.schema.json): authoritative manifest contract.
- [`docs/GODOT-WORKFLOW.md`](GODOT-WORKFLOW.md): the Godot-side analog to this doc.
- [`docs/DECISIONS.md`](DECISIONS.md): cross-cutting decisions.
- [`docs/DEFERRED.md`](DEFERRED.md): future SPECs (Krita / GIMP exporters, live link).
- [`examples/simple_psd/`](../examples/simple_psd/): worked round-trip fixture.
