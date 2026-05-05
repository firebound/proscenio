# SPEC 005 — TODO

Builds the authoring panel that turns the Blender side of Proscenio from "raw Custom Properties on Objects" into a typed, validating, iteration-friendly UI. See [STUDY.md](STUDY.md) for the design rationale and the eight open questions (D1–D8). Implementation post-mortem realigned the contract so the **PropertyGroup is canonical** and Custom Properties are a legacy read-fallback (`fix(blender): writer reads PropertyGroup first…`).

## Decision lock-in

- [x] D1 — panel lives in the 3D View N-key sidebar (extends `PROSCENIO_PT_main`).
- [x] D2 — `PropertyGroup` is canonical; legacy raw Custom Properties remain readable as a fallback. *(Updated from "wrap" → "canonical with fallback" after the bug where defaults never mirrored.)*
- [x] D3 — inline validation for cheap checks, lazy validation for I/O-bound ones.
- [x] D4 — two severity levels: error (blocks export) and warning (informs).
- [x] D5 — sticky export path stored per-document on `bpy.types.Scene`.
- [x] D6 — Validate button reports through a dedicated panel section, not a toast.
- [x] D7 — no stub Slots subpanel; SPEC 004 ships its own.
- [x] D8 — vertex-group summary inspector lands in 005; atlas region + ortho helpers defer to 005.1.

## Property infrastructure

- [x] `blender-addon/properties/__init__.py` ships `ProscenioObjectProps` (sprite_type EnumProperty + hframes/vframes/frame IntProperty + centered BoolProperty), `ProscenioValidationIssue` (CollectionProperty item), and `ProscenioSceneProps` (last_export_path + pixels_per_unit + validation_results CollectionProperty + validation_ran BoolProperty).
- [x] Property groups registered via `bpy.types.Object.proscenio` and `bpy.types.Scene.proscenio` PointerProperties.
- [x] Hydration deferred via `bpy.app.timers.register(..., first_interval=0.0)` so PointerProperty wiring is stable at write time. `@bpy.app.handlers.persistent` `load_post` handler re-runs hydration after every `.blend` load.
- [x] Hydration core extracted to `blender-addon/core/hydrate.py` so the pytest suite can exercise it without a Blender session.
- [x] `unregister()` removes the load_post handler, drops the PointerProperty attributes, and tolerates partial-register fallout via `contextlib.suppress(RuntimeError)` on `unregister_class`.

## Panel restructure

- [x] `PROSCENIO_PT_main` is now a thin parent banner; child panels do the work via `bl_parent_id`.
- [x] `PROSCENIO_PT_active_sprite` — mesh poll, sprite type dropdown, sprite_frame metadata, polygon vertex-group summary, inline validation.
- [x] `PROSCENIO_PT_skeleton` — bone count, missing-armature warning, multi-armature warning.
- [x] `PROSCENIO_PT_animation` — read-only summary of every Action.
- [x] `PROSCENIO_PT_atlas` — read-only atlas filename discovered from materials.
- [x] `PROSCENIO_PT_validation` — populated by the Validate operator's `CollectionProperty`.
- [x] `PROSCENIO_PT_export` — sticky path field, pixels-per-unit field, Validate / Export / Re-export buttons.
- [x] `PROSCENIO_PT_diagnostics` — current smoke test button moves here.

## Validation

- [x] `blender-addon/core/validation.py` ships `Issue` dataclass and `validate_active_sprite` + `validate_export` entry points.
- [x] `Issue` carries `severity: Literal["error", "warning"]`, `message: str`, optional `obj_name`.
- [x] Active-sprite panel renders inline validation icons next to broken rows.
- [x] `PROSCENIO_OT_validate_export` mirrors results into `scene.proscenio.validation_results` for the panel to render.

## Export flow

- [x] `PROSCENIO_OT_export_godot` gates on `validate_export`; errors abort with `self.report` + the panel surfaces the issue list. Successful export updates `scene.proscenio.last_export_path`.
- [x] `PROSCENIO_OT_reexport_godot` runs silently against the sticky path. Visible in the Export subpanel only when `last_export_path` is non-empty.
- [x] Writer reads PropertyGroup first (`Object.proscenio.<field>`), Custom Property as legacy fallback. Defaults flow through cleanly without requiring user interaction. *(This was the post-mortem fix that resolved the "switching sprite_type only mirrored one Custom Property" bug.)*

## Tests

