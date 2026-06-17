# Spec 045: Skeleton, Quick Armature and Animation fixes - TODO

Sequenced from the assessment in [STUDY.md](STUDY.md): 7 rows land now across two PR-sized chunks plus a repro session that gates one decision; one row stays gated on the repro outcome.

## First - the repro that gates the Esc work

- [ ] Run the BL-SKEL-QUICKARM-01 repro in a GUI session and record the scene state vs the report verb for three cases: (a) bare Esc with nothing drawn, (b) Esc after authoring one bone, (c) Enter after authoring one bone. Confirm against the code read: case (a) sweeps the empty auto-rig on both Esc and Enter; cases (b)/(c) both keep the bones today, so Esc and Enter differ only by the report verb (`_exit`, [`quick_armature.py`](../../apps/blender/operators/armature/quick_armature.py) lines 803-822) and not in the scene.
- [ ] Decide from the repro: labels-only (default - keep current data behaviour, fix the hints) or destructive cancel (Esc discards the whole auto-created `Proscenio.QuickRig` even with bones). Write the decision into the STUDY before coding PR 2.

## Now

### PR 1 - Animation panel uses the picked armature (bug)

- [ ] Rework `PROSCENIO_OT_set_active_action` in [`selection.py`](../../apps/blender/operators/selection.py) (lines 96-132) to resolve the target via `resolve_skeleton_target(context)` from [`core/armature/skeleton_target.py`](../../apps/blender/core/armature/skeleton_target.py) instead of `context.scene.objects` armature scan; `report_warn` and cancel when it returns `None` (message in the Skeleton panel's "no rig picked" vocabulary).
- [ ] Drop the multi-armature heuristic (lines 117-127) - the picker disambiguates - and update the `bl_description` (lines 101-104) that still advertises "the first armature in the scene".
- [ ] Headless test in a new `tests/operators/test_set_active_action.py`: assigns to the picked armature when set; warns + cancels (no assignment) when the picker is empty; ignores a non-picked second armature in the scene.

### PR 2 - Quick Armature + Skeleton chrome (one GUI smoke verifies all)

- [ ] Make the confirm / exit chords differ and change with session state in `emit_chord_layout` ([`_status_bar.py`](../../apps/blender/operators/armature/_status_bar.py) lines 46-47), reusing the existing `_default_chain`-swap pattern (lines 33-38) to read a session-state flag (e.g. `cls._last_bone_name`): relabel Return as "keep" / "finish", and while nothing is drawn let the Esc chord read "cancel (discards empty rig)". (Apply the destructive-cancel branch in [`quick_armature.py`](../../apps/blender/operators/armature/quick_armature.py) `_exit` / `_sweep_empty_armature` only if the repro chose it - keep the `_created_armature_this_session` picked-target guard either way.)
- [ ] Flag "disconnected" child bones in `PROSCENIO_UL_bones.draw_item` ([`skeleton.py`](../../apps/blender/panels/skeleton.py) lines 60-65): append "disconnected" when `item.parent is not None and not getattr(item, "use_connect", False)`.
- [ ] Add a `draw_header` override to `PROSCENIO_PT_skeleton` ([`skeleton.py`](../../apps/blender/panels/skeleton.py) beside `draw_header_preset`, lines 83-84) showing "Skeleton: <name>" from `_explicit_target(context)`; fall back to the plain "Skeleton" label when the picker is empty or the target is gone.
- [ ] Rename `PROSCENIO_PT_armature` `bl_label` from "Armature" to "Active Armature" ([`skeleton.py`](../../apps/blender/panels/skeleton.py) line 126); leave `bl_idname` / `bl_parent_id` untouched; trim the redundant in-body label (line 149) if the header name makes it redundant.
- [ ] Remove the 3D-viewport-header hint surface from [`quick_armature.py`](../../apps/blender/operators/armature/quick_armature.py): the append branch (lines 756-758), the `_view3d_header_appended` ClassVar (line 136) and its double-invoke guard (lines 163-164), the teardown in `_unregister_handlers` (lines 774-777), the sweep in `_sweep_orphan_handlers` (lines 942-945), and `_draw_view3d_header_quick_armature` (lines 904-917). The status bar keeps the same chords via `_draw_statusbar_quick_armature`.
- [ ] One GUI smoke pass over `BL-SKEL-*`, `BL-ANIM-01..03`, and `BL-SKEL-QUICKARM-01`: confirm the dynamic Esc / confirm hints, the disconnected flag, the header name, the renamed subpanel, and that the viewport header no longer shows the chord strip (no leaked handler after a reload).

## Gated

- **Destructive Esc cancel** - Esc deletes the whole auto-created `Proscenio.QuickRig` even when it has bones (never the user-picked target). Real bug surface (a misfired Esc discards a session). Trigger: the repro above showing users expect Esc to throw the rig away; otherwise the labels-only outcome stands.

## Out of scope (own backlog items)

- **qa-rotation-mode** - Euler-Y vs quaternion authoring choice + safe swap; the safe swap can break animations silently, so it carries its own STUDY. In [`backlog.md`](../backlog.md).
- **qa-quickarm-interaction-revision** - the modifier-tap vocabulary rethink (chords are saturated) plus viewport pick-parent. In [`backlog.md`](../backlog.md).
