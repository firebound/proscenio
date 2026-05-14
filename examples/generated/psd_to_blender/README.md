# psd_to_blender fixtures

End-to-end inputs + goldens for the **PSD -> Blender** half of the Proscenio pipeline. Each fixture exercises one slice of the SPEC 006 + SPEC 011 path that turns a PSD (or its captured manifest) into a Blender scene.

The bucket name follows the direction of the data: a PSD on disk is the source, a `.blend` is the consumer. Tests live with the plugin (`apps/photoshop/uxp-plugin-tests/*`) and run via vitest; manifest-schema-level tests live under `tests/test_*.py` and run via pytest.

## Contents

| Fixture | What it covers |
| --- | --- |
| [`tag_smoke/`](tag_smoke/) | SPEC 011 v1 tag taxonomy parity oracle (synthetic input). Every bracket tag exercised in one layer tree; the captured `tag_smoke.expected.json` becomes the planner's regression baseline. |

## Relationship to other fixture buckets

The procedural fixtures under `examples/generated/` originally sat in a flat layout. The `psd_to_blender/` and (forthcoming) `blender_to_godot/` subdirectories split them by pipeline direction so new tests land in the right bucket without forcing a one-shot relocation of every existing fixture. The pre-existing fixtures (`atlas_pack/`, `blink_eyes/`, `mouth_drive/`, `shared_atlas/`, `simple_psd/`, `slot_cycle/`, `slot_swap/`) all belong to the `blender_to_godot/` direction; they remain at the flat top level for now and will migrate when the cost of leaving them is higher than the cost of the rename ripple (see [`scripts/fixtures/README.md`](../../../scripts/fixtures/README.md) for the script-side index).

> A fixture without a downstream golden is a fixture in name only. Every entry under this bucket must commit a frozen output (manifest, `.proscenio`, or snapshot JSON) and a test that re-runs the producer and diffs against it.
