# Atlas

Compose source images into one shared atlas. Packing is optional - skip it and each sprite keeps its own texture.

- **Pack Atlas** walks every sprite with a texture, runs MaxRects packing, and writes `<blend>.atlas.png` + `.atlas.json`. Non-destructive: UVs and materials are untouched.
- **Apply Packed Atlas** snapshots the pre-apply state, then rewrites every sprite's UVs and material to address the packed atlas.
- **Unpack Atlas** reverts a previous apply from the snapshot (it survives save / reload; `Ctrl+Z` does not).

A packed `Sprite Frame` still slices correctly: its quad UVs cover the full sheet, so the packer keeps the sheet as one block and Godot subdivides that block by `hframes` / `vframes`. Set `Isolated material` on a sprite to keep its own shader while still drawing from the packed atlas.
