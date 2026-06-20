# Atlas

Compose source images into one shared atlas. Packing is optional - skip it and each sprite keeps its own texture. The panel opens with a read-out of the texture linked in the scene's materials (labelled as a packed atlas or a source image) and the current pixels-per-unit (read-only here - the [Export](10-pipeline.md#export) subpanel owns the editable field).

The **Atlas packer** box holds the pack settings - padding in pixels between cells, the maximum atlas size, and a power-of-two toggle - then the operators:

- **Pack Atlas** walks every sprite with a texture, runs MaxRects packing, and writes `<blend>.atlas.png` + `.atlas.json`. Non-destructive: UVs and materials are untouched.
- **Apply Packed Atlas** snapshots the pre-apply state, then rewrites every sprite's UVs and material to address the packed atlas. It stays disabled until a packed manifest exists beside the `.blend`.
- **Unpack Atlas** reverts a previous apply from the snapshot (it survives save / reload; `Ctrl+Z` does not), and shows only once an apply has run.

A packed `Sprite Frame` still slices correctly: its quad UVs cover the full sheet, so the packer keeps the sheet as one block and Godot subdivides that block by `hframes` / `vframes`. Set `Isolated material` on a sprite to keep its own shader while still drawing from the packed atlas, or `Exclude from atlas` (both on the [Active Mesh](02-element.md#active-mesh) subpanel) to keep a sprite out of packing entirely.
