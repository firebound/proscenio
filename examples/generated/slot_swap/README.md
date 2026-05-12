# slot_swap fixture

Minimal isolation fixture for the **slot system**: a pseudo-arm that
swings while its weapon attachment swaps mid-animation.

- 1 polygon mesh `arm` (16x32 pseudo-arm sprite, parented to bone)
- 1 armature `arm_rig` with bone `arm` (perpendicular to the XZ
  picture plane, tail toward the Front Ortho camera)
- 1 slot Empty `weapon` parented to the bone tip;
  `proscenio.is_slot=True`, `proscenio.slot_default="club"`
- 2 attachments parented to the slot Empty:
  - `club` (32x32 polygon mesh, club.png)
  - `sword` (32x32 polygon mesh, sword.png)
- 2 actions named `swing` (one on the armature, one on the slot
  Empty - Blender renames the second to `swing.001` due to the
  global uniqueness constraint):
  - Arm bone: Y rotation -pi/6 -> +pi/6 -> -pi/6 over 24 frames
  - Slot Empty: `proscenio_slot_index` 0 (club) -> 1 (sword) -> 0
    (club), constant interpolation

## Directory layout

```text
examples/generated/slot_swap/
├── slot_swap.blend                       [SOURCE - built by build_blend.py]
├── slot_swap.expected.proscenio          [GOLDEN - CI-diffed validation midpoint]
├── pillow_layers/                        [DERIVED - Pillow draws the 3 attachments]
│   ├── arm.png        32x8  - horizontal forearm
│   ├── club.png       32x32 - club attachment
│   └── sword.png      32x32 - sword attachment
└── godot/
    ├── SlotSwap.tscn                     Godot wrapper
    └── SlotSwap.gd                       empty stub
```

## Why dedicated PNGs per attachment

The slot system swaps **discrete meshes**, not cells of a shared
spritesheet. Each attachment owns its mesh + its own material +
its own image texture. A spritesheet would imply
`sprite_frame`-style frame-index swapping inside one mesh; that's
the `blink_eyes` / `mouth_drive` story, not this one.

## Rebuilding the fixture

```bash
py scripts/fixtures/slot_swap/draw_layers.py
blender --background --python scripts/fixtures/slot_swap/build_blend.py
```

After rebuilding, regenerate the golden via the writer so
`apps/blender/tests/run_tests.py` keeps passing.

## Manual testing flow

1. Open `slot_swap.blend` in Blender (after enabling the addon).
2. **Save As** `slot_swap_workbench.blend` to keep the canonical
   fixture untouched.
3. Press play on the timeline - arm should swing left/right, and
   the weapon attachment should swap from club to sword at the apex
   of the swing.
4. Select the `weapon` Empty - the **Active Slot** subpanel should
   appear with `club` and `sword` listed as attachments, club marked
   as the default.
5. (Optional) Toggle the default attachment to `sword` via the
   star icon on the panel; re-play to see the new starting state.
