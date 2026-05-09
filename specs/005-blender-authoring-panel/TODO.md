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

## SPEC 005.1.c.1 — region authoring (shipped)

Wave 5.1.c was split: this PR ships region authoring (UI + override + snap operator). The atlas packer ships separately as 5.1.c.2.

- [x] `ProscenioObjectProps.region_mode` (`auto`/`manual` enum) + `region_x/y/w/h` FloatProperty.
- [x] Writer respects `region_mode == "manual"` via `core/region.py` (extracted for testability). Auto path = current behavior (UV bounds for polygon, omitted for sprite_frame). Manual path emits `region_x/y/w/h` verbatim.
- [x] Active Sprite panel renders a "Texture region" box: read-only hint in auto mode, four floats + `Snap to UV bounds` button in manual mode.
- [x] `PROSCENIO_OT_snap_region_to_uv` — copies the active mesh's UV bounds into the manual region floats (seeds manual mode with current auto value).
- [x] `tests/test_region.py` — 7 pytest assertions covering auto bounds / manual override / Custom Property fallback / `manual_region_or_none` gate.

## Post-005.1.c.1 fix bundle (shipped)

Manual testing (2026-05-05) surfaced four bugs and three UX gaps. All fixed in one branch (`fix/spec-005-bug-fixes-and-polish`) since they share the same root cause (mirror semantics).

### Bugs

- [x] CP set partial after first edit — only the touched field's update callback fired, leaving other CPs absent. Fix: every callback now delegates to `core/mirror.py::mirror_all_fields` which writes the full 10-field map.
- [x] Reload Scripts → PropertyGroup defaults — partial CPs left rehydration with nothing to restore. Fix: mirror-all keeps CPs complete; hydrate's `OBJECT_PROPS` map extended with the 5 region keys.
- [x] `.blend` save with programmatic edits → partial CPs persisted. Fix: `@bpy.app.handlers.persistent save_pre` handler flushes PG → CP for every object before save.
- [x] CP edited directly → PG out-of-date until reload. Documented as expected behavior — editing CPs is power-user only; PG is canonical, CP is read-only mirror. STUDY.md captures the rationale.

### UX gaps

- [x] Skeleton subpanel showed only bone count. Now ships `PROSCENIO_UL_bones` UIList rendering name + parent + length per row.
- [x] F3 search "proscenio" returned nothing. Every operator's `bl_label` now starts with `Proscenio:`. Panel button labels override `text=` to keep the short version.
- [x] sprite_frame mesh in PAINT_WEIGHT mode silently showed nothing useful. Now an info hint explains "weight paint not applicable to sprite_frame (Sprite2D is not deformed by bones)".
- [x] sprite_frame region size opaque. Active Sprite panel now reads the linked image's pixel dimensions and renders `atlas: WxH px / region: WxH px / frame: WxH px (HxV grid)` so the user can verify the spritesheet grid lines up.
- [x] `tests/test_mirror.py` — 5 pytest assertions covering mirror-all field set / missing-attribute skip / caster-error skip / mirror+hydrate round trip / OBJECT_PROPS region key coverage. Total now 30 (validation 12 + properties 6 + region 7 + mirror 5).

## SPEC 005.1.c.2 — atlas packer (shipped)

- [x] `core/atlas_packer.py` — vendored MaxRects-BSSF, bpy-free, ~200 LOC. Tries doubling sizes from `start_size` up to `max_size`; padding around each placement. POT mode rounds up to nearest power of 2.
- [x] `core/atlas_io.py` — bpy-side helpers: `collect_source_images` walks meshes for image-textured materials; `compose_atlas` builds a `bpy.types.Image` via numpy (bundled with Blender) and saves PNG; `write_manifest` / `read_manifest` for the JSON sidecar.
- [x] `PROSCENIO_OT_pack_atlas` — non-destructive. Walks scene meshes, collects sources, runs MaxRects, writes `<blend>.atlas.png` + `<blend>.atlas.json`. Does **not** touch UVs or materials. Requires saved `.blend`.
- [x] `PROSCENIO_OT_apply_packed_atlas` — destructive but undoable. Reads manifest, rewrites UVs to address packed atlas coordinates, links each sprite to a shared `Proscenio.PackedAtlas` material (or swaps just the image when `material_isolated=True`).
- [x] `ProscenioSceneProps` gains `pack_padding_px` (default 2, max 64), `pack_max_size` (default 4096, max 8192), `pack_pot` (default off). All exposed in the Atlas subpanel.
- [x] `ProscenioObjectProps` gains `material_isolated: BoolProperty` (default False). Marked sprites keep their own material on apply, only the image node swaps to the packed atlas.
- [x] Atlas subpanel renders a "Atlas packer" box: padding/max_size/POT props, Pack button always available, Apply button visible when `<blend>.atlas.json` exists next to the file.
- [x] `tests/test_atlas_packer.py` — 8 pytest assertions covering empty input / single rect / non-overlap / inside bounds / atlas growth / max_size cap / POT rounding / padding separation.

