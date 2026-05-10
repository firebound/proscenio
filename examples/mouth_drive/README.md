# mouth_drive fixture

End-to-end fixture for the **Drive from Bone** feature, structured to
match the typical 2D cutout authoring layout:

- 1 sprite_frame mesh `mouth` (4 cells, 32x32 each, 128x32 spritesheet)
- 1 armature `mouth_rig` with **two horizontal bones** (lying along
  world X, the front-ortho 2D plane):
  - `mouth_pos` -- positions the mouth in 2D space; the sprite mesh
    is parented to it.
  - `mouth_drive` -- driver source; rotation around its Z axis is
    wired (via a pre-installed Scripted driver) to
    `mouth.proscenio.frame`.
- 1 action `mouth_drive_anim` keyframing `mouth_drive` rotation
  -pi/2 -> +pi/2 -> 0 over 24 frames, cycling the sprite through
  all 4 mouth shapes via the driver. `mouth_pos` exists structurally
  (the sprite is parented to it) but currently stays at rest --
  see tests/BUGS_FOUND.md for the writer-side issue that drops
  pose-location Z for horizontal bones.

The driver mirrors what the **Drive from Bone** panel operator
produces: `transform_space=WORLD_SPACE`, `rotation_mode=XYZ`,
expression `var * 2 + 2`. Re-running the operator on this fixture
should be idempotent (replaces the existing driver, same wiring).

## Directory layout

The fixture is split by **role in the pipeline**: `.blend` at the root
is the source-of-truth; everything in subfolders is regenerable from
it (or, for procedural fixtures like this one, from the matching
script).

```text
examples/mouth_drive/
├── mouth_drive.blend                       [SOURCE -- built by build_blend.py from pillow_layers/]
├── mouth_drive.expected.proscenio          [GOLDEN -- CI-diffed validation midpoint]
├── pillow_layers/                          [DERIVED -- Pillow draws each frame + spritesheet]
│   ├── mouth_0.png        32x32 -- mouth open
│   ├── mouth_1.png        32x32 -- mid-open with tongue
│   ├── mouth_2.png        32x32 -- closed (lip line)
│   ├── mouth_3.png        32x32 -- talking shape
│   └── mouth_spritesheet.png   128x32 -- concatenation, the texture the mesh references
└── godot/
    ├── MouthDrive.tscn                     Godot wrapper (instances the imported scene)
    └── MouthDrive.gd                       empty stub
```

## Why both per-frame PNGs and a spritesheet?

- The **spritesheet** (`mouth_spritesheet.png`) is what the
  sprite_frame mesh references at runtime. `hframes=4`, `vframes=1`
  slice it in both Blender (preview shader) and Godot (`Sprite2D`).
- The **per-frame PNGs** are kept around as authoring-side documentation
  and to make visual diffs in PRs readable (binary spritesheet diffs
  in code review are useless).

## Rebuilding the fixture

```bash
py scripts/fixtures/mouth_drive/draw_layers.py
blender --background --python scripts/fixtures/mouth_drive/build_blend.py
```

The first step regenerates the PNGs (Pillow only, no Blender). The
second step rebuilds the `.blend` from the PNGs and saves it with a
**relative** image filepath (`//pillow_layers/mouth_spritesheet.png`)
so the fixture works cross-machine.

After rebuilding, regenerate the golden via the writer (any of the
existing helper scripts) so `apps/blender/tests/run_tests.py` keeps
passing.

## Manual testing flow

1. Open `mouth_drive.blend` in Blender (after enabling the addon).
2. **Save As** `mouth_drive_workbench.blend` to keep the canonical
   fixture untouched.
3. Press play on the timeline -- the action should drive both
   `mouth_pos` (vertical bob) and `mouth_drive` (rotation), and the
   sprite cell should cycle through frames 0..3 as `mouth_drive`
   rotates.
4. Stop playback. Select the `mouth` mesh, click **Setup Preview**
   in the Active Sprite panel to see the slicer shader in viewport.
5. Enter Pose mode on `mouth_rig`, select `mouth_drive`, R Z to
   rotate manually -- watch the sprite cell change live.
6. Re-author the driver: select `mouth` mesh, in Active Sprite >
   Drive from Bone, click **Drive from Bone** with the panel's
   pre-filled values. Should be idempotent: same wiring, sprite
   keeps responding to bone rotation.
