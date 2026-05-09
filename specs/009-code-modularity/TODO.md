# SPEC 009 — TODO

Reorganization plan derived from [STUDY.md](STUDY.md). Each wave is self-contained: tests pass before and after, behavior does not change, public test imports stay reachable. Waves are independent and can be sequenced freely; the order below reflects expected payoff per change.

The waves apply only to the Blender addon. The GDScript plugin and the Photoshop JSX side are out of scope for SPEC 009 (sections 20 and 21 of STUDY.md document why).

## Decision lock-in

- [x] D1 — `operators/__init__.py` becomes a package; concrete operators land in topical submodules. The `__init__.py` only orchestrates registration.
- [x] D2 — `panels/__init__.py` becomes a package; panels group by subpanel concern. Cross-panel helpers live in `panels/_helpers.py`.
- [x] D3 — `exporters/godot/writer.py` becomes `exporters/godot/writer/` package with one module per emission concern (skeleton, sprites, slots, animations).
- [x] D4 — `core/` keeps its current advertised contract but gets a shared-fundamentals submodule (`core/_props.py`, `core/_select.py`, `core/_report.py`, `core/cp_keys.py`) for the DRY extractions identified in STUDY section 8.
- [x] D5 — `core/validation.py` splits into `core/validation/` subpackage with one module per validator (active sprite, active slot, export). Public re-exports from `core/validation/__init__.py` keep test imports stable.
- [x] D6 — bpy-bound modules currently in `core/` (`atlas_io.py`, `psd_spritesheet.py`, `sprite_frame_shader.py`) move into a sibling subpackage `core/bpy_helpers/`. The package docstring on `core/__init__.py` is updated to reflect the bpy-free contract that holds for the rest of `core/`.
- [x] D7 — Per-wave: lint + mypy strict + pytest 121 must stay green. No behavior change; commits are mechanical moves plus minimal shim imports.
- [x] D8 — No public API breaks. Tests already import from `core.<module>`; if a module splits, the parent `__init__.py` re-exports the public symbols.
- [x] D9 — Each wave ships as its own PR (or stacked PRs) so review can verify one concern at a time.
- [x] D10 — `register()`/`unregister()` per submodule. The package-level orchestrator iterates submodules in order rather than carrying a flat `_classes` tuple.

## Reorganization waves

### Wave 9.1 — Cross-cutting helpers (DRY extractions)

Pre-work before splitting the god-modules. Centralizes the small idioms identified in STUDY section 8 so the operator + panel splits inherit them as imports rather than re-defining them.

- [x] `core/cp_keys.py` — module-level constants for every Custom Property name the addon reads or writes (`PROSCENIO_IS_SLOT`, `PROSCENIO_SLOT_DEFAULT`, `PROSCENIO_SLOT_INDEX`, `PROSCENIO_PRE_PACK`, `PROSCENIO_TYPE`, `PROSCENIO_HFRAMES`, `PROSCENIO_VFRAMES`, `PROSCENIO_FRAME`, etc). Replaces inline `"proscenio_*"` literals.
- [x] `core/props_access.py` — typed accessors `scene_props(context)` and `object_props(obj)` returning `ProscenioSceneProps | None` / `ProscenioObjectProps | None`. Replaces ~12 inline `getattr(scene, "proscenio", None)` repetitions.
- [x] `core/pg_cp_fallback.py` (or absorb into `props_access.py`) — single helper that reads PropertyGroup field first, falls back to Custom Property literal. Replaces three independent implementations in `writer.py` (`_read_proscenio_field`, `_is_slot_empty`, `_read_slot_default`).
- [x] `core/select.py` — bpy-bound helper `select_only(context, obj)`. Replaces 5+ inline copies of the deselect-all-then-select-one idiom. Lives in `core/bpy_helpers/` once D6 lands; in `core/` for this wave with a comment flagging its bpy-bound nature.
- [x] `core/report.py` — `report_info(op, msg)`, `report_warn(op, msg)`, `report_error(op, msg)` that prepend the `"Proscenio: "` prefix and call `op.report({...}, msg)`. Replaces 39 inline copies.
- [x] Tests under `tests/test_cp_keys.py`, `tests/test_props_access.py` — pytest verifies the constants match what the writer expects and the accessors return `None` correctly when PropertyGroup is not registered (existing pattern from `test_properties.py`).

### Wave 9.2 — Operators package split

Convert `operators/__init__.py` (1755 LOC) into a package. The concerns identified in STUDY section 4 each get a module.

