# Spec 031: Rigging and posing - TODO

Sequenced from the assessment in [STUDY.md](STUDY.md): the Drive-from-Bone rework that keeps the flagship driver from looking broken, the two IK items that protect the export, the headless Quick Armature suite, then the export-target display that waits on the export-correctness writer fix; the two retests ride the verification session. The Quick Armature precision cluster, the native-duplicating Skeleton items, and the pose-library evolutions are gated or dropped there with full reasoning.

## Now

### PR 1: Drive from Bone edits two ranges instead of a raw expression

- [ ] Add the four float fields (bone-rotation input range, target-value output range) to the driver PG in [object_props.py](../../apps/blender/properties/object_props.py), with defaults spanning negative rotation so the first driver no longer clamps at 0 - the exact first-contact failure the ui-feedback log records.
- [ ] Build the expression from the ranges in a pure helper (clamped linear map) consumed by the operator in [driver.py](../../apps/blender/operators/driver.py); unit-test the builder, including the negative-rotation default.
- [ ] Redraw the box in [_draw_driver_shortcut.py](../../apps/blender/panels/_draw_driver_shortcut.py): two range rows replace the expression field, with the raw string demoted to an Advanced fallback.
- [ ] Show the live driver value inline in the same box - the readout rides this PR; no Inspect popup, and re-clicking `Drive from Bone` stays the reset since the idempotent re-run already replaces the driver and purges stale siblings.
- [ ] Note in the PR: this closes both the expression-two-ranges and driver-readout-inspect-reset rows ([canonical entries](../backlog-ui-feedback.md#active-sprite-panel)).

### PR 2: Toggle IK wires a target

- [ ] Extend `Toggle IK` in [authoring_ik.py](../../apps/blender/operators/armature/authoring_ik.py) to wire `target`/`subtarget` when inserting the constraint, so the chain solves on its own instead of only while grabbing the constrained bone and the INFO bar stops punting to the Properties editor ([canonical entry](../backlog-ui-feedback.md#toggle-ik--ik-workflow)).
- [ ] Headless test in `apps/blender/tests/operators/`: toggling on yields a solving constraint with a target set; toggling off removes it cleanly.

### PR 3: the bake gate closes the silent IK export hole

- [ ] Add the export-validation check in [export.py](../../apps/blender/core/validation/export.py): an active-influence IK chain whose member bones carry no keyframes while animation drives the target - the case the writer exports as flat intermediate bones - reports an actionable error naming the chain ([canonical entry](../backlog-ui-feedback.md#toggle-ik--ik-workflow)).
- [ ] Add the `nla.bake` wrapper operator (bake the IK chain to bone keyframes over the action range) as the one-click fix the check points at.
- [ ] Headless tests: a keyed-target/unkeyed-chain scene trips the check, a baked scene passes; build the constrained fixture through the PR 2 toggle so the gate exercises the shipped wiring.

### PR 4: headless Quick Armature undo and axis-lock suite

- [ ] New suite under `apps/blender/tests/operators/` (driven by [run_operator_tests.py](../../apps/blender/tests/run_operator_tests.py)) exercising `_create_bone`, `_undo_last_bone`, `_redo_last_bone`, and `_post_process_world_point` from [quick_armature.py](../../apps/blender/operators/armature/quick_armature.py) - all callable without the modal event loop ([canonical entry](../backlog.md#quick-armature-follow-ups-deferred-polish)).
- [ ] Cover the in-modal undo/redo stack (create bones across chains, undo to empty, redo to full, names and parenting stable) and the snap-then-lock ordering of `_post_process_world_point` (grid snap before X/Z axis lock, Y pinned to 0).

### PR 5: the Skeleton panel names the export armature

Sequenced strictly after the writer-respects-the-picker fix in the [export-correctness spec](../027-export-correctness/STUDY.md) - naming the export target while `find_armature` ([scene_discovery.py](../../apps/blender/exporters/godot/writer/scene_discovery.py)) still returns the first armature in the scene would advertise a lie.

- [ ] Show the effective export armature in the **Skeleton** panel ([skeleton.py](../../apps/blender/panels/skeleton.py)): the picker's name when set, the writer's actual fallback choice when unset - completing the partial skeleton-armature-picker row ([canonical entry](../backlog-ui-feedback.md#skeleton-panel)).
- [ ] Re-read the picker tooltip in [scene_props.py](../../apps/blender/properties/scene_props.py) once the writer fix lands and align any copy that is still ahead of or behind the shipped behavior.

### Retests (verification session)

Both ride the cross-spec [verification session](../EXECUTION_MAP.md#verification-session-not-a-spec) - no code work here.

- [ ] Skeleton row-click selects the bone in the viewport - fix `dcd08f6` is in code; one GUI smoke confirms and closes the [bug entry](../backlog-bugs-found.md#skeleton-panel-row-click-no-uilist-não-seleciona-bone-no-viewport).
- [ ] Save Pose succeeds against a writable asset library and errors actionably without one - fix `7d10f69` is in code; one GUI smoke confirms and closes the [bug entry](../backlog-bugs-found.md#save-pose-to-library-unexpected-library-type-sem-orientação-ao-usuário).

## Deferred

All gated; no untriggered deferrals. Triggers from the assessment in [STUDY.md](STUDY.md).

- **Quick Armature rotation-mode choice** - gate; trigger: a quaternion-default rig measurably hurts authoring on a real character (the four opaque Graph Editor channels or a clumsy Drive-from-Bone target); export is already correct either way, and the keyframe-guarded safe-swap is risky.
- **Quick Armature pick-parent-in-viewport** - gate; trigger: a real rigging session shows mid-sketch reparenting often enough to pay for bone-tip hit-testing and a new chord in the saturated vocabulary.
- **Quick Armature chain-aware name suffixes** - gate; trigger: after-the-fact batch rename stops covering on a real multi-chain rig.
- **Quick Armature auto _L/_R suffix with X-Mirror** - gate; trigger: a bilaterally symmetric rig fixture ships end to end; mirrored create entangles the in-modal undo stack.
- **Drive from Bone sticky panel** - gate; trigger: re-measure the mesh-to-pose-bone swap pain after the two-ranges rework (PR 1) lands; proceed only if it still hurts, since the fix is a poll-architecture change.
- **Drive a slot attachment from a bone** - gate; trigger: a real rig asks for bone-driven attachment swaps; new driver target plus roundtrip burden until then.
- **IK chain helper** - gate; trigger: after the target wiring (PR 2) ships, a rigging session still asks for one-click target-plus-pole scaffolding.
- **IK round-trip (live constraints in Godot)** - gate; trigger: Godot's 2D SkeletonModification stack graduates from experimental and the flipped-rig bugs close; the bake gate (PR 3) covers the export need meanwhile.
- **Pose auto-categorise by armature** - gate; trigger: a second character's poses enter the library; native catalogs cover one rig.

## Dropped

Rationale from the assessment in [STUDY.md](STUDY.md), one line each.

- **Quick Armature preview-line clamp** - the red line plus "outside canvas" tooltip shipped as the accepted option; the clamp half is cosmetic geometry on a modal.
- **Quick Armature numeric length entry** - a text-entry state machine inside the modal; Edit Mode <kbd>E</kbd> plus typed length already covers precision one <kbd>Tab</kbd> away.
- **Quick Armature local-axis lock** - local equals global in the XZ-locked, origin-anchored workflow; the double-press distinction has no reachable case.
- **Quick Armature defaults help topic** - field tooltips self-describe; the existing quick_armature topic is the home.
- **Skeleton inline bone rename** - row-click owns the click; row-click plus <kbd>F2</kbd> is the native rename path.
- **Skeleton bone-collection management** - duplicates the native Bone Collections panel one editor away.
- **Skeleton richer hierarchy editing** - Edit Mode is the hierarchy editor; the readout is read-only by design.
- **IK/FK runtime switch** - a film-rig technique; export is baked and the toggle covers authoring, so a runtime switch has no consumer.
- **Pose apply-to-selection** - the native Asset Shelf apply already targets selected bones.
- **Pose thumbnails via the preview camera** - native auto-preview ships with pose assets; flat-render swatches are cosmetic.
