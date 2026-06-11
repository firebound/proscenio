# Spec 027: Export correctness - TODO

Sequenced from the assessment in [STUDY.md](STUDY.md): all five verdicts are now. The three small unit-coverable chunks land first, then the multi-polygon chunk last as the one cross-app PR touching the wire shape; the single GUI confirmation rides the already-planned verification session.

## Now

### PR 1: one picker-first armature resolver for writer and validator

- [ ] Add a shared picker-first resolver: prefer `scene.proscenio.active_armature`, fall back to first ARMATURE in scene order, guarding the headless path (`scene.proscenio` unregistered under `--background`) and stale pointers (picker object deleted or no longer an ARMATURE in this scene).
- [ ] Route `find_armature` ([`scene_discovery.py`](../../apps/blender/exporters/godot/writer/scene_discovery.py)) through the resolver so the writer exports the armature the user picked.
- [ ] Route the `available_bones` derivation in `validate_export` ([`export.py`](../../apps/blender/core/validation/export.py)) through the same resolver so validate and export agree in multi-armature scenes.
- [ ] Unit tests: picker wins over scene order; stale pointer and headless both fall back to the first armature.
- [ ] Note in the PR: the Skeleton panel copy naming the effective armature stays with the rigging-and-posing spec (the `skeleton-armature-picker` row pairs with this fix).

### PR 2: slot validator reads the truth

- [ ] Skip the parent-bone warning in `_validate_element_against_armature` ([`export.py`](../../apps/blender/core/validation/export.py)) for meshes whose `parent` is a slot Empty - `is_slot_empty` is already imported in the module; slot attachments inherit their bone through the slot by design.
- [ ] Reroute `_check_slot_default` ([`active_slot.py`](../../apps/blender/core/validation/active_slot.py)) through `read_field` so a `proscenio_slot_default` edited in the Custom Properties UI validates the same as a panel edit.
- [ ] Add the help hint that direct Custom-Property edits do not refresh the panel (panels are the expected workflow).
- [ ] Extend [`test_validation_export.py`](../../tests/test_validation_export.py): a slot-attachment mesh no longer flags; a CP-only slot default is validated.

### PR 3: transform-key check sees layered actions

- [ ] Lift the writer's `action_fcurves` fallback ([`animations.py`](../../apps/blender/exporters/godot/writer/animations.py) - empty `fcurves` falls back to layers > strips > channelbags) into a shared duck-typed home.
- [ ] Route `_has_bone_transform_keys` ([`active_slot.py`](../../apps/blender/core/validation/active_slot.py)) through it so keys inserted into Blender 4.4+ layered actions are detected.
- [ ] Unit tests with layered-action mocks (empty `fcurves`, keys living in channelbags) asserting the check fires.
- [ ] The GUI confirmation (the warning fires on a real 5.1.1 layered action) rides the planned verification session - no dedicated session.

### PR 4: multi-polygon meshes export whole (cross-app)

- [ ] Add an additive-optional `polygons` index-array field to `MeshElement` ([`proscenio.py`](../../packages/models/src/proscenio_models/proscenio.py)) with a schema changelog note; ship at format version 1 per the STUDY (the format-migration-path enabler is still open in the schema-expressiveness spec, so a bump would strand old importers).
- [ ] Writer ([`sprites.py`](../../apps/blender/exporters/godot/writer/sprites.py) `build_element`): emit all vertices, per-face index arrays, and whole-mesh weights; keep the field-less single-face shape so existing goldens do not churn.
- [ ] Godot builder ([`mesh_builder.gd`](../../apps/godot/addons/proscenio/builders/mesh_builder.gd)): assign `Polygon2D.polygons` when the field is present; an old importer ignores it and still renders the outline.
- [ ] Regression fixtures: an automesh-densified mesh round-trips whole (today every automesh mesh silently exports as its first triangle); the single-quad goldens stay byte-stable.
