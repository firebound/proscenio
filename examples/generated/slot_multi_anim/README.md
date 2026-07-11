# slot_multi_anim fixture

Isolation fixture for **per-animation slot swaps** (spec 079 core): one slot
Empty that carries a DIFFERENT attachment-visibility timeline per animation -
the case single-active-action reading could not express.

- 1 polygon mesh `arm` (32x8 forearm, skinned to bone `arm`)
- 1 armature `arm_rig` with bone `arm` (lateral, in the XZ picture plane)
- 1 slot Empty `weapon` bound to bone `arm`;
  `proscenio_is_slot=True`, `proscenio_slot_default="club"`
- 2 attachments parented to the slot Empty:
  - `club` (32x32 polygon mesh, club.png) - the default
  - `torch` (32x32 polygon mesh, torch.png)
- 2 animations, authored on the Blender 4.4+ slotted-action model (each an
  independent action datablock, kept alive with a fake user):
  - `idle` - both attachments hidden the whole clip -> the writer collapses to
    the `(none)` sentinel. No bone motion.
  - `attack` - `club` shown, `torch` hidden, plus a gentle `arm` swing, so the
    animation carries a `bone_transform` track that the slot track merges onto.

Each attachment holds its own `hide_render` channelbag in BOTH action
datablocks (on its own action slot), even though its active binding ends on
`attack`; the writer scans every action and matches each mesh's slot by
identity, so it recovers both timelines. The golden proves it: `idle` exports a
`slot_attachment` track of `(none)`, `attack` exports one of `club`.

## Directory layout

```text
examples/generated/slot_multi_anim/
├── slot_multi_anim.blend                  [SOURCE - built by build_blend.py]
├── slot_multi_anim.expected.proscenio     [GOLDEN - CI-diffed validation midpoint]
├── pillow_layers/                         [DERIVED - Pillow draws the 3 layers]
│   ├── arm.png        32x8  - horizontal forearm
│   ├── club.png       32x32 - club attachment
│   └── torch.png      32x32 - torch attachment
└── godot/
    ├── SlotMultiAnim.tscn                  Godot wrapper
    └── SlotMultiAnim.gd                    plays "attack" at runtime
```

## Rebuilding the fixture

```bash
python packages/fixtures/slot_multi_anim/draw_layers.py
blender --background --python packages/fixtures/slot_multi_anim/build_blend.py
```

After rebuilding, regenerate the golden via the writer so
`apps/blender/tests/run_tests.py` keeps passing:

```bash
blender --background examples/generated/slot_multi_anim/slot_multi_anim.blend \
    --python packages/fixtures/_shared/export_proscenio.py
```

## Manual testing flow

1. Open `slot_multi_anim.blend` in Blender (after enabling the addon).
2. In the Action editor, switch the active animation between `idle` and
   `attack`; the viewport should show no weapon on `idle` and the club on
   `attack` (visibility previews natively - no handler).
3. Scrub `attack` - the arm swings and the club rides the bone tip.
```
