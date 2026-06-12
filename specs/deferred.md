# Deferred work

Items with real value, sequenced for a second stage but not held behind a written trigger (those are in [gated.md](gated.md)). The difference from a gate: a deferred item is scheduled work waiting its turn, usually to ride a related change so its cost is shared, whereas a gate waits on a demand signal that may never come. Carved out of specs 027-035 during the 2026-06-11 reconciliation (those specs shipped their near-term work and their folders were pruned; see [_index.md](_index.md)). Companion homes: [dropped.md](dropped.md) (value below cost), [decisions.md](decisions.md) (locked calls).

## 028 - schema-expressiveness

- **sprite-appearance (blend-mode half)** - Emit the `proscenio_blend_mode` Custom Property the Blender material already carries onto elements, and map it to a `CanvasItemMaterial` (additive / multiply / subtract), downgrading screen / overlay to normal with a warning. Deferred (not gated): the value is already upstream (the PSD manifest plus the `proscenio_blend_mode` stamp), so this is bounded Wave-1 work rather than new capability. It is second-stage because `CanvasItemMaterial` covers add/multiply/subtract but not screen/overlay, so PSD parity needs a documented downgrade rather than a day-one ship. (The light appearance half - modulate / z_index / flip - shipped in #105.)
- **node-name-collision-polish** - Document the `_001` collision-suffix convention instead of prefixing node names. Deferred: the suffixes are purely cosmetic, and prefixing node names would churn the track-target lookups that resolve by name, so the lower-risk answer is a documentation pass scheduled alongside the next Godot-importer touch.

## 032 - slot-attachments

- **slots-native-uilist** - Standardize the slots list to a native `template_list` / UIList. Deferred: it swaps working per-row buttons for a widget whose selection sync already cost a fix on the Skeleton panel (still needs-retest), so the gain is consistency only; it rides the next slots-panel touch rather than triggering its own.
- **slot-no-bone fix button** (the deferred half of the shipped warn-only `slot-no-bone-warning`; no separate backlog row) - A one-click "Parent to Bone" remedy beside the unparented-slot warning. Deferred: the warning shipped sharing the validator predicate, but the fix needs a new bone-picker operator, so it follows once the warn surface has soaked.

## 033 - atlas-packing

- **shrink-start-size** - Shrink-to-fit / configurable atlas start size (the `start_size=256` floor at `atlas_packer.py:65` is never passed and has no scene prop). Deferred: atlas waste is real only at fixture scale, so the change rides the next packer-touching PR to share the fixture regeneration rather than triggering one of its own.
