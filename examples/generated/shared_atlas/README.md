# shared_atlas fixture (SPEC 007)

Tests the **sliced atlas packer** end-to-end (SPEC 005.1.c.2.1). Three polygon meshes reference the same shared atlas PNG, each mapped to a different quadrant via UV bounds. The packer must extract each sprite's slice (just its quadrant, not the whole atlas) into the new packed atlas.

## Directory layout

```text
examples/generated/shared_atlas/
├── shared_atlas.blend              [SOURCE — 3 polygon meshes referencing atlas.png with partial UVs]
├── shared_atlas.expected.proscenio [GOLDEN — CI-diffed validation midpoint]
├── atlas.png                       256x256, three colored shapes in three quadrants
└── godot/
    ├── SharedAtlas.tscn            Godot wrapper (SPEC 001)
    └── SharedAtlas.gd              empty stub
```

## Sprites

| Name | Shape | Color | UV bounds |
| --- | --- | --- | --- |
| `red_circle` | circle | red | (0.0, 0.5)–(0.5, 1.0) — top-left |
| `green_triangle` | triangle | green | (0.5, 0.5)–(1.0, 1.0) — top-right |
| `blue_square` | square | blue | (0.0, 0.0)–(0.5, 0.5) — bottom-left |

The bottom-right quadrant is intentionally transparent so any regression that re-packs the whole atlas instead of slicing surfaces as visible empty space.

## Skeleton

Single bone `root` only. No animation. The fixture exists to test the packer, not the bone-transform path.

## Building from source

Two-stage: PNG generation runs without Blender, `.blend` assembly runs in headless Blender.

```sh
# 1. Generate the atlas PNG (requires only Python + Pillow).
python scripts/fixtures/shared_atlas/draw_atlas.py

# 2. Assemble the .blend.
blender --background --python scripts/fixtures/shared_atlas/build_blend.py

# 3. Generate the golden .proscenio under godot/.
blender --background examples/generated/shared_atlas/shared_atlas.blend \
    --python scripts/fixtures/_shared/export_proscenio.py
```

Output is committed to the repo. Re-run whenever the fixture spec changes.

## What this fixture catches when broken

- Sliced packer regression — if the slicer fails to honor UV bounds, the packed atlas will contain copies of the entire shared atlas instead of the per-sprite quadrant.
- UV remap regression — if Apply Packed Atlas writes wrong UV coordinates, sprites will sample the wrong quadrant in the packed atlas (visible misalignment).
- Manifest format regression — `slot` + `slice` + `source_w/h` round-tripping.
