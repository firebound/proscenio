# Spec 078 TODO: Automesh dense-fill fix + front-ortho snap

Execution plan for [STUDY.md](STUDY.md). Two independent tracks; no ordering between them.

## Track A - Automesh dense-fill

### A1. Fill the whole silhouette (stop treating the inner ring as a hole)

- [x] [cdt.py](../../apps/blender/core/bpy_helpers/automesh/cdt.py): `build_mesh_via_delaunay` now always uses `output_type=1` (CDT_INSIDE) and never auto-detects holes. The original `output_type=2 if inner or holes` carved the eroded inner ring as a hole; the intermediate `2 if holes else 1` still risked it whenever a real alpha hole was present (CodeRabbit), because CDT auto-hole-detection is unreliable against the bridge's orientation flow. Genuine alpha holes are carved downstream by the deterministic `delete_faces_inside_holes` centroid prune, so the inner ring stays a constraint loop only.
- [x] [bridge.py](../../apps/blender/core/bpy_helpers/automesh/bridge.py): `_compute_steiner_points` passes `[]` for the inner argument to `interior_points_for_annulus` so the Dense grid fills inside the outer contour; `inner_world` is kept in the min-separation `boundary_for_filter`. Docstring corrected.
- [x] [authoring_pipeline.py:359](../../apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py#L359): the interactive authoring path already passed `inner=[]` (its preview always filled the full interior); this fix makes the one-shot build match it. No change needed - confirmed consistent.
- [x] [scene_props.py](../../apps/blender/properties/scene_props.py): `margin_pixels` description rewritten (it adds an inner edge-density loop; it no longer produces a ring / excludes the interior). pt-BR i18n catalog entry updated to match.

### A2. Lock the behaviour with a test

- [x] `test_boundary_margin_does_not_starve_dense_interior_fill`: with `margin_pixels > 0`, Dense keeps close to its `margin_pixels=0` vert count and stays materially denser than Simple. Verified it fails without the fix (Dense and Simple both 128 verts). Existing simple<dense test stays green.
- [x] `test_cdt_keeps_the_inner_ring_filled_alongside_a_real_hole`: a margin ring plus a genuine hole produces a filled centre and a carved hole (guards the margin+hole combination CodeRabbit flagged). Note: the collapse does not reproduce with synthetic square loops at the CDT layer, so this is a behaviour-contract test, not a fail-without-fix regression; the fix rests on removing the unreliable auto-detection the module already documents.
- [x] Pure `tests/automesh/test_density.py` stays unchanged and green (the density module contract is untouched).

## Track B - Front-ortho snap for the interactive modals

### B1. Shared view-session infra

- [x] Moved `ViewSnapshot` (+ `_log_view`) to `bpy_helpers/_shared/view_session.py` with a constructor `tag` (default `Proscenio`).
- [x] Quick Armature's import updated to the new path; no behaviour change (its own `lock_to_front_ortho` toggle is unchanged).
- [x] Added `FrontOrthoModalMixin`: owns `_front_ortho_view`, exposes `lock_to_front_ortho: BoolProperty(default=True)`, and provides `enter_front_ortho(context, report, tag=...)` + `exit_front_ortho(report)`. No `from __future__ import annotations` in the module (it would break the RNA property registration).

### B2. Apply to the three modals

- [x] Automesh authoring, Manual Mesh, Edit Weights inherit the mixin; `enter_front_ortho` in `invoke` (after the precondition gate), `exit_front_ortho` in `_finish` (covers cancel).
- [x] The mixin's `lock_to_front_ortho` reuses Quick Armature's exact name + description so it stays out of the i18n catalog. The `exit_front_ortho` call in each `_finish` is wrapped in `contextlib.suppress(Exception)` (a view-restore failure must not abort the mode/selection restore, matching the other teardown steps).
- [ ] Deferred: a per-tool PG field + panel checkbox so the artist can opt out interactively. The operator property (default True) forces front ortho for now, which matches the "only front ortho" intent; the panel toggle is a fast-follow.

### B3. Verify the snap lifecycle

- [x] Headless smoke: `test_front_ortho_mixin_lifecycle_noops_without_a_viewport_region` drives the mixin `enter`/`exit` with no `region_data` and asserts neither raises nor reports.
- [ ] Manual QA (log in the QA Companion): entering each tool snaps to Front Ortho and exiting restores the prior view (a full view round-trip needs an interactive region).

## Track C - Gates + close-out

- [x] Gates: ruff + ruff-format, mypy, `tests/` pytest (1002, density unchanged), the in-Blender operator suite (300), and the 8/8 export goldens byte-identical.
- [ ] On ship, prune `078-authoring-dense-and-ortho/` and record the summary + PR in [index.md](index.md). Code rides this branch + PR.

## Definition of done

- Automesh Dense produces a denser FILLED mesh than Simple with `margin_pixels > 0` (no empty centre), including when a genuine alpha hole is present; the density module + its tests are untouched.
- Automesh, Manual Mesh, and Edit Weights snap to Front Orthographic on entry (default ON) and restore on exit, reusing the shared `ViewSnapshot`.
- All gates green; goldens byte-identical.