## SPEC 005.1.c.2.1 — sliced atlas support (shipped)

Manual validation of 5.1.c.2 on the dummy fixture exposed that sprites whose source image is a shared atlas (the head spritesheet sits inside `atlas.png` alongside torso/legs) repacked the entire shared image into each slot, leaving the actual sprite area in the wrong place. Sprite_frame meshes ended up sampling transparent regions because their `hframes/vframes` slice was applied to the full packed atlas, not to the head's sub-region.

- [x] `core/uv_bounds.py` — bpy-free helpers: `uv_bbox_to_pixels` (UV bounds → source-pixel rect with optional padding) + `remap_uv_into_slot` (single UV → packed-atlas UV).
- [x] `atlas_io.SourceImage` gains `slice_px: tuple[int, int, int, int]`. `collect_source_images` walks the mesh's UV layer and computes the slice via `uv_bbox_to_pixels`.
- [x] `compose_atlas` extracts the slice sub-region from the source image and pastes it into the packed slot (instead of copying the full source image).
- [x] Manifest format bumped to v2 — adds `source_w/h` + `slice_x/y/w/h` per placement. v1 manifests still load (slice defaults to slot for backward compat).
- [x] `apply_packed_atlas` per-sprite-kind dispatch:
  - polygon: rewrites UVs through the slice → slot transform so the original sprite area inside the source maps cleanly into the slot.
  - sprite_frame: sets `region_mode = "manual"` + `region_x/y/w/h` to the slot in atlas-normalized coords, so Sprite2D's `hframes/vframes` slice the correct sub-rect.
- [x] `tests/test_uv_bounds.py` — 8 pytest assertions covering empty UVs (full image fallback) / full-cover UVs / partial slice / expand padding / clamp to image edges / remap with full slice / remap with partial slice / remap far corner.

## SPEC 005.1.c.2.2 — Unpack operator (shipped)

Closes the "non-destructive across session boundaries" gap. Apply was already idempotent and Ctrl+Z-undoable, but a saved + reopened `.blend` lost the original UVs and material reference.

- [x] `PROSCENIO_OT_apply_packed_atlas` snapshots the pre-Apply state into a Custom Property (`proscenio_pre_pack`) before mutating each mesh: original material name, original image node name, full `region_mode` + `region_x/y/w/h`. Plus duplicates the active UV layer to `<name>.pre_pack`. Snapshot is **idempotent** — second apply on an already-packed sprite leaves the existing snapshot alone (so Unpack still reverts to original-original).
- [x] `PROSCENIO_OT_unpack_atlas` reads the snapshot, copies the saved UVs back into the active layer, removes the `.pre_pack` layer, restores the material reference and the region fields, then deletes the Custom Property.
- [x] Atlas subpanel renders the Unpack button only when at least one mesh in the scene carries a snapshot (`_scene_has_pre_pack_snapshot`).
- [x] Cycle survives `.blend` save/reload: snapshot CP is stored on the Object datablock, persists with the file. Unpack reads from the saved CP and restores cleanly.

## SPEC 005.1.d — advanced authoring wave (in flight)

Closes the polish gap left after 5.1.a/b/c shipped. Sub-divided per feature so each lands as its own focused PR. Some items in the original defer list are already shipped via earlier waves (`PROSCENIO_OT_toggle_ik_chain`, `PROSCENIO_OT_bake_current_pose`, `PROSCENIO_OT_create_ortho_camera`, `PROSCENIO_OT_reproject_sprite_uv`) and are not repeated here.

### 5.1.d.1 — Driver constraint shortcut (in flight)

