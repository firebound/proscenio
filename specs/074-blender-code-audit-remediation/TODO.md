# Spec 074 TODO: Blender code-audit remediation

Drives [STUDY](STUDY.md). Sequenced by risk (D3). Each phase is one gates-green PR. **Rule (D2): no item ships without a green guard - where the audit found NO GUARD, write the regression test first (reproduce -> fix -> pass).** Every `file:line` was verified against HEAD on 2026-06-29; locate by symbol if drifted. Item format: `id - fix - guard`.

Gates each PR: `uv run ruff check` + `ruff format --check` (+ `uvx ruff format --check` for CI parity) + `uv run mypy --config-file apps/blender/pyproject.toml` + repo-root `uv run pytest tests/` + in-Blender `run_operator_tests.py` + `run_tests.py` goldens (8/8).

## Phase 1 - High-severity correctness (fix first; all currently unguarded)

- [ ] **bone-frame0-negative-time** - `animations.py collect_bone_keys`: clamp `time = max(0.0, (frame-1)/fps)` (match the sprite_frame / slot writers). - GUARD: add a writer unit test keying a bone at frame 0, assert `build_bone_track` emits `time == 0.0` without raising.
- [ ] **finish-flag-clear-last** - both `_finish` (`automesh_authoring.py`, `draw_mesh_vertices.py`): move `mark_stopped(_MODAL_NAME)` to the top (or `finally`), and/or wrap each cleanup step in `contextlib.suppress(RuntimeError)` like `edit_weights._finish`. - GUARD: add a headless test that makes a cleanup step raise and asserts `is_running(_MODAL_NAME)` is False after.
- [ ] **redo-wrong-parent** - `quick_armature.py _redo_last_bone`: pin the parent before redo (`cls._last_bone_name = record.parent_to_last_name`) or thread an explicit `parent_name` into `_create_bone`. - GUARD: test - draw A, draw B-on-A, select A, draw C-on-A, undo C, redo C, assert C's parent is A.
- [ ] **keyframe-slot-index-drift** (decide O3 first) - `attachment.py keyframe_slot_attachment` + reader `slot_animations.py`: bind the keyframe to the attachment NAME, not the positional child index. **Binding mechanism is a design fork (O3): string CP read by the writer, vs a stable-order field keeping the integer fcurve** - the first touches the export round-trip. - GUARD: rewrite `test_keyframe_slot_attachment` (it pins the buggy positional contract) + add: key `axe`, delete an earlier child, assert export still resolves `axe`.
- [ ] **regen-wipes-provenance** + **noop-regen-overwrites-provenance** (shared root cause) - `automesh_hook.py _snapshot_from_existing_sidecar`: read per-vert provenance from the parsed prior sidecar into the snapshot instead of flat `auto_seed`; the reproject carry logic then resurrects `user_paint`. - GUARD: strengthen `test_automesh_regen.py` (today asserts `"reprojected" or "auto_seed" in provenances` - passes WITH the bug): bind -> set entries `user_paint` -> regen (identical + changed topology) -> assert `user_paint` survives.
- [ ] **regen-drops-snapshots** - `automesh_hook.py`: carry `existing.snapshots` forward on both the identical-topology and topology-changed branches. - GUARD: test - bind -> save named snapshot -> regen (preserve ON) -> assert `read_snapshots(obj)` still has it.

## Phase 2 - Medium correctness + the rest of the provenance cluster

