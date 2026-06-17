# Spec 046: Slots list and attachment UX - TODO

Sequenced from the assessment in [STUDY.md](STUDY.md): five rows land now across four PR-sized chunks, one (the synced-collection attachment backing) gates on a written trigger. Sequence after spec 043's identity-based index fix lands, or share its corrected `_sync_active_index` — the slot list inherits the F-06 filter-reorder bug the moment it has a slot-only filter.

## Now

### PR 1 - the reusable native-list component (structural keystone)

- [ ] Add a list wrapper to [`_helpers.py`](../../apps/blender/panels/_helpers.py) next to the existing affordance drawers: a collection-backed mode (thin `template_list` wrapper taking `dataptr`/`propname`/active-index, matching the Outliner / Skeleton / Animation shape) and a custom-draw mode for sequence-backed lists (a bounded, scroll-capped `column` over a Python sequence, so the attachment list and spec 044's override list can adopt it).
- [ ] Make the active-index sync **identity-based and filter-aware**: map the scene-prop index through the UIList's `flt_neworder` so the highlight lands on the right row under a filter/sort, fixing the spec 043 / F-06 bug once instead of per panel. Coordinate with [`_sync_active_index`](../../apps/blender/operators/selection.py) (lines 153-167) — share the corrected version, do not fork it.
- [ ] Add a **selection mode (single vs multi)** to the wrapper (backlog `list-multiselect`): single is the default; multi honors Shift/Ctrl on the row-click operator and keeps a per-item selected state with a custom per-row marker (since `template_list` shows only one active row). Decided adopters — multi: Outliner (objects, via `obj.select_set`), Skeleton (bones, via `bone.select`), Weight Paint overrides (batch mode-set); single: Animation, the slot list, slot default attachment. This is where the Outliner Shift-select request lands.
- [ ] Headless tests for the index mapping (raw-collection index in, filtered display index out) so the F-06 class of bug is pinned for every adopter.

### PR 2 - migrate the project slot list

- [ ] Add an `active_slot_index` `IntProperty(min=0)` to [`scene_props.py`](../../apps/blender/properties/scene_props.py) alongside `active_outliner_index` / `active_bone_index` / `active_action_index`.
- [ ] Add a `PROSCENIO_UL_slots` UIList whose `filter_items` keeps only slot Empties (a strict subset of the Outliner's `filter_items` at [`outliner.py`](../../apps/blender/panels/outliner.py) lines 86-124) and honors a name filter.
- [ ] Replace the hand-rolled slot loop in [`slots.py`](../../apps/blender/panels/slots.py) (lines 117-128) with the PR 1 collection-backed wrapper bound to `scene.objects` + `active_slot_index`, keeping the child-count readout per row.
- [ ] Route `proscenio.select_slot` ([`operators/slot/select.py`](../../apps/blender/operators/slot/select.py)) through the corrected identity-based sync so clicking a row and selecting in the viewport stay in agreement.

### PR 3 - migrate the attachment list + drop the duplicate warning

- [ ] Move the per-child attachment rows in [`slots.py`](../../apps/blender/panels/slots.py) (lines 186-205) into the PR 1 custom-draw mode (option 2 backing — the derived `empty.children` view, no synced collection), with a bounded scroll height so the list stops growing the panel unboundedly. Preserve every affordance: the `set_slot_default` `SOLO_ON`/`SOLO_OFF` toggle, the name, the kind label/icon, and the `keyframe_slot_attachment` button.
- [ ] Remove the redundant inline empty-slot INFO line (`slots.py` lines 180-183); the validator's `slot '...' has no MESH children` error ([`core/validation/active_slot.py`](../../apps/blender/core/validation/active_slot.py) lines 28-29), already drawn by the issue loop at `slots.py` lines 215-216, carries the message with the correct severity.
- [ ] Confirm the validator still early-returns on the no-children case so nothing else regresses; assert in a headless test that an empty slot yields exactly one surfaced message.

### PR 4 - attach-to-existing-slot mesh picker

- [ ] Add a mesh-picker operator (mesh-only — the bone half is already shipped via `proscenio.bind_slot_to_bone` in [`operators/slot/bind.py`](../../apps/blender/operators/slot/bind.py) and is out of scope) that opens an `invoke_props_dialog` with a `prop_search` over scene meshes, mirroring the Bind to Bone dialog (`bind.py` lines 75-81), and re-parents the picked mesh into the active slot via `parent_keep_world`.
- [ ] Keep `proscenio.add_slot_attachment` ([`operators/slot/attachment.py`](../../apps/blender/operators/slot/attachment.py) lines 40-67) as the already-selected fast path; surface both in the Active Slot panel.
- [ ] Headless test: the picker attaches a named mesh with the slot active and nothing else selected (the single-selection deadlock the picker exists to break).

## Gated

- **Synced `CollectionProperty` attachment backing (option 1)** - replace the custom-draw attachment list with a real `proscenio.attachments` collection on the slot Empty, rebuilt from `empty.children` via a `depsgraph_update_post` handler (never in `draw`), to gain a native scrollbar, a native name filter, and a persisted active row. Trigger: the attachment list needs a stored active row, native filtering, or drag-reorder that the derived view cannot serve, OR the custom-draw list demonstrably desyncs in practice. Design note: it adds a second index space that must stay in agreement with the swap-keyframe index in `attachment.py` (line 142) and survive re-parents, deletes, and undo.

## Verification

- [ ] GUI smoke pass over `BL-SLOTS-*`: list search, row selection highlight (with a filter active), attachment scroll bound, the mesh picker, and the default/keyframe toggles.
- [ ] Selection + undo checks on each migrated list (the highlight follows viewport selection; undo of an attach/re-parent does not strand the highlight or the list).
- [ ] Confirm spec 044's override list can adopt the PR 1 component unchanged (its named dependency).
