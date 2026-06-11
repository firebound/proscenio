# Spec 030: Skinning and weight paint - TODO

Sequenced from the assessment in [STUDY.md](STUDY.md): the two blocking bind bugs first, then the panel-correction batches, then the re-import flow protection. The aspirational cluster is gated or dropped there with full reasoning.

## Now

### PR 1: fix the brush-curve presets throwing on click

- [ ] Capture the exact traceback once in a GUI session (the bug entry never got it) and record it in the PR description.
- [ ] Rebuild the curve robustly in [brush_preset.py](../../apps/blender/operators/skinning/brush_preset.py): insert points in ascending-x order, refetch collection proxies after every `remove`/`new` mutation, wrap the rebuild in try/except that reports `WARNING` instead of propagating RuntimeError.
- [ ] Add a headless regression test that applies every preset in [brush_curve_presets.py](../../apps/blender/core/skinning/brush_curve_presets.py) to a real brush datablock and asserts the resulting point locations.

### PR 2: make the Bind subpanel honest and complete

- [ ] Gate the per-bone overrides box in `_draw_bind` ([weight_paint.py](../../apps/blender/panels/weight_paint.py)) to the planar modes; under `Bone Heat (Blender native)` show a hint label that overrides apply only to the planar modes (closes the inert-overrides bug without touching [bind_apply.py](../../apps/blender/core/bpy_helpers/skinning/bind_apply.py)).
- [ ] Add the clear path: third state in [set_bone_mode.py](../../apps/blender/operators/skinning/set_bone_mode.py) that pops the bone's key from the modes dict, plus a per-row default/clear button in the overrides box.
- [ ] Name the picker armature in the **Bind** subpanel body so the target is visible without scrolling to the parent readout.
- [ ] Move `Bind to Picker Armature` below the overrides box so the order reads Mode, overrides, then the action that consumes them.
- [ ] Headless tests: overrides box gating by mode is a draw-helper decision worth a pure helper + unit; clear-path round-trip via [bone_modes.py](../../apps/blender/core/skinning/bone_modes.py) read/write.
- [ ] Note in the PR: this completes the Soft/Hard runtime per-bone toggle backlog row - the toggle and rebind already work under the planar modes; no separate work remains.

### PR 3: Weight Transfer visibility

- [ ] Surface `max_distance` in the **Weight Transfer** subpanel ([weight_paint.py](../../apps/blender/panels/weight_paint.py)) feeding the operator property in [copy_weights_to_selected.py](../../apps/blender/operators/skinning/copy_weights_to_selected.py).
- [ ] Report per-target coverage (`X/Y verts received weights`) and emit a `WARNING` naming each target with zero coverage, with the hint to raise `Max Distance` or move the meshes closer.
- [ ] Headless tests: zero-coverage and partial-coverage targets assert the report severity and text.

### PR 4: Snapshot naming and live-applying Import

- [ ] Unify naming: fold the **Sidecar IO** buttons under the **Snapshot** subpanel (or rename it `Snapshot Export/Import`) and relabel the operators in [sidecar_io.py](../../apps/blender/operators/skinning/sidecar_io.py) so "sidecar" never appears user-facing.
- [ ] Make Import apply to live weights when the imported payload's topology hash matches the live mesh (reuse `apply_sidecar`); when it differs, report that the snapshot was stored only and point at the automesh preserve flow, mirroring [restore_weight_snapshot.py](../../apps/blender/operators/skinning/restore_weight_snapshot.py) semantics.
- [ ] Headless tests: import-with-matching-hash asserts vertex-group weights changed; import-with-mismatch asserts CP stored and weights untouched.

### PR 5: flat-mesh weight display via the native overlay

- [ ] Expose the native viewport weight-paint overlay opacity (and the zero-weights display option) from the **Edit Weights** subpanel so the texture stays visible while painting; document the upstream caveat that opacity 0 is not fully invisible (Blender issue 145603).
- [ ] Add one help-topic line documenting the native pose-while-painting combo (pose bones live inside Weight Paint mode) - this replaces the dropped live pose-mode preview item.

### PR 6: weight-preserving PSD re-import

- [ ] Short-circuit the mesh rebuild in `_ensure_mesh` ([planes.py](../../apps/blender/importers/photoshop/planes.py)) when the matched layer's placement size and geometry offset are unchanged - the common art-retouch case keeps mesh, densification, and weights untouched.
- [ ] When the placement did change, wire `maybe_pre_regen_snapshot` / `maybe_post_regen_reproject` ([automesh_hook.py](../../apps/blender/core/bpy_helpers/skinning/automesh_hook.py)) around the rebuild per matched layer, honoring `preserve_on_regen`; weights reproject onto the fresh quad and a follow-up automesh regen redistributes them.
- [ ] Update the re-import semantics docstring in [planes.py](../../apps/blender/importers/photoshop/planes.py) (it currently documents the data loss as the contract).
- [ ] Headless end-to-end test: import fixture, bind, paint a weight, re-import unchanged (assert weights identical), re-import with changed bounds (assert weights reprojected, not wiped).

## Deferred

- **Auto-patch joint cover** - gate; trigger: a humanoid fixture ships end to end AND the artist reports articulation gaps that overlapping art plus seam weighting cannot hide.
- **Bone Heat per-bone override post-pass** (extension of PR 2) - gate; trigger: a user binding with `Bone Heat (Blender native)` asks for per-bone Soft/Hard control instead of switching the mode to `Proximity`.
- **Spine-style custom weight overlay** (extension of PR 5) - gate; trigger: a real skinning session judges the native overlay opacity insufficient on flat meshes.

## Dropped

- **Bone-strength region painting** - duplicates the shipped `Envelope` bind plus native bone envelopes behind a new gizmo surface; Moho itself treats region binding as the non-default refinement.
- **Live pose-mode preview** - native Blender already poses bones live inside Weight Paint mode; PR 5 documents the combo instead.
- **Cubism-style glue seam-bind** - Godot has no vertex-stitch runtime constraint, so glue would author data the export must discard.
- **Smart-bone corrective drivers** - requires a morph/vertex track the schema lacks and Polygon2D cannot play; re-propose only inside a future schema-level morph feature.
- **Mirror humanoid binding** - cutout limbs are separate asymmetric drawings in the standard 3/4 view; no symmetric mesh to mirror, no symmetric fixture, brush X-mirror covers the single-mesh case.
- **Bezier brush stroke** - silhouette authoring belongs to the mesh-authoring spec; polyline strokes plus arc-length resample already smooth contours, and stroke feel is the most expensive test class for zero demand.