- [x] `operators/__init__.py` shrinks to a thin orchestrator: imports submodule packages, calls each submodule's `register()` / `unregister()`. No operator class definitions remain.
- [x] `operators/help_dispatch.py` — `PROSCENIO_OT_status_info`, `PROSCENIO_OT_help`, `PROSCENIO_OT_smoke_test`.
- [x] `operators/export_flow.py` — `PROSCENIO_OT_validate_export`, `PROSCENIO_OT_export_godot`, `PROSCENIO_OT_reexport_godot`, private helpers `_populate_validation_results`, `_run_writer`, `_gate_on_validation`.
- [x] `operators/selection.py` — `PROSCENIO_OT_select_issue_object`, `PROSCENIO_OT_select_outliner_object`, `PROSCENIO_OT_toggle_outliner_favorite`. Uses `core/select.py`.
- [x] `operators/authoring_camera.py` — `PROSCENIO_OT_create_ortho_camera`. Standalone enough for its own module.
- [x] `operators/authoring_ik.py` — `PROSCENIO_OT_toggle_ik_chain`.
- [x] `operators/uv_authoring.py` — `PROSCENIO_OT_reproject_sprite_uv`, `PROSCENIO_OT_snap_region_to_uv`.
- [x] `operators/atlas_pack/` — package because it has size + helpers:
  - [x] `operators/atlas_pack/__init__.py` — re-exports.
  - [x] `operators/atlas_pack/pack.py` — `PROSCENIO_OT_pack_atlas`.
  - [x] `operators/atlas_pack/apply.py` — `PROSCENIO_OT_apply_packed_atlas`.
  - [x] `operators/atlas_pack/unpack.py` — `PROSCENIO_OT_unpack_atlas`.
  - [x] `operators/atlas_pack/_paths.py` — shared `_packed_atlas_paths`, snapshot helpers, the `_PRE_PACK_CP_KEY` usage (now via `core/cp_keys.py`).
- [x] `operators/driver.py` — `PROSCENIO_OT_create_driver`, `_ensure_single_driver`.
- [x] `operators/slot/` — package:
  - [x] `operators/slot/__init__.py` — re-exports.
  - [x] `operators/slot/create.py` — `PROSCENIO_OT_create_slot`.
  - [x] `operators/slot/attachment.py` — `PROSCENIO_OT_add_slot_attachment`, `PROSCENIO_OT_set_slot_default`, `_slot_bone_target`.
  - [x] `operators/slot/preview_shader.py` — `PROSCENIO_OT_setup_sprite_frame_preview`, `PROSCENIO_OT_remove_sprite_frame_preview`.
- [x] `operators/pose_library.py` — `PROSCENIO_OT_save_pose_asset`, `PROSCENIO_OT_bake_current_pose`, `_default_pose_asset_name`.
- [x] `operators/quick_armature.py` — `PROSCENIO_OT_quick_armature`, `_mouse_event_to_z0_point`. The pure mouse projection extracted into `core/viewport_math.py` for pytest coverage; the operator becomes a thin shell.
- [x] `operators/import_photoshop.py` stays where it is (already a single-operator file).
- [x] Each submodule has its own `register()` / `unregister()` calling its `_classes` tuple (per Blender community convention, STUDY section 16).

### Wave 9.3 — Panels package split

Convert `panels/__init__.py` (1002 LOC) into a package. Subpanel clusters from STUDY section 5 each get a module; cross-panel helpers land in `_helpers.py`.

- [x] `panels/__init__.py` shrinks to orchestrator + `PROSCENIO_PT_main` (the root banner panel is small and shared).
- [x] `panels/_helpers.py` — `_draw_subpanel_header`, `_OBJECT_FRIENDLY_MODES`, `_POSE_FRIENDLY_MODES`, idname constants. Module-private but shared across the panel package.
- [x] `panels/active_sprite.py` — `PROSCENIO_PT_active_sprite` plus its 19 helpers (`_draw_sprite_frame_readout`, `_draw_region_box`, `_draw_active_sprite_body`, `_draw_polygon_body`, `_draw_preview_shader_buttons`, `_draw_weight_paint_brush`, `_draw_driver_shortcut`, `_discover_atlas_size_for`, `_first_tex_image_size`, `_material_has_slicer`).
- [x] `panels/active_slot.py` — `PROSCENIO_PT_active_slot`, `_attachment_kind_for`, `_attachment_icon_for`.
- [x] `panels/skeleton.py` — `PROSCENIO_PT_skeleton`, `PROSCENIO_UL_bones`.
- [x] `panels/outliner.py` — `PROSCENIO_PT_outliner`, `PROSCENIO_UL_sprite_outliner`, `_outliner_category_rank`.
- [x] `panels/animation.py` — `PROSCENIO_PT_animation`, `PROSCENIO_UL_actions`.
- [x] `panels/atlas.py` — `PROSCENIO_PT_atlas`, `_draw_packer_box` and its supporting helpers.
- [x] `panels/validation.py` — `PROSCENIO_PT_validation`.
- [x] `panels/export.py` — `PROSCENIO_PT_export`.
- [x] `panels/help.py` — `PROSCENIO_PT_help`.
- [x] `panels/diagnostics.py` — `PROSCENIO_PT_diagnostics`.
- [x] Drop the duplicated `_scene_has_pre_pack_snapshot` (operator-side copy survives as the single source; panel imports it via `from ..operators.atlas_pack._paths import scene_has_pre_pack`).

