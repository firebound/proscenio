# simple_psd fixture (SPEC 006)

Smallest end-to-end exercise of the **Photoshop -> Blender importer**:
one polygon layer + one sprite_frame group of 4 frames driven by a v1
PSD manifest. Use this fixture when debugging the manifest -> stamper
-> writer path without the noise of the full doll rig.

## Directory layout

```text
examples/generated/simple_psd/
├── simple_psd.blend                       [SOURCE - built by build_blend.py from the manifest]
├── simple_psd.expected.proscenio          [GOLDEN - CI-diffed validation midpoint]
├── simple_psd.photoshop_manifest.json     [INPUT - hand-authored SPEC 006 v1 manifest]
├── pillow_layers/                         [INPUT - per-layer PNGs the manifest references]
│   ├── square.png                64x64 - polygon layer
│   ├── arrow_0.png               32x32 - sprite_frame, frame 0 (up)
│   ├── arrow_1.png               32x32 - sprite_frame, frame 1 (right)
│   ├── arrow_2.png               32x32 - sprite_frame, frame 2 (down)
│   ├── arrow_3.png               32x32 - sprite_frame, frame 3 (left)
│   └── arrow_spritesheet.png    128x32 - preview (importer composes its own internal sheet)
├── _spritesheets/                         [DERIVED - composed by the importer; gitignored]
│   └── arrow.png
└── godot/
    ├── SimplePSD.tscn                     Godot wrapper
    └── SimplePSD.gd                       autoplay stub (default_animation + autoplay exports)
```

## Pipeline at a glance

```text
simple_psd.photoshop_manifest.json (hand-authored)
    +
pillow_layers/*.png (drawn by Pillow)
    │
    ├──► blender --background --python scripts/fixtures/simple_psd/build_blend.py
    │       └──► simple_psd.blend (importer stamps polygon + sprite_frame planes)
    │
    └──► simple_psd.expected.proscenio    scripts/fixtures/_shared/export_proscenio.py
            └──► CI compares against re-export of simple_psd.blend each run
```

The fixture is a **roundtrip integration test** of the SPEC 006
importer: any regression in the manifest parser, the polygon stamper,
the sprite_frame composer, or the world-rect coordinate conversion
shows up as a golden-diff in the next `run_tests.py` pass.

## Layers

| Manifest entry | Kind | Position (px) | Size (px) | z_order |
| --- | --- | --- | --- | --- |
| `square` | polygon | (16, 32) | 64 x 64 | 1 |
| `arrow` | sprite_frame (4 frames) | (144, 48) | 32 x 32 | 0 |

Canvas is 256 x 128 px at `pixels_per_unit = 100`. The polygon sits
left, the arrow sits right; z_order 0 (arrow) lands closer to the
camera than z_order 1 (square) via the `Z_EPSILON` offset (D6).

## Skeleton

Stub armature with a single `root` bone (D3). Both meshes are parented
to the armature object via `parent_type='OBJECT'`.

## Building from source

Three stages: Pillow PNG generation, importer-driven `.blend` assembly,
golden `.proscenio` export.

```sh
# 1. Generate PNGs into pillow_layers/ (requires only Python + Pillow).
python scripts/fixtures/simple_psd/draw_layers.py

# 2. Assemble the .blend by running the addon importer on the manifest.
blender --background --python scripts/fixtures/simple_psd/build_blend.py

# 3. Generate the golden .proscenio at the fixture root.
blender --background examples/generated/simple_psd/simple_psd.blend \
    --python scripts/fixtures/_shared/export_proscenio.py
```

`run_tests.py` auto-discovers `simple_psd/` once the golden is in
place; no edit to the runner required.

## What this fixture catches when broken

- Manifest parser regression on `format_version`, `kind` discriminator,
  `frames[]` array, `position`/`size` shape.
- Polygon stamper regression: mesh size, world rect, UV layout.
- Sprite_frame stamper regression: spritesheet compose ordering, frame
  count, `hframes`/`vframes` tagging, full-canvas UV.
- Coordinate conversion regression (D6): PSD top-left vs Blender
  XZ-centred.
- Idempotent re-import: rerunning `build_blend.py` reuses meshes by
  `proscenio_import_origin` tag instead of duplicating.
