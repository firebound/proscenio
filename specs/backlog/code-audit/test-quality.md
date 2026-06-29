# Test quality

Verdict: the suite is **healthy**. It exercises real code, mock discipline is confined to the bpy/IO boundary, and failure modes are tested as first-class cases. Only one phase-1 "fake test" survived verification (and even that was downgraded to a partial gap), plus a handful of weak assertions worth tightening. One phase-1 test-org claim was refuted (`weight-transfer-test-docs` - see [refuted.md](refuted.md)).

## Measured coverage (not inferred)

Run via `apps/blender/tests/run_coverage.py` (fixtures suite, in-Blender, rc=0) + repo-root `pytest --cov=apps/blender`.

- **Pure `core/` (bpy-free) coverage is excellent** - almost every module 85-100%. The only real gaps: `core/i18n.py` 0% (also a layering smell, see [dependency-direction.md](dependency-direction.md)), `core/_shared/json_cp.py` 62%, `core/_shared/material_images.py` 62%.
- **bpy-coupled modules (operators/, panels/, core/bpy_helpers/) read as 0% under plain pytest only as a measurement artifact** - their operator tests require the in-Blender harness (`run_operator_tests.py`); under raw pytest those tests error on missing bpy and contribute no coverage. Their real coverage comes from the Blender run. Do not read the pytest 0% as untested.

## Fake / weak tests