Branch: `feat/spec-005.1.d.1-driver-shortcut`. Smallest authoring shortcut for the driver-driven texture-swap pattern (forearm rotation flips front/back forearm sprite). Wraps Blender's native `driver_add` + a `TRANSFORMS` driver variable so the user does not hand-author the scripted-driver shape every time.

- [x] `ProscenioObjectProps` gains five driver fields: `driver_target` (Enum: `frame`/`region_x`/`region_y`/`region_w`/`region_h`), `driver_source_armature` (PointerProperty filtered to ARMATURE objects), `driver_source_bone` (StringProperty backed by `prop_search` against the picked armature), `driver_source_axis` (Enum: ROT/LOC × X/Y/Z), `driver_expression` (StringProperty, default `var`). Authoring-only — no CP mirror needed.
- [x] Active Sprite subpanel renders a "Drive from bone" box with the five pickers + the action button. No mode-switching required: the user picks armature + bone via `prop_search` directly in the sidebar regardless of Object / Pose / Edit mode. Button stays disabled until both armature and bone are picked.
- [x] `PROSCENIO_OT_create_driver` operator. Reads picker state from `Object.proscenio.driver_*` on `invoke`, re-mirrors the redo overrides back to the PG on `execute` so the panel reflects the latest choice. Idempotent: re-running on the same `(sprite, target_property)` pair removes the existing driver before adding the fresh one — no duplicate FCurves.
- [x] Operator redo panel exposes `target_property` + `source_axis` + `expression` + `armature_name` + `bone_name` for in-place tweaking via F9.
- [x] Manual smoke test: `examples/doll/doll.blend`, picked `forearm.L` mesh + `doll.rig` armature + `forearm.L` bone in the panel, clicked Drive from Bone, driver appeared in the Drivers Editor on `forearm.L.proscenio.region_x` with `var` expression and TRANSFORMS variable pointing at `doll.rig:forearm.L.ROT_Z`.

### 5.1.d.2 — Pose library shim (planned)

Branch: `feat/spec-005.1.d.2-pose-library`. Surface "Save current pose to Asset Browser" button. Tiny shim over Blender native pose library -- Blender already does the heavy lifting (`POSELIB_OT_create_pose_asset`).

