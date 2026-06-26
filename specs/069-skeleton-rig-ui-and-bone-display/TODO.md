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

- [x] `apps/blender/core/bpy_helpers/bone_widgets.py`: `ensure_bone_widget(shape)` builds a 2D wire `WGT-proscenio-<shape>` mesh object (circle / square / diamond / line / triangle / arrow), `use_fake_user`, deduped by name, unlinked from any scene.
- [x] `proscenio.assign_bone_shape` - shape + scope (active / selected / collection) + scale + offset, sets `custom_shape` on the target pose bones.
- [x] `proscenio.color_bone_collection` - palette enum (+ custom triplet), applies `bone.color` to every bone in a collection. `invoke_props_dialog`.
- [x] register the new module in `operators/armature/__init__.py`.

## Panels (`panels/skeleton.py`)

- [x] `PROSCENIO_UL_bones.draw_item`: connectivity icons (`LINKED` / `UNLINKED` via `bone_flag_info`), relative toggle (`CON_CHILDOF` via `toggle_bone_relative_parent`), depth indent from `bone_depth` zeroed under A-Z, favorite star column.
- [x] `PROSCENIO_UL_bones.filter_items`: `compute_list_filter` with `bone_sort_key` + favorites visibility hook (keep the per-pass IK scan refresh).
- [x] `PROSCENIO_PT_armature.draw`: `display_type` row (E) + "Favorites" header toggle (C).
- [x] `PROSCENIO_PT_rig_ui` (D): collection rows, nested = labelled child-button row, eye = `is_visible`, button = `select_bone_collection`, color swatch = `color_bone_collection`.
- [x] `PROSCENIO_PT_bone_display` (F): scope segmented + shape grid + scale/offset + Assign.
- [x] register the two new panels.

## Wiring

- [x] `core/_shared/feature_status.py`: `rig_ui`, `bone_display` entries.
- [x] `core/help_topics.py`: `rig_ui`, `bone_display` topics.

## Gates

- [x] ruff, mypy, repo-root pytest, in-Blender operator tests, goldens (per the Blender gate set).