- **edit-weights-invoke-reimplements** `[low/small]` `[adjusted]` - [test_edit_weights_modal.py:35-64](../../../apps/blender/tests/operators/test_edit_weights_modal.py#L35) - `test_invoke_enters_weight_paint_with_preset_applied` re-implements `invoke()`'s mode/preset block (edit_weights.py:93-103) inline rather than driving the operator, so happy-path invoke-wiring regressions go uncaught. Fix: extract the headless-safe subset of invoke (lines 93-103: POSE pre-step, WEIGHT_PAINT switch, `apply_paint_preset`) into `_enter_weight_paint(context, obj, armature, mirror_x)`; have `invoke()` and the test both call it. The modal-only parts (register_handler, timer, modal_handler_add) remain non-headless-testable - keep the manual-testing note for that remainder.

### Repo-root suite weak assertions (low, tighten when touched)

- [test_contour.py:290](../../../tests/automesh/test_contour.py#L290) - `test_single_hole_detected` only asserts `len(holes[0]) >= 1`; passes for any non-empty hole, doesn't pin the documented 2x2/4-cell shape.
- [test_geometry.py:134](../../../tests/automesh/test_geometry.py#L134) - `test_upsample_doubles_density` asserts only `len(out)==32` (already covered elsewhere); proves the count, not the per-edge distribution the name advertises.
- [test_vertex_pen.py:40,51](../../../tests/automesh/test_vertex_pen.py#L40) - ring tests assert only resulting LENGTH; a bug subdividing a different edge by the same total count would still pass. Assert the subdivided verts landed on the intended edge.
- [test_sprites.py:248](../../../tests/writer/test_sprites.py#L248) - comment claims the dropped-group warning runs, but only the return dict is asserted; the warning side-effect is never captured.
- [test_skinning_modes.py:41-47](../../../tests/skinning/test_skinning_modes.py#L41) - `test_proximity_normalizes_per_vert` asserts only `A+B==1.0`; a degenerate 1.0/0.0 split also satisfies it - does not pin the falloff.

## Coverage gaps (verified against real tests)

- **edit-weights-modal-lifecycle** `[medium/medium]` `[confirmed]` - [edit_weights.py](../../../apps/blender/operators/skinning/edit_weights.py) - the invoke/modal/_finish lifecycle (incl. the TIMER external-exit path and ESC/exception finish) is exercised by no automated test; only poll(), a copied invoke block, and helpers are tested. **The one medium-severity finding in this audit.** Fix: drive the operator class directly like test_quick_armature_modal.py does - call `op.modal()` with stub TIMER/ESC/exception events and call `_finish` directly to assert timer removal, overlay unregister, statusbar removal, auto-snapshot on non-cancel, and `restore_session` all fire.
- **draw-mesh-vertices-click-flow** `[low/small]` `[confirmed]` - [draw_mesh_vertices.py](../../../apps/blender/operators/automesh/draw_mesh_vertices.py) - click-to-place modal flow + manual-outer hand-off have no direct coverage (apply is verified indirectly via pipeline-function calls). Fix: accept as a documented Blender-modal limitation, or factor `modal()`'s action-dispatch into a pure helper and assert `_apply` builds `StageOutput(outer=ring, outer_is_manual=True)`.
- **contour-islands-weak-assert** `[low/small]` `[confirmed]` - [test_contour_islands.py](../../../tests/automesh/test_contour_islands.py) - `len(merged) >= len(bare)` is vacuous (return is always one flat Contour); a grafted detour spur would also pass. Fix: assert merged enclosed area (shoelace) approx == `area(bare_block) + area(island_outside_block)` - a detour adds near-zero/negative area and fails.
- **auto-snapshot-truncate-asymmetric** `[low/trivial]` `[confirmed]` `[quick win]` - [test_auto_snapshot_from_vgroups.py](../../../tests/skinning/test_auto_snapshot_from_vgroups.py) - truncation tested only uvs-longer-than-weights. Fix: add/parametrize the weights-longer case asserting `len(entries)==1`. Low value (zip is symmetric) but locks the contract.
- **weight-transfer-cancel-partial-write** `[low/trivial]` `[confirmed]` `[quick win]` - [test_weight_transfer.py](../../../apps/blender/tests/operators/test_weight_transfer.py) - `test_copy_weights_zero_coverage_returns_cancelled` asserts only CANCELLED. Fix: add `assert len(dup.vertex_groups) == 0` to lock the no-partial-write invariant.
- **storage-proxy-vframes-readback** `[low/trivial]` `[adjusted]` `[quick win]` - [test_storage_proxy.py:35](../../../apps/blender/tests/operators/test_storage_proxy.py#L35) - writes `proscenio_vframes=2` but never asserts `proscenio.vframes` reads back 2 (only frame/hframes checked). Fix: add `assert sprite_obj.proscenio.vframes == 2`. (Corrected path: the file is under `apps/blender/tests/operators/`, not `tests/writer/`.)

## Organization (low priority)

- **automesh-test-monolith** `[low/medium]` `[confirmed]` - [test_automesh_authoring.py](../../../apps/blender/tests/operators/test_automesh_authoring.py) - 1066-line, 34-test monolith spanning unrelated concerns with ~14 copy-pasted StageParams setups (`_simple_params()` covers only the 3 newest). Fix: split into focused modules (labels / overlay / persistence / apply-mesh-geometry / manual-outer); hoist the repeated StageParams into a conftest factory - note it must be a base-kwargs factory parametrizable by mode (most inline blocks use the default mode, `_simple_params()` pins `SIMPLE`).
- Minor cross-suite noise (not worth a dedicated pass): mid-file and function-local imports of the unit under test scattered across `tests/automesh/test_stroke_geometry.py`, `tests/skinning/test_authoring_stages.py`, `test_weight_transfer.py`; no `tests/automesh/conftest.py` so the `sys.path` + bpy-mock prelude is copy-pasted into every file; the `_FIELD_TO_CP`/`_cp_key`/`_Obj` stand-in is duplicated verbatim across `tests/writer/test_slots.py` and `test_sprites.py`.

## Documented strengths (so the next reader does not re-audit)

- **Real-code discipline throughout.** Every repo-root test imports and calls the actual pure module under `core/`; no test mocks the unit it tests.
- **Mock discipline is correct.** Externals only are stubbed (bpy/bmesh/mathutils via conftest); crucially the writer's mathutils stand-in reimplements the real linear algebra (Matrix @, etc.), and the bone_modes `_FakeObj` mirrors the real custom-property API.
- **Failure modes are first-class.** ValueError paths (negative/inf/NaN inputs, zero grid, unknown element type, stale rest basis) are pinned with `pytest.raises(..., match=...)` on real messages across binarize/dilate/erode/arc_length_resample/relax_contour/weight_diff/weight_reproject/weight_transfer/erosion_loops.
- **Assertions are quantitative, not vague.** `test_outer_splice.py` pins results by exact shoelace area + corner survival + a non-self-intersection check; density/geometry pin `approx`-equal perimeters and uniform spacing; planar_proximity asserts exact inverse-square/linear splits; the contour B3 pair is a proper guard + counter-guard.
