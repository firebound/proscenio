# Spec 032: Slot attachments - TODO

Sequenced from [STUDY.md](STUDY.md): the blocking placement fix first, then the authoring button and the draw-only panel pass. The non-blocking rows are post-release wave 4 in [EXECUTION_MAP.md](../EXECUTION_MAP.md); inside this spec they run after the blocking chunk.

## Now

### Chunk 1 - slot placement matrix fix (blocking; one fix closes both bugs)

- [x] Compute the world-space geometry center of the selected meshes (`bound_box` corners through `matrix_world`) and write it through `empty.matrix_world` after parenting, replacing the world-into-local `empty.location` assignment ([create.py](../../apps/blender/operators/slot/create.py))
- [x] Headless tests: parented-seed and unapplied-origin fixtures asserting the Empty's world translation lands at the geometry center (and that attachments keep their world transforms via `parent_keep_world`)
- [ ] GUI confirmation on the logged repros: slot_swap_workbench multi-select Path B, and a mesh with origin at world zero and offset geometry

### Chunk 2 - keyframe the active attachment

- [x] Operator: set `proscenio_slot_index` to the chosen attachment's index and `keyframe_insert` on that custom-property data path with constant interpolation, surfaced as a button in the **Active Slot** subpanel ([attachment.py](../../apps/blender/operators/slot/attachment.py), [slots.py](../../apps/blender/panels/slots.py))
- [x] Headless test: invoking on a slot with an action produces exactly the fcurve key the writer already projects ([slot_animations.py](../../apps/blender/exporters/godot/writer/slot_animations.py) contract)
- [ ] GUI smoke: key two attachment swaps, export, confirm the swap plays in Godot (rides the existing slot_cycle/slot_swap verification pass)

### Chunk 3 - panel affordances (draw-only, one PR)

- [x] Inline hint above `Create Slot` naming the two context behaviors: Pose Mode + bone gives a bone-parented slot, Object Mode + meshes gives a wrapping slot ([slots.py](../../apps/blender/panels/slots.py))
- [x] Unparented-slot warning row in the **Active Slot** subpanel ("slot has no parent bone - attachments will not follow any bone"), sharing the predicate from the validator slot-no-parent-bone fix in the export-correctness spec instead of forking a second rule

## Deferred

- Native UIList for the slots list - consistency-only; the selection-sync cost is demonstrated by the Skeleton panel UIList fix still sitting in needs-retest.
- `Parent to Bone` fix button on the unparented warn - a new bone-picker operator; the warning plus native parenting covers it until a session log shows otherwise.
- Skin coordination - gate: a real character ships two or more costume variants on one rig (in Firebound or a user report); the first-class `skins[]` shape additionally waits on the format-migration path from the schema-expressiveness spec, while the additive generated-animations shape can land without it but carries override-fragile runtime semantics. Until the trigger fires, per-slot defaults plus the keyframe button cover single-variant work.

## Dropped

- None - every row traces to logged first-party feedback or a shipped-contract gap; the speculative one is gated above.
