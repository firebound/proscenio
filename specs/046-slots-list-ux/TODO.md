# Spec 046: Slots list and attachment UX - TODO

Sequenced from the assessment in [STUDY.md](STUDY.md): five rows land now across four PR-sized chunks, one (the synced-collection attachment backing) gates on a written trigger. Sequence after spec 043's identity-based index fix lands, or share its corrected `_sync_active_index` - the slot list inherits the F-06 filter-reorder bug the moment it has a slot-only filter.

## Now

### PR 1 - the reusable native-list component (structural keystone)

Deferred, not built. The two near-term `template_list` consumers (the migrated slot list and the Outliner) share only the eight-line `template_list` call; their `draw_item` bodies differ entirely (slot name + child count vs the category-ranked label, favorite star, and now the multi-select marker), so a wrapper would abstract the one line they have in common and fork on everything that matters. The repo's no-premature-abstraction rule wants a real second consumer first. The identity-based, filter-aware index sync the component was meant to carry already exists as `source_index_for_name` in [`outliner_view.py`](../../apps/blender/core/outliner_view.py) (the bpy-free helper both the slot list and the Outliner select operators route through) and is unit-tested there, so the F-06 class of bug is already pinned without the wrapper. Trigger to build the wrapper: spec 044's Weight Paint override list lands as the genuine third consumer and wants the same shape.

- [x] ~~Add a list wrapper to `_helpers.py`~~ - deferred (see above); the shared index logic lives in `outliner_view.source_index_for_name` instead.
- [x] Active-index sync is identity-based and filter-aware via `source_index_for_name`, mapping through the UIList's `flt_neworder`; the slot list and Outliner select operators both use it.
- [x] Selection mode (single vs multi) shipped as a capability of the Outliner select operator itself (Shift extends, Ctrl toggles, per-row marker reads `obj.select_get()`), not on a wrapper - see the Outliner multi-select follow-up PR below.
- [x] Headless tests for the index mapping live with `source_index_for_name` and the slot/outliner select operators.

### PR 2 - migrate the project slot list (done)

- [x] Added an `active_slot_index` `IntProperty(min=0)` to [`scene_props.py`](../../apps/blender/properties/scene_props.py) alongside `active_outliner_index` / `active_bone_index` / `active_action_index`.
- [x] Added `PROSCENIO_UL_slots` ([`slots.py`](../../apps/blender/panels/slots.py)) whose `filter_items` keeps only slot Empties in the view layer, name-filtered, sorted by name.
- [x] Replaced the hand-rolled slot loop with `template_list("PROSCENIO_UL_slots", ...)` bound to `bpy.data, "objects"` + `active_slot_index`, keeping the child-count readout per row (left-aligned name via split).
- [x] Routed `proscenio.select_slot` ([`operators/slot/select.py`](../../apps/blender/operators/slot/select.py)) through `source_index_for_name` so clicking a row and selecting in the viewport stay in agreement.

### PR 3 - migrate the attachment list + drop the duplicate warning (done)

- [x] Moved the per-child attachment rows into a boxed custom-draw column with a `scale_y` cap (option 2 backing - the derived `empty.children` view, no synced collection). The cap bounds growth rate; it is not a native scrollbar (that is the gated synced-collection upgrade). Every affordance preserved: the `set_slot_default` `SOLO_ON`/`SOLO_OFF` toggle, the name, the kind label/icon, and the `keyframe_slot_attachment` button.
- [x] Removed the redundant inline empty-slot INFO line; the validator's `slot '...' has no MESH children` error ([`core/validation/active_slot.py`](../../apps/blender/core/validation/active_slot.py)), drawn by the panel's issue loop, carries the message with the correct severity.
- [x] The validator early-returns on the no-children case; `test_slot_with_no_children_emits_error` in [`tests/test_slot_validation.py`](../../tests/test_slot_validation.py) asserts exactly one surfaced message.

### PR 4 - attach-to-existing-slot mesh picker (done)

- [x] Added `proscenio.attach_mesh_to_slot` ([`operators/slot/attachment.py`](../../apps/blender/operators/slot/attachment.py)) - mesh-only; opens `invoke_props_dialog` with a `prop_search` over scene objects and re-parents the picked mesh into the active slot via `parent_keep_world`.
- [x] Kept `proscenio.add_slot_attachment` as the already-selected fast path; both surface in the Active Slot panel ("Attach Mesh" + "Add Selected").
- [x] Headless test [`test_attach_mesh_to_slot.py`](../../apps/blender/tests/operators/test_attach_mesh_to_slot.py): the picker attaches a named mesh with the slot active and nothing else selected.

### Outliner multi-select (follow-up PR, off main)

The Shift-select request the spec routed through the component's selection mode, shipped on the Outliner directly since the wrapper was deferred:

- [ ] `proscenio.select_outliner_object` reads the click event in `invoke`: Shift extends the selection, Ctrl toggles the clicked object, a plain click replaces (today's behavior).
- [ ] A per-row selection marker in `draw_item` reads `obj.select_get()` so multi-selected rows read back (the `template_list` active highlight only marks one row).
- [ ] Headless tests for the extend / toggle / replace selection paths.

## Gated

- **Synced `CollectionProperty` attachment backing (option 1)** - replace the custom-draw attachment list with a real `proscenio.attachments` collection on the slot Empty, rebuilt from `empty.children` via a `depsgraph_update_post` handler (never in `draw`), to gain a native scrollbar, a native name filter, and a persisted active row. Trigger: the attachment list needs a stored active row, native filtering, or drag-reorder that the derived view cannot serve, OR the custom-draw list demonstrably desyncs in practice. Design note: it adds a second index space that must stay in agreement with the swap-keyframe index in `attachment.py` (line 142) and survive re-parents, deletes, and undo.

## Verification

- [ ] GUI smoke pass over `BL-SLOTS-*`: list search, row selection highlight (with a filter active), attachment scroll bound, the mesh picker, and the default/keyframe toggles.
- [ ] Selection + undo checks on each migrated list (the highlight follows viewport selection; undo of an attach/re-parent does not strand the highlight or the list).
- [ ] Confirm spec 044's override list can adopt the PR 1 component unchanged (its named dependency).
