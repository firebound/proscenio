# Spec 069 TODO: Skeleton Rig UI and bone display

Implementation plan for the eight LOCKED decisions in [STUDY.md](STUDY.md). Order is dependency-first: the bpy-free sort module and the shared collection helper land before the operators and panels that consume them.

## B - Bone-list sort (hierarchy / flat-alpha)

- [x] `apps/blender/core/bone_view.py` (bpy-free): `bone_depth(bone)` and `bone_sort_key(bone, *, sort_alpha)` - ancestor-name chain off (depth-first, parent before children), single name bucket on (flat). Mirrors `core/outliner_view.py`.
- [x] `tests/test_bone_view.py` (repo-root, pure pytest): depth, hierarchy order, flat-alpha order.

## Decision 8 - shared collection-iteration helper

- [x] `apps/blender/core/bpy_helpers/_shared/bone_collections.py`: `iter_collection_bones(armature, collection_name)` over `data.collections_all` (nested reachable by name), missing/empty guarded.

## C - Per-bone favorite

- [x] `apps/blender/properties/bone_props.py`: `ProscenioBoneProps` with `is_favorite`.
- [x] `properties/__init__.py`: register + `Bone.proscenio = PointerProperty(...)`.
- [x] `properties/scene_props.py`: `skeleton_show_favorites` BoolProperty.

## A / C / D - bone-row + collection operators (`operators/selection.py`)

- [x] `proscenio.bone_flag_info` - no-op, dynamic `description` per flag (connected / disconnected tooltips). INTERNAL.
- [x] `proscenio.toggle_bone_relative_parent` - flips `bone.use_relative_parent`, REGISTER/UNDO.
- [x] `proscenio.toggle_bone_favorite` - flips `bone.proscenio.is_favorite`.
- [x] `proscenio.select_bone_collection` - selects every bone of a collection (replace semantics), via `iter_collection_bones` + `bone_select_only`/`add`.

## F / G - appearance operators (`operators/armature/bone_appearance.py` new)

- [~] ~~`apps/blender/core/bpy_helpers/bone_widgets.py`: `ensure_bone_widget(shape)`~~ **DROPPED 2026-06-26** - file deleted (custom shapes can't orient across a 2D rig's bone rolls; see STUDY decision 7).
- [~] ~~`proscenio.assign_bone_shape`~~ **DROPPED 2026-06-26** - operator + the Bone Display subpanel removed.
- [x] `proscenio.color_bone_collection` - palette enum (+ custom triplet), applies `bone.color` to every bone in a collection. `invoke_props_dialog`.
- [x] register the new module in `operators/armature/__init__.py`.

## Panels (`panels/skeleton.py`)

- [x] `PROSCENIO_UL_bones.draw_item`: connectivity icons (`LINKED` / `UNLINKED` via `bone_flag_info`), relative toggle (`CON_CHILDOF` via `toggle_bone_relative_parent`), depth indent from `bone_depth` zeroed under A-Z, favorite star column.
- [x] `PROSCENIO_UL_bones.filter_items`: `compute_list_filter` with `bone_sort_key` + favorites visibility hook (keep the per-pass IK scan refresh).
- [x] `PROSCENIO_PT_armature.draw`: `display_type` row (E) + "Favorites" header toggle (C).
- [x] `PROSCENIO_PT_rig_ui` (D): collection rows, nested = labelled child-button row, eye = `is_visible`, button = `select_bone_collection`, color swatch = `color_bone_collection`.
- [~] ~~`PROSCENIO_PT_bone_display` (F)~~ **DROPPED 2026-06-26** - subpanel removed with the custom-shape feature.
- [x] register the new panel (Rig UI).

## Wiring

- [x] `core/_shared/feature_status.py`: `rig_ui` entry (the `bone_display` entry was removed with the dropped feature).
- [x] `core/help_topics.py`: `rig_ui` topic (the `bone_display` topic + anchor were removed with the dropped feature).

## Follow-up (2026-06-26) - nested-collection fix + theme read-out