- [x] `tests/test_validation.py` — 12 pytest assertions covering both `validate_active_sprite` (polygon clean / no polygons warns / sprite_frame happy path / hframes=0 errors / vframes=0 errors / unknown sprite type errors / non-mesh ignored) and `validate_export` (no armature blocks / matching vertex group clean / orphan groups error / parent-bone-only soft / unparented warns).
- [x] `tests/test_properties.py` — 6 pytest assertions covering `hydrate_object` (skips when proscenio is None / copies sprite_type / copies full sprite_frame metadata / leaves defaults when Custom Properties absent / partial overrides / type-error swallow).
- [x] CI's `lint-python` job runs `pytest tests/` after `mypy --strict`.
- [x] Existing `blender-addon/tests/run_tests.py` (Blender-driven writer round-trip) untouched — still passes after the SPEC 005 refactor.

## Documentation

- [x] `.ai/skills/blender-addon-dev.md` rewritten — project layout includes the new `properties/` and `core/`, "Headless tests" section calls out both runners, new "Authoring sprites in the panel (SPEC 005)" subsection walks through every panel section + the round-trip with raw Custom Properties + sticky-path re-export + validation gate.
- [x] `STATUS.md` updated to reflect SPEC 005 shipped (panel, validation, sticky path).
- [x] `README.md` iteration loop step mentions the panel as the recommended authoring path.

## Manual validation

- [x] Reload addon, open `examples/dummy/dummy.blend`. Active sprite panel populates from existing Custom Properties (head shows `sprite_frame`, legs/torso show `polygon`).
- [x] Toggle the head dropdown back to `polygon` and back to `sprite_frame`; writer output reflects the change without needing all 5 Custom Properties to be set manually (PropertyGroup is the source of truth, defaults flow through).
- [x] Set the sticky export path; click Re-export; the file updates without a file dialog.
- [ ] Click Validate with a deliberately broken state (sprite_frame mesh with `hframes = 0`); panel surfaces the issue, Export button reports an error. *(Manual sanity test, run when convenient.)*
- [ ] Open a `.blend` from before SPEC 005; verify the panel reads existing Custom Properties without breaking, edits round-trip cleanly. *(Manual, requires a legacy fixture.)*

## SPEC 005.1.a — panel polish wave (shipped)

- [x] Click-to-select on Issues (`PROSCENIO_OT_select_issue_object` — Validation rows are emboss-less operator buttons that select + activate the offending object).
- [x] Shortcut cheat-sheet panel (`PROSCENIO_PT_help` — static idname/label table for F3 search).
- [x] Bake current pose as keyframe (`PROSCENIO_OT_bake_current_pose` — pose-mode-only, inserts loc/rot/scale on every pose bone at the playhead; rendered inline in the Skeleton subpanel).
- [x] Mode-aware subpanels (`_OBJECT_FRIENDLY_MODES` / `_POSE_FRIENDLY_MODES` — Active Sprite hides outside object/edit-mesh/weight-paint/vertex-paint; Skeleton hides outside object/pose/edit-armature).
- [x] Animation collections list editing (`PROSCENIO_UL_actions` + `template_list` against `bpy.data.actions`; `ProscenioSceneProps.active_action_index` selects the row).

## SPEC 005.1.b — helpers wave (shipped)

- [x] Camera ortho preview (`PROSCENIO_OT_create_ortho_camera` — creates/focuses `Proscenio.PreviewCam` with `ortho_scale = max(resolution_x, resolution_y) / pixels_per_unit`; rendered as a button in the Export subpanel).
- [x] IK chain toggle (`PROSCENIO_OT_toggle_ik_chain` — pose-mode-only; adds/removes a marker-named "Proscenio IK" constraint on the active pose bone, default `chain_count=2`. Hand-added IK constraints are left untouched).
- [x] Reproject sprite UV (`PROSCENIO_OT_reproject_sprite_uv` — Smart UV Project on the active mesh only; saves + restores prior selection/mode/active object so the user lands back where they were).
- [x] Inline weight paint brush controls (`_draw_weight_paint_brush` — when in `PAINT_WEIGHT` mode the polygon summary box is replaced by unified-aware brush size/strength/weight + auto-normalize toggle).
- Driver constraint shortcut deferred to 5.1.d (lowest-value of the wave; Blender's stock driver editor already covers the use case).

## Defer (SPEC 005.1.c/d — see `RESEARCH.md` matrix)

- Atlas region helper (D8 — "Snap UV bounds → texture_region").
- Atlas packer integration (PyTexturePacker dep).
- Pose library shim (Asset Browser).
- Driver constraint shortcut.
- Spriteobject custom outliner with search/filter.
- `region_rect` authoring polish.
- Vertex weight visualization overlay.
- Per-user default export-path preference.
- Localization scaffolding (`i18n_id`).
- Properties Editor placement of the Active sprite section (D1.B alternative).
- "Reset to defaults" button per subpanel.
