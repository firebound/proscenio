# Spec 052: Blender operator robustness - TODO

Two PRs. Each item is independent; group them only to keep review surfaces coherent.

## PR 1 - export and atlas correctness

- [ ] First export reads `scene.proscenio.pixels_per_unit` instead of the ExportHelper default of 100. `export_flow.py:158-167`, `pipeline.py:89`. (High: editing the panel field silently does nothing on the first export today.)
- [ ] Import stops silently overwriting the scene pixels-per-unit with the manifest value, or warns when it differs. `importers/photoshop/__init__.py:94-107`.
- [ ] Apply Packed Atlas counts a sprite as rewritten only when `_rewrite_uvs` succeeded, not unconditionally for `element_type == "sprite"`. `atlas_pack/apply.py:165-216`.
- [ ] Atlas apply wraps `read_manifest(manifest_json)` in `except (json.JSONDecodeError, KeyError, TypeError, ValueError)` and reports-and-cancels rather than leaking a raw traceback. `atlas_pack/apply.py:64`.
- [ ] The sprites writer pairs `iter_poly_vertices` with `iter_poly_loop_indices` under `zip(..., strict=True)` so a mismatched-count polygon fails early instead of truncating to wrong topology. `exporters/godot/writer/sprites.py:216`.
- [ ] Filter Constrained Delaunay holes to those with at least three vertices before line 175 sets the with-holes output type, and drop the now-redundant guard in `_build_cdt_inputs`. `core/bpy_helpers/automesh/cdt.py:175`, `:91-93`.

## PR 2 - operator feedback and guards

- [ ] Bake Current Pose inserts only on the channel matching each bone's `rotation_mode`, leaving no garbage fcurves on the unused channel. `pose_library.py:143-145`.
- [ ] Quick Armature `invoke` reads `lock_to_front_ortho` from the property group so the panel toggle takes effect without an F3 override. `quick_armature.py:200-221`.
- [ ] Copy Weights to Selected returns CANCELLED (not FINISHED) on a zero-coverage transfer so it is not a successful undo step with nothing applied. `copy_weights_to_selected.py:49-51`.
- [ ] Bake IK to Keyframes restores per-bone selection after scoping `nla.bake`. `authoring_ik.py:201-213`.
- [ ] Action-row no-armature / not-found / multi-armature feedback surfaces even at log level "errors" so a failed click is not silent. `report.py:50-53`, `selection.py`.
- [ ] The Drive-from-Bone shortcut button computes `has_bones = bones is not None and len(bones) > 0` rather than `bool(getattr(...))`, which is truthy for a zero-bone armature. `panels/_draw_driver_shortcut.py:41`, matching `properties/_dynamic_items.py:59`.
- [ ] The selection action guards `armature.animation_data` / `animation_data_create()` with `except ReferenceError: report_warn(...); return {"CANCELLED"}` for a deleted armature. `operators/selection.py:188-190`, matching `panels/skeleton.py:112`.
- [ ] Sidecar `_entry_from_dict` wraps its `float(...)` conversions in `try/except (TypeError, ValueError)` re-raising a descriptive `ValueError`, honoring `from_json`'s "always raises ValueError" contract. `core/skinning/sidecar_schema.py:115-119`.
