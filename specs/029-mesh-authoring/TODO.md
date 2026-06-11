# Spec 029: Mesh authoring - TODO

Sequenced from [STUDY.md](STUDY.md): the blocking splice fix first, then two batched polish PRs. The polish rows are post-release wave 4 in [EXECUTION_MAP.md](../EXECUTION_MAP.md); inside this spec they run after the blocking chunk.

## Now

### Chunk 1 - fix the Stage 2 extend/cut splice (blocking)

- [ ] Re-anchor the splice at the stroke/contour segment crossings instead of nearest-outer-vert-to-inside-sample, removing the winding/seam arc conflation in `_splice_outside_run` ([outer_splice.py](../../apps/blender/core/automesh/outer_splice.py))
- [ ] Treat on-boundary stroke samples as inside for the extend mask so snap-anchored strokes stop classifying as fully outside (the pen snap in [automesh_authoring.py](../../apps/blender/operators/automesh/automesh_authoring.py) places endpoints exactly on outer verts)
- [ ] Align `_resolve_outer_override_local` with the preview's value-equality no-op check so the "stroke ignored" warning actually fires ([authoring_pipeline.py](../../apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py), the dead `is` test)
- [ ] Harden [test_outer_splice.py](../../tests/automesh/test_outer_splice.py): assert the bump lands in the correct arc (not just that it exists), plus against-winding, seam-straddling, and snapped-endpoint strokes
- [ ] Acknowledge committed Stage 2 cuts before APPLY (stage label count or tooltip), since cuts change no overlay by design and read as a no-op
- [ ] GUI re-run of the queued scenarios: backlog-manual-testing 1.23 T1 and 1.25 T6/T9 (extend, cut overlay, spliced-outer preview)

### Chunk 2 - props and labels (one PR)

- [ ] Rename `Mesh resolution` so the name stops reading backwards (lower = denser), or invert the scale; sync `help_topics.py` and `docs/02-blender-addon/05-mesh-generation.md` ([scene_props.py](../../apps/blender/properties/scene_props.py))
- [ ] Flip `Density follows bones` default to OFF in the scene PG and the operator prop ([scene_props.py](../../apps/blender/properties/scene_props.py), [automesh.py](../../apps/blender/operators/automesh/automesh.py))
- [ ] Move `Interior spacing` out of the dense-only block into the main numeric column - the modal reads it in SIMPLE mode too ([mesh_generation.py](../../apps/blender/panels/mesh_generation.py))
- [ ] Rename the `Automesh (modal)` button and the "Multi-stage modal preview" label to action-oriented copy; sync the help topic (the guide-page mention belongs to the guide-doc rename sweep in the ui-help-surfaces spec)

### Chunk 3 - regen trust and element gating (one PR)

- [ ] Mirror `Preserve weights on regen` (readout + the same scene prop) in the **Automesh from Alpha** and **Automesh Interactive** subpanels where regen actually runs ([mesh_generation.py](../../apps/blender/panels/mesh_generation.py))
- [ ] Gate the **Mesh Generation** panel and the automesh operators on `element_type == "mesh"` with a warn-not-hide, copying the Weight Paint `_is_mesh_element` pattern ([mesh_generation.py](../../apps/blender/panels/mesh_generation.py), [automesh.py](../../apps/blender/operators/automesh/automesh.py))
- [ ] Validation check: a `sprite` element's mesh stays a single quad (4 verts, 1 face); warn otherwise
- [ ] One sentence in the gate warn / help topic pointing sprites at native bone-parenting (<kbd>Ctrl+P</kbd> > `Bone`) - this is the replacement for the dropped rigid-bind operator

## Deferred

- Manual hull authoring - gate: an artist authoring real game art hits a hull alpha-trace cannot produce AND the Edit Mode + `Reproject UV` fallback proves too clumsy in a logged session; revisit only after the extend/cut splice it would reuse has soaked. If the trigger has not fired by 1.0, prune the backlog entry too.

## Dropped

- Sprite rigid single-bone bind - native bone-parenting already is the rigid bind; the element-gating warn plus the help sentence in chunk 3 covers discovery, so a dedicated operator would wrap a one-keystroke native action (propose removing the entry from backlog.md).