- [x] `core/bpy_helpers/_shared/bone_collections.py`: `iter_collection_bones` prefers `BoneCollection.bones_recursive` (fallback `bones`) so a parent collection resolves its 4.1+ nested children's bones - fixes "collection '<parent>' has no bones" on color / select.
- [x] `bone_collections.py`: `collection_theme_label(armature, name)` - the shared `THEME##` number when the collection's bones agree on one slot, else `""`.
- [x] `panels/skeleton.py` Rig UI rows are three parts (user-specified 2026-06-26): fixed eye (`_RIG_UI_EYE_UNITS`) | flexible middle that the select button(s) split equally | fixed theme selector. Eye + theme selector are built only from non-stretching widgets so they match on every row, independent of the middle.
- [x] `panels/skeleton.py` `_draw_swatch` / `_theme_bone_color_set`: theme selector = three same-width slots so themed/no-theme rows align - a dot (a fixed `template_node_socket` in the theme color when themed; an invisible non-breaking-space spacer when not, NOT a transparent socket, which still draws its outline as a redundant second circle), a number label (the `THEME##` number, or a ` ` spacer - an empty `""` collapses since `ui_units_x` is only a minimum), and ONE picker operator icon (`COLOR`) on every row (no separate `RADIOBUT_OFF` for no-theme - user asked for a single icon). NEVER a `prop(color)` field: it stretches and expands the whole selector. (`split` and a one-row tree were tried and rejected.)
- [x] `interaction-mockup.html`: Rig UI section redone to the agreed three-part row (fixed eye | equal-split select buttons | fixed theme selector = colored dot + theme number + one picker icon, blank when no theme), and the dropped Bone Display section removed. Design settled visually before the Blender translation.
- [x] `tests/operators/test_bone_display_ops.py`: nested-collection color reaches child bones.
- [~] Custom-shape widgets (`bone_widgets.py`, `assign_bone_shape`, Bone Display subpanel) **DROPPED 2026-06-26**. A first fix re-oriented the outlines from the bone-local X-Z plane to Y-Z (so an arrow followed the bone instead of stabbing into the screen), but the deeper problem is unfixable without invasive roll work: a `custom_shape` is anchored in bone-local space, so flat 2D widgets only orient correctly when every bone's roll is consistent - a real rig's are not, so it only looked right on the bone pointing right. Removed in favor of the native `display_type` dropdown (E). See STUDY decision 7.

## H / Decision 9 - per-bone export exclusion

- [x] `apps/blender/core/bone_export.py` (bpy-free): `bone_is_exported(bone)` = `use_deform AND NOT proscenio.exclude_from_export`, `getattr`-defaulted.
- [x] `tests/test_bone_export.py` (repo-root, pure pytest): deform/non-deform, flagged, missing-PG degrade.
- [x] `properties/bone_props.py`: `exclude_from_export: BoolProperty` on `ProscenioBoneProps`.
- [x] `exporters/godot/writer/skeleton.py` + `writer/__init__.py`: route the skip, `_nearest_deform_ancestor`, and the `deform_bones` set through `bone_is_exported`.
- [x] `operators/selection.py`: `proscenio.toggle_bone_export` (armature + bone), flips the flag, REGISTER/UNDO.
- [x] `panels/skeleton.py` `_draw_bone_flags`: per-bone export toggle reading the combined gate, depressed when excluded. Icon is `EXPORT` (exported) / `CANCEL` (excluded) - render/visibility icons are avoided since this is the Godot export, not the viewport.
- [x] `operators/driver.py` `create_driver`: auto-set `exclude_from_export` on the Drive-from-Bone source bone.
- [x] `tests/operators/`: headless toggle test, driver auto-mark test, and a flagged-deform-bone export-leak test.

## Follow-up (2026-06-27) - Rig UI nested recursion + empty-state + button fill

