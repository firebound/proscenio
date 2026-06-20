# Element

Per-element settings the writer reads for the active mesh. The parent panel holds the element-type selector and a draw-order nudge; the body splits into subpanels. The header reads `Element: <name>` while there is room and drops to `Element` on a narrow panel.

The **element type** decides the Godot node: `Mesh` exports a `Polygon2D` (a deformable cutout with UVs and weights), `Sprite` exports a `Sprite2D` (a spritesheet sliced by an hframes x vframes grid). `Depth offset` is a manual draw-order nudge in PSD-layer units, added on top of the PSD-order depth before it becomes the Godot `z_index` - a positive value pushes the element back, a negative value pulls it forward, so you can reorder a plane without re-importing. A hand-authored mesh that has no Proscenio element data yet shows an `Incorporate as Element` button that adopts it with a Mesh or Sprite default. The element type is locked while you are in Weight Paint mode. Validation issues for the active element render at the foot of the panel.

## Active Mesh

Shown when the element type is Mesh. The mesh exports as a Polygon2D - its vertices carry their own positions, so the Blender origin is baked in at export. The body shows the polygon and vertex-group counts and three controls:

- `Reproject UV` rebuilds the mesh's UV layout from its geometry (a planar projection - U follows X, V follows Z) so the texture lines up again after you move vertices.
- `Isolated material` keeps this sprite's own material when packing instead of linking it to the shared packed-atlas material - for effect sprites that need their own shader.
- `Exclude from atlas` keeps the sprite out of [Pack Atlas](08-atlas.md) entirely: its UVs and material are left untouched and it ships its own texture.

## Active Sprite

Shown when the element type is Sprite. Only the spritesheet metadata is exported, not the quad geometry:

- **hframes / vframes** - the spritesheet grid (columns x rows).
- **frame** - the cell shown at rest pose; animation tracks override it.

The sprite is always centred on its node - the writer's offset math assumes it, so this is a fixed internal constant rather than a toggle. The `[origin]` PSD tag sets the pivot for a sprite; it is ignored on a Mesh.

Below the fields a read-out reports the linked atlas size, the region size (full atlas, or the manual rect), and the resulting per-frame size for the current grid. A **Material Preview** sub-box hosts `Setup Preview` / `Remove Preview`, which wire (and un-wire) a shader-node slicer plus drivers so Material Preview shows the active cell on the quad instead of the full atlas.

## Attach to Bone

Shown for a sprite element. Rigidly parents the sprite to a single bone - the non-slot way to make a sprite follow one bone, with no swap. `Parent To Bone` prefills the active pose bone when one is current, otherwise it routes through a picker dialog; `Clear Bone Parent` detaches it. It exports as a `Sprite2D` parented to that `Bone2D`. A bone lying in the picture plane rotates the rigid sprite out of the camera plane - the panel warns and points you at a [slot](03-slots.md) for a flat follow on any bone.

## Texture Region

Which part of the texture the element samples. **Auto** reads the region from the mesh UV bounds at export (for a sprite, the region is omitted and the full atlas is used); **Manual** reads `region_x/y/w/h` verbatim for atlas slicing. On a mesh in Manual mode, `Snap to UV bounds` fills the four fields from the current UV layout. Reproject UV changes the UVs; the region only reads them.

## Drive from Bone

Wires a Blender driver between a pose bone and a sprite `proscenio.*` property - good for changes that vary continuously with rotation (iris scroll, a threshold flag). For a clean either/or swap, use a [slot](03-slots.md) instead.

Pick the `Target` property (frame index, or a region channel), the source `Armature`, `Bone`, and `Axis`. The axis defaults to `Bone Rot Y` (rotation around world Y, the front-ortho camera axis - the visible 2D angle); the other rotation and location channels are offered too. By default the driver is a clamped linear map: `In Min` / `In Max` are the bone-channel range and `Out Min` / `Out Max` the target-value range, with the default input range spanning negative-to-positive rotation so a bone swung back does not clamp to zero. The `Advanced expression` toggle swaps the two ranges for a raw expression over `var` (the bone channel). A live `Value` line reads back the driven target. Re-running on the same target replaces its driver rather than duplicating it; the existing-drivers list below removes them one at a time.
