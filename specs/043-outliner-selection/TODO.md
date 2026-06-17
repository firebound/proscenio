# Spec 043: Outliner selection correctness - TODO

Assessment in [STUDY.md](STUDY.md): 5 rows land now, one defers. Implemented in a single PR (the three STUDY chunks were small and cohesive; no chunk grew enough to warrant splitting). The favorites question was decided **filter-only** - the star keeps the favorites-only filter and the copy was corrected, no sort-key change.

## Now (implemented)

### Stale-row crash guard

- [x] [`PROSCENIO_OT_select_outliner_object.execute`](../../apps/blender/operators/selection.py) pre-checks `context.view_layer.objects.get(self.obj_name) is None` and `report_warn` + `CANCELLED` before delegating; `select_only` ([`select.py:23-35`](../../apps/blender/core/bpy_helpers/_shared/select.py)) is left untouched so the slot/camera/bone callers keep their raise-when-not-selectable contract.
- [x] Headless test: a `bpy.data.objects` row absent from the view layer warns + cancels instead of raising; the in-view-layer click path still selects. (`test_outliner_selection.py`)

### Correct highlight + follow viewport selection

- [x] **Index-space resolved by the documented contract, not a GUI repro:** `template_list.active_index` is an index into the *source* collection (`bpy.data.objects`); Blender maps it to the visible row via `flt_neworder` internally. So the existing by-name source-index write was already correct in principle; no rewrite of `_sync_active_index` was needed. (The one thing headless cannot prove is the *visual* landing under sort/filter - that stays a manual GUI smoke, `BL-OUTLN-06`.)
- [x] Identity -> source-index mapping factored into [`core/outliner_view.py`](../../apps/blender/core/outliner_view.py) (`source_index_for_name`, `category_rank`, `is_outliner_relevant`), bpy-free, where spec 046's reusable list component can import it. `panels/outliner.py` now imports `category_rank`/`RANK_HIDDEN` from it instead of holding a private copy.
- [x] `on_depsgraph_update` ([`properties/_handlers.py`](../../apps/blender/properties/_handlers.py)) extended via `sync_outliner_to_active_object`: maps the viewport's active object through `source_index_for_name`, writes `active_outliner_index` **only when changed**, early-outs on a non-Proscenio active object (`is_outliner_relevant` / rank 9). Reuses the existing `except Exception` guard + `_tag_view3d_areas_redraw`; no second handler. The armature-pointer hygiene was split into `_clear_dangling_active_armature` so both jobs run per tick.
- [x] Headless tests for `source_index_for_name`, `is_outliner_relevant`, and the follow handler (follows a relevant active object, ignores a camera, no-ops when already correct). (`test_outliner_selection.py`)

### Single search field + favorites copy

- [x] Removed the Proscenio search drawer: dropped the `outliner_filter` `row.prop` draw and stopped honoring `outliner_filter` in `filter_items` (now `flt_text = self.filter_name` only). The `outliner_filter` PG field is left defined-but-unused in [`scene_props.py:468`](../../apps/blender/properties/scene_props.py) (removing a registered prop affects saved files; defer to a wider prop sweep). (Finding F-04.)
- [x] Favorites: **filter-only** decision. Corrected the [`object_props.py`](../../apps/blender/properties/object_props.py) `is_outliner_favorite` description to say favorites keep their category order (do not move to the top); the toggle-operator description and `BL-OUTLN-08` checklist copy already matched. No sort-key change. (Finding F-01.)
- [x] Left-align the row labels (a spec 036 item, folded in here since this PR already restructures `draw_item`): split the row, draw the label in a `LEFT`-aligned sub-row, keep the favorite star in the split remainder. Spec 036's `left-align-names` is marked `done` pointing here. The parent-nested tree with expand/collapse was **dropped** (no native Python tree widget - see [`dropped.md`](../dropped.md)).

## Remaining (manual gates, not blocking the headless suite)

- [ ] GUI smoke: `BL-OUTLN-06` (highlight lands on the correct visual row under filter/sort, and follows a viewport selection), `BL-OUTLN-01`/`BL-OUTLN-04` (native filter is the only search), `BL-OUTLN-08` (star = filter only), and the **left-align** (labels hug the left edge, star stays at the right). `BL-OUTLN-06` is marked `todo` in the checklist pending this pass.
- [ ] Measure the depsgraph-callback cost on a large scene (fires on every transform/frame change) and confirm no write-during-draw warning. The follow path is a guarded comparison that early-outs on the common path, but the on-scene cost is GUI-only to confirm.

## Deferred

- **List source: `scene.objects` vs `bpy.data.objects`** - sourcing the list from `scene.objects`/`view_layer.objects` would eliminate the stale-row crash by construction (only selectable objects ever appear), but it perturbs the `_outliner_category_rank` / `filter_items` / active-index logic the PR 2 fixes depend on. Gate: revisit only after the PR 2 identity fix is stable, and only if the source swap does not disturb the rank/sort/index mapping. The explicit guard in PR 1 is the safe minimum and ships regardless.
  - **Resolved 2026-06-17 the light way (follow-up PR `fix/outliner-hide-stale-rows`):** rather than migrate the source collection, `filter_items` now hides any row whose object is not in the current view layer (a deleted/undone datablock lingers in `bpy.data.objects` but leaves the view layer). The list stays bound to `bpy.data.objects`, so the rank/sort/active-index mapping is untouched; the visibility rule lives in the bpy-free `outliner_view.row_visible` (unit-tested). The PR 1 click-guard stays as defense in depth. The full `scene.objects` source migration is no longer needed for the stale-row symptom.

## Cross-spec coordination

- **Spec 036** left-aligns the same `draw_item` rows ([`outliner.py:70-84`](../../apps/blender/panels/outliner.py)). PR 1 is operator-only and does not collide; sequence PR 3's `outliner.py` drawer edit with 036's row edit so they do not fight.
- **Spec 046** builds the reusable list component and needs the identity-based active-index fix (its STUDY records a prior Skeleton-panel selection-sync cost). The shared helper from PR 2 is the artifact 046 must import rather than re-derive - keep it importable from a shared module.