- [x] `core/rig_ui_view.py` (bpy-free): `rig_ui_rows(top_collections)` -> `list[RigUIRow]`, flattening the collection tree depth-first pre-order. A branch is a header row whose buttons are its direct children, then each branch child recurses into its own header row; a top-level leaf is a single headerless self-button row. Mirrors `core/bone_view.py`.
- [x] `tests/test_rig_ui_view.py` (repo-root, pure pytest): leaf row, branch row, branch-child recursion, deep nesting depth-first, top-level order, empty input.
- [x] `panels/skeleton.py` `PROSCENIO_PT_rig_ui`: `draw` consumes `rig_ui_rows` through one uniform `_draw_row` (header + eye | buttons | theme) at every depth; `_draw_eye` resolves the row's collection by name (placeholder when the data dropped it). Was the un-recursed 2-level draw that lost levels 3+.
- [x] Empty-state: `poll` now returns true whenever a rig is picked (not only with collections); `draw` shows `icon="INFO"` notice "no bone collections - add them in Blender's Bone Collections panel" instead of the panel vanishing - matches the IK-chains / Pose-mode empty-state convention.
- [x] Button-fill (Bug 1): theme selector pinned to `_RIG_UI_THEME_UNITS` total width so themed and no-theme rows reserve the same selector width and the middle buttons always split the same remaining width. Root cause was the unpinned selector growing on themed rows (the `template_node_socket` dot is wider than the no-theme spacer). NOTE: needs visual confirmation in Blender - layout widths are not measurable headless.
- [x] `tests/operators/test_bone_display_ops.py`: `rig_ui_rows` integration on real 3-level `BoneCollection` nesting (validates the `.children` recursion on live data).
- [x] One color control per tree: `RigUIRow.is_top_level` flags rows from a top-level collection; only those have a live picker, which colors the whole subtree (`color_bone_collection` + `collection_theme_label` stay recursive). (Supersedes a brief direct-only-color attempt - a bone shared across nested collections still read as "propagating", so the deliberate single color point at the top is the clean model.) Tests: subtree color, subtree theme label, `is_top_level` flagging (headless + on real collections).
- [x] Column alignment (recurring bug): the theme selector's three columns (dot/number/picker) are drawn on EVERY row, top-level and nested, with identical widgets so the columns line up and the middle buttons end at the same x. `ui_units_x` is a *minimum* not a cap, so the prior "pin the selector width" did nothing - a themed `template_node_socket` dot was wider than a no-theme nbsp label. Fix: dot is ALWAYS a socket (theme color or `_RIG_UI_NO_THEME_DOT` empty circle), number always a label, picker always the operator (live `COLOR` on top-level, disabled `BLANK1` reserved on nested). Verified headlessly only - the actual alignment needs the user's eyes in Blender.
- [x] `interaction-mockup.html` Rig UI render rewritten to the nested tree + recursion (theme selector on every row, picker top-level only, subtree re-tint); docstring + `help_topics.py` + `STUDY.md` + `docs/.../04-skeleton.md` Rig UI section updated.

## Follow-up (2026-06-27) - Active Armature row cleanup + Quick Armature UX

- [x] Bone-list row (`PROSCENIO_UL_bones.draw_item` + `_draw_bone_flags`): left/right split by interactivity. The row's left icon is now connectivity (`_bone_connectivity_icon`: `LINKED` / `UNLINKED` / `BONE_DATA` root) in place of the redundant `BONE_DATA` type icon (every row is a bone); the right side is interactive only - the no-op connectivity info icon is removed from there.
- [x] Removed the now-orphan `proscenio.bone_flag_info` operator + `_BONE_FLAG_TOOLTIPS` from `operators/selection.py` (and its registration). Connectivity reads from the left icon; the click-less tooltip carrier is dead weight (per-flag hover text dropped, acceptable).
- [x] Relative-parenting toggle keeps the flat `emboss=False` style of its neighbors but swaps the icon by state (was a single `CON_CHILDOF` whose flat depress was invisible): filled `PINNED` on / hollow `UNPINNED` off (same filled/hollow read as the favorite star). (An embossed variant and an `ORIENTATION_PARENT`/`GLOBAL` pair were tried and rejected. Icon pair GUI-tunable.)
- [x] `operators/armature/quick_armature.py` `_handle_reparent_pick`: a successful pick drops straight back to Draw mode (the Tab landing) and clears the pick highlight, so the next drag chains onto the picked parent; a miss stays in Reparent. Tests updated: hit returns to Draw, miss stays in Reparent.
- [x] `panels/skeleton.py` `PROSCENIO_PT_quick_armature.draw`: while the modal runs (`_statusbar_appended`), the panel mirrors the live chord cheatsheet via `emit_chord_layout` (the same status-bar/header renderer, swaps per Draw/Reparent), echoing the automesh interactive modal-indicator pattern. Drawn in a native collapsible `layout.panel(default_closed=True)` section so it stays out of the way until expanded.
- [x] Chord spacing: two fixes. (1) Rewrote the armature status-bar vocabulary (`operators/armature/_status_bar.py`) from the split `(icon, "")` + `("", text)` form to the automesh "attached" `(icon, text)` form - one label per gesture, meaning on the key icon, the `+` / `/` joiner carried as a modifier's text. (2) The `chord` primitive (`operators/_status_bar.py`): a keycap icon (`EVENT_CTRL` etc.) butts straight against its label text (reads as a run-together "Ctrl"+"grid snap"). Fixed by giving each non-empty text a leading space (labels keep leading spaces - the bone list indents the same way) AND forcing `row.alignment = "LEFT"` - the real "huge gap" cause was the default `EXPAND` alignment splitting the row width equally between the labels, pushing a combo's meaning to the panel's right edge (neither `align=True` nor `align=False` changes that; alignment does). Fixes both the panel cheatsheet and the status bar (shared `emit_chord_layout` + `chord`); also tidies the automesh status bar.
- [x] Exit button: while a session runs, the panel button reads "Exit Quick Armature" (icon `X`) instead of "Quick Armature"; a re-invoke sets `_exit_requested` and the running modal finishes on its next event (instead of restarting). Test: `_exit_requested` makes `modal` finish (cancelled for an empty session) and clears the flag.
- [x] Quick Armature panel cheatsheet wrapped in a collapsible `layout.panel(default_closed=True)` section (closed by default).
- [x] Docs: `STUDY.md` (LOCKED A + B follow-ups), `docs/.../04-skeleton.md` (Active Armature + Quick Armature), `interaction-mockup.html` bone-list row updated.