### Wave 9.4 — Writer package split

Convert `exporters/godot/writer.py` (869 LOC) into `exporters/godot/writer/` package per STUDY section 7.

- [x] `exporters/godot/writer/__init__.py` — exposes the public `export(filepath, *, pixels_per_unit)` entry. Internally orchestrates the section emitters in order.
- [x] `exporters/godot/writer/scene_discovery.py` — `_find_armature`, `_find_sprite_meshes`, `_find_atlas_image`, `_doc_name`. bpy-bound.
- [x] `exporters/godot/writer/skeleton.py` — `_compute_bone_world_godot`, `_build_skeleton`, `_world_to_godot_xy`, `_godot_world_angle_from_dir`, `_wrap_pi`. Most of the math is bpy-free except the `bpy.types.Bone` walker; isolate the math under `core/coords.py` for tests.
- [x] `exporters/godot/writer/sprites.py` — `_build_sprite`, `_build_sprite_frame`, weights pipeline (`_resolve_known_groups`, `_vertex_bone_weights`, `_build_sprite_weights`, `_resolve_sprite_bone`, `_read_proscenio_field`).
- [x] `exporters/godot/writer/slots.py` — `_build_slots`, `_is_slot_empty`, `_read_slot_default`. Both fallback predicates now go through `core/pg_cp_fallback.py`.
- [x] `exporters/godot/writer/slot_animations.py` — `_build_slot_animations`, `_build_slot_attachment_track`, `_merge_slot_animations_into`.
- [x] `exporters/godot/writer/animations.py` — `_build_animations`, `_action_fcurves`, `_collect_bone_keys`, `_build_animation`, `_build_bone_track`, `_resolve_pose_entry`, `_quat_to_screen_angle`, `_parse_bone_data_path`, absolute helpers (`_absolute_position`, `_absolute_rotation`, `_absolute_scale`).
- [x] `exporters/godot/writer/_schema.py` — `BoneDict`, `RestLocal`, `SpriteFrameDict`, `WeightDict` TypedDicts. Lives next to the writer that emits the shape; SPEC 008 may promote to a top-level schema-typed module.
- [x] Existing tests targeting writer paths run against `exporters.godot.writer` — the package `__init__.py` re-exports the public entry, so tests stay unchanged.

### Wave 9.5 — Validation subpackage

Convert `core/validation.py` (361 LOC) into `core/validation/` per STUDY section 6.

- [x] `core/validation/__init__.py` — re-exports `Issue`, `validate_active_sprite`, `validate_active_slot`, `validate_export`. Existing tests continue to import from `core.validation`.
- [x] `core/validation/issue.py` — `Issue` dataclass.
- [x] `core/validation/active_sprite.py` — `validate_active_sprite` + sprite-specific private helpers.
- [x] `core/validation/active_slot.py` — `validate_active_slot` + slot-specific private helpers (`_check_slot_default`, `_check_slot_child_bones`, `_check_slot_child_transform_keys`, etc).
- [x] `core/validation/export.py` — `validate_export` + atlas walkers (`_validate_atlas_files`, `_iter_object_atlas_images`, etc).
- [x] `core/validation/_shared.py` — `_read_sprite_type`, `_read_int`, `_armature_bone_names`, `_abspath_or_none`. Functions consumed by multiple validators.

### Wave 9.6 — bpy-free vs bpy-bound clarification

Per STUDY section 6, the "bpy-free `core/`" claim has drifted. Clean it up.