- [ ] `PROSCENIO_OT_save_pose_asset` operator: bundles armature's current pose + active action keyframes into a pose asset under the Asset Browser. Inputs: pose name (defaults to action name + frame). Wraps the native operator with sensible defaults pulled from the active scene.
- [ ] Skeleton subpanel button "Save Pose to Library" (pose-mode only, surfaces beside Bake Current Pose / Toggle IK).
- [ ] `core/feature_status.py` adds `pose_library` row (BLENDER_ONLY).
- [ ] `core/help_topics.py` adds `pose_library` topic (what it does, how Blender's Asset Browser consumes it, why this is a no-op at .proscenio export time).
- [ ] Manual smoke test: enter pose mode on `doll.rig`, set a pose, click Save Pose -- pose appears in Asset Browser.

### 5.1.d.3 — Quick armature (click-drag bone draw, shipped)

Branch: `feat/spec-005.1.d.3-quick-armature`. COA Tools' rapid skeleton-creation operator. Modal viewport tool for click-drag bone authoring without entering Edit Mode. Lower-priority -- Blender's Edit Mode + Shift+E (extrude) covers the core use case but loses the rapid-iteration flow when sketching new rigs.

- [x] `PROSCENIO_OT_quick_armature` modal operator: invoke captures mouse, click-drag draws a bone from press point to release point, auto-parents to previous bone in the chain when Shift held. Esc / right-click to exit modal. Bones land flat on world z=0 (2D pipeline). Each release internally toggles the QuickRig in/out of Edit Mode so the user never sees the mode switch.
- [x] Skeleton subpanel button "Quick Armature" (always available, creates `Proscenio.QuickRig` on first use, extends it on subsequent runs).
- [x] `core/feature_status.py` adds `quick_armature` row (BLENDER_ONLY).
- [x] `core/help_topics.py` adds `quick_armature` topic with the click-drag flow + Shift-modifier behavior.
- [ ] Manual smoke test: empty scene -> Quick Armature -> draw 5 bones in chain -> verify hierarchy in outliner. *(Modal -- only exercisable interactively, no headless equivalent.)*

### 5.1.d.4 — Spriteobject custom outliner (shipped)

Branch: `feat/spec-005.1.d.4-outliner`. `UIList` that lists sprite_objects + armatures + bones in a sprite-centric hierarchical browser with search + filter. Replaces / supplements Blender's native outliner for big rigs (doll fixture has 64 bones + 22 sprite meshes -- finding "brow.L mesh" requires scroll + expand + filter every time).

- [x] `PROSCENIO_UL_sprite_outliner` `bpy.types.UIList`: feeds `bpy.data.objects`; `filter_items` hides non-Proscenio rows + applies the substring filter + the favorites toggle, then sorts by category (slots first with `[slot]` prefix, attachments indented with `↳`, sprite meshes second, armatures last with `[arm]` prefix). Text filter is live -- no enter required.
- [x] New top-level subpanel `PROSCENIO_PT_outliner` (sibling of Skeleton, between Skeleton + Animation). Hosts a one-row toolbar (filter input + favorites toggle) + the UIList.
- [x] `ProscenioSceneProps` gains `outliner_filter: StringProperty` + `outliner_show_favorites: BoolProperty` + `active_outliner_index: IntProperty`. `ProscenioObjectProps` gains `is_outliner_favorite: BoolProperty`.
- [x] Click row → `PROSCENIO_OT_select_outliner_object` (decoupled from `select_issue_object` so the tooltip does not lie about validation context).
- [x] Click SOLO icon next to a row → `PROSCENIO_OT_toggle_outliner_favorite` flips `is_outliner_favorite`.
- [x] `core/feature_status.py` adds `outliner` row (BLENDER_ONLY).
- [x] `core/help_topics.py` adds `outliner` topic with What/How/Layout/Where sections.
- [ ] Manual smoke test: doll fixture -> outliner -> filter "brow" -> click row -> active object becomes brow.L. Click SOLO on brow.L -> toggle 'Favorites only' -> verify only brow.L survives. *(Manual; no headless equivalent for UIList draw.)*

### 5.1.d.5 — Feature-status badges + in-panel help (in flight)

Closes the "what is godot-ready vs blender-only vs planned" discoverability gap surfaced during 5.1.d.1 manual smoke testing. Bundled into the same PR as 5.1.d.1 so the new driver shortcut ships with the badge + help popup that explain what it does.

- [x] `core/feature_status.py` — pure-Python `FeatureStatus` enum (`GODOT_READY`, `BLENDER_ONLY`, `PLANNED`, `OUT_OF_SCOPE`) + `STATUS_BADGES` icon/label/tooltip map + per-feature `FEATURE_STATUS` dispatch table. Unknown ids fall back to `BLENDER_ONLY` so a missing entry surfaces a generic badge instead of crashing the panel draw.
- [x] `core/help_topics.py` — `HelpTopic` dataclass with title + summary + ordered `HelpSection`s + optional `see_also` cross-references. 9 topics shipped: `pipeline_overview`, `active_sprite`, `skeleton`, `animation`, `atlas`, `validation`, `export`, `drive_from_bone`, `import_photoshop`. Plain-text only -- Blender's `UILayout.label` renders one line per call.
- [x] `PROSCENIO_OT_help` operator. `INTERNAL` flag (hidden from the operator search). `invoke()` opens via `wm.invoke_popup` at 480 px width; `draw()` renders title + summary + sections + see-also list.
- [x] `_draw_panel_header` helper renders the standardized `<badge label> <icon> <?>` row at the top of every Proscenio subpanel (Active Sprite, Skeleton, Animation, Atlas, Validation, Export). Pipeline-overview button on the root panel.
- [x] "Drive from bone" box in Active Sprite gains an inline status badge + dedicated help button so the 5.1.d.1 onboarding lands in context.
- [x] `tests/test_feature_status.py` — 7 pytest assertions (badge metadata + dispatch + fallback + subpanel-id coverage + duplicate-key guard).
- [x] `tests/test_help_topics.py` — 8 pytest assertions, including a `see_also` cross-reference check that fails CI if a help topic points at a deleted/renamed `specs/<NNN-slug>/` directory.

## Defer (lower-priority polish — see `RESEARCH.md` matrix)

- Edge-extend padding pixels (currently transparent; may show bleed at bilinear filtering with mip-maps).
- Vertex weight visualization overlay.
- Per-user default export-path preference.
- Localization scaffolding (`i18n_id`).
- Properties Editor placement of the Active sprite section (D1.B alternative).
- "Reset to defaults" button per subpanel.