## Follow-up (2026-06-27) - Quick Armature runs in Edit Mode

- [x] The modal now runs the whole session in EDIT on the target armature instead of toggling EDIT->OBJECT per bone. `invoke` captures the entry mode (`_restore_mode`) and enters edit once; `_create_bone` / `_undo_last_bone` / `_redo_last_bone` operate on `edit_bones` directly via the idempotent `_enter_armature_edit` (no per-bone round trip, no object-selection juggling); the fresh bone is set as the active edit bone. `_exit` commits to OBJECT (for counting / sweep / selection restore) then returns the user to `_restore_mode`.
- [x] Right-click no longer exits (`_is_exit_event` is Esc-only); it passes through so edit-mode bone selection works (the user's ask). Esc / Enter still finish (shown on the cheatsheet).
- [x] Live reads made Edit-aware (data.bones is stale mid-session): `_world_tail_tips` (reparent pick) and the connect-snap press point go through `_live_bone_tails`; `_seed_chain_parent_from_active` reads `edit_bones.active` in edit.
- [x] Tests: `_bones(arm)` reads the live collection (edit_bones in edit); the fixture resets to Object mode per run; the probe rewraps the new statics (`_enter_armature_edit`, `_live_bone_tails`) with `staticmethod`. All quick-armature modal tests green (16).

## Follow-up (2026-06-27) - Quick Armature reparent = native selection, no Tab, no tail-pick

- [x] Dropped the Draw/Reparent sub-mode + Tab switch AND the whole tail-tip pick subsystem: removed `_mode`, `_switch_mode`, `_modal_reparent`, `_handle_reparent_mousemove`, `_is_mode_switch_event`, `_handle_reparent_pick`, `_select_edit_bone`, `_resolve_pick_at_cursor`, `_world_tail_tips`, `_pick_radius_world`, `_pick_target_name`, `_PICK_RADIUS_PX`, the `Mode`/`next_mode`/`resolve_pick`/`region_event_to_xz*` imports, the overlay `_draw_reparent_tips` + `_REPARENT_*` constants, and `next_mode`/`Mode` from `quick_armature_math` (+ their math test).
- [x] Reparent is now native selection: right-click passes through (Blender selects the bone), and `_modal_draw`'s `RIGHTMOUSE` branch is gone. At each LMB press `_sync_chain_parent_to_active` adopts the armature's active edit bone as the chain parent (`_last_bone_name`), so a connected draw starts from whatever is selected; nothing active leaves the last-authored bone as the parent. `_live_bone_tails` stays for the connect-snap.
- [x] Status bar / panel cheatsheet: single set + `RMB select bone = chain from it`. `bl_description` updated.
- [x] Tests: removed `test_switch_mode_*`, `test_world_tail_tips_*`, `test_reparent_pick_*`; added `test_sync_chain_parent_*` (adopts the active edit bone; no-op without one). 12 quick-armature tests green.

## Gates

- [x] Original spec-069 implementation: ruff, mypy, repo-root pytest, in-Blender operator tests, goldens.
- [x] **Re-gate the 2026-06-26 follow-ups** (export exclusion, Rig UI theme selector, custom-shape removal): ruff, mypy, repo-root pytest, in-Blender operator tests (240) + goldens (8/8) all green locally.
- [x] 2026-06-27 Rig UI nesting follow-up: ruff, mypy, repo-root pytest (881), in-Blender operator tests (241) + goldens (8/8) all green. Bug-1 button-fill still pending the user's visual check in Blender.
- [x] 2026-06-27 Active Armature row + Quick Armature UX follow-up: ruff, mypy, repo-root pytest (882), in-Blender operator tests (242) + goldens (8/8) all green. Connectivity-left-icon, embossed relative toggle, and the Quick Armature panel cheatsheet still want the user's visual check in Blender.
