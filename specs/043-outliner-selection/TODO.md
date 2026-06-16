# Spec 043: Outliner selection correctness - TODO

Sequenced from the assessment in [STUDY.md](STUDY.md): 5 rows land now across three PR-sized chunks, one defers. PR 1 (the crash) is shippable on its own and does not touch `draw_item`, so it can land ahead of spec 036's row-layout work.

## Now

### PR 1 - stale-row crash guard (shippable alone)

- [ ] In [`PROSCENIO_OT_select_outliner_object.execute`](../../apps/blender/operators/selection.py) (lines 53-59), guard against a row whose object is not in the current view layer: pre-check `self.obj_name in context.view_layer.objects` (or equivalent) and `report_warn` + return `CANCELLED` instead of letting `select_only` raise. Do **not** suppress inside `select_only` ([`core/bpy_helpers/_shared/select.py:23-35`](../../apps/blender/core/bpy_helpers/_shared/select.py)) - it is shared with `select_issue_object`, `select_bone_by_name`, the slot/camera operators, and a blanket suppress there silently changes their contract.
- [ ] Headless test: a `bpy.data.objects` row pointing at an object absent from the view layer warns and cancels rather than raising `RuntimeError: ... not in View Layer`; the existing in-view-layer click path still selects.

### PR 2 - correct highlight + follow viewport selection (verified together)

- [ ] **First, reproduce the unknown:** confirm in a running Blender which index space `template_list.active_index` lives in - source-collection index (`bpy.data.objects` order) or displayed slot (`flt_neworder`). The fix below differs materially between the two; do not code until this is settled. (Finding F-06; [`outliner.py:120-124`](../../apps/blender/panels/outliner.py), [`selection.py:153-167`](../../apps/blender/operators/selection.py).)
- [ ] Factor the identity -> active-index mapping into a shared helper that runs the same hide/filter/sort logic as [`filter_items`](../../apps/blender/panels/outliner.py) (lines 86-124): skip matches that are filtered out (`flt_flags[i] == 0`), and when a name is ambiguous across data-blocks prefer the object actually in the view layer. Place it where spec 046's reusable list component can import it.
- [ ] Rewrite `_sync_active_index` ([`selection.py:153-167`](../../apps/blender/operators/selection.py)) - or its `active_outliner_index` call site at `selection.py:58` - to use that helper so a click highlights the row the user actually clicked under any filter/sort.
- [ ] Extend the existing `on_depsgraph_update` handler ([`properties/_handlers.py:69-100`](../../apps/blender/properties/_handlers.py)) to map `scene.view_layer.objects.active` through the same helper and write `active_outliner_index` **only when it changed**. Early-out when the active object is unchanged or is a non-Proscenio (`_outliner_category_rank == 9`) row. Reuse the handler's existing `except Exception` guard and `_tag_view3d_areas_redraw`. Do not add a second handler/registration - it is already wired at [`properties/__init__.py:83-84`](../../apps/blender/properties/__init__.py).
- [ ] Measure the added cost on a large scene (the callback fires on every transform/frame change) and confirm no write-during-draw warning.
- [ ] Headless tests for the identity mapping (filtered-out skip, ambiguous-name view-layer preference, sort-reordered list) and a GUI smoke pass over `BL-OUTLN-06` (highlight follows click) plus a new manual check that viewport selection moves the highlight.

### PR 3 - single search field + favorites cleanup

- [ ] Remove the Proscenio search drawer: drop the `row.prop(scene_props, "outliner_filter", ...)` draw at [`outliner.py:148`](../../apps/blender/panels/outliner.py) **and** stop honoring `outliner_filter` in `filter_items` (collapse the `flt_text` logic at `outliner.py:95-99` to just the native `self.filter_name`). Leave the `outliner_filter` field defined-but-unused in [`scene_props.py:468-475`](../../apps/blender/properties/scene_props.py) unless a wider prop sweep removes it (removing a registered prop affects saved files). Coordinate this `outliner.py` edit with spec 036's row-layout work. (Finding F-04.)
- [ ] Favorites ordering: either add favorite-ness as the primary sort key in `filter_items` (`outliner.py:120`) so the "pins to the top" copy becomes true, **or** correct the description ([`object_props.py:253`](../../apps/blender/properties/object_props.py)) and the `BL-OUTLN-08` checklist copy to "favorites survive the favorites-only filter." Pick one. (Finding F-01, low severity.)
- [ ] Headless test for the favorites sort (if the sort-key route is taken); GUI smoke over `BL-OUTLN-01` (filter by typing), `BL-OUTLN-04` (native filter now the only one), `BL-OUTLN-08` (star behavior).

## Deferred

- **List source: `scene.objects` vs `bpy.data.objects`** - sourcing the list from `scene.objects`/`view_layer.objects` would eliminate the stale-row crash by construction (only selectable objects ever appear), but it perturbs the `_outliner_category_rank` / `filter_items` / active-index logic the PR 2 fixes depend on. Gate: revisit only after the PR 2 identity fix is stable, and only if the source swap does not disturb the rank/sort/index mapping. The explicit guard in PR 1 is the safe minimum and ships regardless.

## Cross-spec coordination

- **Spec 036** left-aligns the same `draw_item` rows ([`outliner.py:70-84`](../../apps/blender/panels/outliner.py)). PR 1 is operator-only and does not collide; sequence PR 3's `outliner.py` drawer edit with 036's row edit so they do not fight.
- **Spec 046** builds the reusable list component and needs the identity-based active-index fix (its STUDY records a prior Skeleton-panel selection-sync cost). The shared helper from PR 2 is the artifact 046 must import rather than re-derive - keep it importable from a shared module.
