# Deferred work

Items with real value, sequenced for a second stage but not held behind a written trigger (those are in [gated.md](gated.md)). The difference from a gate: a deferred item is scheduled work waiting its turn, usually to ride a related change so its cost is shared, whereas a gate waits on a demand signal that may never come. Carved out during the 2026-06-11 reconciliation (the durable number-to-topic map is [_index.md](_index.md)). Companion homes: [dropped.md](dropped.md) (value below cost), [decisions.md](decisions.md) (locked calls).

## Schema expressiveness

- **sprite-appearance (blend-mode half)** - Emit the `proscenio_blend_mode` Custom Property the Blender material already carries onto elements, and map it to a `CanvasItemMaterial` (additive / multiply / subtract), downgrading screen / overlay to normal with a warning. Deferred (not gated): the value is already upstream (the PSD manifest plus the `proscenio_blend_mode` stamp), so this is bounded Wave-1 work rather than new capability. It is second-stage because `CanvasItemMaterial` covers add/multiply/subtract but not screen/overlay, so PSD parity needs a documented downgrade rather than a day-one ship. (The light appearance half - modulate / z_index / flip - shipped in #105.)

(2026-06-16: **node-name-collision-polish** promoted to [backlog.md](backlog.md#fila-da-sprint).)

## Slot attachments

(2026-06-16: **slots-native-uilist** promoted to [backlog.md](backlog.md#fila-da-sprint).)

- **slot-no-bone fix button** (the deferred half of the shipped warn-only `slot-no-bone-warning`; no separate backlog row) - A one-click "Parent to Bone" remedy beside the unparented-slot warning. Deferred: the warning shipped sharing the validator predicate, but the fix needs a new bone-picker operator, so it follows once the warn surface has soaked.

## Atlas packing

- **shrink-start-size** - Shrink-to-fit / configurable atlas start size (the `start_size=256` floor at `atlas_packer.py:65` is never passed and has no scene prop). Deferred: atlas waste is real only at fixture scale, so the change rides the next packer-touching PR to share the fixture regeneration rather than triggering one of its own.

## Example fidelity

- **test-godot builds against the real baked goldens** - Drive the Godot smoke test from the Blender-baked goldens (`examples/generated/**/*.expected.proscenio`) instead of hand-authored copies: run `sync_fixtures.py` in the `test-godot` CI job to populate `apps/godot/examples/`, then have [test_importer.gd](../apps/godot/tests/test_importer.gd) walk the synced goldens and assert the builders produce a sane node tree (counts, kinds, weights, slots, tracks). Audit the four hand-authored fixtures (`dummy`, `effect`, `skinned_dummy`, `slots_demo`), keep only the genuine edge cases the baked goldens do not cover, and retire the committed `tests/fixtures/mixed_feature.proscenio` copy in favour of its synced golden (today it drifts: it still carries four bones with no chain while the source has five chained). Deferred: the open/render/animate fidelity shipped, and this is the test-infra half that closes the golden-copy drift and the writer-to-builder end-to-end gap; a headless assert still cannot catch a visually-wrong-but-structurally-consistent export, so it rides the next test-godot touch rather than blocking. The `.scratch/render_proof.gd` runtime harness used through the grind can seed it. (2026-06-16: re-verified still not done - the `test-godot` CI job does not run `sync_fixtures.py`, `test_importer.gd` still walks the hand-authored `apps/godot/tests/fixtures/*.proscenio`, and `mixed_feature.proscenio` is still committed there.)

## Photoshop overhaul

(2026-06-16: **multiGet document reader** promoted to [backlog.md](backlog.md#fila-da-sprint). Spec 041 reworked the PS plugin but deliberately deferred multiGet - the index line says so ("multiGet + dedup deferred"); it is now pulled into the sprint.)

- **shared adaptation per tick / lazy preview** - Adapt the document once per `version` bump and feed the tag-tree + export-preview + active-layer consumers from one snapshot (or defer the preview off the tag-paint path). Deferred: it removes the redundant second walk per event, but it is React-hook timing only a real panel can validate; the layerID-key + adaptive-poll wins already cut the felt jank. Its sibling (multiGet reader) was promoted to the backlog on 2026-06-16; this one rode the same session, so consider pulling it along when the multiGet work is scheduled.

(2026-06-16: **scope the busy flag off the whole tag list** promoted to [backlog.md](backlog.md#fila-da-sprint) as a quick win - it was tagged "cheap and self-contained".)

The full IPC perf diagnosis (root cause, community references, per-entry scope sketches) lived in a photoshop-performance backlog file, deleted when the photoshop-overhaul work shipped; recover it from git history if the multiGet work needs the references.
