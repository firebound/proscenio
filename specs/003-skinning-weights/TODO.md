# SPEC 003 — TODO

Wires the `weights` field that has been in the schema since v1 into a real `Polygon2D.skeleton` + `set_bones()` import path. See [STUDY.md](STUDY.md) for the design rationale and the seven locked questions (D1–D7).

## Decision lock-in

- [x] D1 — writer normalizes weights to sum-to-1 per vertex before emitting.
- [x] D2 — vertices with zero total weight fall back to the sprite's resolved bone (the same one rigid-attach would have used).
- [x] D3 — writer drops vertex groups whose name does not match an armature bone, logs a warning per group.
- [x] D4 — schema's bone-major `weights: [{bone, values[]}]` shape stays. No `format_version` bump.
- [x] D5 — single `polygon_builder.gd` handles both rigid and skinned paths via internal data branch.
- [x] D6 — animation builder unchanged. `bone_transform` tracks deform skinned meshes through Godot's native pipeline.
- [x] D7 — implicit authoring: presence of vertex groups whose names match bones turns skinning on. No new Custom Property.

## Schema and format docs

- [ ] No schema change — `weights` field already in [`schemas/proscenio.schema.json`](../../schemas/proscenio.schema.json) since v1. Verify the inline `description` reflects "consumed by importer post-SPEC 003" instead of "accepted but ignored".
- [ ] Update [`.ai/skills/format-spec.md`](../../.ai/skills/format-spec.md): replace the "Skinning weights (v1)" section's "ignored by importer" disclaimer with the live behavior. Add an authored example showing a torso sprite with weights split across `torso` and `legs`.

## Blender writer

- [ ] In [`blender-addon/exporters/godot/writer.py`](../../blender-addon/exporters/godot/writer.py), replace `_resolve_sprite_bone`'s "first vertex group wins" heuristic with a real weight-collection step that runs whenever the mesh has vertex groups. The single-bone fallback survives only for sprites without groups.
- [ ] Implement `_build_sprite_weights(obj, mesh, armature_bones) -> list[WeightDict]` returning the schema's bone-major shape. Skip vertex groups whose name is not a bone (log warning); normalize sums per vertex (writer-side); fall back to the sprite's resolved bone for vertices with zero total weight.
- [ ] Add a `WeightDict` `TypedDict` mirroring the schema entry.
- [ ] Surface a `RuntimeError` if a sprite's mesh has vertex groups but the writer cannot resolve any of them to bones — clearer than emitting an empty `weights` array.
- [ ] Run the schema validator inside `run_tests.py` against the fresh writer output (already in place).

## Godot importer

- [ ] In [`polygon_builder.gd`](../../godot-plugin/addons/proscenio/builders/polygon_builder.gd), branch when `sprite_data.has("weights")` and the array is non-empty:
  - Resolve `Skeleton2D` NodePath: `polygon.skeleton = polygon.get_path_to(skeleton)` after `add_child`.
  - For each weight entry, resolve the bone by name to its `Bone2D` and call `polygon.set_bone(NodePath, weights_for_that_bone)` (or the closest current API — verify against Godot 4.6).
  - Drop the warning log; replace with a `print_verbose` confirmation listing the bone names that picked up.
- [ ] Keep the rigid-attach path: sprites without `weights` (or with empty array) parent to their resolved bone exactly as today.
- [ ] If a bone name in `weights` does not resolve to a `Bone2D` under the skeleton, push an `error` and skip that bone (do not crash the import).

## Tests

- [ ] Extend [`godot-plugin/tests/test_importer.gd`](../../godot-plugin/tests/test_importer.gd) with a third fixture `skinned_dummy.proscenio` that includes weights — assert `polygon.skeleton` resolves, `polygon.bones` has the expected count, and a known vertex's weight values match.
- [ ] Add `godot-plugin/tests/fixtures/skinned_dummy.proscenio` hand-written: one root + two-bone chain, one mesh sprite weight-split between the two bones.
- [ ] Update [`godot-plugin/tests/fixtures/dummy.proscenio`](../../godot-plugin/tests/fixtures/dummy.proscenio) only if the regression assertion needs adjustment — preference is to keep it untouched (pure backwards-compat).
- [ ] Update [`blender-addon/tests/run_tests.py`](../../blender-addon/tests/run_tests.py) — no logic change, but the regen-on-FAIL workflow should pick up weights on `dummy.blend` if the user paints any. Document this in the run_tests.py docstring.
- [ ] Verify `dummy.blend`'s torso has at least one vertex weighted to `legs` so the regenerated golden fixture exercises the new writer path.

## Documentation

- [ ] Add a "Painting weights" subsection to [`.ai/skills/blender-addon-dev.md`](../../.ai/skills/blender-addon-dev.md): how to enter weight paint mode, name vertex groups after bones, the writer's normalization expectation.
- [ ] Update [`.ai/skills/godot-plugin-dev.md`](../../.ai/skills/godot-plugin-dev.md) "Choosing the rendering path" to mention that skinning unlocks here, formalizing what was forecasted in SPEC 002.
- [ ] Update [`STATUS.md`](../../STATUS.md) — move SPEC 003 to shipped; bump LOC counts; reference the new fixture.

## Manual validation

- [ ] On `dummy.blend`, paint vertex weights on the torso mesh: 0.7 to `torso` near the top, 0.3 to `legs` near the bottom. Export. Observe the imported scene: animating `legs` should now pull the lower torso vertices noticeably while the upper ones stay anchored to `torso`.
- [ ] Plugin-uninstall test: with SPEC 001 wrapper scene + skinned `dummy.scn`, disable the Proscenio plugin, reload, confirm the deformation still plays. Skinning is a `Polygon2D` core feature — must work without the plugin.

## Defer (potential SPEC 003.1 if demand emerges)

- Per-vertex skinning visualization tool inside the Blender addon (color-code by dominant bone).
- A "fix orphaned weights" migration helper triggered when a bone is renamed.
- GPU-side skinning compute shader — sits behind the GDExtension hard rule and the [Architecture revisits backlog entry](../backlog.md).
- Skinning-aware atlas region reflow — when a sprite's weights move vertices outside the original `texture_region`, recompute. Probably never needed; document and revisit only if reported.
