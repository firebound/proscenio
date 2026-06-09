# Element

Per-element settings the writer reads for the active mesh. The parent panel holds the element-type selector; the body splits into subpanels.

The **element type** decides the Godot node: `Mesh` exports a `Polygon2D` (a deformable cutout with UVs and weights), `Sprite` exports a `Sprite2D` (a spritesheet sliced by an hframes x vframes grid).

## Active Mesh

Shown when the element type is Mesh. The mesh exports as a Polygon2D - its vertices carry their own positions, so the Blender origin is baked in at export.

## Active Sprite

Shown when the element type is Sprite. Only the spritesheet metadata is exported, not the quad geometry:

- **hframes / vframes** - the spritesheet grid (columns x rows).
- **frame** - the cell shown at rest pose; animation tracks override it.
- **centered** - Godot `Sprite2D.centered`: texture centred on the node origin, or its top-left at the origin.

## Texture Region

Which part of the texture the element samples. **Auto** reads the region from the mesh UV bounds at export; **Manual** reads `region_x/y/w/h` verbatim for atlas slicing. *Snap to UV bounds* fills the manual fields from the current UV.

## Drive from Bone

Wires a Blender driver between a pose bone and a sprite `proscenio.*` property - good for changes that vary continuously with rotation (iris scroll, a threshold flag). For a clean either/or swap, use a [slot](03-slots.md) instead.
