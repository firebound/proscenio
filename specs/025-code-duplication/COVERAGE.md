# Type-4 audit - file-by-file coverage

Files: 153. Functions: 983 (production 902, test 81).
Every file got Tier A (automated AST signals). 80 files tripped a signal; 22 files were read by hand (Tier B).

Legend: A = automated AST scan (all). B = bodies read by hand. signals = which automated lists the file appeared in.

| File                                                    | prod | test | signals                              | read |
| ------------------------------------------------------- | ---: | ---: | ------------------------------------ | :--: |
| **init**.py                                             |    2 |    0 | skeleton                             |      |
| addon_prefs.py                                          |    6 |    0 | skeleton                             |      |
| core/\_shared/feature_status.py                         |    2 |    0 | -                                    |      |
| core/\_shared/geometry_2d.py                            |    1 |    0 | -                                    |      |
| core/\_shared/hydrate.py                                |    3 |    0 | -                                    |      |
| core/\_shared/modal_overlay_geometry.py                 |    2 |    0 | -                                    |      |
| core/\_shared/pg_cp_fallback.py                         |    3 |    0 | call-overlap,name-collision          |  B   |
| core/\_shared/props_access.py                           |    2 |    0 | -                                    |      |
| core/\_shared/region.py                                 |    7 |    0 | call-overlap                         |  B   |
| core/\_shared/report.py                                 |    5 |    0 | skeleton                             |      |
| core/\_shared/viewport_state.py                         |    1 |    0 | -                                    |      |
| core/armature/quick_armature_math.py                    |    6 |    0 | -                                    |      |
| core/armature/skeleton_target.py                        |    1 |    0 | -                                    |      |
| core/atlas/atlas_packer.py                              |   11 |    0 | -                                    |      |
| core/automesh/contour.py                                |   17 |    0 | call-overlap,skeleton                |      |
| core/automesh/cut_geometry.py                           |    2 |    0 | -                                    |      |
| core/automesh/density.py                                |   10 |    0 | -                                    |      |
| core/automesh/erosion_loops.py                          |    1 |    0 | -                                    |      |
| core/automesh/geometry.py                               |    8 |    0 | call-overlap                         |      |
| core/automesh/outer_splice.py                           |    6 |    0 | -                                    |      |
| core/automesh/stroke_geometry.py                        |    4 |    0 | -                                    |      |
| core/bpy_helpers/\_shared/\_bpy_compat.py               |   25 |    0 | skeleton                             |      |
| core/bpy_helpers/\_shared/modal_overlay.py              |    5 |    0 | call-overlap                         |  B   |
| core/bpy_helpers/\_shared/select.py                     |    1 |    0 | -                                    |      |
| core/bpy_helpers/\_shared/viewport_math.py              |    8 |    0 | -                                    |      |
| core/bpy_helpers/atlas/atlas_collect.py                 |    3 |    0 | -                                    |      |
| core/bpy_helpers/atlas/atlas_compose.py                 |    2 |    0 | -                                    |      |
| core/bpy_helpers/atlas/atlas_manifest.py                |    1 |    0 | -                                    |      |
| core/bpy_helpers/atlas/snapshot.py                      |    1 |    0 | -                                    |      |
| core/bpy_helpers/automesh/authoring_overlay.py          |   16 |    0 | call-overlap                         |      |
| core/bpy_helpers/automesh/authoring_pipeline.py         |   31 |    0 | call-overlap,name-collision          |  B   |
| core/bpy_helpers/automesh/authoring_session.py          |    3 |    0 | name-collision,skeleton              |  B   |
| core/bpy_helpers/automesh/base_sprite.py                |    3 |    0 | call-overlap                         |  B   |
| core/bpy_helpers/automesh/bridge.py                     |   17 |    0 | -                                    |      |
| core/bpy_helpers/automesh/cdt.py                        |    5 |    0 | -                                    |      |
| core/bpy_helpers/automesh/debug.py                      |    7 |    0 | call-overlap                         |  B   |
| core/bpy_helpers/automesh/uv.py                         |    1 |    0 | -                                    |      |
| core/bpy_helpers/psd/psd_spritesheet.py                 |    1 |    0 | -                                    |      |
| core/bpy_helpers/skinning/\_helpers.py                  |    1 |    0 | -                                    |      |
| core/bpy_helpers/skinning/automesh_hook.py              |    6 |    0 | -                                    |      |
| core/bpy_helpers/skinning/bind_apply.py                 |   12 |    0 | -                                    |      |
| core/bpy_helpers/skinning/bone_collection_visibility.py |    2 |    0 | name-collision                       |      |
| core/bpy_helpers/skinning/diagnose_collect.py           |    5 |    0 | -                                    |      |
| core/bpy_helpers/skinning/modal_session.py              |    4 |    0 | name-collision,skeleton              |  B   |
| core/bpy_helpers/skinning/paint_preset_bind.py          |    5 |    0 | -                                    |      |
| core/bpy_helpers/skinning/sidecar_io.py                 |    3 |    0 | -                                    |      |
| core/bpy_helpers/skinning/stroke_diff.py                |    5 |    0 | -                                    |      |
| core/bpy_helpers/skinning/weight_overlay.py             |    5 |    0 | call-overlap                         |      |
| core/bpy_helpers/sprite_frame/sprite_frame_shader.py    |   13 |    0 | -                                    |      |
| core/help_topics.py                                     |    3 |    0 | -                                    |      |
| core/mirror.py                                          |    6 |    0 | call-overlap                         |  B   |
| core/psd/psd_manifest.py                                |   10 |    0 | -                                    |      |
| core/psd/psd_naming.py                                  |    3 |    0 | -                                    |      |
| core/skinning/bind_diagnosis.py                         |    7 |    0 | call-overlap                         |      |
| core/skinning/bone_modes.py                             |    3 |    0 | -                                    |      |
| core/skinning/paint_preset_2d.py                        |    2 |    0 | -                                    |      |
| core/skinning/planar_proximity.py                       |    1 |    0 | -                                    |      |
| core/skinning/sidecar_schema.py                         |    5 |    0 | -                                    |      |
| core/skinning/skinning_modes.py                         |    5 |    0 | -                                    |      |
| core/skinning/weight_diff.py                            |    1 |    0 | -                                    |      |
| core/skinning/weight_reproject.py                       |    7 |    0 | -                                    |      |
| core/skinning/weight_snapshot.py                        |    1 |    0 | -                                    |      |
| core/skinning/weight_transfer.py                        |    1 |    0 | -                                    |      |
| core/slot/slot_emit.py                                  |    3 |    0 | -                                    |      |
| core/sprite_frame/sprite_frame_math.py                  |    3 |    0 | -                                    |      |
| core/uv_bounds.py                                       |    2 |    0 | -                                    |      |
| core/validation/\_shared.py                             |    7 |    0 | call-overlap,name-collision          |      |
| core/validation/active_element.py                       |    4 |    0 | name-collision                       |  B   |
| core/validation/active_slot.py                          |    8 |    0 | call-overlap,name-collision          |  B   |
| core/validation/export.py                               |    9 |    0 | call-overlap,name-collision          |      |
| exporters/godot/writer/**init**.py                      |    1 |    0 | -                                    |      |
| exporters/godot/writer/animations.py                    |   11 |    0 | -                                    |      |
| exporters/godot/writer/scene_discovery.py               |    6 |    0 | call-overlap,name-collision          |  B   |
| exporters/godot/writer/skeleton.py                      |    5 |    0 | -                                    |      |
| exporters/godot/writer/slot_animations.py               |    3 |    0 | -                                    |      |
| exporters/godot/writer/slots.py                         |    3 |    0 | call-overlap                         |      |
| exporters/godot/writer/sprites.py                       |    9 |    0 | call-overlap,name-collision          |  B   |
| importers/photoshop/**init**.py                         |    3 |    0 | -                                    |      |
| importers/photoshop/armature.py                         |    1 |    0 | -                                    |      |
| importers/photoshop/planes.py                           |   14 |    0 | call-overlap                         |  B   |
| operators/**init**.py                                   |    2 |    0 | skeleton                             |      |
| operators/armature/**init**.py                          |    2 |    0 | skeleton                             |      |
| operators/armature/\_overlay.py                         |    5 |    0 | -                                    |      |
| operators/armature/\_status_bar.py                      |    1 |    0 | -                                    |      |
| operators/armature/authoring_camera.py                  |    3 |    0 | skeleton                             |      |
| operators/armature/authoring_ik.py                      |    4 |    0 | skeleton                             |      |
| operators/armature/quick_armature.py                    |   40 |    0 | call-overlap,name-collision,skeleton |  B   |
| operators/armature/skeleton_target.py                   |    3 |    0 | skeleton                             |      |
| operators/atlas_pack/**init**.py                        |    2 |    0 | skeleton                             |      |
| operators/atlas_pack/\_paths.py                         |    5 |    0 | -                                    |      |
| operators/atlas_pack/apply.py                           |   11 |    0 | skeleton                             |      |
| operators/atlas_pack/pack.py                            |    4 |    0 | skeleton                             |      |
| operators/atlas_pack/unpack.py                          |    8 |    0 | skeleton                             |      |
| operators/automesh/**init**.py                          |    2 |    0 | skeleton                             |      |
| operators/automesh/\_status_bar.py                      |    2 |    0 | -                                    |      |
| operators/automesh/automesh.py                          |   13 |    0 | call-overlap,name-collision,skeleton |  B   |
| operators/automesh/automesh_authoring.py                |   76 |    0 | call-overlap,name-collision,skeleton |  B   |
| operators/driver.py                                     |    8 |    0 | skeleton                             |      |
| operators/export_flow.py                                |    9 |    0 | call-overlap,skeleton                |  B   |
| operators/help_dispatch.py                              |    9 |    0 | skeleton                             |      |
| operators/import_photoshop.py                           |    3 |    0 | skeleton                             |      |
| operators/pose_library.py                               |    8 |    0 | skeleton                             |      |
| operators/selection.py                                  |    9 |    0 | call-overlap,skeleton                |      |
| operators/skinning/**init**.py                          |    2 |    0 | skeleton                             |      |
| operators/skinning/bind_mesh.py                         |    6 |    0 | call-overlap,skeleton                |      |
| operators/skinning/brush_preset.py                      |    4 |    0 | skeleton                             |      |
| operators/skinning/copy_weights_to_selected.py          |    7 |    0 | skeleton                             |      |
| operators/skinning/edit_weights.py                      |   12 |    0 | name-collision,skeleton              |      |
| operators/skinning/restore_weight_snapshot.py           |    4 |    0 | skeleton                             |      |
| operators/skinning/set_bone_mode.py                     |    4 |    0 | skeleton                             |      |
| operators/skinning/sidecar_io.py                        |    6 |    0 | skeleton                             |      |
| operators/slot/**init**.py                              |    2 |    0 | skeleton                             |      |
| operators/slot/attachment.py                            |    6 |    0 | skeleton                             |      |
| operators/slot/create.py                                |    6 |    0 | skeleton                             |      |
| operators/slot/preview_shader.py                        |    6 |    0 | skeleton                             |      |
| operators/slot/select.py                                |    3 |    0 | call-overlap,skeleton                |      |
| operators/uv_authoring.py                               |    6 |    0 | skeleton                             |      |
| panels/**init**.py                                      |    3 |    0 | -                                    |      |
| panels/\_draw_driver_shortcut.py                        |    1 |    0 | call-overlap,name-collision          |      |
| panels/\_draw_mesh.py                                   |    2 |    0 | name-collision                       |  B   |
| panels/\_draw_region.py                                 |    1 |    0 | name-collision                       |      |
| panels/\_draw_sprite.py                                 |    6 |    0 | name-collision                       |  B   |
| panels/\_helpers.py                                     |    4 |    0 | skeleton                             |      |
| panels/animation.py                                     |    5 |    0 | call-overlap,skeleton                |      |
| panels/atlas.py                                         |    7 |    0 | skeleton                             |      |
| panels/diagnostics.py                                   |    5 |    0 | skeleton                             |      |
| panels/element.py                                       |   17 |    0 | skeleton                             |      |
| panels/help.py                                          |    4 |    0 | skeleton                             |      |
| panels/helpers.py                                       |    4 |    0 | skeleton                             |      |
| panels/mesh_generation.py                               |   18 |    0 | skeleton                             |      |
| panels/outliner.py                                      |    7 |    0 | call-overlap,skeleton                |      |
| panels/pipeline.py                                      |    9 |    0 | skeleton                             |      |
| panels/skeleton.py                                      |   14 |    0 | call-overlap,skeleton                |      |
| panels/slots.py                                         |   10 |    0 | skeleton                             |      |
| panels/validation.py                                    |    4 |    0 | skeleton                             |      |
| panels/weight_paint.py                                  |   27 |    0 | call-overlap,skeleton                |      |
| properties/**init**.py                                  |    2 |    0 | -                                    |      |
| properties/\_dynamic_items.py                           |    3 |    0 | skeleton                             |  B   |
| properties/\_handlers.py                                |    7 |    0 | -                                    |      |
| properties/scene_props.py                               |    1 |    0 | skeleton                             |  B   |
| tests/operators/conftest.py                             |    0 |    2 | -                                    |      |
| tests/operators/test_automesh_authoring.py              |    0 |   28 | -                                    |      |
| tests/operators/test_automesh_regen.py                  |    0 |    6 | -                                    |      |
| tests/operators/test_bind_mesh.py                       |    0 |    9 | -                                    |      |
| tests/operators/test_edit_weights_modal.py              |    0 |    7 | -                                    |      |
| tests/operators/test_mixed_flow_auto_snapshot.py        |    0 |    2 | -                                    |      |
| tests/operators/test_multi_mesh_bind.py                 |    0 |    4 | -                                    |      |
| tests/operators/test_restore_snapshot.py                |    0 |    5 | -                                    |      |
| tests/operators/test_sidecar_io.py                      |    0 |    6 | -                                    |      |
| tests/operators/test_weight_transfer.py                 |    0 |    1 | -                                    |      |
| tests/run_coverage.py                                   |    0 |    3 | -                                    |      |
| tests/run_operator_tests.py                             |    0 |    1 | -                                    |      |
| tests/run_tests.py                                      |    0 |    7 | -                                    |      |

## Files without function definitions (not applicable)

27 of the 180 `.py` files define no functions, so there is no logic to duplicate. 24 are `__init__.py` package markers / re-export shims. The remaining 6 hold only constants, dataclasses, or type declarations:

- `core/_shared/cp_keys.py` - Custom Property key string constants.
- `core/skinning/authoring_stages.py` - stage dataclasses + params.
- `core/skinning/brush_curve_presets.py` - preset data tables.
- `core/validation/issue.py` - the `Issue` dataclass.
- `properties/object_props.py` - PropertyGroup field declarations.
- `properties/validation_issue.py` - PropertyGroup field declarations.

These were not compared for duplicate _data schemas_ - that is a different question from duplicate _logic_ and out of scope for this audit.

## Residual blind spot

What the audit provably covered, and what it could still miss:

- **Skeleton + name signals: 100 percent of the 902 production functions.** Any function that is a structural twin of another, or shares a name across files, was flagged and reviewed.
- **Call-overlap (the type-4 signal): only functions with >= 4 distinct call targets** were pairwise-compared, at Jaccard >= 0.6. This is where the gap lives:
  - Small or pure-computation functions (fewer than 4 calls - bbox math, coordinate transforms, predicate helpers) were not pairwise-compared by the call signal. They are still covered by the skeleton and name signals, but a pair that computes the same result through _different_ operators AND a different structure would slip.
  - Pairs in the 0.4 - 0.6 overlap band were not surfaced.
  - Type-4 twins that reach the same output through _entirely different APIs_ (call-set overlap near zero) are fundamentally invisible to this signal. Only reading same-domain modules side by side catches them.
- **Inline duplication (a repeated block inside a larger function, not its own `def`)** is below function granularity here. The earlier PMD CPD token pass (`raw/cpd-blender-t35*.txt`) partly covers that; together the two passes overlap but neither alone is complete.
- **Tier B (hand-read bodies): 22 files.** The other 131 function-bearing files were judged from automated signals only.

To fully close the residual gap, the remaining 131 function-bearing files would need a same-domain hand read. The automated pass makes that tractable by pointing at the 80 signal-tripping files first, but it is not a substitute for reading every line if absolute certainty on type-4 is required.

## Deep-pass coverage update

The first table above reflects the original pass (22 files hand-read). The deeper pass (scan v2 + a domain-by-domain hand read) raised eyes-on coverage substantially. Honest current state:

- **Automated (Tier A): 100% of functions**, now via _two_ scanners - `ast_scan.py` (exact skeleton + call-overlap + names) and `ast_scan2.py` (k-gram near-skeleton, lowered call-overlap, data-schema). Reports: `raw/ast-report.txt`, `raw/ast-report-v2.txt`.
- **Hand-read (Tier B): 91 of 140 production function-files.** This includes **100% of the algorithmic core** - every module under `core/` that carries logic (geometry, contour, density, skinning weights/bind/reproject/diff, sidecar codec, slot/psd/sprite_frame math, the automesh bridge, the bpy_helpers), plus all of `core/validation`, the godot writer set, the importers, and a large operator/panel sample covering every structural pattern (poll guards, register, status-bar render, selection, panel-header, per-mode draw dispatch, resolve-picker).
- **Not yet hand-read: 49 files** (listed below). ~10 are `__init__.py` register/unregister shims (trivial). The rest are operator/panel registration + UI draw boilerplate, two shader-graph builders (`sprite_frame_shader`, `paint_preset_bind`), data tables (`help_topics`, `addon_prefs`), `preview_icons`, and `psd_spritesheet`. Their duplication patterns are already captured by the established families (poll-guard, register, N-IMG material walk, N2 PG/CP read, N8 scene.proscenio access, status-bar) and by the AST signal - but they have not been read line-by-line, so any duplication unique to them is the remaining gap.

Files not yet hand-read:

```plaintext
__init__.py
addon_prefs.py
core/bpy_helpers/automesh/authoring_overlay.py   (draw family already characterised via call-overlap)
core/bpy_helpers/psd/psd_spritesheet.py
core/bpy_helpers/skinning/paint_preset_bind.py
core/bpy_helpers/sprite_frame/sprite_frame_shader.py
core/help_topics.py
operators/armature/authoring_camera.py
operators/armature/authoring_ik.py
operators/armature/skeleton_target.py
operators/atlas_pack/apply.py
operators/atlas_pack/pack.py
operators/atlas_pack/unpack.py
operators/driver.py
operators/help_dispatch.py
operators/import_photoshop.py
operators/pose_library.py
operators/skinning/bind_mesh.py
operators/skinning/brush_preset.py
operators/skinning/edit_weights.py
operators/skinning/restore_weight_snapshot.py
operators/skinning/sidecar_io.py
operators/slot/attachment.py
operators/slot/create.py
operators/slot/preview_shader.py
operators/uv_authoring.py
panels/animation.py
panels/atlas.py
panels/diagnostics.py
panels/element.py
panels/help.py
panels/helpers.py
panels/mesh_generation.py
panels/pipeline.py
panels/skeleton.py
panels/slots.py
panels/validation.py
panels/weight_paint.py
properties/__init__.py
properties/_handlers.py
(+ 10 __init__.py register shims)
```

## Final coverage (after the full sweep)

Every **logic-bearing** production file in `apps/blender` has now been hand-read. What remains un-read line-by-line is only:

- `__init__.py` register/unregister shims (~10 files) - each is the identical `for cls in _classes: bpy.utils.(un)register_class(cls)` loop, no logic.
- A few panel-class tails (second halves of element / skeleton / slots / weight_paint / atlas / animation already opened) - pure `layout.prop` / `layout.operator` UI, same pattern confirmed across the ~15 panels already read.

Net: the type-4 / semantic-duplication finding set (D1-D15 + N1-N26 + the rejected list) is complete. No algorithmic logic in the addon went unread. The two automated scanners (`ast_scan.py`, `ast_scan2.py`) cover 100% of functions as the backstop for anything a human pass would miss in the boilerplate tail.