- [ ] **regen-rerig-false-preserve** - `automesh_hook.py`: detect `prior.vertex_group_names` vs new deform-bone names diverging; warn + refuse the false "preserved" claim (or key reproject by prior names). - GUARD: bind rig A, paint, switch picker to rig B, regen, assert warning or correct groups (not silently empty).
- [ ] **vgroup-fallback-wipes-provenance** - `automesh_hook.py _snapshot_from_vgroups_fallback`: on the corrupt/empty-sidecar fall-through, report a warning (provenance is unrecoverable from a corrupt CP - surface the loss, don't swallow it). - GUARD: corrupt sidecar with `user_paint` -> regen -> assert a warning is reported.
- [ ] **restore-snapshot-baseline-names** - `named_snapshot.py`: build `restore_sidecar.vertex_group_names` from the snapshot's own weights, not the live baseline. - GUARD: snapshot -> re-bind with a renamed deform bone (same topology) -> restore -> assert weights survive.
- [ ] **tablet-pressure-resets-tracker** - `edit_weights.py modal`: gate the `pressure < 1e-6` end-of-stroke on an `_stroke_active` flag (set on LMB PRESS, cleared on RELEASE) so a mid-stroke pressure dip does not reset the tracker. - GUARD: test a mid-stroke `MOUSEMOVE pressure=0` then more paint + release, assert tail verts flip to `user_paint`.
- [ ] **manual-draw-invoke-leak** - `draw_mesh_vertices.py invoke` except clause: call `self._finish(context, cancel=True)` before returning CANCELLED (mirror automesh). - GUARD: monkeypatch `_append_statusbar` to raise during invoke, assert no leaked draw handler / `is_running` False.
- [ ] **edit-weights-no-cancel** - `edit_weights.py`: add `def cancel(self, context): self._finish(context, cancel=True)` (its `_finish` is already suppress-wrapped). - GUARD: the existing `test_edit_weights_modal` restore tests cover the delegate; assert `cancel` reaches `_finish`.
- [ ] **register-overlay-partial-leak** + **refresh-overlay-partial-leak** - `authoring_overlay.py register_manual_draw_overlay` / `register_overlay`: wrap the handler-adding body so a partial set self-cleans on raise (`except: unregister_overlay(handles); raise`); this transitively fixes `refresh_overlay`. - GUARD: monkeypatch `draw_handler_add` to raise on the Nth call, assert net-zero handlers added.
- [ ] **automesh-invoke-partial-leak** (dict-key portion) - `automesh_authoring.py`: add the missing `"outer_preview": None` to the initial `_handles` dict (the leak portion folds into the register-overlay fix above). - GUARD: shared with register-overlay test.
- [ ] **animated-delta-rest-rotation** (decide O4 first - heavier than medium) - `animations.py _resolve_pose_entry`: a correct fix needs a per-frame posed-parent sample (scene-step), not a formula tweak. **O4: implement the per-frame bake, OR ship the rest-rotation fast path + a documented limitation (skip the correction when the parent has rotation fcurves).** - GUARD: fixture - parent bone with a rotation key + child with a screen-vertical location key; assert child parent-local position matches the runtime-equivalent.
- [ ] **unweighted-vertex-zero-column** - `sprites.py build_sprite_weights`: when `fallback_bone not in available_bones`, pick a deterministic fallback from the (guaranteed non-empty) `known_groups`. - GUARD: unit test with first vgroup a non-bone + a zero-weight vertex, assert no all-zero weight column.
- [ ] **feet-landing-ignores-origin-offset** - `importers/photoshop/__init__.py _anchor_meshes_at_feet`: add the baked Z offset (`placement[3]`) to `bottom`, or read `mesh.bound_box` min-Z. - GUARD: import test - a sprite layer with `[origin]` + landed anchoring, assert the visual bottom lands on Z=0.

## Phase 3 - Quick-win cleanups (dead-code, inlines, DRY folds, misplaced-code, accessors)

Dead-code (trivial deletes, grep-confirmed 0 refs):

- [ ] **rect-area-dead** - delete `Rect.area` (`atlas_packer.py`). - GUARD: existing packer tests.
- [ ] **vertexpen-dragging-dead** - delete `VertexPen.dragging` (`vertex_pen.py`; drag uses `_drag_index`). - GUARD: `test_vertex_pen`.
- [ ] **bpy-compat-dead-shims** - delete `iter_action_layers` + `iter_action_strips` (`_bpy_compat.py`). - GUARD: full import + suite.
- [ ] **hole-safety-dilate** - delete `HOLE_SAFETY_DILATE_CELLS` + its `core/automesh/__init__.py` re-export (deprecated, 0 importers). - GUARD: `test_contour`.

Trivial inlines / low DRY:

- [ ] **cdt-inputs-passthrough** - inline `_build_stroke_cdt_inputs` at its single call site (`authoring_pipeline.py`), delete the wrapper. - GUARD: `test_cut_geometry` / `test_stroke_geometry`.
- [ ] **modal-session-skinning-chain** - `modal_session.py _restore_overlay_flag`: use `scene_skinning(context)` instead of the inline traversal. - GUARD: `test_edit_weights_modal` lifecycle.
- [ ] **tag-redraw-wrapper-dup** - fold the VIEW_3D+STATUSBAR body into a shared `tag_redraw_view3d_statusbar(wm)` next to `tag_redraw_areas`; the two automesh modals call it. - GUARD: none needed (UI repaint).
- [ ] **writer-image-abspath** - extract `image_abspath(image)` in `scene_discovery.py`; `image_filename` + `bundle._resolve_image_source` call it. - GUARD: `test_export_bundle`.

Misplaced-code (move pure logic out of bpy modules; the pure test travels):

- [ ] **godot-writer-math** - move `world_to_godot_xy` / `godot_world_angle_from_dir` / `wrap_pi` -> `core/godot_export_math.py`, re-export. - GUARD: `tests/writer/test_skeleton.py` (update import).
- [ ] **atlas-manifest-parser** - move `read_manifest` + `Placement` -> `core/atlas/atlas_manifest.py`. - GUARD: NO GUARD - add a round-trip test.
- [ ] **object-props-setter-context** - extract the order->Y arithmetic from `_set_y_draw_order` into a pure helper (the `set=` context read is inherent). - GUARD: add a bpy-free unit test for the math.
- [ ] **weight-panel-sidecar-parse** - replace the panel's inline `json.loads` with a typed `count_entries_by_provenance(obj)` in `sidecar_io.py`. - GUARD: NO GUARD - add a unit test.
- [ ] **planes-placement-math** - move `_Placement` / `_origin_for_kind` / `_layer_placement` -> `core/psd/placement.py`. - GUARD: split `test_sprite_origin` (pure cases -> `tests/psd`).
- [ ] **armature-overlay-geometry** - move `_preview_color_for` + the axis-guideline endpoint math -> `core/armature/quick_armature_math.py`. - GUARD: `tests/test_quick_armature_math.py`.
- [ ] **automesh-snap-math-dup** - the open-stroke `_apply_axis_lock` / `_snap_pen_click` in `automesh_authoring.py` are identical to `VertexPen`; extract shared pure geometry (or drive the open-stroke path through a pen). - GUARD: `test_vertex_pen`.

Dependency-direction (read-only accessors instead of operator privates):

- [ ] **panel-reads-automesh-internals** - add `authoring_modal_state()` (frozen dataclass: active/stage/label/tool); panel consumes it. - GUARD: NO GUARD - add a snapshot test.
- [ ] **panel-reads-quickarm-private** - add `@classmethod is_running(cls)` on Quick Armature; panel calls it instead of `getattr(op, "_modal_running")`. - GUARD: small lifecycle test.
- [ ] **i18n-bpy-top-import** - `core/i18n.py` top-level `import bpy` breaks the core contract; move under `core/bpy_helpers/` (or addon top, or lazy). - GUARD: `test_help_topics` + register round-trip.

DRY clusters (med/small; unify only the shared core - D6):

- [ ] **automesh-modal-preamble** (high value) - extract `poll_mesh_with_image` + `validate_authoring_invoke` -> `operators/automesh/_authoring_preconditions.py`; both modals delegate. - GUARD: `test_draw_mesh_vertices` (polls + exclusivity).
- [ ] **topology-hash-call** - add `topology_hash_of(obj)` (`bpy_helpers/skinning`); replace 4 sites. - GUARD: `test_sidecar_io` / `test_automesh_regen`.
- [ ] **writer-rotate-vec2** - extract `rotate_vec2(dx, dy, angle)` next to `world_to_godot_xy`; 3 callers. - GUARD: `test_animations` rotate tests.
- [ ] **writer-action-length** - promote `_action_length` to a shared writer module; `animations.py` + `slot_animations.py` drop their inline round. - GUARD: writer animation tests.
- [ ] **point-to-segment-projection** - extract `_closest_point_on_segment` (`density.py`); **keep the clamp-policy divergence** (return the raw ratio / take a `clamp` flag). - GUARD: `test_density` TestDistanceToSegment + on-boundary.
- [ ] **material-image-node-walk** - route both inner loops through `iter_material_image_nodes`; **keep atlas's `bpy.data.materials` outer scope**. - GUARD: atlas + panel tests.
- [ ] **handlers-sync-index-to-active** - extract `_sync_index_to_active(scene, index_attr, relevant, *, source)` for outliner + slots (+ optional bone); **do jointly with `depsgraph-handler-linear-scans`** so the fast-path identity guard lands once. - GUARD: `test_outliner_selection` sync tests (+ add a slots noop-when-correct test).
- [ ] **picture-plane-warning-box** - extract `draw_picture_plane_warning(col, bone, hint_lines)` into `panels/_helpers.py`; `slots.py` + `_draw_bone_attach.py` pass their own hints + keep their own guard condition. - GUARD: panel-draw tests (optional label snapshot).
- [ ] **selection-mode-snapshot-dup** - extend `core/bpy_helpers/_shared/select.py` with `SelectionModeSnapshot.capture()` shared by `authoring_session` + `modal_session`; **keep the restore divergence** (authoring's "active untouched when mode unchanged" vs modal's unconditional). - GUARD: add the "active untouched when mode unchanged" test FIRST, then unify capture only.

## Phase 4 - Low-severity bugs + performance

Low bugs:

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

Performance:

- [ ] **arc-length-resample-quadratic** - `geometry.py arc_length_resample`: carry `accumulated` incrementally; delete `edge_index_start_distance` (this dissolves **perimeter-length-dup**). - GUARD: `test_geometry` TestArcLengthResample (behavior-equivalence, non-flaky).
- [ ] **depsgraph-handler-linear-scans** - `_handlers.py`: add the bone variant's fast-path identity guard to the outliner + slots sync (jointly with the `handlers-sync-index-to-active` DRY fix). - GUARD: `test_outliner_selection` noop-when-correct.
- [ ] **steiner-filter-quadratic** - `bridge.py _compute_steiner_points`: bbox-reject per hole before the full `point_in_polygon`. - GUARD: NO GUARD - add a pure equivalence test (bbox-pruned == brute-force).
- [ ] **read-alpha-grid-full-walk** - `bridge.py read_alpha_grid`: cache the `AlphaGrid` per `(image, downscale)` for the modal session. - GUARD: NO GUARD - add a `_max_alpha_in_block` unit test first (pure), then the cache.
- [ ] **find-best-inner-rotation-quadratic** - `geometry.py`: cap the search window (numpy-free contract) or correct the docstring. - GUARD: `test_geometry` TestFindBestInnerRotation.

## Phase 5 - Test-quality (the one medium + hardenings + organization)

- [ ] **edit-weights-modal-lifecycle** (MEDIUM) - cover `modal` / `_finish` via the `_Probe` pattern from `test_quick_armature_modal.py`: TIMER external-exit, ESC->cancel, raising tracker->`_finish(cancel)`, `_finish` removes timer/overlay/statusbar + auto-snapshot only on non-cancel + `restore_session` always (stubs must raise to prove the suppress).
- [ ] **edit-weights-invoke-reimplements** - extract `_enter_weight_paint(context, obj, armature, *, mirror_x)`; `invoke` + the test both call it.
- [ ] **eval-frame-sandbox** - add a restricted-eval failure-mode test for `_eval_frame` (math/var resolves; name errors / disallowed builtins / non-numeric -> None). (Not RCE - build-time tool.)
- [ ] Tighten the weak assertions: **test_contour single-hole** (assert bbox `(4,5,4,5)`), **test_geometry upsample** (assert uniform spacing), **test_vertex_pen edge-landing** (assert `(1.0,0.0)` + `(2.0,1.0)` in ring), **test_sprites dropped-group** (`capsys` assert the warn), **test_skinning_modes proximity** (assert 0.5/0.5 split).
- [ ] Coverage adds: **draw-mesh `_output`** (StageOutput `outer_is_manual` + provisional fold stroke via `_Probe`), **contour-islands shoelace-area** assert, **auto-snapshot reverse-truncate** case, **weight-transfer** `assert len(dup.vertex_groups) == 0` after CANCELLED, **storage-proxy** `assert proscenio.vframes == 2`.
- [ ] Organization: split **automesh-test-monolith** (38 tests) by concern + a StageParams conftest factory; add **tests/automesh/conftest.py** for the `sys.path` + bpy-mock prelude (070's files copy-paste it).

## Phase 6 - Dead module removal (O2 resolved: delete)

- [ ] **psd-naming-module-orphaned** - delete `apps/blender/core/psd/psd_naming.py` + `tests/test_psd_naming.py`. Verified: spritesheet frames are authored in Photoshop (`[spritesheet]` tag -> `planner.ts` -> explicit manifest `frames` list) and Blender consumes the manifest; the Blender-side guess-from-layer-names module is the wrong layer and has zero callers. No feature lost. - GUARD: full import + suite stays green after removal.

## Structural decomposition -> spec 075 (NOT here)

The entire god-modules / SRP decomposition theme (the 3 large splits `automesh-authoring-operator` / `quick-armature-operator` / `skinning-props-pg`, the ~14 smaller SRP extractions, and `no-orphan-sweep`'s per-instance->ClassVar refactor) moved to [075-blender-structural-decomposition](../075-blender-structural-decomposition/TODO.md) per D4 - actively worked, not gated. Coordinate the overlaps: `automesh-snap-math-dup` / `place-and-tag-hidden-dep` (here, Phase 3) touch files 075 splits; land the 074 cleanup first or note the conflict.

## Post-merge cleanup (ONLY after the final phase merges)

- [ ] Drain [backlog/code-audit/](../backlog/code-audit/) - the resolved findings leave; rewrite `bugs.md` with the confirmed/refuted verdicts (or remove it); any genuinely-deferred remainder moves to [deferred.md](../deferred.md) / [gated.md](../gated.md).
- [ ] Prune this spec folder; index in [`index.md`](../index.md) with the PR number(s) (074 -> pruned).
