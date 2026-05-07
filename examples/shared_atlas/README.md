# shared_atlas fixture (SPEC 007)

Tests the **sliced atlas packer** end-to-end (SPEC 005.1.c.2.1). Three polygon meshes reference the same shared atlas PNG, each mapped to a different quadrant via UV bounds. The packer must extract each sprite's slice (just its quadrant, not the whole atlas) into the new packed atlas.

## Contents (after running the build script)

```plaintext
shared_atlas/
├── atlas.png                       256×256, three colored shapes in three quadrants
├── shared_atlas.blend              3 polygon meshes referencing atlas.png with partial UVs
├── shared_atlas.expected.proscenio golden — CI diffs against re-export
├── SharedAtlas.tscn                Godot wrapper (manual user pattern, SPEC 001)
├── SharedAtlas.gd                  empty stub
└── README.md
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

```bash
# 1. Generate the atlas PNG (requires only Python + Pillow).
python scripts/fixtures/draw_shared_atlas.py

# 2. Assemble the .blend.
blender --background --python scripts/fixtures/build_shared_atlas.py

# 3. Generate the golden .proscenio.
blender --background examples/shared_atlas/shared_atlas.blend \
    --python scripts/fixtures/export_proscenio.py
```

Output is committed to the repo. Re-run whenever the fixture spec changes.

## What this fixture catches when broken

- Sliced packer regression — if the slicer fails to honor UV bounds, the packed atlas will contain copies of the entire shared atlas instead of the per-sprite quadrant.
- UV remap regression — if Apply Packed Atlas writes wrong UV coordinates, sprites will sample the wrong quadrant in the packed atlas (visible misalignment).
- Manifest format regression — `slot` + `slice` + `source_w/h` round-tripping.
