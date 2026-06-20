# Spec 054: Code review cleanup - TODO

Five grouped commits. Anything regenerated (codegen output) re-runs the generator after the fix.

## PR 1 - test gaps

- [ ] Give the weight-reproject donors distinct weight dicts and place the target nearer one, so the nearest-pick fallback actually fails when nearest-selection breaks. `tests/skinning/test_weight_reproject.py:66,95`.
- [ ] Materialize the TypeScript-emit glob to a list and assert it is non-empty before the loop, so an empty directory does not pass validating nothing. `tests/codegen/test_ts_emit.py:44`.
- [ ] Add the "vert gained by paint" case to weight-diff: `before={1:1.0}, after={0:0.25,1:1.0}` asserting `diff_weights == {0}`. `tests/skinning/test_weight_diff.py`.
- [ ] Add `test_restore_3x_round_trip` for the 3.x `bone.hide` fallback, reusing the `_armature_3x` helper. `tests/skinning/test_bone_collection_visibility.py:41`.
- [ ] Add `test_point_on_boundary_returns_false` to assert the documented "boundary = outside" contract. `tests/automesh/test_density.py:60-86`.

## PR 2 - DRY and dead code

- [ ] Extract `_rewrite_images_to_relpath` to `packages/fixtures/_shared/blend_utils.py` and import it from the four `build_blend.py` copies. `simple_psd:103`, `slot_cycle:198`, `mixed_feature:433`, `slot_swap:341`.
- [ ] Move the `REPO_ROOT` + `sys.path.insert` bootstrap into `tests/skinning/conftest.py`, following `tests/writer/conftest.py`; drop it from the 14 test files.
- [ ] Remove the never-called weight-paint brush mirror `draw_weight_paint()`, or wire it into the PAINT_WEIGHT branch. `panels/_draw_mesh.py:28-44`, `panels/element.py:56-61`.
- [ ] Remove the unreachable `obj is None or obj.type != "MESH"` fallback label (the subpanel poll already requires a mesh element). `panels/mesh_generation.py:213-214`.
- [ ] Remove the dead `bpy.data.images.get(atlas_png.stem)` lookup that never hits. `operators/atlas_pack/apply.py:66-68`.

## PR 3 - redundant and cosmetic

- [ ] Drop the per-operand `list()` in `outer_world + inner_world + interior_points`. `core/bpy_helpers/automesh/cdt.py:84`.
- [ ] Drop the dead `bool()` wrapper around `getattr(props, "exclude_from_atlas", False)`. `operators/atlas_pack/pack.py:30`.
- [ ] Rewrite the double-negative `not (filter_text and filter_text not in ...)`. `core/outliner_view.py:71`.
- [ ] Consume the trailing newline when stripping the eslint-disable marker so the emitted `.ts` has no double blank line; re-run codegen. `packages/codegen/src/proscenio_codegen/ts_emit.py:86`.
- [ ] Type the test ClassVars as `ClassVar[list[Any]]`. `apps/blender/tests/operators/test_quick_armature_modal.py:45-46`.

## PR 4 - docs, comments, help

- [ ] Rewrite the weight-reproject docstring "carries its provenance verbatim" to describe the actual normalization at line 106. `core/skinning/weight_reproject.py:98`.
- [ ] Correct the stale `apps/godot/<name>/` path in the sync-fixtures docstring. `scripts/godot/sync_fixtures.py:34`.
- [ ] Correct the shared-atlas "Run with" path. `packages/fixtures/shared_atlas/build_blend.py:5`.
- [ ] Note both cp311 (3.11) and cp313 (3.13) in the blender-dev Python-version line. `.ai/skills/blender-dev.md:12`.
- [ ] Drop the stray "the" in the doll README. `examples/authored/doll/03_blender_setup/README.md:70`.
- [ ] Add the "Bake IK to Keyframes" sentence to the pose-mode help topic. `apps/blender/core/help_topics.py:878-882`.

## PR 5 - infra and convention

- [ ] Add a top-level `permissions: contents: read` to the CI workflow. `.github/workflows/ci.yml`.
- [ ] Switch the frozen validator dataclass fields to `tuple[...]` with `field(default_factory=tuple)` and pass tuples at the construction sites. `packages/validator/src/proscenio_validator/_types.py:61,69,70`.
- [ ] Add a no-hard-wrap line to `.ai/conventions/docs.md` ("prose is one line per paragraph or bullet; let the editor soft-wrap; never hand-wrap markdown bodies or comment paragraphs").
