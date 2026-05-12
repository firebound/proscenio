# atlas_pack fixture (SPEC 005.1.c)

Workbench for the **atlas packer** -- Pack / Apply / Unpack flow on the Atlas subpanel. Nine distinct sprite meshes, nine distinct PNGs, nine materials. The fixture exists so the panel has something to chew on with enough variety to make padding / POT / max-size behavior visible.

Each PNG is a flat-colored 32x32 square with a bold black digit (1..9) centered on it -- digit lets you eyeball where each sprite landed inside the packed atlas after Pack.

## Directory layout

```text
examples/generated/atlas_pack/
├── atlas_pack.blend             [SOURCE -- built by build_blend.py]
├── atlas_pack.expected.proscenio [GOLDEN -- CI-diffed validation]
├── pillow_layers/
│   ├── sprite_1.png .. sprite_9.png   32x32, distinct color + digit
└── godot/
    ├── AtlasPack.tscn           Godot wrapper (SPEC 001 pattern)
    └── AtlasPack.gd             empty stub
```

## Contents of the .blend

| Element | Detail |
| --- | --- |
| Armature `atlas_pack.armature` | 1 bone `root` at origin, tail along world -Y (Front Ortho convention). No animation. |
| Sprite meshes `sprite_1` .. `sprite_9` | 32x32 quads (32 / 100 = 0.32 world units side), parented `parent_type=BONE` to `root`. Arranged 3x3 grid, 0.4 units between centers. |
| Materials `sprite_N.mat` | One per sprite. Principled BSDF + ShaderNodeTexImage referencing `pillow_layers/sprite_N.png` with `interpolation="Closest"` (pixel-art). |
| UVs | 0..1 rect on each quad's own texture. |
| Actions | None. |

## Building from source

Two stages: PNG generation runs without Blender, `.blend` assembly runs in headless Blender.

```sh
# 1. Generate 9 PNGs under pillow_layers/.
python scripts/fixtures/atlas_pack/draw_layers.py

# 2. Assemble the .blend.
blender --background --python scripts/fixtures/atlas_pack/build_blend.py

# 3. Generate the golden .proscenio at the fixture root (used by run_tests.py).
blender --background examples/generated/atlas_pack/atlas_pack.blend \
    --python scripts/fixtures/_shared/export_proscenio.py
```

## What this fixture catches when broken

- Atlas packer regression: pack 9 distinct images into a single atlas without overlap.
- Padding regression: `pack_padding_px` not honored (sprites touch in packed atlas).
- POT regression: `pack_pot=True` not rounding up.
- Apply regression: UVs not rewritten to packed atlas coords.
- Unpack regression: `<active>.pre_pack` snapshot UV layer not restored.
- Material isolation regression: `material_isolated=True` swapping the wrong image, or losing per-sprite materials.

## Testing the Atlas panel (manual)

See [`tests/MANUAL_TESTING.md`](../../tests/MANUAL_TESTING.md) section 1.10 -- this fixture is the workbench used there.

Quick smoke (high level):

1. Open `atlas_pack.blend` in Blender.
2. N-panel > Proscenio > Atlas > **Pack Atlas**. Output: `atlas_pack.atlas.png` (single PNG with 9 sub-images) + `atlas_pack.atlas.json` (sprite -> (x,y,w,h) map).
3. **Apply Packed Atlas**. UVs rewritten; sprite materials swapped to `Proscenio.PackedAtlas` (or kept per-sprite if `material_isolated=True`).
4. Scrub viewport. Each sprite still shows its digit on its color -- proof Apply did not scramble UVs.
5. **Unpack**. UVs back to original 0..1; original materials restored.
