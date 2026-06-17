# Spec 045: Skeleton, Quick Armature and Animation fixes - TODO

From the assessment in [STUDY.md](STUDY.md): 7 rows land now (implemented in one PR), one stays gated. The Esc repro is a manual GUI session (a headless harness cannot pump the modal); the code read already confirms the data behaviour, so the decision was made **labels-only** (see the STUDY decision note). The destructive-cancel stays gated.

## Now (implemented - one PR)

### Animation panel uses the picked armature (bug)

- [x] `PROSCENIO_OT_set_active_action` ([`selection.py`](../../apps/blender/operators/selection.py)) now resolves the target via `resolve_skeleton_target(context)` instead of scanning `context.scene.objects`; `report_warn` + cancel when the picker is empty ("no armature picked - pick one in the Skeleton panel"). Multi-armature heuristic dropped; `bl_description` updated off "the first armature in the scene".
- [x] Headless tests in `tests/operators/test_set_active_action.py`: assigns to the picked armature; warns + cancels when the picker is empty; ignores a non-picked second armature.

### Quick Armature + Skeleton chrome

- [x] Dynamic confirm / exit chords in `emit_chord_layout` ([`_status_bar.py`](../../apps/blender/operators/armature/_status_bar.py)): Return relabeled "finish"; the Esc chord reads "cancel (discards empty rig)" while `_last_bone_name` is empty, "exit (keeps bones)" once a bone is authored. Labels-only - no destructive branch (gated).
- [x] `PROSCENIO_UL_bones.draw_item` ([`skeleton.py`](../../apps/blender/panels/skeleton.py)) flags "disconnected" when `item.parent is not None and not use_connect`.
- [x] Skeleton header shows "Skeleton: <name>" via `draw_header` (bl_label blank, since Blender renders draw_header left of bl_label here so the whole title lives in one place). A custom draw_header label has no native truncation, so a width gate drops the `<name>` (keeping the short "Skeleton") below `_SKELETON_HEADER_NAME_MIN_WIDTH` rather than letting the long title vanish. See Review feedback.
- [x] `PROSCENIO_PT_armature` `bl_label` renamed "Armature" -> "Active Armature" (`bl_idname` / `bl_parent_id` untouched); the in-body label trimmed to the bone count.
- [x] Removed the 3D-viewport-header hint surface from [`quick_armature.py`](../../apps/blender/operators/armature/quick_armature.py) (all six references: ClassVar, double-invoke guard, register append, `_unregister_handlers` teardown, `_sweep_orphan_handlers` sweep, and `_draw_view3d_header_quick_armature`). The status bar keeps the chords.
- [ ] GUI smoke (manual - the modal/panels do not render headless): `BL-SKEL-*`, `BL-ANIM-01..03`, `BL-SKEL-QUICKARM-01` - dynamic Esc/finish hints, disconnected flag, header name, renamed subpanel, and the viewport header no longer showing the chord strip (no leaked handler after reload).

## Review feedback (2026-06-17, folded into this PR)

- [x] Skeleton header "Skeleton: <name>" - took three iterations. (1) `bl_label="Skeleton"` + `draw_header ": name"` rendered reversed (": name Skeleton") because Blender draws draw_header LEFT of bl_label here. (2) `bl_label=""` + full title in draw_header read in order but the whole label vanished when narrow (custom draw_header labels have no native truncation). (3) Final: keep `bl_label=""` + full title in draw_header, and width-gate the name - below `_SKELETON_HEADER_NAME_MIN_WIDTH` draw_header drops to the short "Skeleton" (which survives narrow widths), restoring "Skeleton: <name>" when wide. This matches the user's "Skeleton: stays, name disappears when small" intent; a true per-part native truncation is not possible (only bl_label truncates, and it is forced right of draw_header).
- [x] **Cross-panel target convention.** Panels that act on a selection owned by another panel now declare it uniformly: `draw_picker_readout` renamed to `draw_target_readout` and reads "Target: Skeleton <name>" (was "Picker: <name>"). The owner panel (Skeleton) is excluded - it holds the picker widget. Applied to Mesh Generation, Weight Paint, and **Animation** (which had no read-out before).
- [x] Weight Paint Bind dropped its own "Target:" line - the Weight Paint parent read-out already covers it.
- [x] Bone list names were centered (UIList operator-button centering, same as the Outliner); left-aligned via a split + LEFT sub-row so the depth indent is visible.
- [x] Narrow N-panel: the header status + `?` icons overlapped the title. `draw_subpanel_header` now drops the icons below `_HEADER_ICONS_MIN_WIDTH` (region width), so headers shed their extras and the native `bl_label` titles truncate like Blender's own. Threshold is GUI-tunable (`BL-CHROME-09`). (The Skeleton header vanishing was fixed separately by reverting to a native `bl_label` - see the bullet above.)

## Gated

- **Destructive Esc cancel** - Esc deletes the whole auto-created `Proscenio.QuickRig` even when it has bones (never the user-picked target). Real bug surface (a misfired Esc discards a session). Trigger: a GUI repro showing users expect Esc to throw the rig away; otherwise the labels-only outcome stands.

## Out of scope (own backlog items)

- **qa-rotation-mode** - Euler-Y vs quaternion authoring choice + safe swap; the safe swap can break animations silently, so it carries its own STUDY. In [`backlog.md`](../backlog.md).
- **qa-quickarm-interaction-revision** - the modifier-tap vocabulary rethink (chords are saturated) plus viewport pick-parent. In [`backlog.md`](../backlog.md).
