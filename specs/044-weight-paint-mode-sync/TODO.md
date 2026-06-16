# Spec 044: Weight Paint mode sync and bind parameters - TODO

Sequenced from the assessment in [STUDY.md](STUDY.md): four rows land now across three PR-sized chunks, one gates on spec 046's reusable list component, one defers as a spec-sized follow-on. Carry the honest limit everywhere: the provenance overlay refreshes at **stroke end**, not live during a stroke - the modal brackets a native brush operator and has no per-sample hook.

## Now

### PR 1 - mode-sync unit (external-exit + stroke-end refresh + button label)

All three turn on `context.active_object.mode` and route exit through the single `_finish` path; ship together so the reads cannot drift.

- [ ] Add an `event_timer_add` poll to [`edit_weights.py`](../../apps/blender/operators/skinning/edit_weights.py): on each `TIMER` tick in `modal()` (~110-131), if `context.active_object.mode != "WEIGHT_PAINT"` call `self._finish(context, cancel=False)` - the only context where `_finish`'s `mode_set` / `undo_push` (~135-136) are legal. Do NOT call `_finish` from a depsgraph handler (restricted context, corrupts the depsgraph). Remove the timer in `_finish` (~133-144) alongside the overlay handle.
- [ ] On stroke end, tag a redraw on all VIEW_3D areas (reuse the `_tag_redraw_view3d` idiom from [`automesh_authoring.py`](../../apps/blender/operators/automesh/automesh_authoring.py):320) instead of the single `context.area.tag_redraw()` at edit_weights.py:119-120, and add the redraw tag to the `WINDOW_DEACTIVATE` (~122-124) and zero-pressure `MOUSEMOVE` (~125-127) flip paths that today flip but never tag. The overlay batch is already rebuilt every draw (`weight_overlay._draw_callback`, ~91-108) - no batch caching to add.
- [ ] Relabel the entry button in [`weight_paint.py`](../../apps/blender/panels/weight_paint.py) `_draw_edit_weights` (~246-280, button at ~265-269): when `obj.mode == "WEIGHT_PAINT"` show "Exit Painting Mode" (different icon); the exit click sets Object mode so the modal's TIMER poll runs `_finish` - one exit path, no duplicated teardown.
- [ ] Headless test: a `TIMER` tick with the active object's mode flipped away from `WEIGHT_PAINT` ends the modal and restores the overlay flag (extend [`test_edit_weights_modal.py`](../../apps/blender/tests/operators/test_edit_weights_modal.py)). GUI smoke: `BL-WPAINT-EDIT-01` (paint stroke marks white at stroke end), `BL-WPAINT-EDIT-02` (Esc + native-control exit both restore), button label flips in/out of mode.

### PR 2 - Proximity params panel draw + clear-empty-vgroups

- [ ] Draw `bind_falloff_power` and `bind_max_distance` in [`weight_paint.py`](../../apps/blender/panels/weight_paint.py) `_draw_bind` (~158-190), guarded by `bind_mode == "PROXIMITY"` (the local is already read at ~172-175). Props, operator (`bind_mesh.py:80-94`), invoke seeding (~106-109), and apply (~138-143) are all already wired - layout only. Closes the `BL-WPAINT-SWEEP` note.
- [ ] Add a clear-empty-vertex-groups operator: collect `obj.vertex_groups` with no weight > 0 (reuse the predicate behind `stroke_diff._read_group_weights`, ~87-95), present an `invoke_confirm`/popup listing the group names to delete, then remove them. Poll for a mesh element. Confirm copy must note the sidecar `vertex_group_names` relationship for bound meshes (empty groups are safe to drop; do not mass-delete base groups blindly). Surface as a Bind- or Snapshot-subpanel button, not a bare shortcut.
- [ ] Headless tests: panel-shape test asserts both params draw only under Proximity; operator test on a fixture with one weighted + one empty group deletes only the empty one and leaves the sidecar entry count intact.

## Gated

- **Override-list scroll** - gate: spec 046's reusable list component merges first (046's scope names this list as an adopter; do not hand-roll a second `UIList`). Then migrate `_draw_bone_overrides` ([`weight_paint.py`](../../apps/blender/panels/weight_paint.py):193-243) onto the shared component, preserving the per-row Soft/Hard depress state and the Clear-enable predicate; verify against `BL-WPAINT-BIND-02`. Interim fallback only if 046 slips: a collapsible "active overrides only" view (draw bones already carrying an override via `read_bone_modes`, plus a count) to bound the height without a new widget.

## Deferred

- **Named weight snapshots** - a new save-point data structure (multiple named snapshots with an explicit "return to before / after paint" target) plus its file I/O; spec-sized, not a row here. The current single "Reset to Last Saved Weights" stays. Revisit if the snapshot confusion is still reported after the mode-sync fix lands (the live-vs-after-paint ambiguity is partly a symptom of the overlay not tracking the mode, which PR 1 addresses).
