# SPEC 013 - TODO

Weight paint ergonomics + automesh. See [STUDY.md](STUDY.md) for the full design + decisions D1-D16 (locked at planning time after 9-tool survey + 6-theme community-pain synthesis).

Waves:

- **Wave 13.1** = first cut, SHIPPED (automesh + hole-support amendment via PR #51).
- **Wave 13.2** = follow-up features that close the bind / paint / sidecar / interactive-authoring story. Features listed by name; pick the order at start-of-wave per dependency notes below.
- **Wave 13.3** = productivity polish (region painting, multi-mesh batch, weight transfer, soft/hard bone toggle, etc).
- **Wave 13.4** = aspirational (Auto-Patch joint cover, Cubism Glue equivalent, Smart Bones).

Sub-letter numbering (13.1.a / 13.1.b / 13.1.c …) was tried in iteration and got noisy fast. Each wave now holds named features instead. Commit history retains the old labels for the PR #51 work.

## Decision lock-in

- [ ] D1 - automesh paradigm = alpha-trace one-shot (pure-Python, no OpenCV).
- [ ] D2 - mesh topology shape = annulus (outer + inner contour + Constrained Delaunay). **Amended (Wave 13.1, hole support):** alpha holes now cut out of the mesh via explicit per-hole constraint loops + centroid-based post-process face prune.
- [ ] D3 - mesh data preservation anchor = `proscenio_base_sprite` vertex group; re-runs remove only verts NOT in this group.
- [ ] D4 - bone heat solver usage = explicit user opt-in only, NEVER default. **Amended (Wave 13.2-panel):** BONE_HEAT now allowed as default for 2D pickers; D11 pre-flight still runs before every bind path. See STUDY.md D4 amendment for trigger.
- [ ] D5 - initial bind algorithm default = planar proximity falloff (custom, NOT bone heat); enum offers PROXIMITY / ENVELOPE / SINGLE_NEAREST / EMPTY. **Amended (Wave 13.2-panel):** enum gains BONE_HEAT as 5th value AND becomes the default; planar proximity demoted to fallback per D4 amendment.
- [ ] D6 - weight preservation through mesh regen = sidecar JSON keyed by UV anchors + auto-reproject on regen + visible provenance overlay.
- [ ] D7 - weight paint modal wrapper = one-button enter / exit, auto-restore on exit + crash; lift COA2 `COATOOLS2_OT_EditWeights` pattern (fixed: Bone Collections instead of `bone.hide` global, `try/finally` restore, ESC hard-exit).
- [ ] D8 - 2D paint preset = auto-apply on modal enter (`Front Faces Only=False`, `Falloff=Projected`, brush radius in screen px, `Auto Normalize=True`); header pill "2D paint preset: ON".
- [ ] D9 - GPU weight overlay viz = colorband discs per vertex (lift COA2 6-stop colorband, alpha 0 for zero-weight verts).
- [ ] D10 - ESC in any draw modal = hard exit + release pending stroke; no conditional behaviour.
- [ ] D11 - pre-flight diagnosis on auto-weight failure = structured guidance per failure cause; pre-flight detects unapplied scale / flipped normals / overlapping verts / isolated islands / bones outside mesh bbox; emits actionable message (never raw stack trace).
- [ ] D12 - tablet RELEASE detection = `event.pressure==0` + `WINDOW_DEACTIVATE` + timer-based fallback (synthesize RELEASE if no movement for N ms).
- [ ] D13 - subpanel placement = new `Skinning` subpanel parallel to `Skeleton` in the Proscenio sidebar.
- [ ] D14 - symmetry mirror axis source = picker armature mirror flag (single source of truth, parallel to SPEC 012 D16 contract).
- [ ] D15 - density-under-bones automesh = ON by default when picker has armature, OFF otherwise; reuse picker bone positions.
- [ ] D16 - soft vs hard bone toggle = defer to Wave 13.3 (Wave 13.2 covers via `bind_init_mode` PROXIMITY vs SINGLE_NEAREST).

## Wave 13.1 - SHIPPED (PR #51)

First-cut automesh + alpha hole support. Lifted Spine / COA2's "no holes" restriction so Proscenio differentiates from both surveyed tools.

What landed:

- Pure-Python alpha contour walker (Moore neighbour + 4/8 binary morphology); zero third-party Python deps.
- Annulus topology with outer + inner contour + interior Steiner points fed into Constrained Delaunay (`mathutils.geometry.delaunay_2d_cdt`).
- Alpha hole detection: background islands fully enclosed by foreground are traced as constraint loops + cut out via centroid post-process face prune. Loose edges / verts cleaned after.
- Density-under-bones (D15): when picker armature exists, Steiner points cluster along bone segments.
- `proscenio_base_sprite` vertex group preserves the original 4 quad corners across regens (D3).
- Debug pipeline stages (raw_contours / smoothed / resampled / interior_points / bridges / fill_no_interior / final): each emits a wireframe companion in the `Proscenio.Debug` collection without committing to the active mesh (except `fill_no_interior` + `final` which do commit, intentionally).
- 5 fixtures (blob / lshape / hand / ring / swirl). Swirl is hi-res AA 512x512 "8-shape" with 2 holes - smoke target for the multi-hole + smooth-curvilinear silhouette paths.
- Headless `validate_automesh.py` per-pixel coverage + hole-bleed metrics + RGBA debug PNG output. Wired into CI via `--ci-only` filter that skips heavyweight fixtures (swirl) to keep CI runtime under budget.

## Wave 13.2 - follow-up features

Pick features per dependency notes; not all need shipping in a single PR. Recommended start order: cleanup → bind → paint → sidecar → panel → interactive modal → docs.

### Code-quality cleanup (prerequisite for everything else)

Branch: `refactor/spec-013-cleanup`.

Sonar local + warnings emitted during PR #51 review iteration:

**Hot spots (cognitive complexity, limit = 15)**:

| File:Line | Function | Cognitive |
| --- | --- | --- |
| `scripts/validate_automesh.py:316` | `_measure_coverage` | 47 |
| `apps/blender/core/alpha_contour.py:125` | `erode` | 31 |
| `scripts/validate_automesh.py:521` | `main` | 30 |
| `apps/blender/operators/automesh.py:205` | `execute` | 24 |
| `apps/blender/core/alpha_contour.py:92` | `dilate` | 22 |
| `scripts/validate_automesh.py:477` | `_check_invariants` | 20+ |
| `apps/blender/core/bpy_helpers/automesh_bmesh.py:498` | `_build_mesh_via_delaunay` | 20 |
| `scripts/validate_automesh.py:159` | `_resolve_image` | 19 |
| `scripts/validate_automesh.py:270` | `measure_mesh` | 18 |
| `apps/blender/core/bpy_helpers/automesh_bmesh.py:102` | `read_alpha_grid` | 18 |
| `apps/blender/core/bpy_helpers/automesh_bmesh.py:757` | `build_automesh` | 18 |

**Other**:

- `automesh_bmesh.py` = 1063 LOC (3.5x the 300 LOC smell threshold).
- `validate_automesh.py` = 660 LOC (2x threshold).
- `_point_in_triangle_xz` duplicated across `automesh_bmesh.py` + `validate_automesh.py` (DRY violation).
- `_fill_inner_via_delaunay` + `_build_annulus_strip` in `automesh_bmesh.py` = DEAD CODE after the single-pass CDT refactor (no callers found via grep). Delete in cleanup.
- SPRITE_BOUNDS shape repeated 5 times in validator (S1871).
- Validator's duplicate-branch in argparse setup (S1871).
- Sonar S101 false positives on `PROSCENIO_OT_*` / `PROSCENIO_PT_*` (46 across project) - configure Sonar to ignore the same way ruff already does.

**Concrete checklist (each item = 1 commit)**:

1. Configure `sonar-project.properties` to ignore S101 on `PROSCENIO_OT_/PT_` class names.
2. Delete dead code (`_fill_inner_via_delaunay`, `_build_annulus_strip`) from `automesh_bmesh.py`.
3. Extract `apps/blender/core/geometry_2d.py` with shared `point_in_triangle_xz`. Update both callers; delete dups.
4. Refactor `alpha_contour.dilate` + `erode` (cognitive 22 / 31). Extract `_single_dilate_pass` + `_single_erode_pass` helpers; outer loops become thin wrappers.
5. Reorganize automesh into a domain package:
   - `apps/blender/core/automesh/` package with:
     - `__init__.py` (re-exports public surface)
     - `contour.py` (current `alpha_contour.py` content)
     - `geometry.py` (current `automesh_geometry.py` content)
     - `density.py` (current `automesh_density.py` content)
   - `apps/blender/core/bpy_helpers/automesh/` package with:
     - `__init__.py` (re-exports `build_automesh`)
     - `bridge.py` (orchestrator + read_alpha_grid + pixel_contour_to_world)
     - `cdt.py` (`_build_mesh_via_delaunay` + `_delete_faces_inside_holes`)
     - `base_sprite.py` (vertex group `_initialize` / `_delete` / `_remove`)
     - `uv.py` (`_stamp_uvs`)
     - `debug.py` (current `automesh_debug.py` content)
6. Refactor `build_automesh` (1063 LOC monolith). Extract per-stage helpers: `_extract_contours_world`, `_smooth_resample`, `_compute_interior_steiners`, `_apply_cdt_to_mesh`. Orchestrator becomes < 60 LOC.
7. Refactor `_measure_coverage` (cognitive 47). Extract `_iterate_pixels`, `_classify_pixel`, `_paint_debug_pixel`, `_record_leak`.
8. Refactor validator main (cognitive 30). Extract `_filter_ci_safe_sprites`, `_print_report`, `_write_report_json`.
9. Split validator into package `scripts/automesh_validator/` (keep `scripts/validate_automesh.py` as a thin shim so CI + manual invocations stay on the same path):
   - `cli.py` (argparse + `main` orchestrator)
   - `coverage.py` (`measure_coverage` + `compute_hole_pixel_mask` + `_classify_pixel` + `CoverageContext`)
   - `invariants.py` (`SpriteInvariants` + `SPRITE_BOUNDS` + `check_invariants`)
   - `measurement.py` (`measure_mesh` + `run_validation` + `_resolve_image`)
   - `report.py` (console + JSON output formatting)
   - `addon_loader.py` (`load_and_register_addon` + `ensure_core_on_sys_path`)
10. SPRITE_BOUNDS dedup (S1871). Define `SpriteInvariants` `@dataclass` with named fields; SPRITE_BOUNDS becomes `dict[str, SpriteInvariants]`.
11. Reorganize tests: `tests/automesh/` subdir with `test_contour.py`, `test_geometry.py`, `test_density.py`, `test_holes.py`. Pytest auto-discover continues working via root conftest.
12. Validate after each commit: `pytest tests/`, `blender --background --python apps/blender/tests/run_tests.py`, `blender --background --python scripts/validate_automesh.py -- --ci-only`. Zero behaviour drift gate.

**Project convention adopted by this cleanup**: domain packages for features. `core/<feature>/` + `core/bpy_helpers/<feature>/`. Applies forward only - other features (`atlas_packer`, `skeleton_target`, ...) migrate when next touched. No big-bang.

**Out of scope for this wave**:

- Pushing pytest coverage to Sonar (separate post-cleanup chore).
- Migrating non-automesh features to the new domain-package layout (gradual when touched).

Cost: ~1.5-2 days. Low risk thanks to validator + 313 pytest + headless fixture-diff gate.

### Planar proximity bind (D4 + D5 + D11) - SHIPPED on `feat/spec-013.2-bind`

Bind a mesh to a bone chain via a custom planar-distance algorithm that never hits the bone-heat solver; surface structured diagnosis when something goes wrong.

Spec: [`bind-design.md`](bind-design.md).
Plan: [`docs/superpowers/plans/2026-05-17-spec-013.2-bind.md`](../../docs/superpowers/plans/2026-05-17-spec-013.2-bind.md).

What landed:

- Pure modules under `apps/blender/core/skinning/`: `planar_proximity.py` (1/dist^power normalized), `bind_diagnosis.py` (5 D11 pre-flight checks), `skinning_modes.py` (PROXIMITY / ENVELOPE / SINGLE_NEAREST / EMPTY dispatcher), `sidecar_schema.py` (WeightSidecar stub + topology hash). 32 pure pytest tests covering them.
- bpy-bound helpers under `apps/blender/core/bpy_helpers/skinning/`: `diagnose_collect.py` (KD-tree overlap above 1k verts) + `bind_apply.py` (vertex group write + sidecar JSON stamp).
- Operator `apps/blender/operators/bind_mesh.py` -> `PROSCENIO_OT_bind_mesh_to_armature` with F3 properties (bind_init_mode / falloff_power / max_distance / use_bone_heat).
- Sidecar stub: `obj["proscenio_weight_sidecar"]` JSON written atomically AFTER vertex groups succeed. Wave 13.2-sidecar wave populates `entries` later.
- NEW test layer: headless operator pytest at `apps/blender/tests/operators/test_bind_mesh.py` (6 tests via `blender --background --python apps/blender/tests/run_operator_tests.py`). Pattern documented in `.ai/conventions.md` "Headless operator pytest pattern".
- CI wired: `Headless operator tests` step added to `test-blender` job; pytest installed into Blender's bundled Python at job start.
- MANUAL_TESTING.md gained one UI-only residue entry (1.20) for the panel button + F3 redo smoke; everything else covered headless.

Out of scope (deferred):

- Coverage report pipeline (pytest-cov + sonar push).
- Hypothesis property-based testing.
- ENVELOPE radii editor UI (Wave 13.2-paint owns it; bind alone exposes radii via per-bone `proscenio_envelope_radius` Custom Property + fallback 1.0).
- Scene PropertyGroup persistence for bind_init_mode / falloff_power / max_distance (Wave 13.2-panel).
- Sidecar `entries` population + reproject (Wave 13.2-sidecar).

### Weight paint modal wrapper (D7 + D8 + D9 + D10 + D12 + D14)

One-button entry into a 2D-safe weight paint context with custom overlay + hard guarantees on exit cleanup + ESC handling.

- `core/paint_preset_2d.py`: frozen `PaintPresetSnapshot` dataclass with 8 brush toggles. `apply_preset(snapshot)` returns previous values for restore.
- `core/bpy_helpers/paint_preset_bind.py`: reads / writes `context.tool_settings.weight_paint`. Mirror axis pulled from `scene.proscenio.active_armature` mirror flag (D14).
- `core/bpy_helpers/weight_overlay.py`: GPU `draw_handler_add` callback drawing 6px filled discs per vertex coloured by active vertex group weight via 6-stop colorband. Alpha 0 for zero-weight verts. Toggle to draw provenance instead (D6 hook).
- `operators/edit_weights.py`: `PROSCENIO_OT_edit_weights_modal`. Snapshot brush + viewport + Bone Collections + active + selection on invoke; switch armature to POSE, mesh to WEIGHT_PAINT, apply 2D preset, auto-select vertex group matching first selected pose bone, register overlay + header pill. ESC = hard exit (D10). `WINDOW_DEACTIVATE` triggers in-flight stroke flush. D12 tablet release via `event.pressure` when available. `_finish` / `cancel` restore via try/finally; wraps cumulative paint in single undo push.
- `core/bone_collection_visibility.py`: Bone Collections visibility (Blender 4.0+) instead of COA2's `bone.hide` global flag. Snapshot + restore round-trip.
- Header pill via `_draw_statusbar_edit_weights` (reuse SPEC 012 D6 chord-layout helper). Icons: `EVENT_ESC`, `MOD_MIRROR`, `BRUSHES_ALL`.
- Crash safety: any exception hits `_finish` via try/except/finally; log to console; report INFO with restoration message.

Tests (pytest, bpy-free):

- `tests/test_paint_preset_2d.py` - apply_preset returns prior values; idempotent restore.
- `tests/test_bone_collection_visibility.py` - snapshot + restore via SimpleNamespace mocks; covers empty-collections + Blender-3.x-fallback.
- Modal smoke deferred to MANUAL_TESTING.md.

### Weight sidecar + reproject (D6) - the differentiator

Make automesh regen non-destructive. Once a user has painted weights, regenerating the mesh at a different resolution preserves their work via UV-anchored re-projection.

- `core/weight_sidecar.py`: `WeightSidecar` dataclass with vertex_group_names + entries (uv_anchor + weights + provenance) + mesh_topology_hash.
- `core/weight_reproject.py`: `reproject(sidecar, new_vertex_uvs)`. For each new vertex, find 3 nearest UV anchors, barycentric-interpolate weights, mark `reprojected`. Verts with no close anchor fall back to proximity seed, marked `auto_seed`.
- `core/bpy_helpers/sidecar_io.py`: serialize to JSON, write to `obj["proscenio_weight_sidecar"]` Custom Property (survives addon disable per SPEC 005 storage rules).
- Automesh integration: when `scene.proscenio.skinning.preserve_on_regen` is True and object has non-zero sidecar entries: snapshot current weights, regenerate mesh, reproject onto new topology, INFO with counts.
- `operators/restore_weight_snapshot.py`: `PROSCENIO_OT_restore_weight_snapshot`. Re-applies sidecar to current mesh without regen.
- Provenance hooks: bind tags all verts `auto_seed`; edit weights modal tags painted verts `user_paint` via diff. Panel pill: "187 paint / 42 seed / 0 reprojected".
- Vertex provenance overlay toggle on weight overlay (user_paint = white outline, auto_seed = gray, reprojected = cyan).

Tests (pytest, bpy-free):

- `tests/test_weight_sidecar.py` - serialize/deserialize round-trip, topology hash detects changes, JSON shape stable.
- `tests/test_weight_reproject.py` - identical-topology = no-op; coarser-to-finer interpolates correctly; verts with no close anchor fall back to auto_seed.

Sprite-changed-in-Photoshop workflow (from PR #51 smoke discussion) is exactly this feature: artist edits PNG, re-exports, automesh regen reprojects weights via UV anchors instead of forcing manual repaint.

### PropertyGroup + Skinning panel (D13) - SHIPPED on `feat/spec-013.2-panel`

Wave 13.2-panel: Bind sub-box landed in the existing `PROSCENIO_PT_skinning` panel; bind operator pivots to BONE_HEAT default (D4 amendment).

Spec: [`panel-design.md`](panel-design.md).
Plan: [`docs/superpowers/plans/2026-05-20-spec-013.2-panel.md`](../../docs/superpowers/plans/2026-05-20-spec-013.2-panel.md).

What landed:

- `ProscenioSkinningProps` gains `bind_init_mode` (5-value enum, default BONE_HEAT) + `bind_falloff_power` + `bind_max_distance`. Settings persist across `.blend` reloads.
- `BindMode` literal gains `BONE_HEAT` value. `bind_weights_for_mode` returns None for BONE_HEAT (sentinel for the bpy caller to delegate to Blender).
- `apply_bind` dispatches to `_apply_bone_heat` (delegates to `bpy.ops.object.parent_set(ARMATURE_AUTO)`) when mode is BONE_HEAT; same counters shape + sidecar JSON as the algorithm path.
- `PROSCENIO_OT_bind_mesh_to_armature` removes `use_bone_heat` BoolProperty, expands enum, adds `invoke()` reading PG defaults, surfaces "try PROXIMITY as fallback" hint when bone heat fails.
- `PROSCENIO_PT_skinning` gains `_draw_bind_box` helper between Automesh and Debug sub-boxes. Mode dropdown + button; button disabled when picker armature missing.
- Headless tests updated: happy_path + sidecar tests now exercise BONE_HEAT default; new test pins PROXIMITY fallback path.
- MANUAL_TESTING 1.20 rewritten with concrete panel steps for both BONE_HEAT default + disabled-button-when-picker-missing.

Out of scope (deferred):

- Edit Weights sub-box (Wave 13.2-paint).
- F3 menu binding (cross-cutting addon change, separate concern).
- Fixing the projection bug + tightening falloff in PROXIMITY (PROXIMITY is now a rarely-used fallback; low priority).

### Weight sidecar - snapshot + reproject - SHIPPED on `feat/spec-013.2-sidecar`

Wave 13.2-sidecar: WeightSidecar.entries populates on bind + reprojects across automesh regen via UV-anchor barycentric interpolation. Materializes D6 (the differentiator vs Spine / COA Tools 2).

Spec: [`sidecar-design.md`](sidecar-design.md).
Plan: [`docs/superpowers/plans/2026-05-20-spec-013.2-sidecar.md`](../../docs/superpowers/plans/2026-05-20-spec-013.2-sidecar.md).

What landed:

- `SidecarEntry(uv_anchor, weights, provenance)` dataclass + `ProvenanceKind` literal (auto_seed / user_paint / reprojected). `WeightSidecar.entries` widens to `list[SidecarEntry]`. `from_json` validates provenance values.
- Pure `weight_reproject.py` - hand-rolled O(n) KNN + 2D barycentric over UV anchors. Zero bpy / mathutils import.
- bpy `sidecar_io.py` - `snapshot_sidecar` builds populated sidecar from vertex_groups + active UV layer; `apply_sidecar` writes entries back. UV missing falls back to empty entries (best-effort).
- bpy `automesh_hook.py` - `maybe_pre_regen_snapshot` + `maybe_post_regen_reproject`; T4 identical-hash short-circuit, T8 UV-missing fallback applies in BOTH paths (pre-regen snapshot returns empty entries; post-regen reproject WARNs + writes auto_seed stub - never aborts), normal reproject path replaces None results with auto_seed empty-weights.
- `apply_bind` (both planar + BONE_HEAT paths) stamps populated `auto_seed` entries via `snapshot_sidecar` instead of empty stub.
- `ProscenioSkinningProps` gains `preserve_on_regen` (default ON, U1) + `show_provenance_overlay` (default OFF, U2; GPU draw handler ships in Wave 13.2-paint).
- `automesh_from_sprite` execute() brackets `build_automesh` with the pre/post hook pair; status bar reports `sidecar: X reprojected + Y auto-seed of Z verts`.
- `PROSCENIO_OT_restore_weight_snapshot` operator - reapplies stored sidecar, errors on topology mismatch.
- `PROSCENIO_PT_skinning` gains `_draw_snapshot_box` helper - toggles + counts pill (paint/seed/reprojected) + Restore button (greyed out without sidecar).
- Refactor: dedupe `BASE_SPRITE_GROUP_NAME` import + extract `wipe_non_base_groups` into `_helpers.py`.
- Headless tests: 4 new (automesh_regen x2 + restore_snapshot x2). Pure tests: 10 new (reproject x8 + entry round-trip x2). Total 47 pure + 11 headless.
- MANUAL_TESTING 1.21 covers 6 T-cases (populate / regen / restore / counts / disabled-button / topology-error).

Out of scope (deferred):

- Provenance overlay GPU draw handler -> Wave 13.2-paint.
- Live `user_paint` provenance tagging via paint modal diff -> Wave 13.2-paint.
- Sidecar import/export to external file -> Wave 13.3.
- `proscenio.copy_weights_to_selected` cross-mesh transfer -> Wave 13.3.

### Edit Weights modal + provenance overlay - SHIPPED on `feat/spec-013.2-paint`

Wave 13.2-paint: one-button entry into 2D-safe weight paint with GPU provenance overlay, per-stroke `user_paint` flip via diff, hard ESC exit, Edit Weights sub-box in panel.

Spec: [`paint-design.md`](paint-design.md).
Plan: [`docs/superpowers/plans/2026-05-21-spec-013.2-paint.md`](../../docs/superpowers/plans/2026-05-21-spec-013.2-paint.md).

What landed:

- `PaintPresetSnapshot` frozen dataclass + `PRESET_2D` constant (Front Faces locked OFF per T46254 regression guard). Symmetric apply/restore.
- Pure `weight_diff.py` - diff_weights with eps tolerance; missing-vert in either side counts as touched.
- `bone_collection_visibility.py` - Blender 4.0+ Bone Collections snapshot/restore with 3.x bone.hide fallback. Module is bpy-free (duck-typed inputs).
- `paint_preset_bind.py` - reads/writes tool_settings.weight_paint with defensive hasattr checks for API drift.
- `weight_overlay.py` - POST_VIEW GPU draw handler. UNIFORM_COLOR shader; one POINTS batch per provenance color (cyan/white/gray). Mode='weight' branch reserved for Wave 13.3.
- `stroke_diff.py` - StrokeDiffTracker class. Pre-stroke snapshot + post-stroke diff + flip touched entries' provenance to user_paint + rewrite sidecar JSON.
- `modal_session.py` - EditWeightsSession dataclass + capture + restore. Object lookups by name so restore survives undo-driven object recreation.
- `PROSCENIO_OT_edit_weights_modal` - mono-operator owning invoke/modal/finish. ESC hard-exit, WINDOW_DEACTIVATE flushes in-flight stroke, MOUSEMOVE+pressure=0 catches pen-lift.
- Skinning panel gains Edit Weights sub-box between Bind + Snapshot. Button greys out when picker or sidecar missing.
- Headless tests: 5 new. Pure tests: 11 new (paint_preset x4 + weight_diff x4 + bone_collection_visibility x3). Total 58 pure + 16 headless.
- MANUAL_TESTING 1.22 covers 6 T-cases (enter modal / stroke / ESC restore / Reload Scripts / single undo / disabled button).

Out of scope (deferred):

- Weight-gradient overlay UI toggle -> Wave 13.3.
- Per-bone soft/hard mode toggle (D16) -> Wave 13.3.
- proscenio.copy_weights_to_selected cross-mesh transfer -> Wave 13.3.
- Smart Bones / corrective drivers -> Wave 14+.
- Live pose-mode preview in weight paint -> Wave 13.3.
- Brush curve presets ("Hard edge" / "Soft falloff" / "Crease") -> Wave 13.3.

### Interactive modal automesh - SHIPPED on `feat/spec-013.2-interactive-modal`

Wave 13.2-interactive-modal: 5-stage modal preview of the automesh pipeline. Each stage (outer contour / inner loops / user Steiner points / Steiner preview / apply) shows a GPU overlay; sliders re-run live; user Steiners click-place + persist via Custom Property. Final APPLY pipes through build_automesh + Wave 13.2-sidecar reproject so existing weights survive.

Spec: [`interactive-modal-design.md`](interactive-modal-design.md).
Plan: [`docs/superpowers/plans/2026-05-22-spec-013.2-interactive-modal.md`](../../docs/superpowers/plans/2026-05-22-spec-013.2-interactive-modal.md).

What landed:

- `AuthoringStage` IntEnum + `StageParams` (frozen, equality-based dirty detection) + `StageOutput` (mutable, accumulates across stages).
- Pure `erosion_loops.py` - hand-rolled wrapper around contour.erode + find_first_boundary + trace_contour. Computes N successively-eroded inner loops from a base mask.
- bpy `authoring_session.py` - capture/restore prior viewport state via name-based object lookups.
- bpy `authoring_overlay.py` - POST_VIEW GPU draw handlers per stage. UNIFORM_COLOR shader (shared with modal_overlay). LINE_STRIP for polylines + POINTS for dots. All GPU state wrapped in try/finally so failures do not leak point_size or blend.
- bpy `authoring_pipeline.py` - per-stage compute + apply_mesh terminal helper. apply_mesh invokes maybe_pre_regen_snapshot + maybe_post_regen_reproject from Wave 13.2-sidecar so existing weights survive APPLY (B1 fix preserves user_paint provenance).
- `PROSCENIO_OT_automesh_authoring` modal operator - invoke captures session + computes OUTER + registers overlay + starts 100ms TIMER. ENTER advances; BACKSPACE retreats; ESC cancels. LEFTMOUSE (USER_STEINERS) click-places; Shift+LEFTMOUSE deletes nearest within world threshold. TIMER polls StageParams + recomputes current stage on PG diff (throttled slider re-run).
- Skinning panel gains Automesh authoring sub-box between Automesh one-shot + Bind. Coexists - one-shot stays as the quick path.
- ProscenioSkinningProps gains authoring_inner_loop_count (default 2) + authoring_inner_loop_spacing (default 0.15).
- Headless tests: 5 new. Pure tests: 8 new (erosion_loops x5 + authoring_stages x3). Total 69 pure + 21 headless.
- MANUAL_TESTING 1.23 covers 6 T-cases (enter modal / slider live re-run / click placement / shift-click delete / APPLY commit / APPLY preserves weights).

Known gap (deferred to Wave 13.3 or build_automesh extension PR):

- **apply_mesh does not consume output.user_steiners + output.inner_loops at APPLY.** build_automesh today does its own full pipeline; the modal's previewed inner loops + user-placed Steiners are PREVIEW-ONLY. Custom Property persistence is in place so a future build_automesh extension (accept optional user_steiners + inner_loops_override constraints) can honor them without further modal changes. Cleanup prerequisite (cognitive-47 build_automesh refactor) becomes a blocker for closing this gap.

Out of scope (deferred):

- User-drawn inner loops (free-draw polylines as CDT constraint edges) -> Wave 13.3.
- Drag-stroke Steiner placement (multiple points per drag) -> Wave 13.3.
- Brush stroke for alpha-boundary trace (D1.B paradigm enum) -> Wave 13.3.
- Stage 4 editable Steiners (drag-to-move, delete-with-X) -> Wave 13.3.
- Pose-mode preview mid-modal -> Wave 13.3.
- build_automesh extension to honor authoring inputs at APPLY -> blocking on cleanup prerequisite.

### Interactive modal automesh authoring (original brainstorm sketch, superseded by SHIPPED block above)

User reflection after PR #51: one-shot produces over-dense meshes for simple sprites AND user has no in-flight course correction. Modal lifts each existing debug stage to interactive preview.

Proposed pipeline (each step = a modal stage the user can step forward / backward through):

1. **Outer contour preview.** GPU overlay of the outer polyline. User adjusts resolution / alpha threshold / margin via N-panel; preview re-runs live.
2. **Inner subdivision loops.** N concentric inner-loop polylines (morphological erosions of the outer at increasing kernel sizes). User picks count + spacing via slider. These are CONSTRAINT edges the eventual Delaunay respects, giving user control over where edge loops sit before any face exists.
3. **User-pointed interest points.** Free-draw / click overlay where user marks Steiner points to preserve (muscle bulges, fold seams). Unifies with the user-drawn density markers idea below but at coarser level (single points, not painted regions).
4. **Steiner preview.** GPU dots for the full Steiner cluster (uniform / bone-density / user-pointed) before any triangulation. User refines spacing / density per region.
5. **Apply.** Run CDT with outer + inner loops + holes + user Steiners + bone Steiners as constraints; post-process face prune; write to mesh.

Restructures `build_automesh` from "one function that produces a mesh" into "a state machine that surfaces each pipeline stage as an interactive preview". The current debug stages are the SKELETON of this state machine; the modal lifts each from "print + debug wireframe" to "GPU overlay + user input + step forward".

Implementation sketch:

- New modal operator `proscenio.automesh_authoring` (parallel to current `automesh_from_sprite`, NOT replacing - one-shot stays as the quick path).
- Modal uses same GPU overlay scaffold as Quick Armature (`core/bpy_helpers/modal_overlay.py`). Header pill shows current stage + ESC=cancel + ENTER=next + BACKSPACE=prev.
- Each stage's parameters in `scene.proscenio.skinning.authoring_*` so the user can resume mid-modal after a viewport interaction.
- Inner subdivision loops = N polylines computed as morphological erosions of outer contour. Reuses `dilate`/`erode` from `alpha_contour`.
- User-pointed Steiners stored on mesh as `proscenio_user_steiners: list[(x, z)]` Custom Property; persist across regens.
- Final apply pipes everything into existing `_build_mesh_via_delaunay` + `_delete_faces_inside_holes` chain.

Open decisions when this feature starts (need a `/brainstorming` session):

- Does the modal REPLACE one-shot or COEXIST? (Recommendation: coexist.)
- Inner loops as N concentric erosions, OR user-drawn polylines, OR both?
- User-pointed Steiners join the weight sidecar (keyed by UV anchor) for survival across regen?

Prerequisites:

- Code-quality cleanup complete (cognitive-47 monolith is hostile to per-stage lifting).
- Weight paint modal scaffold shipped (provides modal-lifecycle patterns to lift).

### Docs + smoke

- [x] `.ai/skills/blender-dev.md` "Edit Weights modal pattern" subsection (companion to SPEC 012's modal overlay + hint placement patterns). Covers snapshot + apply + restore + try/finally crash safety + Bone Collections visibility + per-stroke provenance diff.
- [x] `.ai/skills/blender-dev.md` "Pure-Python image processing" extended with weight_reproject hand-rolled KNN + barycentric note (same no-third-party-deps rule extends to sidecar wave).
- [x] `.ai/skills/format-spec.md` "Skinning weights" gains "Authoring story" subsection cross-referencing SPEC 013 waves (automesh + bind + edit + reproject + restore).
- [x] `tests/MANUAL_TESTING.md` 1.20 (bind/panel) + 1.21 (sidecar) + 1.22 (paint) cover T-cases for bind / edit / snapshot / reproject. 1.19 reserved for Wave 13.1 automesh-only flows.
- Reload-Scripts safety smoke - re-run "Reload Scripts" after entering Edit Weights modal; verify no orphan draw handlers, no panel crash, brush state restored. (Pending - manual T-case to add to 1.22.)
- Cross-armature smoke - bind mesh to one armature, change picker to another, re-bind; verify sidecar persists and reprojects. (Pending - manual T-case to add to 1.20 or 1.21.)
- Headless Blender script via `--background --python` to confirm registration / unregister cycle clean. (Pending - separate effort; the existing `run_operator_tests.py` runner covers ops registration as a side effect of fixture load.)

## Wave 13.3 - productivity polish

Productivity layer on top of Wave 13.2. Each item is self-contained; ship in its own PR when the trigger lands.

- **Soft vs Hard bone toggle (D16, Animate lift).** Per-bone enum on vertex group metadata (`group.proscenio_bone_mode = "SOFT" | "HARD"`); rebind re-derives respecting the mode. Soft = proximity falloff; Hard = single-nearest. Trigger: user complains proximity bleed is too soft on a specific limb.
- **Bone strength region painting (Moho lift).** Per-bone elliptical / capsule influence widget. Drag a handle along the bone to grow / shrink radius. Region drives initial weight map procedurally. Trigger: proximity default does not give enough control for shapes like long hair or tails.
- **User-drawn density markers (PR #51 smoke feedback).** Artist paints on sprite (grease pencil or GPU overlay) to mark regions of interest (muscle bulges, cloth folds, joint creases). Marks translate into extra Steiner point clusters at automesh time. Distinct from Wave 13.2's interactive modal at coarse level: this is painted REGIONS persisted on the mesh, modal is per-point clicks during authoring. Implementation sketch: `proscenio_density_marks: list[(x, z, weight, kind)]` Custom Property; per-mark color in the overlay differentiates kinds (muscle / fold / crease).
- **Multi-mesh batch bind.** Bind operator takes selected meshes (not just active); same algorithm against picker armature. Useful for character imports with N sprites + 1 rig.
- **Weight transfer between sprites.** `proscenio.copy_weights_to_selected`. Source mesh (active) + N target meshes (selected); for each target vertex, look up nearest source vertex by world position + copy weight dict. Solves COA2 issues [#18](https://github.com/Aodaruma/coa_tools2/issues/18) + [#73](https://github.com/Aodaruma/coa_tools2/issues/73).
- **Live pose-mode preview in weight paint.** Scrub the bone to a posed angle, see how the mesh deforms, scrub back without leaving Edit Weights modal. Pose-scrub overlay + hotkey to toggle rest pose.
- **Sidecar import / export to file.** Operator to dump weight sidecar JSON to / load from a file. Enables version-controlled weight backups outside the .blend.
- **Brush settings curve presets.** Quick-select named curve presets in the Edit Weights modal status pill ("Hard edge", "Soft falloff", "Crease", "Smooth blend"). Saves brush curve editor trips.
- **Bezier brush stroke for alpha-boundary trace.** Wave 13.2's free-draw alternative to the alpha-trace one-shot. Adds D1.B to the paradigm enum when real workflows demand it.

### Suspect bugs - needs investigation (manual smoke 2026-05-21)

Items observed during paint-wave manual smoke that may be real bugs OR test-flow confusion. Each needs an isolated headless repro before fixing.

- **B1: reproject does not preserve user_paint provenance.** ~~`weight_reproject.reproject_entries` always stamps `provenance="reprojected"` on new entries; if old entry was `user_paint`, the marker is lost on automesh regen.~~ **FIXED** on branch `fix/spec-013-reproject-preserves-user-paint`: `_carry_user_paint_provenance` propagates `user_paint` when any of the 3 barycentric donor anchors carried that marker (any-donor wins, conservative choice for preserving artist intent). +2 pure tests.
- **B2: chained automesh regen produces visually chaotic weights.** Smoke flow `bind -> paint -> regen 0.25 -> regen 0.3 -> regen 0.25` ended with weights scattered randomly across mesh (not the painted region). Reproject reports `135 seed / 114 reprojected of 249` so it "ran" but result is wrong. Hypothesis: UV anchors inconsistent across automesh runs (alpha walker produces different vert order each run, UV first-loop assignment shifts), OR barycentric blend producing wrong weights when donors are spread thin. Repro: needs headless test with 2 deterministic meshes + known weights + assert reproject preserves them within tolerance.
- **B3: resolution 0.5 destroys silhouette (Wave 13.1 regression).** Automesh at `Mesh resolution = 0.5` produced 44 verts / 27 faces of disconnected fragments instead of low-poly hand silhouette. Lower (0.25 default) works; 0.5 falls apart. Hypothesis: Moore-neighbour walker loses adjacency at coarse pixel stride OR hole detector misfires on downscaled binary mask. Out of scope for SPEC 013.2 (lives in alpha_contour.py). Repro: `bpy.ops.proscenio.automesh_from_sprite(resolution=0.5)` on `examples/generated/automesh/automesh.blend` hand fixture.

## Wave 13.4 - aspirational

- **Auto-Patch joint cover at articulations (Toon Boom Harmony lift).** One-click joint-cover operator. Given two child meshes sharing a parent bone, generate seam geometry + weight blend that hides the inner-elbow hole as the joint bends. Trigger: humanoid fixture lands + user complains about inner-elbow gap.
- **Cubism Glue equivalent.** Operator that seam-binds overlapping vertices of two meshes with a weight slider biasing which side dominates. Different surface than Auto-Patch (covers any seam, not just articulations).
- **Smart-Bone-style corrective drivers.** Per-bone shape key driven by bone rotation; user records a corrective pose at a specific angle and the addon emits a driver. Goes into SPEC 014 (animation system) not SPEC 013.
- **Mirror humanoid binding.** One mesh on one side, click to mirror to the other. Couples to symmetric rigs. Trigger: first humanoid fixture lands.

## Refinement log

| Commit | Change | Why |
| --- | --- | --- |
| PR #51 merged | Wave 13.1 shipped (automesh + hole-support amendment) | First-cut automesh + D2 amendment lifting Spine / COA2's "no holes" restriction; 5 fixtures including AA swirl with 2 holes |
| post-merge | Wave 13.2 cleanup feature added | Sonar warnings + cognitive-complexity drift surfaced during PR review iteration; foundation needs cleanup before bind / paint / sidecar build on top |
| post-merge | Wave 13.2 interactive modal feature added | User reflection: one-shot produces over-dense meshes for simple sprites + no in-flight course correction; modal lifts each existing debug stage to interactive user-facing preview |
| post-merge | Wave numbering deflattened (dropped 13.1.a / 13.1.b / 13.1.c …) | Sub-letter scheme got noisy fast; each wave now holds named features. Commit history retains old labels for PR #51 work |
| post-merge (Wave 13.2 bind) | Wave 13.2 bind shipped; bind-design.md spec + plan linked | Headless operator pytest pattern proven |
| post-merge (Wave 13.2 bind) | diagnose_flipped_normals convention inverted (Y>=0 = flipped, was Y<=0); `_flip_normals_to_positive_y` workaround removed from headless test | Proscenio Front Ortho convention: camera at -Y looking +Y; sprite "facing camera" = normal in -Y. Verified against automesh output (432/432 faces at Y=-1). Original assumption (+Y = correct) was inverted; fixture builder is NOT buggy, was the diagnose check |
| post-merge (Wave 13.2-panel) | D4 amended - BONE_HEAT allowed as default bind mode; Skinning panel gains Bind sub-box | Manual smoke on PR #54 surfaced bone heat produces better falloff for 2D pickers; F3-only access for bind was a UX blocker. Pivot resolves both |
| post-merge (Wave 13.2-sidecar) | Wave 13.2-sidecar shipped - populated WeightSidecar + reproject across regen + restore operator + panel Snapshot sub-box | Materializes D6 differentiator (Spine / COA2 lose weights on regen; Proscenio survives via UV-anchor barycentric reproject) |
| post-merge (Wave 13.2-paint) | Wave 13.2-paint shipped - Edit Weights modal + GPU provenance overlay + per-stroke user_paint flip + Skinning panel sub-box | Closes D6/D7/D8/D9/D10/D12/D14 - one-button entry to 2D-safe weight paint with provenance feedback the artist actually sees in the viewport |
| post-merge (Wave 13.2-interactive-modal) | Wave 13.2-interactive-modal shipped - 5-stage modal preview of the automesh pipeline + click-placed user Steiners + sidecar reproject on APPLY | Closes "Interactive modal automesh authoring" TODO item; preview-only at APPLY (build_automesh extension follows once cleanup prereq lands); coexists with one-shot automesh_from_sprite |

## Out of scope (permanently)

Rejected for SPEC 013; do not propose again without re-opening the decision:

- OpenCV / numpy as install-time dependency (COA2 adoption lesson per Constraints + D1).
- Per-brush mirror as the source of truth (D14).
- ESC as deselect-only inside any draw modal (D10).

## Successor SPECs

- **SPEC 014 (planned: animation polish)** - inherits weight-aware vertex-group machinery; Smart-Bone-style corrective drivers land there.
- **SPEC 004 (slots)** maturity unlocks auto-attach mesh to slot + per-slot weight variations.
- **A future "Quick Mesh" operator** (mentioned in SPEC 012 successor list) is the direct sibling to automesh - lift the modal scaffold from Wave 13.2's Edit Weights wrapper if pursued.
