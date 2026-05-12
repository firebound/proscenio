# blink_eyes fixture (SPEC 007)

Tests the **`sprite_frame` track type** end-to-end: a Blender mesh
tagged as sprite_frame, its `frame` property animated through a Blender
action, and the writer emitting a `sprite_frame` animation track in the
resulting `.proscenio`.

## Directory layout

The fixture is split by **role in the pipeline**: `.blend` at the root is the source-of-truth; everything in subfolders is regenerable from it (or, for procedural fixtures like this one, from the matching script).

```text
examples/generated/blink_eyes/
├── blink_eyes.blend                       [SOURCE - built by build_blend.py from pillow_layers/]
├── blink_eyes.expected.proscenio          [GOLDEN - CI-diffed validation midpoint]
├── pillow_layers/                         [DERIVED - Pillow draws each frame + spritesheet]
│   ├── eye_0.png         32x32 - eye open
│   ├── eye_1.png         32x32 - partially closing
│   ├── eye_2.png         32x32 - nearly closed
│   ├── eye_3.png         32x32 - fully closed
│   └── eye_spritesheet.png   128x32 - concatenation, the texture the mesh references
└── godot/
    ├── BlinkEyes.tscn                     Godot wrapper
    └── BlinkEyes.gd                       empty stub
```

## Why both per-frame PNGs and a spritesheet?

- The **spritesheet** (`eye_spritesheet.png`) is what the sprite_frame
  mesh references at runtime. `hframes=4`, `vframes=1` slice it.
- The **per-frame PNGs** are kept around so SPEC 006's
  `<name>_<index>` Photoshop-layer convention can be tested by re-
  packing them into the sheet (the expected workflow once the importer
  ships).

## Skeleton

Single-bone armature: `head`. The `eye` mesh is parented to it (no skinning).

## Action

`blink` - 12 frames, animates `eye.proscenio.frame`:

```text
1  -> 0
3  -> 1
5  -> 2
7  -> 3
9  -> 2
11 -> 1
12 -> 0
```

Eye opens-closes-opens. The writer should emit a single `sprite_frame`
track on the `eye` target with these keys.

## Building from source

Two-stage: PNG generation runs without Blender, `.blend` assembly runs in headless Blender.

```sh
# 1. Generate PNGs into pillow_layers/ (requires only Python + Pillow).
python scripts/fixtures/blink_eyes/draw_layers.py

# 2. Assemble the .blend.
blender --background --python scripts/fixtures/blink_eyes/build_blend.py

# 3. Generate the golden .proscenio under godot/.
blender --background examples/generated/blink_eyes/blink_eyes.blend \
    --python scripts/fixtures/_shared/export_proscenio.py
```

## What this fixture catches when broken

- Writer regression on `sprite_frame` track emission.
- Sprite_frame metadata mishandling (`hframes`, `vframes`, `frame`, `centered`).
- Sliced atlas packer regression - the spritesheet has a clear visible
  content area; if Pack/Apply puts UVs in the wrong place, the eye
  preview in Blender will obviously be in the wrong slot.
- Region-mode (auto / manual) regression - sprite_frame `texture_region`
  should be omitted in auto mode, set explicitly after Apply Packed Atlas.
