# blink_eyes fixture (SPEC 007)

Tests the **`sprite_frame` track type** end-to-end: a Blender mesh
tagged as sprite_frame, its `frame` property animated through a Blender
action, and the writer emitting a `sprite_frame` animation track in the
resulting `.proscenio`.

## Contents (after running the build script)

```
blink_eyes/
├── layers/
│   ├── eye_0.png         32x32 — eye open
│   ├── eye_1.png         32x32 — eye partially closing
│   ├── eye_2.png         32x32 — eye nearly closed
│   └── eye_3.png         32x32 — eye fully closed
├── eye_spritesheet.png   128x32 — concatenation of the 4 frames (the actual texture)
├── blink_eyes.blend
├── blink_eyes.expected.proscenio    golden — CI diffs against re-export
├── BlinkEyes.tscn                   Godot wrapper
└── BlinkEyes.gd                     empty stub
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

`blink` — 12 frames, animates `eye.proscenio.frame`:

```
1  → 0
3  → 1
5  → 2
7  → 3
9  → 2
11 → 1
12 → 0
```

Eye opens-closes-opens. The writer should emit a single `sprite_frame`
track on the `eye` target with these keys.

## Building from source

```bash
blender --background --python scripts/fixtures/build_blink_eyes.py
```

## What this fixture catches when broken

- Writer regression on `sprite_frame` track emission.
- Sprite_frame metadata mishandling (`hframes`, `vframes`, `frame`, `centered`).
- Sliced atlas packer regression — the spritesheet has a clear visible
  content area; if Pack/Apply puts UVs in the wrong place, the eye
  preview in Blender will obviously be in the wrong slot.
- Region-mode (auto / manual) regression — sprite_frame `texture_region`
  should be omitted in auto mode, set explicitly after Apply Packed Atlas.
