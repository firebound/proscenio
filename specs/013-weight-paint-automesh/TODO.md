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
- [ ] D4 - bone heat solver usage = explicit user opt-in only, NEVER default. No default-bind code path may call `parent_with_automatic_weights` blind.
- [ ] D5 - initial bind algorithm default = planar proximity falloff (custom, NOT bone heat); enum offers PROXIMITY / ENVELOPE / SINGLE_NEAREST / EMPTY (no BONE_HEAT in first cut).
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
- BONE_HEAT BindMode enum value (bone-heat stays behind F3-only opt-in BoolProperty per D4).

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

### PropertyGroup + Skinning panel (D13)

- `properties/scene_props.py`: `ProscenioSkinningProps` PropertyGroup. Pointer wired on `ProscenioSceneProps.skinning`.
- `panels/skinning.py`: `PROSCENIO_PT_skinning` subpanel parallel to `PROSCENIO_PT_skeleton`. Layout:
  - "Picker armature" row (mirror of Skeleton picker, read-only).
  - "Automesh" sub-box: resolution / alpha threshold / margin / density-under-bones + `Automesh from Sprite` button.
  - "Bind" sub-box: `bind_init_mode` dropdown + `Bind to Picker Armature` button.
  - "Edit Weights" sub-box: 2D preset toggle + `Edit Weights` button.
  - "Snapshot" sub-box: preserve-on-regen toggle + `Restore Snapshot` button + sidecar provenance counts.
- Panel polling: only show when active object is mesh-type. Warn when picker is unset.
- Operator buttons disabled with tooltip when prerequisites unmet.
- F3 search discoverability: all 5 operators registered with descriptive `bl_label`.

### Interactive modal automesh authoring

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

- `.ai/skills/blender-dev.md` gains "Weight paint modal pattern" subsection (companion to SPEC 012's modal overlay + hint placement patterns). Covers snapshot + apply + restore + try/finally crash safety + Bone Collections visibility.
- `.ai/skills/blender-dev.md` gains "Pure-Python contour walking" subsection documenting why automesh does not use OpenCV.
- `.ai/skills/format-spec.md` cross-reference SPEC 013 as the authoring story for SPEC 003's weights wire format.
- `tests/MANUAL_TESTING.md` 1.19 extends with T-cases for bind / edit / snapshot / reproject.
- Reload-Scripts safety smoke - re-run "Reload Scripts" after entering Edit Weights modal; verify no orphan draw handlers, no panel crash, brush state restored.
- Cross-armature smoke - bind mesh to one armature, change picker to another, re-bind; verify sidecar persists and reprojects.
- Headless Blender script via `--background --python` to confirm registration / unregister cycle clean.

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
- **Fixture builder -Y normals fix.** `scripts/fixtures/automesh/build_blend.py:_build_sprite_quad` emits quads with -Y face normals because the `from_pydata` corner order is read clockwise from +Y. Bind preflight rejects -Y normals (correctly), so `apps/blender/tests/operators/test_bind_mesh.py` works around this with a `_flip_normals_to_positive_y` helper. Real users hit +Y normals after running automesh (`bmesh.ops.recalc_face_normals`). Fix: reverse face winding in `_build_sprite_quad` (or call `bmesh.ops.recalc_face_normals` before saving), regenerate `automesh.blend`, drop the helper from the test file. Trigger: any time the fixture is regenerated, or when adding new operator tests that bind to fresh sprite quads.

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
| post-merge (Wave 13.2 bind) | Wave 13.2 bind shipped; bind-design.md spec + plan linked; Wave 13.3 fixture-builder followup added | Headless operator pytest pattern proven; fixture quad winding wart surfaced + workarounded in tests, real fix deferred to 13.3 |

## Out of scope (permanently)

Rejected for SPEC 013; do not propose again without re-opening the decision:

- OpenCV / numpy as install-time dependency (COA2 adoption lesson per Constraints + D1).
- Bone-heat solver as default bind algorithm (D4).
- Per-brush mirror as the source of truth (D14).
- ESC as deselect-only inside any draw modal (D10).

## Successor SPECs

- **SPEC 014 (planned: animation polish)** - inherits weight-aware vertex-group machinery; Smart-Bone-style corrective drivers land there.
- **SPEC 004 (slots)** maturity unlocks auto-attach mesh to slot + per-slot weight variations.
- **A future "Quick Mesh" operator** (mentioned in SPEC 012 successor list) is the direct sibling to automesh - lift the modal scaffold from Wave 13.2's Edit Weights wrapper if pursued.
