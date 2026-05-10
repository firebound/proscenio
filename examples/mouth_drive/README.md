# mouth_drive fixture

Minimal isolation fixture for the **Drive from Bone** feature:

- 1 sprite_frame mesh `mouth` (4 cells, 32x32 each, 128x32 spritesheet)
- 1 armature `mouth_rig` with bone `mouth_drive`
- Mesh parented to the bone (`parent_type=BONE`)
- **No driver pre-installed** -- the fixture is meant to be opened and
  the user manually invokes the "Drive from Bone" panel operator on
  the Blender side. After authoring, the round-trip emits a
  `bone_transform` track that the Godot importer expands into an
  AnimationPlayer track on the imported scene.

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
3. Select the `mouth` mesh in Object mode.
4. In the Active Sprite panel, scroll to **Drive from Bone**:
   - Pick `mouth_rig` as the Armature.
   - Pick `mouth_drive` as the Bone.
   - Pick `Region X` (or `Frame index`) as the Target.
   - Click **Drive from Bone**.
5. Switch to Pose mode on the armature, rotate `mouth_drive` around Z,
   and watch the sprite cell update live (with `Setup Preview` enabled
   on the mesh).