- [x] `core/__init__.py` docstring updated: state which submodules are bpy-free and which are bpy-bound rather than claiming the whole package is bpy-free.
- [x] Move `core/atlas_io.py`, `core/psd_spritesheet.py`, `core/sprite_frame_shader.py` into `core/bpy_helpers/`. The package keeps its API (re-export from `bpy_helpers/__init__.py`).
- [x] Existing imports update to the new path. Pytest tests that import these are limited (`test_sprite_frame_shader.py` already patches bpy via `SimpleNamespace`).
- [x] If preferred (alternative under D6), keep them in `core/` but add file-level docstring banner stating the bpy dependency.

### Wave 9.7 — Properties module hygiene

`properties/__init__.py` is 493 LOC, less acute than operators / panels but still mixed-concern (3 PropertyGroups + dynamic enum items handler + 4 hydration handlers).

- [x] `properties/__init__.py` becomes orchestrator + the three PropertyGroup classes (which must register before anything else, so colocation is justified).
- [x] `properties/_handlers.py` — `_on_blend_load`, `_on_blend_save_pre`, `_deferred_hydrate`, `_hydrate_existing_objects`. The `@bpy.app.handlers.persistent` decorators stay with the handler definitions.
- [x] `properties/_dynamic_items.py` — `_driver_bone_items`, `_DRIVER_BONE_ITEMS_CACHE`, `_NO_ARMATURE_ITEMS`, `_NO_BONES_ITEMS`. Isolates the EnumProperty-callable GC workaround.

### Wave 9.8 — Dispatch + content registries audit

`core/help_topics.py` (539 LOC) and `core/feature_status.py` (142 LOC) are content registries. Big but cohesive.

- [x] No structural change to `feature_status.py` — the dispatch table is one source of truth and is small enough.
- [x] `core/help_topics.py` — option to keep as one file (preferred — the table is hard to read split across 13 files) but split off the `HelpTopic` / `HelpSection` dataclasses + the `topic_for` / `known_topic_ids` API into `core/help_topics/_api.py` if contributors find the file daunting. Defer the split until the table grows past ~25 entries.

### Wave 9.9 — Public API + import contract

After the splits, codify the import contract so future contributors don't reintroduce drift.

- [x] `.ai/conventions.md` gets a "Module organization" section listing the rules: package per concern, `__init__.py` orchestrates, submodules carry their own `register()`/`unregister()`, cross-cutting helpers in `_helpers.py` or `core/`, bpy-bound modules confined to `core/bpy_helpers/`.
- [x] CI ruff config gains a `lint.per-file-ignores` entry that flags excessive top-level definitions per file (manual rule of thumb, not enforced — track as a comment in the convention).
- [x] `.ai/skills/blender-addon-dev.md` "Project layout" section updated to reflect the new tree (operators package, panels package, writer package, core subpackages).

## Out of scope

- GDScript plugin (`godot-plugin/addons/proscenio/`) — already factored per STUDY section 20.
- Photoshop JSX (`photoshop-exporter/`) — language constraint, see STUDY section 21.
- Behavior changes, bug fixes, new features. Strictly structure-only.
- Renaming public symbols. The bl_idname strings, class names, and test-imported function names stay byte-identical.
- Performance work. Lazy-import patterns are preserved as-is.
- Removing `# type: ignore` comments. The 26 / 38 / 3 / 2 ignores identified in STUDY section 13 stay where they are; eliminating them would require typed-bpy-stub adoption which is out of scope.

## Open questions to resolve before kicking off

The decisions above lock the high-level shape. These remain open:

- Q1 — Sub-package depth: `operators/atlas_pack/__init__.py` plus three submodules vs a flat `operators/atlas_pack.py` of ~250 LOC. STUDY suggests the package; revisit when actually splitting if the surface is small enough.
- Q2 — Where `core/select.py` lives in Wave 9.6: does it move to `core/bpy_helpers/select.py` along with the other bpy-bound modules, or stay in `core/` because every operator imports it? Lean toward `bpy_helpers/` for consistency.
- Q3 — Whether to ship Waves 9.1–9.9 as nine PRs, three groups (helpers, splits, hygiene), or one stack. Lean toward three groups: helpers (9.1) first, splits (9.2/9.3/9.4/9.5/9.7) second, hygiene (9.6/9.8/9.9) third.
- Q4 — Whether `_classes` tuples should remain per-module, or whether Blender's `bpy.utils.register_classes_factory` (auto-discovers classes via `__subclasses__`) is preferred. Existing addon uses the explicit tuple; keep it for predictability.
- Q5 — Whether to introduce `pyproject.toml` ruff rules that warn on files exceeding a LOC threshold. Lean against — ruff doesn't ship this rule, and other linters that do (e.g. radon, mccabe) add tooling weight without large payoff.
