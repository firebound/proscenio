# Spec 076 TODO: Blender code-audit remainder

Drives [STUDY](STUDY.md). The unshipped tail of spec 074 (Phases 4-6 + the two decision-gated correctness bugs), regrouped so 074 could prune. **Rule (D2): no item ships without a green guard - where the audit found NO GUARD, write the regression test first (reproduce -> fix -> pass).** Every `file:line` was verified against HEAD in the 2026-06-28 audit; locate by symbol if drifted. Item format: `id - fix - guard`.

Gates each PR: `uv run ruff check` + `ruff format --check` (+ `uvx ruff format --check` for CI parity) + `uv run mypy --config-file apps/blender/pyproject.toml` + repo-root `uv run pytest tests/` + in-Blender `run_operator_tests.py` + `run_tests.py` goldens (8/8).

## Phase A - Low-severity bugs

- [ ] **bone-length-armature-scale** - `skeleton.py`: multiply emitted `length` by the planar armature scale. - GUARD: writer test with a non-unit un-applied armature scale.
- [ ] **flipv-offset-double-count** - `sprites.py _compute_sprite_offset`: compute the offset from an un-mirrored matrix. - GUARD: writer test - off-center quad + `scale.y=-1`.
- [ ] **direct-frame-collapse-no-grid** - `sprite_frame_animations.py`: warn (don't silently collapse) when frame keys exist but the grid is unset/1x1. - GUARD: unit test - frame keys + unset grid -> single key + warning.
- [ ] **bundle-filename-collision** - `bundle.py bundle_textures`: detect two distinct images resolving to the same basename, record + warn instead of silently dropping. - GUARD: test - two same-basename images from different folders.
- [ ] **bind-diagnosis-index-crash** - `bind_diagnosis.py diagnose_isolated_islands`: guard `0 <= idx < vert_count` on raw face members (pure exported fn). - GUARD: test an out-of-range face index does not raise.
- [ ] **inplane-prebend-root-anchor** - `authoring_ik.py`: slice `members[1:-1]` so the root anchor is not nudged. - GUARD: >=3-bone chain, assert root anchor `rotation_euler.y == 0`.
- [ ] **spritesheet-shader-no-modulo** - `spritesheet_shader.py`: add a MODULO-by-vframes node on the row path (mirror the column path). - GUARD: headless node-eval test for an out-of-range frame vs `cell_offset_y`.
- [ ] **drop-slicer-drivers-dead** - `spritesheet_shader.py _drop_slicer_drivers`: read `material.node_tree.animation_data` + match the real socket data_path. - GUARD: headless test - apply slicer, remove node, assert no orphan node-tree drivers.
- [ ] **corrupt-prepack-stuck-cp** - `unpack.py`: delete the stale `PROSCENIO_PRE_PACK` key before `continue` when its JSON is corrupt. - GUARD: `test_atlas_unpack_rescue` - corrupt key, assert removed.
- [ ] **feet-landing-name-over-tag** - `importers/photoshop/__init__.py`: invert to tag-first/name-fallback (reuse `_layer_for_object`). - GUARD: test - renamed stamped mesh colliding with another layer name, assert the tagged layer's size is used.
- [ ] **slot-default-min-name** (benign/cosmetic, optional) - `slot_emit.py _resolve_default`: fall back to `attachments[0]` (child order) instead of `min(attachments)`. - GUARD: `_resolve_default` unit test.
- [ ] **degenerate-close-corrupt-state** `[medium]` - `vertex_pen.py _snap`: require `len(points) >= 3` to close (the inline pen already does); a 2-vert close leaves a stray duplicate vert + edge_subdiv that corrupts the next CDT. - GUARD: `test_vertex_pen` - a 2-vert close does not leave residue / re-arms.
- [ ] **driver-source-bone-enum-remap** `[low]` - `_dynamic_items.py driver_source_bone`: emit explicit string ids in the EnumProperty items so the selection stores the bone NAME, not a positional index that a bone rename/reorder silently re-maps. (Sibling of O3's positional-index class - do it alongside `keyframe-slot-index-drift`.) - GUARD: unit test - reorder bones, assert the stored driver source still resolves the same bone.
- [ ] **commit-contour-outer-not-manual** `[low, latent]` - `automesh_authoring.py _commit_contour`: set `outer_is_manual = True` when it sets `output.outer` (currently dead - the contour tool was removed - but a live trap if re-added). - GUARD: assert a committed contour keeps `outer_is_manual` through APPLY, OR delete the dead `_commit_contour` if confirmed unreachable.

## Phase B - Performance

- [ ] **arc-length-resample-quadratic** - `geometry.py arc_length_resample`: carry `accumulated` incrementally; delete `edge_index_start_distance` (this dissolves the audit's **perimeter-length-dup** duplication finding). - GUARD: `test_geometry` TestArcLengthResample (behavior-equivalence, non-flaky).
- [ ] **steiner-filter-quadratic** - `bridge.py _compute_steiner_points`: bbox-reject per hole before the full `point_in_polygon`. - GUARD: NO GUARD - add a pure equivalence test (bbox-pruned == brute-force).
- [ ] **read-alpha-grid-full-walk** - `bridge.py read_alpha_grid`: cache the `AlphaGrid` per `(image, downscale)` for the modal session. - GUARD: NO GUARD - add a `_max_alpha_in_block` unit test first (pure), then the cache.
- [ ] **find-best-inner-rotation-quadratic** - `geometry.py`: cap the search window (numpy-free contract) or correct the docstring. - GUARD: `test_geometry` TestFindBestInnerRotation.

> **Done in 074 Phase 3:** `depsgraph-handler-linear-scans` - the outliner + slots syncs already gained the bone variant's fast-path identity guard when `handlers-sync-index-to-active` folded (PR #182). No work left here.

## Phase C - Test-quality (the one medium + hardenings + organization)

> **D3: `edit-weights-modal-lifecycle` unblocks spec 075 Phase C** (its D6 waits on this coverage before the large operator splits). Land it first if 075's large splits are wanted sooner.

- [ ] **edit-weights-modal-lifecycle** (MEDIUM) - cover `modal` / `_finish` via the `_Probe` pattern from `test_quick_armature_modal.py`: TIMER external-exit, ESC->cancel, raising tracker->`_finish(cancel)`, `_finish` removes timer/overlay/statusbar + auto-snapshot only on non-cancel + `restore_session` always (stubs must raise to prove the suppress).
- [ ] **edit-weights-invoke-reimplements** - extract `_enter_weight_paint(context, obj, armature, *, mirror_x)`; `invoke` + the test both call it.
- [ ] **eval-frame-sandbox** - add a restricted-eval failure-mode test for `_eval_frame` (math/var resolves; name errors / disallowed builtins / non-numeric -> None). (Not RCE - build-time tool.)
- [ ] Tighten the weak assertions: **test_contour single-hole** (assert bbox `(4,5,4,5)`), **test_geometry upsample** (assert uniform spacing), **test_vertex_pen edge-landing** (assert `(1.0,0.0)` + `(2.0,1.0)` in ring), **test_sprites dropped-group** (`capsys` assert the warn), **test_skinning_modes proximity** (assert 0.5/0.5 split).
- [ ] Coverage adds: **draw-mesh `_output`** (StageOutput `outer_is_manual` + provisional fold stroke via `_Probe`), **contour-islands shoelace-area** assert, **auto-snapshot reverse-truncate** case, **weight-transfer** `assert len(dup.vertex_groups) == 0` after CANCELLED, **storage-proxy** `assert proscenio.vframes == 2`.
- [ ] Organization: split **automesh-test-monolith** (38 tests) by concern + a StageParams conftest factory; add **tests/automesh/conftest.py** for the `sys.path` + bpy-mock prelude (070's files copy-paste it).

## Phase D - Dead module removal (O2 resolved: delete)

- [ ] **psd-naming-module-orphaned** - delete `apps/blender/core/psd/psd_naming.py` + `tests/test_psd_naming.py`. Verified: spritesheet frames are authored in Photoshop (`[spritesheet]` tag -> `planner.ts` -> explicit manifest `frames` list) and Blender consumes the manifest; the Blender-side guess-from-layer-names module is the wrong layer and has zero callers. No feature lost. - GUARD: full import + suite stays green after removal.

## Decision-gated correctness bugs (O3 / O4 locked 2026-07-01 - see STUDY)

- [ ] **keyframe-slot-index-drift** (**O3 -> A, locked**) - `attachment.py keyframe_slot_attachment` + reader `slot_animations.py`: bind the keyframe to the attachment NAME via a string Custom Property read by the writer (not the positional child index). Touches the export round-trip -> regenerate the `slot_swap` / `slot_cycle` goldens. - GUARD: rewrite `test_keyframe_slot_attachment` (it pins the buggy positional contract) + add: key `axe`, delete an earlier child, assert export still resolves `axe`.
- [ ] **animated-delta-rest-rotation** (**O4 -> A, locked**) - `animations.py _resolve_pose_entry`: implement the per-frame posed-parent sample (scene-step, like `sprite_frame_animations._bake_track`) - the full correct bake, no documented gap. - GUARD: fixture - parent bone with a rotation key + child with a screen-vertical location key; assert child parent-local position matches the runtime-equivalent.

## Post-merge cleanup (ONLY after the final phase merges)

- [ ] Drain the remaining [backlog/code-audit/](../backlog/code-audit/) leads this spec resolves; any genuinely-deferred remainder moves to [deferred.md](../deferred.md) / [gated.md](../gated.md).
- [ ] Prune this spec folder; index in [`index.md`](../index.md) with the PR number(s) (076 -> pruned).
