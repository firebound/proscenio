# Spec 032: Slot attachments

Fix slot placement and finish the slot/attachment panel.

## Scope

- **Fix slot Empty with a parented seed** - it lands wrong when the seed mesh already has a parent.
- **Fix slot Empty with an unapplied origin** - it lands at the object origin, not the geometry center.
- **Native UIList for the slots list**.
- **Clarify Path A vs Path B** affordance.
- **Warn when a slot has no parent bone**, with a fix button.
- **Keyframe the active attachment** - an authoring button.
- **Skin coordination** - named attachment sets across slots.

## Study

Surface read 2026-06-11 against `main`: the create operator (`operators/slot/create.py`), the attachment operators (`operators/slot/attachment.py`), the panel (`panels/slots.py`), the writer's slot track emission (`exporters/godot/writer/slot_animations.py`), the Godot consumption (`animation_builder.gd`), and the schema (`packages/models/src/proscenio_models/proscenio.py`).

### Surface notes

**The two placement bugs are one fix - confirmed.** Both live in the same Path B branch of the create operator (`create.py:79-85`). With a parented seed, the operator copies the seed's parent onto the new Empty and then assigns a world translation into the parent-local `empty.location` with no `matrix_parent_inverse` (`create.py:85`), so the offset compounds through the parent matrix. With an unapplied origin, the value assigned is also the wrong reference: `seed.matrix_world.to_translation()` is the object origin, not the visible geometry. One patch closes both - compute the world-space center of the selection's geometry (`bound_box` corners through `matrix_world`) and write it through `empty.matrix_world` after parenting, the same write-through pattern `parent_keep_world` (`core/bpy_helpers/_shared/parenting.py:15-28`) already applies to the attachments two lines below (`create.py:90-91`). Headless-testable: parented-seed and offset-origin fixtures asserting the Empty's world translation.

**Keyframe-active-attachment already has its export half shipped.** The writer projects `proscenio_slot_index` fcurves on the slot Empty into `slot_attachment` tracks (`slot_animations.py:14-22,85-90`), and the Godot importer expands them into per-attachment visibility tracks (`animation_builder.gd:79-84,129-133`). Nothing under `operators/slot/` writes a keyframe - `attachment.py` carries add-attachment and set-default only - so the only authoring path today is hand-creating a custom-property fcurve, deep Blender arcana for the format's standard part-swap mechanism. The missing piece is one bounded operator: set `proscenio_slot_index` to the chosen attachment's index, `keyframe_insert` on that data path, constant interpolation. No schema or importer change.

**Panel rows, verified open.** The slot list is per-row operator buttons, not `template_list` (`panels/slots.py:61-72`). The **Active Slot** subpanel prints a bare `bone: (unparented)` label with no warning or remedy (`panels/slots.py:113-116`). The create operator polls `context.scene is not None` (`create.py:60-62`), so `Create Slot` is always enabled with no hint about which of the two context-dependent behaviors will run. The unparented warn should reuse the predicate the export-correctness spec is fixing for the validator's slot-no-parent-bone false positive, not fork a second rule.

**Skins would be the first cross-app capability in this spec.** The schema `Slot` is name/attachments/bone/default (`proscenio.py:207-212`); no skins field exists anywhere. Two shapes per the backlog sketch: (a) additive - Blender-only authoring plus the writer emitting one generated visibility animation per skin over the existing slot_attachment machinery, zero schema and zero Godot change, but skins-as-animations is fragile at runtime since any later slot key in a playing animation overrides the "applied" skin; (b) first-class `skins[]` - a schema bump gated on the format-migration path (the schema-expressiveness spec) plus a Godot-side selector, the first piece of runtime API the importer-only Godot plugin would carry. Either shape is real coordination surface across three apps, and the written demand trigger (a character shipping two costume variants on one rig) has not fired in-project.

### Research notes

- **Spine skins** ([Skins - Spine User Guide](https://en.esotericsoftware.com/spine-skins), [spine-unity Mix and Match](http://en.esotericsoftware.com/spine-unity-mix-and-match), [4Enjoy: character customization in Spine](https://www.4enjoy.com/articles/character-customization-in-spine-how-does-it-work-skins-and-linked-mesh-tools/)): a core, heavily-adopted feature - outfit swaps and mix-and-match equipment built on skin placeholders under slots, with a dedicated runtime API; studios document whole customization pipelines on it. The demand class is real, and the feature leans on exactly the runtime layer Proscenio's importer-only Godot plugin deliberately does not have.
- **Slot attachment keyframing** ([Keys - Spine User Guide](http://en.esotericsoftware.com/spine-keys), [Spine forum: keyframing attachment visibility](http://esotericsoftware.com/forum/Keyframing-attachment-visibility-2607)): keying the slot's active attachment is the standard part-swap mechanism - a key button sits next to each slot in the tree, and blinks or frame-by-frame substitution are taught as keyed attachment swaps. A one-click "key the active attachment" affordance is baseline genre ergonomics on an already-shipped track type, not new capability.

### Assessment

Scores: flow-value (5 = core pipeline correctness/productivity), test-burden (5 = recurring manual GUI), bug-surface (5 = new modal/stateful surface), underuse-risk (5 = speculative).

| Item | Flow value | Test burden | Bug surface | Underuse risk | Verdict | Why |
| --- | --- | --- | --- | --- | --- | --- |
| Fix slot Empty with a parented seed | 4 | 2 | 1 | 2 | now | Blocking; the slot system's entry point lands wrong; one matrix fix shared with the row below |
| Fix slot Empty with an unapplied origin | 4 | 2 | 1 | 2 | now | Same patch: world geometry center written through `matrix_world` |
| Native UIList for the slots list | 2 | 3 | 3 | 3 | defer | Swaps working rows for a widget whose selection sync already cost a fix on the Skeleton panel (still needs-retest); consistency-only gain |
| Clarify Path A vs Path B | 3 | 1 | 1 | 2 | now | Draw-only hint naming which context produces which slot; pairs with the placement fix |
| Warn when a slot has no parent bone | 3 | 1 | 1 | 2 | now (warn only) | Label sharing the validator predicate; the `Parent to Bone` fix button is deferred (new bone-picker operator) |
| Keyframe the active attachment | 4 | 2 | 2 | 2 | now | Export half shipped and tested; the button closes the authoring gap on the format's standard swap mechanism |
| Skin coordination | 3 | 4 | 4 | 5 | gate | Real genre demand, zero in-project demand; three-app surface plus unresolved runtime semantics; trigger in TODO |

### Verdict summary

5 now, 1 defer (plus the fix-button half of the warn row deferred), 1 gate, 0 drop. The now set is two bugfix/polish PRs plus one bounded operator that completes an already-shipped track contract. Skins - the one genuinely new capability - waits for a real two-variant character; per-slot defaults plus the keyframe button cover everything a single-variant character needs today.
