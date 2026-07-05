# Spec 078 TODO: Automesh dense-fill fix + front-ortho snap

Execution plan for [STUDY.md](STUDY.md). Two independent tracks; no ordering between them.

## Track A - Automesh dense-fill

### A1. Fill the whole silhouette (stop treating the inner ring as a hole)

- [ ] [cdt.py:181](../../apps/blender/core/bpy_helpers/automesh/cdt.py#L181): `output_type = 2 if holes else 1` (the inner ring is a constraint loop, not a hole; only real alpha holes flip to with-holes). Update the `build_mesh_via_delaunay` docstring block that claims the inner ring's interior is excluded ([cdt.py:144-149](../../apps/blender/core/bpy_helpers/automesh/cdt.py#L144-L149)).
- [ ] [bridge.py:585](../../apps/blender/core/bpy_helpers/automesh/bridge.py#L585): pass `[]` for the inner argument to `interior_points_for_annulus` so the Dense grid fills inside the outer contour. Keep `inner_world` in the min-separation `boundary_for_filter` ([bridge.py:607](../../apps/blender/core/bpy_helpers/automesh/bridge.py#L607)). Correct the `_compute_steiner_points` docstring (the annulus-skip note).
- [ ] [authoring_pipeline.py:359](../../apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py#L359): the interactive authoring path already passes `inner=[]` (its preview always filled the full interior); this fix makes the one-shot build match it, so no change is needed here - just confirm consistency.
- [ ] [scene_props.py:106-121](../../apps/blender/properties/scene_props.py#L106-L121): rewrite the `margin_pixels` description - it adds an inner edge-density loop at the silhouette; it no longer produces a ring / excludes the interior.

### A2. Lock the behaviour with a test

- [ ] In-Blender operator test ([apps/blender/tests/operators/test_automesh_authoring.py](../../apps/blender/tests/operators/test_automesh_authoring.py)): with `margin_pixels > 0`, Dense fills the interior (verts inside the eroded inner ring exist and faces cover the centre - no hole) and `dense_verts` is materially greater than `simple_verts` (not a 1-vert margin). Keep the existing simple<dense test green.
- [ ] Confirm the pure `tests/automesh/test_density.py` stays unchanged and green (the density module contract is untouched).

## Track B - Front-ortho snap for the interactive modals

### B1. Shared view-session infra

- [ ] Move `ViewSnapshot` (+ `_log_view`) from [bpy_helpers/armature/view_session.py](../../apps/blender/core/bpy_helpers/armature/view_session.py) to `bpy_helpers/_shared/view_session.py`; give the log tag a constructor arg (default `Proscenio`) so it is not Quick-Armature-specific.
- [ ] Update Quick Armature's import to the new path ([quick_armature.py:68](../../apps/blender/operators/armature/quick_armature.py#L68)); no behaviour change.
- [ ] Add `FrontOrthoModalMixin` to the same module: owns a `_view: ClassVar[ViewSnapshot]`, exposes `lock_to_front_ortho: BoolProperty(default=True)`, and provides `enter_front_ortho(context, report)` (capture + conditional snap) and `exit_front_ortho(report)` (restore).

### B2. Apply to the three modals

- [ ] Automesh authoring ([operators/automesh/automesh_authoring.py](../../apps/blender/operators/automesh/automesh_authoring.py)): inherit the mixin; call `enter_front_ortho` in `invoke` (after the precondition gate) and `exit_front_ortho` in `_finish`/`cancel`.
- [ ] Manual Mesh ([operators/automesh/draw_mesh_vertices.py](../../apps/blender/operators/automesh/draw_mesh_vertices.py)): same wiring.
- [ ] Edit Weights ([operators/skinning/edit_weights.py](../../apps/blender/operators/skinning/edit_weights.py)): same wiring (snap before entering weight-paint mode; restore on exit).
- [ ] The mixin's `lock_to_front_ortho` reuses Quick Armature's exact name + description so it stays out of the i18n catalog. The `exit_front_ortho` call in each `_finish` is wrapped in `contextlib.suppress(Exception)` (a view-restore failure must not abort the mode/selection restore, matching the other teardown steps).
- [ ] Deferred: a per-tool PG field + panel checkbox so the artist can opt out interactively. The operator property (default True) forces front ortho for now, which matches the "only front ortho" intent; the panel toggle is a fast-follow.

### B3. Verify the snap lifecycle

- [ ] Headless smoke: each modal's `invoke` reads the toggle and does not raise when no `region_data` (the `ViewSnapshot.capture`/`snap` no-op path). A full view-round-trip needs an interactive region, so the deep assert stays a manual QA walk.
- [ ] Manual QA (log in the QA Companion): entering each tool snaps to Front Ortho and exiting restores the prior view; toggling the checkbox OFF authors from the current view.

## Track C - Gates + close-out

- [ ] Gates: ruff + ruff-format, mypy, `tests/` pytest (density unchanged), the in-Blender operator suite, and the 8/8 export goldens (Track A changes authoring-time mesh gen; the baked goldens must stay byte-identical - if a fixture regenerates automesh, re-bake and justify).
- [ ] On ship, prune `078-authoring-dense-and-ortho/` and record the summary + PR in [index.md](index.md). Code rides this branch + PR.

## Definition of done

- Automesh Dense produces a visibly denser FILLED mesh than Simple with `margin_pixels > 0` (no empty centre); the density module + its tests are untouched.
- Automesh, Manual Mesh, and Edit Weights snap to Front Orthographic on entry (default ON) and restore on exit, reusing the shared `ViewSnapshot`.
- All gates green; goldens byte-identical.
