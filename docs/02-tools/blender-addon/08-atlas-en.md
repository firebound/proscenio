# Atlas

Compose the scene's source images into one shared atlas, rewrite UVs to address it, and restore the originals on demand. Packing is optional - skip it and each element keeps its own texture - so this is an optimization step before export, not a required stage. It sits eighth in the sidebar and is collapsed by default.

The panel opens with a read-out of the texture linked in the scene's materials, labelled `packed atlas:` when it is the shared sheet for this `.blend` or `source image:` when it is a discovered source. Below it sits the current pixels-per-unit, read-only here because the [Export](10-pipeline.md#export) subpanel owns the editable field. With no texture found the read-out shows `no atlas linked in materials`.

The **Atlas packer** box holds the pack settings and the three operators. The settings are scene fields, saved with the `.blend`:

- `Pack padding` - pixels of padding reserved around each cell in the packed sheet. Default 2, clamped to 0-64.
- `Pack max size` - a hard cap on the packed sheet's dimensions in pixels; the pack fails rather than exceeding it. Default 4096, clamped to 64-8192.
- `Power-of-two atlas` - rounds the packed dimensions up to a power of two (a legacy GPU optimization). Off by default.

All three operators require Object Mode, because a mesh's UV data sits behind BMesh while in Edit Mode.

**Pack Atlas** walks every element mesh that has a source image, runs MaxRects (best-short-side-fit) packing at the configured padding and cap, and writes `<blend>.atlas.png` plus `<blend>.atlas.json` next to the `.blend`. It is non-destructive: UVs and materials are untouched, so it is safe to re-run while tuning the settings. A mesh flagged `Exclude from atlas` is left out of the walk entirely; if the sprites do not fit the cap, the pack reports the failure and writes nothing.

**Apply Packed Atlas** reads the manifest and rewrites each element's UVs from source-image space into its slot in the packed sheet, then links the element to the shared `Proscenio.PackedAtlas` material. A sprite element also gets its texture region switched to manual, pointing at its slot. The button stays disabled until a packed manifest exists beside the `.blend`. Before it rewrites anything, Apply snapshots each element's pre-apply state (its original UVs as a duplicated UV layer, plus its material and texture region) so Unpack can restore it. Re-running Apply restores from that snapshot first, so a second apply does not shrink the slot by re-packing already-packed UVs. The operator is undoable - <kbd>Ctrl+Z</kbd> reverts it - and it reports how many elements it rewrote and how many it skipped.

**Unpack Atlas** reverts a previous apply from the snapshot, restoring every element's original UVs, material, and texture region. It appears only once an apply has run. Unlike Apply's <kbd>Ctrl+Z</kbd>, the snapshot lives in the `.blend`, so Unpack still works after a save and reload. If an original material was deleted between apply and unpack, that element's UVs are still restored and the missing material is reported.

**Keeping an element out of the shared sheet.** Two per-element flags on the [Active Mesh](02-element.md#active-mesh) subpanel control how an element relates to the atlas. `Isolated material` keeps the element on its own shader while still drawing pixels from the packed sheet; `Exclude from atlas` keeps it out of packing entirely, so it retains its own UVs, texture, and material.

A packed sprite-frame element still slices correctly. Its quad UVs cover the full sheet, so the packer keeps that sheet as one block and Godot subdivides the block by `hframes` and `vframes`.
