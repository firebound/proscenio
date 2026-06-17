# Spec 044: Weight Paint mode sync and bind parameters - TODO

Sequenced from the assessment in [STUDY.md](STUDY.md): four rows land now (implemented in one PR - the mode-sync unit and the panel/operator additions were cohesive and small enough not to split), one gates on spec 046's reusable list component, one defers as a spec-sized follow-on. Carry the honest limit everywhere: the provenance overlay refreshes at **stroke end**, not live during a stroke - the modal brackets a native brush operator and has no per-sample hook.

## Now (implemented - one PR; PR3 stays gated on spec 046)

### Mode-sync unit (external-exit + stroke-end refresh + button label)

Shipped together - all three turn on `obj.mode` and route exit through the single `_finish` path. Headless caveat: the Blender test harness cannot pump a modal end to end (proven by the existing `test_edit_weights_modal.py` comments), so the TIMER tick, the stroke-end redraw, and the button label are GUI-smoke; the headless anchor is the overlay-flag-restore contract `_finish` depends on.

- [x] `event_timer_add` poll added in `invoke` ([`edit_weights.py`](../../apps/blender/operators/skinning/edit_weights.py), `_MODE_WATCH_INTERVAL = 0.2`); `modal()` `TIMER` branch calls `self._finish(context, cancel=False)` when `active.mode != "WEIGHT_PAINT"` - the only legal context for its `mode_set`/`undo_push`. Timer removed in `_finish`. No depsgraph handler involved.
- [x] Stroke-end redraw now tags all VIEW_3D areas via `_tag_redraw_view3d` (wraps `tag_redraw_areas`) on the RELEASE, `WINDOW_DEACTIVATE`, and zero-pressure `MOUSEMOVE` flip paths - fixes "white only after re-entering the mode" (a single `context.area.tag_redraw()` tagged only the release area).
- [x] Entry button in [`weight_paint.py`](../../apps/blender/panels/weight_paint.py) `_draw_edit_weights` reads "Exit Painting Mode" when `obj.mode == "WEIGHT_PAINT"` and routes the click through `object.mode_set` (Object) so the modal's TIMER poll runs `_finish` - one exit path.
- [x] Headless anchor: `test_restore_returns_overlay_flag_to_prior` locks that `restore_session` returns `show_provenance_overlay` to its captured value. GUI smoke: `BL-WPAINT-EDIT-01/02/03`, `BL-WPAINT-SWEEP` (all marked `todo`).

### Proximity params panel draw + clear-empty-vgroups

- [x] `bind_max_distance` + `bind_falloff_power` now draw in `_draw_bind` guarded by `bind_mode == "PROXIMITY"` (data path was already wired - layout only). Closes the `BL-WPAINT-SWEEP` note.
- [x] New `proscenio.clear_empty_vertex_groups` operator ([`clear_empty_vgroups.py`](../../apps/blender/operators/skinning/clear_empty_vgroups.py)): `empty_vertex_group_names` collects groups with no weight > 0 in one vert pass; `invoke_props_dialog` lists the names with the "empty = safe to drop" note; `execute` removes them. Polls for a mesh with groups. Surfaced as a Bind-subpanel button.
- [x] Headless tests (`test_clear_empty_vgroups.py`): removes only the empty group (weighted survives), cancels when none empty, poll requires groups. (The panel-shape Proximity test is GUI-smoke - this codebase does not render panels headlessly.)

## Gated

- **Override-list scroll** - gate: spec 046's reusable list component merges first (046's scope names this list as an adopter; do not hand-roll a second `UIList`). Then migrate `_draw_bone_overrides` ([`weight_paint.py`](../../apps/blender/panels/weight_paint.py):193-243) onto the shared component, preserving the per-row Soft/Hard depress state and the Clear-enable predicate; verify against `BL-WPAINT-BIND-02`. Interim fallback only if 046 slips: a collapsible "active overrides only" view (draw bones already carrying an override via `read_bone_modes`, plus a count) to bound the height without a new widget.

## Deferred

- **Named weight snapshots** - a new save-point data structure (multiple named snapshots with an explicit "return to before / after paint" target) plus its file I/O; spec-sized, not a row here. The current single "Reset to Last Saved Weights" stays. Revisit if the snapshot confusion is still reported after the mode-sync fix lands (the live-vs-after-paint ambiguity is partly a symptom of the overlay not tracking the mode, which PR 1 addresses).
