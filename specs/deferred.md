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

- **test-godot generic golden walk (partial - the drift + focused guards landed)** - The `test-godot` CI job now runs `sync_fixtures.py` to populate `apps/godot/examples/`, the drifting `tests/fixtures/mixed_feature.proscenio` copy is retired, and [test_golden_scenes.gd](../apps/godot/tests/test_golden_scenes.gd) walks the real baked `mixed_feature` + `mouth_drive` goldens with focused regression guards (the four bugs that slipped: bone/sprite name collision, slot anchor at the cumulative rest, parent-local animation delta, sprite-frame wrap). Still deferred: a GENERIC walk over all eight goldens with broad sane-tree asserts (counts, kinds, weights, slots, tracks), plus the audit of the four remaining hand-authored fixtures (`dummy`, `effect`, `skinned_dummy`, `slots_demo`) - those have no baked equivalent, so they stay until a generic walk subsumes them. A headless assert still cannot catch a visually-wrong-but-structurally-consistent export, so the generic breadth rides the next test-godot touch rather than blocking.

## Photoshop overhaul

(2026-06-16: **multiGet document reader** promoted to the backlog; 2026-06-18: shipped in spec 048 - async reader behind the DOM-walk fallback, validated against a real PSD in a live session and threaded through both read paths.)

- **shared adaptation per tick / lazy preview (narrowed - the multiGet reader landed)** - The spec-048 live session (2026-06-18) landed the async multiGet reader behind the DOM-walk fallback and threaded it through BOTH read paths (`useTagTree` and `useExportPreview` via `previewExportAsync`), so the redundant second walk per `version` bump is now two cheap one-round-trip reads rather than two slow per-property DOM walks. Still deferred: collapsing those into a SINGLE `adaptDocument` snapshot per tick that feeds the tag tree, the export preview, and the active-layer consumers from one read. That last redundancy is a React-hook timing refactor only a real panel can validate; with both paths already on the fast read the remaining win is small, so it rides the next read-path touch rather than triggering its own session.

(2026-06-16: **scope the busy flag off the whole tag list** promoted to [backlog.md](backlog.md#fila-da-sprint) as a quick win - it was tagged "cheap and self-contained".)

The full IPC perf diagnosis (root cause, community references, per-entry scope sketches) lived in a photoshop-performance backlog file, deleted when the photoshop-overhaul work shipped; recover it from git history if the multiGet work needs the references.
