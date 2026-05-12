# SPEC 003 - TODO

Wires the `weights` field that has been in the schema since v1 into a real `Polygon2D.skeleton` + `set_bones()` import path. See [STUDY.md](STUDY.md) for the design rationale and the seven locked questions (D1–D7).

## Decision lock-in

- [x] D1 - writer normalizes weights to sum-to-1 per vertex before emitting.
- [x] D2 - vertices with zero total weight fall back to the sprite's resolved bone (the same one rigid-attach would have used).
- [x] D3 - writer drops vertex groups whose name does not match an armature bone, logs a warning per group.
- [x] D4 - schema's bone-major `weights: [{bone, values[]}]` shape stays. No `format_version` bump.
- [x] D5 - single `polygon_builder.gd` handles both rigid and skinned paths via internal data branch.
- [x] D6 - animation builder unchanged. `bone_transform` tracks deform skinned meshes through Godot's native pipeline.
- [x] D7 - implicit authoring: presence of vertex groups whose names match bones turns skinning on. No new Custom Property.

## Schema and format docs

- [x] No schema change needed - `weights` field already in [`schemas/proscenio.schema.json`](../../schemas/proscenio.schema.json) since v1. The shape stays identical.
- [x] Updated [`.ai/skills/format-spec.md`](../../.ai/skills/format-spec.md): the "Skinning weights" section now describes live behavior with an authored example.

## Blender writer

- [x] [`writer.py`](../../apps/blender/exporters/godot/writer.py) now collects per-bone weights from vertex groups whenever the mesh has any. Single-bone resolution still drives the "rigid" path for sprites without groups.
- [x] `_build_sprite_weights(obj, mesh, vertex_indices, fallback_bone, available_bones) -> list[WeightDict]` returns bone-major output, skips unmatched group names with a warning, normalizes per-vertex sums, and falls back to the resolved bone for zero-weight vertices.
- [x] `WeightDict` `TypedDict` added; mypy `--strict` clean.
- [x] `RuntimeError` raised when a sprite has vertex groups but none resolve to bones - fail-fast at export.
- [x] Schema validator inside `run_tests.py` continues to assert the writer's fresh output (already in place from SPEC 002).

## Godot importer

- [x] [`polygon_builder.gd`](../../apps/godot/addons/proscenio/builders/polygon_builder.gd) branches when `sprite_data.weights` is present and non-empty:
  - Sets `polygon.skeleton = polygon.get_path_to(skeleton)`.
  - Calls `polygon.add_bone(bone_path, weights)` for each weight entry.
  - Skinned polygons are parented to the `Skeleton2D` (not to a `Bone2D`) so vertex weights drive deformation rather than parent-transform inheritance.
- [x] Rigid-attach path preserved for sprites without `weights` - `polygon` stays a child of its resolved `Bone2D`.
- [x] Missing bone in a `weights` entry → `push_error` + skip that bone; importer does not crash the rest of the rig.

## Tests

- [x] Added `apps/godot/tests/fixtures/skinned_dummy.proscenio`: 3 bones (root → lower → upper) and one torso sprite weight-split across `upper` (top vertices) and `lower` (bottom vertices).
- [x] Extended [`test_importer.gd`](../../apps/godot/tests/test_importer.gd) with `_run_skinned_checks` - asserts polygon parents to skeleton, `skeleton` NodePath is set, bone count, and known vertex weights. Total assertions 22 → 31.
- [x] [`apps/godot/tests/fixtures/dummy.proscenio`](../../apps/godot/tests/fixtures/dummy.proscenio) untouched - pure regression fixture for the rigid path.
- [x] `apps/blender/tests/fixtures/dummy/expected.proscenio` regenerated to capture the writer's new `weights` output for `dummy.blend`'s vertex-grouped meshes (legs, torso).

## Documentation

- [x] "Painting weights for skinning (SPEC 003)" subsection in [`.ai/skills/blender-dev.md`](../../.ai/skills/blender-dev.md) covering vertex-group naming, normalization, fallback, RuntimeError, sprite_frame exclusion.
- [x] [`.ai/skills/godot-dev.md`](../../.ai/skills/godot-dev.md) "Choosing the rendering path" updated - `polygon` row mentions live skinning via `Polygon2D.skeleton` + `add_bone()`.
- [x] [`STATUS.md`](../../STATUS.md) - moved to shipped on merge.

## Manual validation

These are user-driven smoke tests against a real Blender + Godot loop. Not gated by CI.

- [ ] On `dummy.blend`, paint vertex weights on the torso mesh: e.g. 0.7 to `torso` near the top, 0.3 to `legs` near the bottom. Export. Observe the imported scene: animating `legs` should now pull the lower torso vertices noticeably while the upper ones stay anchored to `torso`.
- [ ] Plugin-uninstall test: with SPEC 001 wrapper scene + skinned `.scn`, disable the Proscenio plugin, reload, confirm the deformation still plays. Skinning is a `Polygon2D` core feature - must work without the plugin.

## Defer (potential SPEC 003.1 if demand emerges)

- Per-vertex skinning visualization tool inside the Blender addon (color-code by dominant bone).
- A "fix orphaned weights" migration helper triggered when a bone is renamed.
- GPU-side skinning compute shader - sits behind the GDExtension hard rule and the [Architecture revisits backlog entry](../backlog.md).
- Skinning-aware atlas region reflow - when a sprite's weights move vertices outside the original `texture_region`, recompute. Probably never needed; document and revisit only if reported.
