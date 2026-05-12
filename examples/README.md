# Examples

Fixtures used by the Proscenio test harness + as on-disk documentation for the pipeline. Two tiers, kept in separate places so contributors can tell at a glance which fixtures are regenerable and which require hand-editing.

## Tier 0 - Hand-authored sources (`examples/authored/`)

Fixtures created and maintained by hand in Blender. Treat the `.blend` as the source-of-truth - there is no script that rebuilds it. Modifications happen interactively, with explicit regeneration of every derived artefact (render layers, photoshop manifest, goldens) afterwards.

- [`authored/doll/`](authored/doll/) - canonical SPEC 004 + SPEC 006 character rig. Body parts as polygon meshes, skinned to an Armature; lives at the centre of the Blender ↔ Photoshop authoring loop.

The `authored/` subdirectory exists specifically to telegraph this asymmetry. New hand-authored fixtures land there too.

## Tier 1 - Procedural fixtures (`examples/generated/`)

Fixtures rebuilt from a script under [`scripts/fixtures/<name>/`](../scripts/fixtures/) (Pillow + headless Blender). Safe to delete and regenerate. Each isolates one feature end-to-end so a regression has a small, named blast radius.

| Fixture | Feature exercised |
|---|---|
| [`generated/atlas_pack/`](generated/atlas_pack/) | atlas packer (Pack / Apply / Unpack), 9 distinct sprites with own textures |
| [`generated/blink_eyes/`](generated/blink_eyes/) | `sprite_frame` animation track type |
| [`generated/mouth_drive/`](generated/mouth_drive/) | `sprite_frame` + Drive-from-Bone (driver-driven frame index) |
| [`generated/shared_atlas/`](generated/shared_atlas/) | multi-sprite shared atlas, region slicing |
| [`generated/simple_psd/`](generated/simple_psd/) | PSD manifest import (procedural manifest, no real Photoshop) |
| [`generated/slot_cycle/`](generated/slot_cycle/) | slot system, 3 attachments cycling |
| [`generated/slot_swap/`](generated/slot_swap/) | slot system + bone rotation (swing + weapon swap in one action) |

The conventions for adding a new procedural fixture live in [`scripts/fixtures/README.md`](../scripts/fixtures/README.md).

## Discovery

`apps/blender/tests/run_tests.py` walks every subdirectory of `examples/` that contains an `<name>.expected.proscenio` golden and pairs it with the matching `<name>.blend`. The runner handles both `authored/` and `generated/` nesting transparently via recursive glob - adding new fixtures under either tree is the same registration step.
