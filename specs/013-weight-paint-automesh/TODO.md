# Weight paint + automesh - TODO

Weight paint ergonomics + automesh. See [STUDY.md](STUDY.md) for the full design + decisions D1-D21 (locked at planning time after 9-tool survey + 6-theme community-pain synthesis, plus stroke / interior-mode / gesture lock-ins from the productivity follow-up).

Scope tiers:

- **First cut, SHIPPED** (PR #51) - automesh from alpha + hole-support amendment.
- **Productivity follow-up, SHIPPED** (PRs #54, #58, #59, #61, #62, #63, #64) - bind / paint / sidecar / interactive-authoring / stroke redesign / interior modes / toggle-pen gesture. Closes the authoring loop.
- **Successor work** - productivity polish (region painting, multi-mesh batch, weight transfer, soft/hard bone toggle, etc).
- **Aspirational** - Auto-Patch joint cover, Cubism Glue equivalent, Smart Bones / corrective drivers.

Each tier holds named features. The commit history carries the older numeric tags for the SHIPPED work.

## Decision lock-in

- [x] D1 - automesh paradigm = alpha-trace one-shot (pure-Python, no OpenCV).
- [x] D2 - mesh topology shape = annulus (outer + inner contour + Constrained Delaunay). **Amended (the first cut, hole support):** alpha holes now cut out of the mesh via explicit per-hole constraint loops + centroid-based post-process face prune.
- [x] D3 - mesh data preservation anchor = `proscenio_base_sprite` vertex group; re-runs remove only verts NOT in this group.
- [x] D4 - bone heat solver usage = explicit user opt-in only, NEVER default. **Amended (the panel work):** BONE_HEAT now allowed as default for 2D pickers; D11 pre-flight still runs before every bind path. See STUDY.md D4 amendment for trigger.
- [x] D5 - initial bind algorithm default = planar proximity falloff (custom, NOT bone heat); enum offers PROXIMITY / ENVELOPE / SINGLE_NEAREST / EMPTY. **Amended (the panel work):** enum gains BONE_HEAT as 5th value AND becomes the default; planar proximity demoted to fallback per D4 amendment.
- [x] D6 - weight preservation through mesh regen = sidecar JSON keyed by UV anchors + auto-reproject on regen + visible provenance overlay.
- [x] D7 - weight paint modal wrapper = one-button enter / exit, auto-restore on exit + crash; lift COA2 `COATOOLS2_OT_EditWeights` pattern (fixed: Bone Collections instead of `bone.hide` global, `try/finally` restore, ESC hard-exit).
- [x] D8 - 2D paint preset = auto-apply on modal enter (`Front Faces Only=False`, `Falloff=Projected`, brush radius in screen px, `Auto Normalize=True`); header pill "2D paint preset: ON".
- [x] D9 - GPU weight overlay viz = colorband discs per vertex (lift COA2 6-stop colorband, alpha 0 for zero-weight verts).
- [x] D10 - ESC in any draw modal = hard exit + release pending stroke; no conditional behaviour.
- [x] D11 - pre-flight diagnosis on auto-weight failure = structured guidance per failure cause; pre-flight detects unapplied scale / flipped normals / overlapping verts / isolated islands / bones outside mesh bbox; emits actionable message (never raw stack trace).
- [x] D12 - tablet RELEASE detection = `event.pressure==0` + `WINDOW_DEACTIVATE` + timer-based fallback (synthesize RELEASE if no movement for N ms).
- [x] D13 - subpanel placement = new `Skinning` subpanel parallel to `Skeleton` in the Proscenio sidebar.
- [x] D14 - symmetry mirror axis source = picker armature mirror flag (single source of truth, parallel to the quick-armature spec D16 contract).
- [x] D15 - density-under-bones automesh = ON by default when picker has armature, OFF otherwise; reuse picker bone positions.
- [x] D16 - soft vs hard bone toggle = defer to successor work (the productivity follow-up covers via `bind_init_mode` PROXIMITY vs SINGLE_NEAREST).

## the first cut - SHIPPED (PR #51)

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

## the productivity follow-up - follow-up features

Pick features per dependency notes; not all need shipping in a single PR. Recommended start order: cleanup → bind → paint → sidecar → panel → interactive modal → docs.

### Code-quality cleanup (prerequisite for everything else) - DONE (organically through the productivity follow-up)

**Status (audit 2026-05-25):** all 5 checklist items below ended up shipped silently across the bind work / sidecar / paint / interactive-modal PRs. The prerequisite flag is removed; no separate cleanup PR needed. Validated:

- `apps/blender/core/automesh/` + `apps/blender/core/bpy_helpers/automesh/` domain packages exist (item 5)
- `apps/blender/core/automesh/geometry.py` exposes shared geometry helpers (item 3 equivalent)
- `dilate` + `erode` are 3-line wrappers around `_apply_morphology` (item 4)
- `_fill_inner_via_delaunay` + `_build_annulus_strip` not found in grep (item 2)
- `sonar-project.properties` has `python:S101` ignore for `apps/blender/operators/**/*.py` etc (item 1)
- `validate_automesh.py` shrunk from 660 LOC -> 48 LOC (refactor went further than the checklist asked)

Original checklist preserved below for audit trail. Sonar warnings emitted during PR #51 review iteration:

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
What landed:

- Pure modules under `apps/blender/core/skinning/`: `planar_proximity.py` (1/dist^power normalized), `bind_diagnosis.py` (5 D11 pre-flight checks), `skinning_modes.py` (PROXIMITY / ENVELOPE / SINGLE_NEAREST / EMPTY dispatcher), `sidecar_schema.py` (WeightSidecar stub + topology hash). 32 pure pytest tests covering them.
- bpy-bound helpers under `apps/blender/core/bpy_helpers/skinning/`: `diagnose_collect.py` (KD-tree overlap above 1k verts) + `bind_apply.py` (vertex group write + sidecar JSON stamp).
- Operator `apps/blender/operators/bind_mesh.py` -> `PROSCENIO_OT_bind_mesh_to_armature` with F3 properties (bind_init_mode / falloff_power / max_distance / use_bone_heat).
- Sidecar stub: `obj["proscenio_weight_sidecar"]` JSON written atomically AFTER vertex groups succeed. The sidecar work populates `entries` later.
- NEW test layer: headless operator pytest at `apps/blender/tests/operators/test_bind_mesh.py` (6 tests via `blender --background --python apps/blender/tests/run_operator_tests.py`). Pattern documented in `.ai/conventions.md` "Headless operator pytest pattern".
- CI wired: `Headless operator tests` step added to `test-blender` job; pytest installed into Blender's bundled Python at job start.
- MANUAL_TESTING.md gained one UI-only residue entry (1.20) for the panel button + F3 redo smoke; everything else covered headless.

Out of scope (deferred):

- Coverage report pipeline (pytest-cov + sonar push).
- Hypothesis property-based testing.
- ENVELOPE radii editor UI (the paint work owns it; bind alone exposes radii via per-bone `proscenio_envelope_radius` Custom Property + fallback 1.0).
- Scene PropertyGroup persistence for bind_init_mode / falloff_power / max_distance (the panel work).
- Sidecar `entries` population + reproject (the sidecar work).

### Weight paint modal wrapper (D7 + D8 + D9 + D10 + D12 + D14)

One-button entry into a 2D-safe weight paint context with custom overlay + hard guarantees on exit cleanup + ESC handling.

- `core/paint_preset_2d.py`: frozen `PaintPresetSnapshot` dataclass with 8 brush toggles. `apply_preset(snapshot)` returns previous values for restore.
- `core/bpy_helpers/paint_preset_bind.py`: reads / writes `context.tool_settings.weight_paint`. Mirror axis pulled from `scene.proscenio.active_armature` mirror flag (D14).
- `core/bpy_helpers/weight_overlay.py`: GPU `draw_handler_add` callback drawing 6px filled discs per vertex coloured by active vertex group weight via 6-stop colorband. Alpha 0 for zero-weight verts. Toggle to draw provenance instead (D6 hook).
- `operators/edit_weights.py`: `PROSCENIO_OT_edit_weights_modal`. Snapshot brush + viewport + Bone Collections + active + selection on invoke; switch armature to POSE, mesh to WEIGHT_PAINT, apply 2D preset, auto-select vertex group matching first selected pose bone, register overlay + header pill. ESC = hard exit (D10). `WINDOW_DEACTIVATE` triggers in-flight stroke flush. D12 tablet release via `event.pressure` when available. `_finish` / `cancel` restore via try/finally; wraps cumulative paint in single undo push.
- `core/bone_collection_visibility.py`: Bone Collections visibility (Blender 4.0+) instead of COA2's `bone.hide` global flag. Snapshot + restore round-trip.
- Header pill via `_draw_statusbar_edit_weights` (reuse the quick-armature spec D6 chord-layout helper). Icons: `EVENT_ESC`, `MOD_MIRROR`, `BRUSHES_ALL`.
- Crash safety: any exception hits `_finish` via try/except/finally; log to console; report INFO with restoration message.

Tests (pytest, bpy-free):

- `tests/skinning/test_paint_preset_2d.py` - apply_preset returns prior values; idempotent restore.
- `tests/skinning/test_bone_collection_visibility.py` - snapshot + restore via SimpleNamespace mocks; covers empty-collections + Blender-3.x-fallback.
- Modal smoke deferred to MANUAL_TESTING.md.

### Weight sidecar + reproject (D6) - the differentiator

Make automesh regen non-destructive. Once a user has painted weights, regenerating the mesh at a different resolution preserves their work via UV-anchored re-projection.

- `core/skinning/sidecar_schema.py`: `WeightSidecar` dataclass with vertex_group_names + entries (uv_anchor + weights + provenance) + mesh_topology_hash.
- `core/skinning/weight_reproject.py`: `reproject(sidecar, new_vertex_uvs)`. For each new vertex, find 3 nearest UV anchors, barycentric-interpolate weights, mark `reprojected`. Verts with no close anchor fall back to proximity seed, marked `auto_seed`.
- `core/bpy_helpers/skinning/sidecar_io.py`: serialize to JSON, write to `obj["proscenio_weight_sidecar"]` Custom Property (survives addon disable per the authoring-panel storage rules).
- Automesh integration: when `scene.proscenio.skinning.preserve_on_regen` is True and object has non-zero sidecar entries: snapshot current weights, regenerate mesh, reproject onto new topology, INFO with counts.
- `operators/restore_weight_snapshot.py`: `PROSCENIO_OT_restore_weight_snapshot`. Re-applies sidecar to current mesh without regen.
- Provenance hooks: bind tags all verts `auto_seed`; edit weights modal tags painted verts `user_paint` via diff. Panel pill: "187 paint / 42 seed / 0 reprojected".
- Vertex provenance overlay toggle on weight overlay (user_paint = white outline, auto_seed = gray, reprojected = cyan).

Tests (pytest, bpy-free):

- `tests/skinning/test_sidecar_schema.py` - serialize/deserialize round-trip, topology hash detects changes, JSON shape stable.
- `tests/skinning/test_weight_reproject.py` - identical-topology = no-op; coarser-to-finer interpolates correctly; verts with no close anchor fall back to auto_seed.

Sprite-changed-in-Photoshop workflow (from PR #51 smoke discussion) is exactly this feature: artist edits PNG, re-exports, automesh regen reprojects weights via UV anchors instead of forcing manual repaint.

### PropertyGroup + Skinning panel (D13) - SHIPPED on `feat/spec-013.2-panel`

the panel work: Bind sub-box landed in the existing `PROSCENIO_PT_skinning` panel; bind operator pivots to BONE_HEAT default (D4 amendment).

Spec: [`panel-design.md`](panel-design.md).
What landed:

- `ProscenioSkinningProps` gains `bind_init_mode` (5-value enum, default BONE_HEAT) + `bind_falloff_power` + `bind_max_distance`. Settings persist across `.blend` reloads.
- `BindMode` literal gains `BONE_HEAT` value. `bind_weights_for_mode` returns None for BONE_HEAT (sentinel for the bpy caller to delegate to Blender).
- `apply_bind` dispatches to `_apply_bone_heat` (delegates to `bpy.ops.object.parent_set(ARMATURE_AUTO)`) when mode is BONE_HEAT; same counters shape + sidecar JSON as the algorithm path.
- `PROSCENIO_OT_bind_mesh_to_armature` removes `use_bone_heat` BoolProperty, expands enum, adds `invoke()` reading PG defaults, surfaces "try PROXIMITY as fallback" hint when bone heat fails.
- `PROSCENIO_PT_skinning` gains `_draw_bind_box` helper between Automesh and Debug sub-boxes. Mode dropdown + button; button disabled when picker armature missing.
- Headless tests updated: happy_path + sidecar tests now exercise BONE_HEAT default; new test pins PROXIMITY fallback path.
- MANUAL_TESTING 1.20 rewritten with concrete panel steps for both BONE_HEAT default + disabled-button-when-picker-missing.

Out of scope (deferred):

- Edit Weights sub-box (the paint work).
- F3 menu binding (cross-cutting addon change, separate concern).
- Fixing the projection bug + tightening falloff in PROXIMITY (PROXIMITY is now a rarely-used fallback; low priority).

### Weight sidecar - snapshot + reproject - SHIPPED on `feat/spec-013.2-sidecar`

the sidecar work: WeightSidecar.entries populates on bind + reprojects across automesh regen via UV-anchor barycentric interpolation. Materializes D6 (the differentiator vs Spine / COA Tools 2).

Spec: [`sidecar-design.md`](sidecar-design.md).
What landed:

- `SidecarEntry(uv_anchor, weights, provenance)` dataclass + `ProvenanceKind` literal (auto_seed / user_paint / reprojected). `WeightSidecar.entries` widens to `list[SidecarEntry]`. `from_json` validates provenance values.
- Pure `weight_reproject.py` - hand-rolled O(n) KNN + 2D barycentric over UV anchors. Zero bpy / mathutils import.
- bpy `sidecar_io.py` - `snapshot_sidecar` builds populated sidecar from vertex_groups + active UV layer; `apply_sidecar` writes entries back. UV missing falls back to empty entries (best-effort).
- bpy `automesh_hook.py` - `maybe_pre_regen_snapshot` + `maybe_post_regen_reproject`; T4 identical-hash short-circuit, T8 UV-missing fallback applies in BOTH paths (pre-regen snapshot returns empty entries; post-regen reproject WARNs + writes auto_seed stub - never aborts), normal reproject path replaces None results with auto_seed empty-weights.
- `apply_bind` (both planar + BONE_HEAT paths) stamps populated `auto_seed` entries via `snapshot_sidecar` instead of empty stub.
- `ProscenioSkinningProps` gains `preserve_on_regen` (default ON, U1) + `show_provenance_overlay` (default OFF, U2; GPU draw handler ships in the paint work).
- `automesh_from_sprite` execute() brackets `build_automesh` with the pre/post hook pair; status bar reports `sidecar: X reprojected + Y auto-seed of Z verts`.
- `PROSCENIO_OT_restore_weight_snapshot` operator - reapplies stored sidecar, errors on topology mismatch.
- `PROSCENIO_PT_skinning` gains `_draw_snapshot_box` helper - toggles + counts pill (paint/seed/reprojected) + Restore button (greyed out without sidecar).
- Refactor: dedupe `BASE_SPRITE_GROUP_NAME` import + extract `wipe_non_base_groups` into `_helpers.py`.
- Headless tests: 4 new (automesh_regen x2 + restore_snapshot x2). Pure tests: 10 new (reproject x8 + entry round-trip x2). Total 47 pure + 11 headless.
- MANUAL_TESTING 1.21 covers 6 T-cases (populate / regen / restore / counts / disabled-button / topology-error).

Out of scope (deferred):

- Provenance overlay GPU draw handler -> the paint work.
- Live `user_paint` provenance tagging via paint modal diff -> the paint work.
- Sidecar import/export to external file -> successor work.
- `proscenio.copy_weights_to_selected` cross-mesh transfer -> successor work.

### Edit Weights modal + provenance overlay - SHIPPED on `feat/spec-013.2-paint`

the paint work: one-button entry into 2D-safe weight paint with GPU provenance overlay, per-stroke `user_paint` flip via diff, hard ESC exit, Edit Weights sub-box in panel.

Spec: [`paint-design.md`](paint-design.md).
What landed:

- `PaintPresetSnapshot` frozen dataclass + `PRESET_2D` constant (Front Faces locked OFF per T46254 regression guard). Symmetric apply/restore.
- Pure `weight_diff.py` - diff_weights with eps tolerance; missing-vert in either side counts as touched.
- `bone_collection_visibility.py` - Blender 4.0+ Bone Collections snapshot/restore with 3.x bone.hide fallback. Module is bpy-free (duck-typed inputs).
- `paint_preset_bind.py` - reads/writes tool_settings.weight_paint with defensive hasattr checks for API drift.
- `weight_overlay.py` - POST_VIEW GPU draw handler. UNIFORM_COLOR shader; one POINTS batch per provenance color (cyan/white/gray). Mode='weight' branch reserved for successor work.
- `stroke_diff.py` - StrokeDiffTracker class. Pre-stroke snapshot + post-stroke diff + flip touched entries' provenance to user_paint + rewrite sidecar JSON.
- `modal_session.py` - EditWeightsSession dataclass + capture + restore. Object lookups by name so restore survives undo-driven object recreation.
- `PROSCENIO_OT_edit_weights_modal` - mono-operator owning invoke/modal/finish. ESC hard-exit, WINDOW_DEACTIVATE flushes in-flight stroke, MOUSEMOVE+pressure=0 catches pen-lift.
- Skinning panel gains Edit Weights sub-box between Bind + Snapshot. Button greys out when picker or sidecar missing.
- Headless tests: 5 new. Pure tests: 11 new (paint_preset x4 + weight_diff x4 + bone_collection_visibility x3). Total 58 pure + 16 headless.
- MANUAL_TESTING 1.22 covers 6 T-cases (enter modal / stroke / ESC restore / Reload Scripts / single undo / disabled button).

Out of scope (deferred):

- Weight-gradient overlay UI toggle -> successor work.
- Per-bone soft/hard mode toggle (D16) -> successor work.
- proscenio.copy_weights_to_selected cross-mesh transfer -> successor work.
- Smart Bones / corrective drivers -> a future animation-system spec.
- Live pose-mode preview in weight paint -> successor work.
- Brush curve presets ("Hard edge" / "Soft falloff" / "Crease") -> successor work.

### Interactive modal automesh - SHIPPED on `feat/spec-013.2-interactive-modal`

the interactive-modal work: 5-stage modal preview of the automesh pipeline. Each stage (outer contour / inner loops / user Steiner points / Steiner preview / apply) shows a GPU overlay; sliders re-run live; user Steiners click-place + persist via Custom Property. Final APPLY pipes through build_automesh + the sidecar work reproject so existing weights survive.

Spec: [`interactive-modal-design.md`](interactive-modal-design.md).
What landed:

- `AuthoringStage` IntEnum + `StageParams` (frozen, equality-based dirty detection) + `StageOutput` (mutable, accumulates across stages).
- Pure `erosion_loops.py` - hand-rolled wrapper around contour.erode + find_first_boundary + trace_contour. Computes N successively-eroded inner loops from a base mask.
- bpy `authoring_session.py` - capture/restore prior viewport state via name-based object lookups.
- bpy `authoring_overlay.py` - POST_VIEW GPU draw handlers per stage. UNIFORM_COLOR shader (shared with modal_overlay). LINE_STRIP for polylines + POINTS for dots. All GPU state wrapped in try/finally so failures do not leak point_size or blend.
- bpy `authoring_pipeline.py` - per-stage compute + apply_mesh terminal helper. apply_mesh invokes maybe_pre_regen_snapshot + maybe_post_regen_reproject from the sidecar work so existing weights survive APPLY (B1 fix preserves user_paint provenance).
- `PROSCENIO_OT_automesh_authoring` modal operator - invoke captures session + computes OUTER + registers overlay + starts 100ms TIMER. ENTER advances; BACKSPACE retreats; ESC cancels. LEFTMOUSE (EDIT_INTERIOR_POINTS) click-places; Shift+LEFTMOUSE deletes nearest within world threshold. TIMER polls StageParams + recomputes current stage on PG diff (throttled slider re-run).
- Skinning panel gains Automesh authoring sub-box between Automesh one-shot + Bind. Coexists - one-shot stays as the quick path.
- ProscenioSkinningProps gains authoring_inner_loop_count (default 2) + authoring_inner_loop_spacing (default 0.15).
- Headless tests: 5 new. Pure tests: 8 new (erosion_loops x5 + authoring_stages x3). Total 69 pure + 21 headless.
- MANUAL_TESTING 1.23 covers 6 T-cases (enter modal / slider live re-run / click placement / shift-click delete / APPLY commit / APPLY preserves weights).

Known gap (deferred to successor work or build_automesh extension PR):

- **apply_mesh does not consume output.user_steiners + output.inner_loops at APPLY.** build_automesh today does its own full pipeline; the modal's previewed inner loops + user-placed Steiners are PREVIEW-ONLY. Custom Property persistence is in place so a future build_automesh extension (accept optional user_steiners + inner_loops_override constraints) can honor them without further modal changes. Cleanup prerequisite (cognitive-47 build_automesh refactor) becomes a blocker for closing this gap.

Out of scope (deferred):

- User-drawn inner loops (free-draw polylines as CDT constraint edges) -> successor work.
- Drag-stroke Steiner placement (multiple points per drag) -> successor work.
- Brush stroke for alpha-boundary trace (D1.B paradigm enum) -> successor work.
- Stage 4 editable Steiners (drag-to-move, delete-with-X) -> successor work.
- Pose-mode preview mid-modal -> successor work.
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

- [x] `.ai/skills/blender-dev.md` "Edit Weights modal pattern" subsection (companion to the quick-armature spec's modal overlay + hint placement patterns). Covers snapshot + apply + restore + try/finally crash safety + Bone Collections visibility + per-stroke provenance diff.
- [x] `.ai/skills/blender-dev.md` "Pure-Python image processing" extended with weight_reproject hand-rolled KNN + barycentric note (same no-third-party-deps rule extends to sidecar wave).
- [x] `.ai/skills/format-spec.md` "Skinning weights" gains "Authoring story" subsection cross-referencing this spec waves (automesh + bind + edit + reproject + restore).
- [x] `tests/MANUAL_TESTING.md` 1.20 (bind/panel) + 1.21 (sidecar) + 1.22 (paint) cover T-cases for bind / edit / snapshot / reproject. 1.19 reserved for the first cut automesh-only flows.
- Reload-Scripts safety smoke - re-run "Reload Scripts" after entering Edit Weights modal; verify no orphan draw handlers, no panel crash, brush state restored. (Pending - manual T-case to add to 1.22.)
- Cross-armature smoke - bind mesh to one armature, change picker to another, re-bind; verify sidecar persists and reprojects. (Pending - manual T-case to add to 1.20 or 1.21.)
- Headless Blender script via `--background --python` to confirm registration / unregister cycle clean. (Pending - separate effort; the existing `run_operator_tests.py` runner covers ops registration as a side effect of fixture load.)

## Stroke redesign + productivity polish (in-flight bundle)

Branch: `feat/spec-013-stroke-redesign`.

### Part A scope - SHIPPED on branch (PR pending review)

Stage 3 stroke redesign + extra_edges CDT extension + mixed-flow auto-snapshot. 14 commits (`407229c..f04065e`), ~900 LOC. Tasks 1-14 of plan.

- **[SHIPPED] Stage 3 paradigm: clicks become strokes** (S1-S9). LMB drag captures raw mouse path, Chaikin 2-iter smooth, resample at `interior_spacing`, snap endpoints to outer contour verts within `interior_spacing * 1.5`, persist as `proscenio_user_strokes` JSON. Backward compat: drag < 5px = single Steiner (click behavior preserved). Ctrl+Z pops last stroke. Shift+LMB hit-tests and deletes containing stroke. Strokes reach `build_automesh` as `extra_steiners` (verts) + `extra_edges` (CDT constraint segments). GPU overlay draws committed strokes (blue verts + edges) + kind=point strokes (yellow dots) + in-progress raw path (light gray). Stage 4 preview also renders stroke edges so artist verifies before APPLY.
- **[SHIPPED] Auto-snapshot from current vertex_groups state (mixed-flow fix - critical)** (M1/M2). When `obj["proscenio_weight_sidecar"]` absent before automesh regen AND `vertex_groups` non-empty AND armature set, build sidecar on-the-fly from current vgroup data via `snapshot_sidecar` (provenance=auto_seed). Closes critical gap where Ctrl+P Armature Auto Weights bind + automesh regen silently wiped weights (user-reported 2026-05-25).

### Part C scope - SHIPPED on branch (PR #63 MERGED 2026-05-28)

Manual smoke on PR #63 (2026-05-27) revealed:

1. **Fan-degenerate triangulation** when Stage 3 strokes commit (visible edge fans radiating from interior verts). Two confirmed root causes: (a) auto-fill grid clusters near stroke verts (Steiner spacing computed without knowing stroke positions); (b) silent vert drop in `_merge_extra_steiners` leaves `extra_edges` indices stale → long-distance edges referencing wrong final-array positions.
2. **Feature gap**: cuts (kind="cut" stroke that separates the mesh into 2 sides) requested for joint articulation + silhouette refinement use cases.

Decision: bundle the fixes + feature into PR #63 rather than ship a baseline that produces low-quality output by default. Ten amendment items rolled into the same PR. The locked stroke-redesign decisions for this work are surfaced in [STUDY.md D17](STUDY.md#d17---stage-3-interior-input-paradigm); the historical planning artifacts were retired once the work shipped.

Adds 10 tasks (~970 LOC + ~18 tests):

- (NEW) filter strokes pre-index-allocation + WARNING report on drops (closes index drift bug)
- (NEW) `interior_points_for_annulus.exclude_zones` kwarg (closes auto-fill cluster bug)
- (NEW) `AuthoringStage.EDIT_OUTLINE` between OUTER and INNER_LOOPS - 5-stage modal becomes 6
- (NEW) Stroke `kind="cut"` (3rd value) + 2-loop offset + face-prune (reuses hole detection)
- (NEW) Stage 2 location-driven gestures (LMB outside = extend, LMB inside = cut, Ctrl = delete)
- (NEW) Stage 4 modifier scheme (LMB = fold-line, Shift = cut, Ctrl = delete - was Shift for delete)
- (NEW) `StageParams.cut_width` slider (default `interior_spacing * 0.3`)
- (NEW) Tooltip near mouse via `blf.draw` showing current intent per stage + modifier state

### Second smoke + gesture redesign - SHIPPED in PR #63 (2026-05-28)

A second smoke after the earlier amendment work drove three more iterations, all merged in PR #63.

- **[SHIPPED `b9283e2`] Cut = corridor hole + cut-to-alpha**. The `split_edges` rip produced jagged separation on triangle soup; replaced by a corridor lens routed through `holes_world` + the proven `delete_faces_inside_holes` prune. `cut_margin` default `0.04`. Cut strokes keep all samples and sever to the silhouette boundary when an endpoint lands in alpha.
- **[SHIPPED `80cb50d`] Stage 4 gesture map redesign**. plain click = point; Shift = fold-line; Ctrl = cut; Alt = delete. Shift/Ctrl each split into pen-tool (click = exact straight segments, finalize on modifier release, no resample) + free-draw (drag). Resolves the Shift=cut / delete reflex clash.
- **[SHIPPED `fb9d886`] Live in-progress preview**. `_draw_live_preview` renders pen/free-draw verts + colored edges (blue fold / red cut) while drawing + a dimmed rubber-band to the cursor in pen mode. Supersedes the gray raw-stroke handler for Stage 4.
- **[SHIPPED `9a1dd15`] CodeRabbit review batch** (productivity files): weight_transfer length guard, bind_mesh warn severity, sidecar_io serialization guard, contour raw_mask docstring, multi_mesh_bind test fixes.

### Authoring UX polish - feat/automesh-authoring-ux-polish - SHIPPED on branch

Deferred from PR #63 - cosmetic/incremental UX, not correctness blockers. Branch: `feat/automesh-authoring-ux-polish`. All 5 items shipped + validated (43 operator tests + 7/7 fixtures + 261 pure tests green).

- **[x] Statusbar hint parity with `quick_armature`** - `_emit_authoring_chord_layout` renders per-stage gesture chords with native EVENT_*/MOUSE_* icons; `_STAGE_NAMES` trimmed to short titles. (`590f8ba`)
- **[x] Cursor tooltip parity** - tooltip now uses `draw_text_panel_2d` (colored + backgrounded); flips to a red warning background when a Stage 4 fold/cut is aimed outside the silhouette. (`590f8ba`)
- **[x] Delete hover-highlight** - the stroke under the cursor is highlighted (bright thick outline) while Alt is held, in Stage 2 + Stage 4, via a shared `_stroke_index_under_cursor` hit-test. (`4de4dac`)
- **[x] Inflated contour preview** - `compute_outer` now dilates by `max(1, margin_pixels)` to match `build_automesh`, so the previewed silhouette is the real boundary instead of an inset that inflated on APPLY. (`01f712c`)
- **[x] Stage 5 (`PREVIEW_INTERIOR`) clarity** - `compute_all_steiners` fills the full outer interior (matching `build_automesh` at the default `margin_pixels=0`) instead of clipping by the innermost modal erosion loop, so the silhouette center is no longer empty. (`23949e9`)

### Mesh interior modes + gesture redesign (2026-05-28 smoke)

Locked decisions for this work are surfaced in [STUDY.md D19, D20, D21](STUDY.md#d19---interior-fill-mode); the historical planning artifacts were retired once the work shipped. Bundled onto `feat/automesh-authoring-ux-polish` (user choice 2026-05-28). OQ1/2/3 resolved at recommended defaults.

Phase 1 - algorithm + steps + Stage 2 remap (~400 LOC). DONE on branch (staged; commits pending):

- **[x]** `automesh_interior_mode` enum (SIMPLE/DENSE, PG default SIMPLE; `StageParams`/`build_automesh` default DENSE for test back-compat) on props + panel (DENSE-only knobs grey out in SIMPLE) + `StageParams`.
- **[x]** SIMPLE CDT path in `build_automesh`/`apply_mesh` (silhouette + holes + user verts only, uniform grid + bone-density fill skipped). Headless: SIMPLE sparser than DENSE. Standalone `automesh_from_sprite` operator also threads `interior_mode` (prop + invoke reads PG) - caught in smoke 2026-05-28 where the op ignored the mode and always ran DENSE.
- **[x]** mode-dependent `active_stages` + index-based nav (`_stages_for_mode`/`_stage_label`); SIMPLE drops INNER_LOOPS; statusbar N/M derived; mode flip mid-modal rebuilds the list + snaps off a dropped stage.
- **[x]** triangulation preview at SIMPLE step 4 - `compute_triangulation_preview` runs the real build on a throwaway obj copy (anti-drift, non-destructive) + cyan wireframe overlay (`_draw_edges`). Recompute on stage-enter + param-dirty (OQ1).
- **[x]** Stage 2 modifier-driven (Shift=extend, Ctrl=cut, Alt=delete; plain drag = no-op) unified with Stage 4; cut overlay RED (orange `_STROKE_VERT_COLOR_CUT_REMOVE` retired, `stage_context` plumbing removed).

MANUAL_TESTING - **post-merge smoke validation** (visual, cannot verify headless; reviewer / on-call smokes after merge, NOT a pre-merge blocker):

- **[ ] SIMPLE step 4 wireframe** - the cyan triangulation overlay matches the mesh APPLY produces (silhouette + fold/cut/steiner verts, no dense fill).
- **[ ] Stage 2 red + modifier** - cut overlay reads RED (matches Stage 4); Shift/Ctrl/Alt dispatch is precise regardless of cursor inside/outside the silhouette.

Phase 2 - gesture model rewrite. DONE on branch (staged; commits pending). Decisions: full toggle pen; subdivisions baked at finish (no `Stroke.subdivisions` schema field - D6); subdivisions on pen straight segments only.

- **[x]** toggle-modal pen shared by Stage 2 + Stage 4: a clean Shift/Ctrl tap enters draw mode (no holding; Ctrl-key combos keep Ctrl+Z undo). LMB click = pen vert, drag = free-draw, RMB/Enter = finish, Esc = cancel line. Modal event routing reordered so DRAW intercepts Enter/RMB/Esc before nav.
- **[x]** X/Z axis lock - `X`/`Z` toggle horizontal/vertical lock (mutually exclusive); the next pen vert snaps to the locked axis vs the last vert.
- **[x]** scroll / digit subdivisions - wheel +/-1, digit 0-9 sets exact; baked into the pen polyline via `subdivide_polyline` at finish. Live preview shows ghost subdivision dots + axis-snapped rubber-band guide.
- **[x] follow-ups** (2026-05-28 smoke 2): (a) tooltip + statusbar refresh on tap-toggle / wheel-subdiv / axis-lock (not only mouse move) via `_refresh_pen_tooltip`; (b) pen-click snaps to nearby existing verts (committed strokes + outer contour) so coords land exactly, AND on finish a pen line whose endpoint meets an existing same-kind stroke's endpoint MERGES into it (`_merge_into_existing`) so connected traces are ONE deletable stroke, not two stacked on a shared vert; clicking the line's first vert closes a loop (`_snap_pen_click`); (c) Stage 2 spliced-outer preview (`compute_outer_preview` + green overlay) shows the silhouette APPLY will build after extend edits, updating on commit/undo/delete.

MANUAL_TESTING - **post-merge smoke validation** (gesture, cannot verify headless; reviewer / on-call smokes after merge, NOT a pre-merge blocker):

- **[ ] Toggle entry/exit** - tap Shift enters fold-pen (statusbar/tooltip show DRAW); tap again on an empty line exits to NEUTRAL.
- **[ ] Pen + finish/cancel** - click 3 verts, RMB or Enter commits the line; Esc on a fresh line discards without cancelling the modal; NEUTRAL Enter still advances the stage.
- **[ ] Ctrl+Z preserved** - Ctrl+Z in NEUTRAL undoes the last stroke (does NOT enter cut-draw).
- **[ ] Axis lock** - press X -> next segment is horizontal; Z -> vertical; toggling switches.
- **[ ] Subdivisions** - wheel/digit bumps the tooltip count; a straight 2-click line with subdiv=2 commits with 2 inserted verts per edge (no single long edge).
- **[ ] Stage 2 parity** - the same pen works in Stage 2 (extend/cut), cut overlay red.
- **[ ] Tooltip/statusbar live** - tapping a tool (Shift/Ctrl) or scrolling subdivisions updates the tooltip + statusbar immediately, without a mouse move.
- **[ ] Snap + merge + loop** - drawing a line that ends on an existing same-kind stroke's endpoint merges into ONE stroke (deleting it removes the whole connected trace, not half); clicking the first vert of the in-progress line closes a loop.
- **[ ] Stage 2 outer preview** - after an extend edit, the green spliced-outer overlay shows the silhouette APPLY will build; updates on undo/delete.

### Part B scope - SHIPPED on branch (PR pending review)

Productivity polish + B3 silhouette fix. 9 commits (`e80c91b..aba0a73`), ~800 LOC. Tasks 16-24 of plan.

- **[SHIPPED] Per-bone SOFT/HARD mode dispatch** (O1/D16). New module `core/skinning/bone_modes.py` (read/write/per-bone-lookup); `bind_apply` extracts `_apply_bone_mode_overrides` + `_merge_per_bone_weights` to splice override columns in. Per-bone toggle UI in bind sub-box (two-button row, depress shows active mode). `proscenio.set_bone_mode` operator persists `obj['proscenio_bone_modes']` dict.
- **[SHIPPED] Multi-mesh batch bind** (O2). Bind operator now iterates selected MESH objects (fallback to active when no selection). Per-mesh body extracted to `_bind_single` helper; per-failure WARNING + final INFO with success count.
- **[SHIPPED] Sidecar import / export** (O3). `proscenio.export_sidecar` + `proscenio.import_sidecar` operators using file dialog. Import validates structure via existing `sidecar_schema.from_json`. Panel sub-box exposes Export + Import buttons.
- **[SHIPPED] Brush curve presets** (O4). 4 named presets (Hard Edge / Soft Falloff / Crease / Smooth Blend) in `core/skinning/brush_curve_presets.py`; `proscenio.set_brush_preset` operator configures `brush.curve.curves[0].points`. Quick-select 4-button row in Edit Weights sub-box.
- **[SHIPPED] B3 silhouette regression at resolution 0.5** (O5). Root cause: `HOLE_SAFETY_DILATE_CELLS=1` foreground dilation in `extract_contours` was closing 1-cell-wide inter-finger corridors at downscaled resolution, generating false 229-point "holes" that CDT punched out. 1-line fix: pass `raw_mask` instead of dilated to `extract_holes`. 2 new regression tests (`test_b3_narrow_corridor_not_a_hole`, `test_b3_real_hole_still_detected`).
- **[SHIPPED] UX1 Restore Weight Snapshot rename** (O6). `bl_label` -> "Reset to Last Saved Weights"; `bl_description` updated to explain what gets reverted. Panel button text updated to match. Relative timestamp skipped (sidecar schema has no timestamp field; out of scope for this PR).
- **[SHIPPED] Weight transfer between sprites** (O7). Pure `core/skinning/weight_transfer.py` (KNN by world position; 5 pure tests). `proscenio.copy_weights_to_selected` operator: active = source, selected (minus active) = targets; per-target vert nearest source within `max_distance` copies weight dict; target `vertex_groups` created as needed. Panel sub-box. Solves COA2 #18 + #73.

### Legacy backlog (productivity polish, superseded by Part A + Part B above)

The original "successor work" planning grouped these 7 items (quick wins + bugs + critical mixed-flow gap, ~830 LOC total). All `[ACTIVE]` markers below are SHIPPED in Part A or Part B; preserved for audit trail:

- **[ACTIVE] Auto-snapshot from current vertex_groups state (mixed-flow fix - critical).** Today `maybe_pre_regen_snapshot` aborts when `obj["proscenio_weight_sidecar"]` is absent, so users who bound via Blender native (`Ctrl+P -> Armature Auto Weights`) silently lose ALL weights on next `Automesh from Sprite` regen. Fix: when sidecar absent but vertex_groups present, build the sidecar on-the-fly from current vertex_groups + UVs before regen, then reproject. Closes the "mixed flows = silent data loss" gap user identified 2026-05-25.
- **[ACTIVE] Soft vs Hard bone toggle (D16, Animate lift).** Per-bone enum on vertex group metadata (`group.proscenio_bone_mode = "SOFT" | "HARD"`); rebind re-derives respecting the mode. Soft = proximity falloff; Hard = single-nearest. Trigger: user complains proximity bleed is too soft on a specific limb.
- **Bone strength region painting (Moho lift).** Per-bone elliptical / capsule influence widget. Drag a handle along the bone to grow / shrink radius. Region drives initial weight map procedurally. Trigger: proximity default does not give enough control for shapes like long hair or tails.
- **User-drawn density markers (PR #51 smoke feedback).** Artist paints on sprite (grease pencil or GPU overlay) to mark regions of interest (muscle bulges, cloth folds, joint creases). Marks translate into extra Steiner point clusters at automesh time. Distinct from the productivity follow-up's interactive modal at coarse level: this is painted REGIONS persisted on the mesh, modal is per-point clicks during authoring. Implementation sketch: `proscenio_density_marks: list[(x, z, weight, kind)]` Custom Property; per-mark color in the overlay differentiates kinds (muscle / fold / crease).
- **[ACTIVE] Multi-mesh batch bind.** Bind operator takes selected meshes (not just active); same algorithm against picker armature. Useful for character imports with N sprites + 1 rig.
- **Weight transfer between sprites.** `proscenio.copy_weights_to_selected`. Source mesh (active) + N target meshes (selected); for each target vertex, look up nearest source vertex by world position + copy weight dict. Solves COA2 issues [#18](https://github.com/Aodaruma/coa_tools2/issues/18) + [#73](https://github.com/Aodaruma/coa_tools2/issues/73).
- **Live pose-mode preview in weight paint.** Scrub the bone to a posed angle, see how the mesh deforms, scrub back without leaving Edit Weights modal. Pose-scrub overlay + hotkey to toggle rest pose.
- **[ACTIVE] Sidecar import / export to file.** Operator to dump weight sidecar JSON to / load from a file. Enables version-controlled weight backups outside the .blend.
- **[ACTIVE] Brush settings curve presets.** Quick-select named curve presets in the Edit Weights modal status pill ("Hard edge", "Soft falloff", "Crease", "Smooth blend"). Saves brush curve editor trips.

### Active PR scope continued

The bundle above also includes:

- **B3 fix (resolution 0.5 silhouette walker).** Confirmed the first cut regression. Investigate alpha walker at coarse pixel stride; fix or document workaround. Out of scope for big algorithm changes; if root cause needs major work, downgrade to "document workaround in panel tooltip" (~30 LOC) instead of fixing.
- **UX1 (Restore Weight Snapshot rename).** Rename button to something less opaque. Candidates: "Revert Manual Paint" or "Reset to Last Saved Weights". Add tooltip showing when snapshot was last saved.

### Deferred to dedicated waves (each needs own brainstorm + plan)

These items are scoped but NOT in the active PR (too big / too design-heavy):

- Bone strength region painting (Moho lift) - ~600 LOC, widget paradigm
- User-drawn density markers - ~400 LOC, paint mode + integrate with automesh
- Weight transfer between sprites - ~250 LOC, cross-mesh KNN operator
- Live pose-mode preview in weight paint - ~400 LOC, modal scaffold + pose-scrub overlay
- Stage 3 redesign: stroke -> CDT constraint edges (replaces click-place-vert per user feedback 2026-05-25) - ~600 LOC, modal refactor + GPU brush feedback
- **Bezier brush stroke for alpha-boundary trace.** the productivity follow-up's free-draw alternative to the alpha-trace one-shot. Adds D1.B to the paradigm enum when real workflows demand it.

### Suspect bugs - needs investigation (manual smoke 2026-05-21)

Items observed during paint-wave manual smoke that may be real bugs OR test-flow confusion. Each needs an isolated headless repro before fixing.

- **B1: reproject does not preserve user_paint provenance.** ~~`weight_reproject.reproject_entries` always stamps `provenance="reprojected"` on new entries; if old entry was `user_paint`, the marker is lost on automesh regen.~~ **FIXED** on branch `fix/spec-013-reproject-preserves-user-paint`: `_carry_user_paint_provenance` propagates `user_paint` when any of the 3 barycentric donor anchors carried that marker (any-donor wins, conservative choice for preserving artist intent). +2 pure tests.
- **B2: chained automesh regen produces visually chaotic weights.** ~~**CONFIRMED on 2026-05-25.** Repro: bind hand fixture (BONE_HEAT default, 249 verts) -> Skinning > Automesh from Sprite again with `Mesh resolution = 0.2`. Console: `automesh built: 64 outer + 0 inner + 191 interior = 255 total, 444 faces` then `sidecar: 125 reprojected + 130 auto-seed of 255 verts` (51% fell through to auto_seed = empty weights).~~ **FIXED.** Root cause confirmed as hypothesis (2): default `max_distance=0.1` in UV space too tight to cover anchor drift between regen runs (51% of target verts fell through to auto_seed). Fix in `weight_reproject.reproject_entries`: bumped default `max_distance` from 0.1 to 0.5 + added nearest-neighbor fallback when 1-2 donors are in range (was returning None and auto-seeding). user_paint provenance propagates through the fallback so artist marks survive chained regens. 4 pure regression tests added (`test_fewer_than_three_old_entries_falls_back_to_nearest`, `test_zero_donors_in_range_still_returns_none`, `test_degenerate_collinear_triangle_falls_back_to_nearest`, `test_user_paint_carried_through_nearest_fallback`).
- **B3: resolution 0.5 destroys silhouette (the first cut regression).** ~~**CONFIRMED on 2026-05-25.** Automesh at `Mesh resolution = 0.5` produced 44 verts / 27 faces of disconnected fragments instead of low-poly hand silhouette.~~ **FIXED** in `feat/spec-013-wire-user-steiners-to-mesh` (Task 21). Root cause: at resolution=0.5 inter-finger gaps in the source image (3-4 px) downscale to 1-2 grid cells; the old `HOLE_SAFETY_DILATE_CELLS=1` foreground dilation before `extract_holes` closed those 1-cell corridors, converting border-connected external background into apparently-enclosed regions -> false CDT hole punches -> disconnected fragments. Fix: `extract_contours` now calls `extract_holes` on the undilated raw mask; the flood-fill from the border correctly classifies narrow corridors as external. +2 pure regression tests (`test_b3_narrow_corridor_not_a_hole`, `test_b3_real_hole_still_detected`). Ring/donut fixtures unaffected - genuinely enclosed holes have no border path regardless of dilation.
- **UX1: Restore Weight Snapshot button label/affordance is confusing.** ~~**OBSERVED on 2026-05-25.**~~ **FIXED** in stroke-redesign Part B (commit 0df5b55). Operator `bl_label` renamed to "Reset to Last Saved Weights"; `bl_description` updated to "Reverts paint edits since the last Bind or Automesh regen"; panel button text override updated to match. Relative timestamp deferred - `WeightSidecar` schema has no timestamp field; adding one is a schema bump out of scope for this PR.
- **UX2: Automesh authoring modal stages had broken visual feedback.** **FIXED on branch `fix/spec-013-modal-ux`** (this PR). Three concrete bugs were hiding the modal's value from the user: viewport did not redraw after ENTER/BACKSPACE (overlays appeared to do nothing until manual zoom/pan), statusbar pill showed only "Automesh Authoring:" with no current-stage indicator, GPU overlay drew at world origin instead of at the sprite's viewport position (offset silhouette to the right of the actual mesh). All three reproduced reliably on the hand fixture; all three resolved by adding `tag_redraw_view3d` after every stage mutation + `_current_stage_label` class var read by the statusbar draw callback + transforming overlay points through `obj.matrix_world` in `authoring_pipeline.compute_outer` / `compute_inner_loops_for_stage`.

## Tech debt - addon-wide

- **mypy strict + bpy.props typing cleanup.** The addon scatters `# type: ignore[valid-type]` on every `bpy.props.FloatProperty(...)` / `EnumProperty(...)` / `StringProperty(...)` assignment-as-annotation (the Blender PG hack mypy strict cannot model) and `# type: ignore[import-not-found]` on every relative `..core.skinning.*` import (mypy resolves relative imports from `apps/blender/` cwd and the `.core.X` path fails from `operators/`, `panels/`). Both patterns are universal across `bind_mesh.py`, `set_bone_mode.py`, `brush_preset.py`, `copy_weights_to_selected.py`, `sidecar_io.py`, and reach into helper modules too. Cleanup path: (a) ship `.pyi` stub files declaring proper `bpy.props.*` return types so the assignment-as-annotation hack types correctly without ignore; (b) extend `pyproject.toml` `[tool.mypy]` with per-module `mypy_path` / `explicit_package_bases` so relative imports resolve consistently; (c) audit + remove the now-obsolete ignores in one sweep. Out of scope for current specs (touches every operator and panel module); track as standalone refactor when next strict-mypy churn happens.

## Aspirational

- **Auto-Patch joint cover at articulations (Toon Boom Harmony lift).** One-click joint-cover operator. Given two child meshes sharing a parent bone, generate seam geometry + weight blend that hides the inner-elbow hole as the joint bends. Trigger: humanoid fixture lands + user complains about inner-elbow gap.
- **Cubism Glue equivalent.** Operator that seam-binds overlapping vertices of two meshes with a weight slider biasing which side dominates. Different surface than Auto-Patch (covers any seam, not just articulations).
- **Smart-Bone-style corrective drivers.** Per-bone shape key driven by bone rotation; user records a corrective pose at a specific angle and the addon emits a driver. Belongs in a future animation-system spec, not in this one.
- **Mirror humanoid binding.** One mesh on one side, click to mirror to the other. Couples to symmetric rigs. Trigger: first humanoid fixture lands.

## Refinement log

| Commit | Change | Why |
| --- | --- | --- |
| PR #51 merged | the first cut shipped (automesh + hole-support amendment) | First-cut automesh + D2 amendment lifting Spine / COA2's "no holes" restriction; 5 fixtures including AA swirl with 2 holes |
| post-merge | the productivity follow-up cleanup feature added | Sonar warnings + cognitive-complexity drift surfaced during PR review iteration; foundation needs cleanup before bind / paint / sidecar build on top |
| post-merge | the productivity follow-up interactive modal feature added | User reflection: one-shot produces over-dense meshes for simple sprites + no in-flight course correction; modal lifts each existing debug stage to interactive user-facing preview |
| post-merge | Numeric sub-letter scheme dropped from tracking | The sub-letter scheme got noisy fast; each tier now holds named features. Commit history retains the older labels for the PR #51 work |
| post-merge (the productivity follow-up bind) | the productivity follow-up bind shipped; bind-design.md spec + plan linked | Headless operator pytest pattern proven |
| post-merge (the productivity follow-up bind) | diagnose_flipped_normals convention inverted (Y>=0 = flipped, was Y<=0); `_flip_normals_to_positive_y` workaround removed from headless test | Proscenio Front Ortho convention: camera at -Y looking +Y; sprite "facing camera" = normal in -Y. Verified against automesh output (432/432 faces at Y=-1). Original assumption (+Y = correct) was inverted; fixture builder is NOT buggy, was the diagnose check |
| post-merge (the panel work) | D4 amended - BONE_HEAT allowed as default bind mode; Skinning panel gains Bind sub-box | Manual smoke on PR #54 surfaced bone heat produces better falloff for 2D pickers; F3-only access for bind was a UX blocker. Pivot resolves both |
| post-merge (the sidecar work) | the sidecar work shipped - populated WeightSidecar + reproject across regen + restore operator + panel Snapshot sub-box | Materializes D6 differentiator (Spine / COA2 lose weights on regen; Proscenio survives via UV-anchor barycentric reproject) |
| post-merge (the paint work) | the paint work shipped - Edit Weights modal + GPU provenance overlay + per-stroke user_paint flip + Skinning panel sub-box | Closes D6/D7/D8/D9/D10/D12/D14 - one-button entry to 2D-safe weight paint with provenance feedback the artist actually sees in the viewport |
| post-merge (the interactive-modal work) | the interactive-modal work shipped - 5-stage modal preview of the automesh pipeline + click-placed user Steiners + sidecar reproject on APPLY | Closes "Interactive modal automesh authoring" TODO item; preview-only at APPLY (build_automesh extension follows once cleanup prereq lands); coexists with one-shot automesh_from_sprite |
| PR #63 merged (2026-05-28) | Stroke redesign + productivity bundle shipped (Part A + B + C + second-smoke gesture redesign + live preview) | 6-stage modal with stroke/cut authoring, corridor-hole cut, pen+free-draw gestures, live colored preview. Remaining UX polish split to `feat/automesh-authoring-ux-polish` to keep #63 shippable |

## Out of scope (permanently)

Rejected for this spec; do not propose again without re-opening the decision:

- OpenCV / numpy as install-time dependency (COA2 adoption lesson per Constraints + D1).
- Per-brush mirror as the source of truth (D14).
- ESC as deselect-only inside any draw modal (D10).

## Successor specs

- **A future animation-polish spec** - inherits the weight-aware vertex-group machinery; Smart-Bone-style corrective drivers land there.
- **Slot system maturity** unlocks auto-attach mesh to slot + per-slot weight variations.
- **A future "Quick Mesh" operator** (called out in the [quick-armature spec](../012-quick-armature-ux/STUDY.md) successor list) is the direct sibling to automesh - lift the modal scaffold from the productivity follow-up's Edit Weights wrapper if pursued.
