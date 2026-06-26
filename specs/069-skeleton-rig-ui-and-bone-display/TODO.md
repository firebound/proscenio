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

- [x] `core/bpy_helpers/_shared/bone_collections.py`: `iter_collection_bones` prefers `BoneCollection.bones_recursive` (fallback `bones`) so a parent collection resolves its 4.1+ nested children's bones - fixes "collection '<parent>' has no bones" on color / select / shape.
- [x] `bone_collections.py`: `collection_theme_label(armature, name)` - the shared `THEME##` number when the collection's bones agree on one slot, else `""`.
- [x] `panels/skeleton.py` Rig UI rows are three parts (user-specified 2026-06-26): fixed eye (`_RIG_UI_EYE_UNITS`) | flexible middle that the select button(s) split equally | fixed theme selector. Eye + theme selector are built only from non-stretching widgets so they match on every row, independent of the middle.
- [x] `panels/skeleton.py` `_draw_swatch` / `_theme_bone_color_set`: theme selector = three same-width slots so themed/no-theme rows align - a dot (a fixed `template_node_socket` in the theme color when themed; an invisible non-breaking-space spacer when not, NOT a transparent socket, which still draws its outline as a redundant second circle), a number label (the `THEME##` number, or a ` ` spacer - an empty `""` collapses since `ui_units_x` is only a minimum), and ONE picker operator icon (`COLOR`) on every row (no separate `RADIOBUT_OFF` for no-theme - user asked for a single icon). NEVER a `prop(color)` field: it stretches and expands the whole selector. (`split` and a one-row tree were tried and rejected.)
- [x] `interaction-mockup.html`: Rig UI section redone to the agreed three-part row (fixed eye | equal-split select buttons | fixed theme selector with color chip + number, or a dim empty marker), so the design is settled visually before the Blender translation.
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

## Gates

- [x] ruff, mypy, repo-root pytest, in-Blender operator tests, goldens (per the Blender gate set).
