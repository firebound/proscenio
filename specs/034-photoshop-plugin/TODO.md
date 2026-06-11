# Spec 034: Photoshop plugin - TODO

Sequenced from the verdicts in [STUDY.md](STUDY.md): one bugfix PR and one retest land now, six items wait behind written triggers, three Character-Animator and UI lifts are pruned.

## Now

### PR 1: make the advanced-fields form able to clear a set tag

- [x] Carry cleared keys explicitly out of `computeChanges` in [tag-form.ts](../../apps/photoshop/src/lib/tag-form.ts) - the backlog sketch is a `{ set, clear }` return shape - replacing the `delete changes[key]` that drops the clear signal (an `exactOptionalPropertyTypes` workaround) before `applyTagChanges` in [tag-writer.ts](../../apps/photoshop/src/lib/tag-writer.ts) can delete the tag.
- [x] Update the Apply path in [Details.tsx](../../apps/photoshop/src/panels/sections/tags/Details.tsx) so a clears-only edit fires the rename - the `Object.keys(changes).length > 0` gate swallows it today while `Apply` reads enabled.
- [x] Extend [tag-form.test.ts](../../apps/photoshop/uxp-plugin-tests/tag-form.test.ts) with the clear cases (`folder`, `path`, `scale`, `origin`, name pattern emptied; origin marker unchecked) plus one round-trip asserting the bracket actually leaves the layer name.
- [x] Docs rider: state the `[mesh]` vs `[polygon]` downstream equivalence in the tag table of the [advanced Photoshop guide](../../docs/00-guides/01-advanced/01-photoshop.md); the deformation branch itself stays gated below.

### Retest: waist 1px drift through the UXP path

- [ ] Re-measure the `waist` size (Blender manifest 255x173 vs 255x172 on the JSX-era re-export) in the cross-spec verification GUI session (see [EXECUTION_MAP.md](../EXECUTION_MAP.md), Verification session) - the UXP png-writer trims with `Document.trim(TRANSPARENT)`, a different bbox engine than the JSX `layer.bounds` read the drift was logged against.
- [ ] On a persisting drift: align rounding (round-half-up on both sides) or re-document the waiver with the fresh number; on a match: close the backlog row.

## Deferred

Gate items; each lands when its trigger fires.

- **Nested [merge] warning** - trigger: an artist reports a sub-layer inside `[merge]` vanishing without realising the collapse was deliberate; then surface a `merge-nested` info entry on the Validate tab.
- **[name:pre*suf] rewrite** - trigger: a fixture or user workflow actually needs prefix/suffix templating on a group; design the rewrite order against it (`joinName` interaction, `[path:NAME]` precedence) - until then the parsed tag stays a reserved slot, as it is in PhotoshopToSpine.
- **kind "mesh" downstream branch** - trigger: mesh-deformation work ships, and the Blender importer branches on the stamped kind (deformable treatment only for `kind: "mesh"`); the PR 1 docs rider covers the equivalence meanwhile.
- **[isolated] warp-independent flag** - trigger: a per-layer pose channel concept lands (authoring panel or continuous-UV-animation work); the tag name stays reserved, nothing parses it today.
- **Stable layer identity** - trigger: a wrong-PNG export report from duplicate sibling names, or a feature that must address layers by stable handle; implementation hint on record: `{ name, index }[]` in `PngWrite.layerPath`.
- **Spectrum shadow-DOM measurement** - trigger: a lag report opening the Tags tab on a >100-layer PSD; the first response swaps the hot widgets to plain HTML (precedent `5c6bef2`), measuring only if the swap is contested.

## Dropped

- **[slice] 9-slice tag** - 9-slice is scalable-UI furniture in every engine doc, the pipeline ships rigged characters, and Godot configures nine-patch insets engine-side on a plain texture - the tag would round-trip editor settings through parser, manifest, importer, and builder for no authoring win.
- **Head-turner view groups** - Character Animator face puppetry bound to a face-rig template and a head-turn runtime Proscenio does not have; slot attachments already express view swapping in this model.
- **Pseudo-keyword auto-tagging** - implicit match-inside-name tagging (Character Animator matches "Ah" inside "My Ah") collides with arbitrary artist naming and contradicts the locked explicit-bracket design that already shipped.
