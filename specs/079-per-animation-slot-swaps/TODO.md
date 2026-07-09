# Spec 079: Per-animation slot swaps - TODO

Swap the authoring model from the `proscenio_slot_index` idprop to direct visibility keyframes on the attachment meshes. The exported `slot_attachment` track, the `.proscenio` schema, and the Godot animation builder are unchanged; the one Godot edit is `_effective_default`'s resting-blank path. Sequenced so main never regresses: PR 1 is the atomic cut (fixtures + operator + writer + cleanup land together, since removing the index reader while the operator still writes an index would break export mid-merge). PR 2 is UI + validation polish. Docs land direct on main.

## PR 1 - Visibility swap model (atomic cut)

Fixtures (author the new model so the writer has something to read):
- [ ] `packages/fixtures/slot_swap/build_blend.py`: replace the `proscenio_slot_index` 0->1->0 keys ([build_blend.py:327](../../packages/fixtures/slot_swap/build_blend.py)) with `hide_render` + `hide_viewport` keyframes on the attachments (show club / show torch / show club), CONSTANT interp.
- [ ] `packages/fixtures/slot_cycle/build_blend.py`: replace the `cycle` index keys ([build_blend.py:189](../../packages/fixtures/slot_cycle/build_blend.py)) with per-attachment visibility keyframes.

Operator (`apps/blender/operators/slot/attachment.py`):
- [ ] Rewrite `keyframe_slot_attachment`: "show only this attachment at the current frame" keys `hide_viewport` + `hide_render` on every sibling (chosen `False`, rest `True`) with CONSTANT interp, instead of writing `proscenio_slot_index`.
- [ ] Add the "(none)" path: key all siblings hidden at the current frame.
- [ ] Resolve the target animation (R3/D3): default to the active rig action's name; on Blender 4.4+ bind the mesh's `animation_data.action` + `action_slot` into that animation's action datablock; on 4.2 use a same-named separate action per mesh. Accept an override animation name.

Writer (`apps/blender/exporters/godot/writer/slot_animations.py`):
- [ ] Read visibility per attachment mesh scoped to that mesh's own `animation_data` - its `action_slot` channelbag on 4.4+, its dedicated action on 4.2 - never the flattened `action_fcurves` (R4: the flattened view double-counts across meshes sharing a slotted action).
- [ ] Collapse authored visibility per frame into one `slot_attachment` key (R2): 0 visible -> "none" key (attachment naming no child); 1 visible -> that attachment; 2+ visible -> first by child sort order.
- [ ] Keep the `slot_attachment` track shape and `merge_slot_animations_into` by name; drop the `proscenio_slot_index` reader.

Cleanup (R5):
- [ ] Remove `PROSCENIO_SLOT_ATTACHMENT_ORDER` and the append-only merge from [cp_keys.py](../../apps/blender/core/_shared/cp_keys.py), [slot_animations.py](../../apps/blender/exporters/godot/writer/slot_animations.py), [attachment.py](../../apps/blender/operators/slot/attachment.py).
- [ ] Close the gated `keyframe-slot-index-drift` item (spec 076 / [gated.md](../gated.md)) - drift cannot occur once swaps key by object identity.

Converter (R3):
- [ ] One-shot operator: convert an Empty's `proscenio_slot_index` track into visibility keyframes on its attachments, so the maintainer's in-flight `firebound_guy` migrates without re-authoring.

Tests / goldens:
- [ ] Regenerate `slot_swap` / `slot_cycle` goldens on the new model.
- [ ] Byte-identical golden pair (R4 invariant): the same character authored the 4.2 way (per-mesh actions) and the 4.4 way (one slotted action) exports identical `.proscenio`.
- [ ] Unit: the collapse rule (0 / 1 / 2+ visible), the "none" key, and per-mesh scoped reading (a slotted action holding two meshes does not cross-read).

## PR 2 - Panel, validation, Godot resting-none

- [ ] `apps/blender/panels/slots.py` (Active Slot): relabel the keyframe button to its show-only semantics; add a "(none) / hide all" keyable row; add the target-animation override dropdown (D3).
- [ ] `apps/blender/panels/animation.py`: list exported animations by name, deduped across rig + visibility datablocks (D2); make `set_active_action` refuse to assign a visibility-only action to the armature.
- [ ] Export validator (`apps/blender/core/validation/checks/slots.py`): warn (lazy + inline) when 2+ attachments are visible in one slot at a frame (R2).
- [ ] `apps/godot/addons/proscenio/builders/slot_builder.gd`: give `_effective_default` an explicit-blank path so a slot can rest with nothing shown, not only hide mid-clip (D4 resting-none).
- [ ] Tests: panel dedup + assign-refusal, the overlap validator warning, the Godot blank-default resting state.

## Docs (direct to main, no PR)

- [ ] `docs/02-tools/blender-addon/03-slots-{en,pt}.md`: rewrite the swap-authoring section for visibility keyframes (show-only / hide-all), the native viewport preview, per-animation swaps following the active animation, and drop every `slot_index` mention.

## Gates / verification

- Blender: `run_operator_tests.py` (172) + `run_tests.py` goldens (8/8) on `Blender 5.1 --background --factory-startup`; the repo-root `uv run pytest tests/` + per-package suites (see the full gate set - a core/ move breaks the repo-root run silently).
- Godot: the `godot_std` `*_console.exe` headless builder tests (`test_builder_guards.gd`, `test_slot_anchor.gd`, the golden-scene walk).
- Verify the 4.2/4.4 byte-identical export on both a 4.2 and a 5.1 build (the multi-version matrix; 5.x-saved fixtures do not open in 4.2, so build the 4.2-shape fixture headless there).
- Code rides a branch + PR; the docs bullet commits direct to main.
