# slot_cycle fixture (SPEC 004)

Smallest end-to-end exercise of the **slot system**: one armature, one slot Empty, three colored attachment polygons, one cycling action. Used to test the writer's `slots[]` + `slot_attachment` track emission and the Godot importer's `Node2D` parent + visibility-toggled child runtime shape.

## Directory layout

```text
examples/slot_cycle/
├── slot_cycle.blend                      [SOURCE -- built by build_blend.py from pillow_layers/]
├── slot_cycle.expected.proscenio         [GOLDEN -- CI-diffed validation midpoint]
├── pillow_layers/                        [DERIVED -- Pillow draws the 3 colored squares]
│   ├── attachment_red.png                32x32 -- slot default
│   ├── attachment_green.png              32x32
│   └── attachment_blue.png               32x32
└── godot/
    ├── SlotCycle.tscn                    Godot wrapper
    └── SlotCycle.gd                      autoplay stub
```

## Slot setup

| Component | Value |
| --- | --- |
| Armature | `slot_cycle.armature` (single `root` bone) |
| Slot Empty | `cycle.slot` (parent_type=OBJECT to armature) |
| `is_slot` | True |
| `slot_default` | `attachment_red` |
| Attachments | `attachment_red` / `attachment_green` / `attachment_blue` (parent_type=OBJECT to the Empty) |

The Empty is **object-parented** (not bone-parented) to the armature -- bone-parenting rotates child meshes to align with the bone direction, which would tilt the XZ-plane attachments out of the screen plane. The doll fixture follows the same pattern (parent_type=OBJECT, weighting via vertex groups).

## Action

`cycle` -- 24 frames keyframing `obj["proscenio_slot_index"]` per second:

```text
1  -> 0 (red)
8  -> 1 (green)
16 -> 2 (blue)
24 -> 0 (red, loop)
```

The writer reads each fcurve key, maps the integer index to the slot's `attachments[]` list, and emits a `slot_attachment` track with constant interpolation. The Godot importer expands that track to N visibility tracks at runtime (one `:visible` per attachment).

## Building from source

Two stages: Pillow PNG generation, headless Blender assembly.

```sh
# 1. Generate the 3 colored 32x32 PNGs into pillow_layers/.
python scripts/fixtures/slot_cycle/draw_layers.py

# 2. Assemble the .blend.
blender --background --python scripts/fixtures/slot_cycle/build_blend.py

# 3. Generate the golden .proscenio at the fixture root.
blender --background examples/slot_cycle/slot_cycle.blend \
    --python scripts/fixtures/_shared/export_proscenio.py
```

`run_tests.py` auto-discovers `slot_cycle/` once the golden is in place.

## What this fixture catches when broken

- Writer regression on `slots[]` emission (slot name, default fallback, attachments list).
- Writer regression on `slot_attachment` track emission (key time conversion frame->seconds, index->attachment name mapping, constant interp).
- Importer regression on `Node2D` slot anchor placement (under bone or skeleton root).
- Importer regression on attachment routing (sprite under slot Node2D, not under bone).
- Default-attachment visibility (red visible at scene load, green + blue hidden).
- Animation track expansion (slot_attachment -> N visibility tracks, NEAREST interp).
